/**
 * @file main.c
 * @brief Multi-box Filament Drybox - RP2350 (Pico 2) Telemetry Test Firmware
 * @author Senior Embedded Engineer
 * 
 * Tento modul zajišťuje simulaci senzorických dat sušičky filamentu,
 * jejich formátování do standardního JSON protokolu a odesílání přes USB CDC (stdio).
 * Podporuje spuštění a zastavení sušení:
 * 1. Palubním tlačítkem BOOTSEL přímo na desce Pico 2
 * 2. Externím tlačítkem na USER_BUTTON_PIN (GPIO 15 proti GND s pull-up)
 * 3. Příkazy ze sériové linky / webového rozhraní (MQTT bridge)
 */

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/time.h"
#include "hardware/gpio.h"
#include "hardware/sync.h"
#include "hardware/structs/io_qspi.h"
#include "hardware/structs/sio.h"

/* ========================================================================== */
/* Konfigurace pinů a parametrů                                               */
/* ========================================================================== */
#define TELEMETRY_INTERVAL_MS   1000UL      /**< Perioda odesílání telemetrie v ms */
#define JSON_BUFFER_SIZE        160         /**< Velikost bufferu pro JSON řetězec */
#define DRYBOX_ID               1           /**< Identifikátor sušicího slotu/boxu */

/* Uživatelské tlačítko (externí tlačítko mezi GPIO 15 a GND) */
#define USER_BUTTON_PIN         15          /**< Externí GPIO tlačítko s pull-up */

/* Parametry prostředí a sušení */
#define AMBIENT_TEMP_C          22.5f       /**< Pokojová teplota komory (°C) */
#define AMBIENT_HUMIDITY_PCT    58.0f       /**< Okolní relativní vlhkost (%) */
#define SIM_TARGET_TEMP_C       55.0f       /**< Cílová teplota sušení (°C) */
#define SIM_MIN_HUMIDITY_PCT    15.0f       /**< Minimální vlhkost při sušení (%) */
#define SIM_INITIAL_WEIGHT_G    450.25f     /**< Výchozí hmotnost cívky (g) */

/* ========================================================================== */
/* Datové struktury                                                           */
/* ========================================================================== */

typedef enum {
    DRY_STATE_STANDBY       = 0,            /**< Nečinný / vypnuto (idle) */
    DRY_STATE_HEATING       = 1,            /**< Aktivní ohřev / sušení (drying) */
    DRY_STATE_TARGET_REACHED= 2,            /**< Dosažena cílová teplota, udržování */
    DRY_STATE_ERROR         = 3             /**< Chybový stav */
} drybox_state_t;

typedef struct {
    uint32_t        id;                     /**< ID boxu */
    float           weight;                 /**< Hmotnost cívky (g) */
    float           temp;                   /**< Teplota komory (°C) */
    float           hum;                    /**< Relativní vlhkost (%) */
    drybox_state_t  dry_state;              /**< Stav procesu sušení */
} drybox_telemetry_t;

/* ========================================================================== */
/* Obsluha tlačítek (BOOTSEL na RP2350 + Externí GPIO)                        */
/* ========================================================================== */

/**
 * @brief Bezpečné čtení stavu palubního tlačítka BOOTSEL na RP2350 za běhu
 */
static bool __no_inline_not_in_flash_func(read_bootsel_button)(void) {
    const uint CS_PIN_INDEX = 1;
    uint32_t flags = save_and_disable_interrupts();

    // Na RP2350 odpojíme output driver QSPI CS pinu pro čtení vstupu
    hw_write_masked(&io_qspi_hw->io[CS_PIN_INDEX].ctrl,
                    IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_VALUE_DISABLE << IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_LSB,
                    IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_BITS);

    for (volatile int i = 0; i < 1000; ++i);

    // Čtení stavu vstupu z registru status (RP2350 bit INFROMPAD)
    bool button_state = !(io_qspi_hw->io[CS_PIN_INDEX].status & IO_QSPI_GPIO_QSPI_SS_STATUS_INFROMPAD_BITS);

    // Obnovení normálního režimu driveru
    hw_write_masked(&io_qspi_hw->io[CS_PIN_INDEX].ctrl,
                    IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_VALUE_NORMAL << IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_LSB,
                    IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_BITS);

    restore_interrupts(flags);
    return button_state;
}

/**
 * @brief Inicializace tlačítek a indikační LED
 */
static void hw_controls_init(void) {
    // LED indikace stavu (GPIO 25 na Pico 2)
#ifdef PICO_DEFAULT_LED_PIN
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
    gpio_put(PICO_DEFAULT_LED_PIN, 1); // Zapnuto při startu (sušení aktivní)
#endif

    // Uživatelské tlačítko na USER_BUTTON_PIN (GPIO 15)
    gpio_init(USER_BUTTON_PIN);
    gpio_set_dir(USER_BUTTON_PIN, GPIO_IN);
    gpio_pull_up(USER_BUTTON_PIN);
}

/**
 * @brief Kontrola požadavku na změnu stavu (tlačítko nebo sériový příkaz)
 * @return true pokud došlo k požadavku na změnu stavu sušení
 */
static bool check_toggle_request(void) {
    static bool prev_btn_pressed = false;
    static uint64_t last_btn_time_us = 0;
    uint64_t now = time_us_64();

    // 1. Kontrola fyzického tlačítka (BOOTSEL nebo externí GPIO 15)
    bool raw_pressed = read_bootsel_button() || (!gpio_get(USER_BUTTON_PIN));
    if (raw_pressed != prev_btn_pressed && (now - last_btn_time_us) > 150000ULL) {
        last_btn_time_us = now;
        prev_btn_pressed = raw_pressed;
        if (raw_pressed) {
            return true;
        }
    } else if (!raw_pressed) {
        prev_btn_pressed = false;
    }

    // 2. Kontrola příkazu ze sériové linky (příkaz z webu / PC)
    int c = getchar_timeout_us(0);
    if (c >= 0) {
        // Vyprázdnění zbytku bufferu (např. \r, \n), aby se příkaz nevyhodnotil 2x
        while (getchar_timeout_us(0) >= 0);

        if (c == 's' || c == 'S' || c == ' ' || c == 't' || c == 'T') {
            return true;
        }
    }

    return false;
}

/* ========================================================================== */
/* Simulace senzorů a fyzikálního chování                                     */
/* ========================================================================== */

static void sim_sensors_init(drybox_telemetry_t *data) {
    data->id = DRYBOX_ID;
    data->weight = SIM_INITIAL_WEIGHT_G;
    data->temp = 22.5f;
    data->hum = 58.0f;
    data->dry_state = DRY_STATE_HEATING;
}

static void sim_sensors_update(drybox_telemetry_t *data, float dt_s) {
    if (data->dry_state == DRY_STATE_STANDBY) {
        /* Vypnuto / Zastaveno: Komora postupně chladne k okolní teplotě */
        if (data->temp > AMBIENT_TEMP_C) {
            data->temp -= (data->temp - AMBIENT_TEMP_C) * (0.05f * dt_s);
        }
        /* Vlhkost se pomalu vrací k okolní pokojové vlhkosti */
        if (data->hum < AMBIENT_HUMIDITY_PCT) {
            data->hum += (AMBIENT_HUMIDITY_PCT - data->hum) * (0.03f * dt_s);
        }
        // Hmotnost se nemění
        return;
    }

    /* 1. Aktivní ohřev */
    float temp_diff = SIM_TARGET_TEMP_C - data->temp;
    if (temp_diff > 0.05f) {
        data->temp += temp_diff * (0.04f * dt_s);
        data->dry_state = DRY_STATE_HEATING;
    } else {
        data->temp = SIM_TARGET_TEMP_C + (sinf(time_us_64() / 2000000.0f) * 0.2f);
        data->dry_state = DRY_STATE_TARGET_REACHED;
    }

    /* 2. Pokles vlhkosti vlivem teploty */
    if (data->hum > SIM_MIN_HUMIDITY_PCT) {
        float hum_decay = (data->temp / SIM_TARGET_TEMP_C) * 0.35f * dt_s;
        data->hum -= hum_decay;
        if (data->hum < SIM_MIN_HUMIDITY_PCT) {
            data->hum = SIM_MIN_HUMIDITY_PCT;
        }
    } else {
        data->hum = SIM_MIN_HUMIDITY_PCT + (cosf(time_us_64() / 3000000.0f) * 0.15f);
    }

    /* 3. Úbytek hmotnosti evaporací vlhkosti */
    if (data->weight > 441.50f && data->temp > 35.0f) {
        data->weight -= 0.004f * dt_s;
    }
}

/* ========================================================================== */
/* Serializace a Transportní vrstva                                           */
/* ========================================================================== */

static bool drybox_serialize_json(const drybox_telemetry_t *data, char *out_buf, size_t max_len) {
    if (!data || !out_buf || max_len == 0) return false;

    const char *status_str = (data->dry_state == DRY_STATE_STANDBY) ? "idle" : "drying";

    int written = snprintf(
        out_buf,
        max_len,
        "{\"id\": %lu, \"weight\": %.2f, \"temp\": %.1f, \"hum\": %.1f, \"dry_state\": %d, \"status\": \"%s\", \"type\": \"PLA\"}",
        (unsigned long)data->id,
        data->weight,
        data->temp,
        data->hum,
        (int)data->dry_state,
        status_str
    );

    return (written > 0 && (size_t)written < max_len);
}

static void drybox_transport_publish(const char *json_payload) {
    printf("%s\n", json_payload);
}

/* ========================================================================== */
/* Hlavní program (Main Entry Point)                                          */
/* ========================================================================== */

int main(void) {
    stdio_init_all();
    hw_controls_init();

    // Čekání na USB CDC (max 5 sekund)
    uint32_t wait_start = to_ms_since_boot(get_absolute_time());
    while (!stdio_usb_connected()) {
        if ((to_ms_since_boot(get_absolute_time()) - wait_start) > 5000) break;
        sleep_ms(50);
    }

    drybox_telemetry_t telemetry;
    sim_sensors_init(&telemetry);

    char json_buffer[JSON_BUFFER_SIZE];
    uint64_t last_telemetry_time_us = time_us_64();
    uint64_t last_sim_step_time_us = time_us_64();

    while (true) {
        uint64_t current_time_us = time_us_64();

        // 1. Obsluha stisku tlačítka nebo příkazu z webu
        if (check_toggle_request()) {
            if (telemetry.dry_state == DRY_STATE_STANDBY) {
                telemetry.dry_state = DRY_STATE_HEATING;
#ifdef PICO_DEFAULT_LED_PIN
                gpio_put(PICO_DEFAULT_LED_PIN, 1);
#endif
            } else {
                telemetry.dry_state = DRY_STATE_STANDBY;
#ifdef PICO_DEFAULT_LED_PIN
                gpio_put(PICO_DEFAULT_LED_PIN, 0);
#endif
            }

            // Okamžité odeslání telemetrie s novým stavem
            if (drybox_serialize_json(&telemetry, json_buffer, sizeof(json_buffer))) {
                drybox_transport_publish(json_buffer);
            }
        }

        // 2. Fyzikální model sušičky (každých 100 ms)
        if ((current_time_us - last_sim_step_time_us) >= 100000ULL) {
            float dt_s = (float)(current_time_us - last_sim_step_time_us) / 1000000.0f;
            sim_sensors_update(&telemetry, dt_s);
            last_sim_step_time_us = current_time_us;
        }

        // 3. Pravidelná periodická telemetrie (každou sekundu)
        if ((current_time_us - last_telemetry_time_us) >= (TELEMETRY_INTERVAL_MS * 1000ULL)) {
            last_telemetry_time_us = current_time_us;

            if (drybox_serialize_json(&telemetry, json_buffer, sizeof(json_buffer))) {
                drybox_transport_publish(json_buffer);
            }
        }

        tight_loop_contents();
    }

    return 0;
}
