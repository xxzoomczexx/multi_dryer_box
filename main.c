/**
 * @file main.c
 * @brief Multi-box Filament Drybox - Master Node RP2350 (Pico 2 W) Firmware
 * @author Senior Embedded Engineer
 * 
 * Tento kód běží na Raspberry Pi Pico 2 W (RP2350 + CYW43439).
 * Připojuje se k Wi-Fi síti, provádí DNS překlad MQTT brokeru a přes lwIP stack
 * odesílá telemetrii sušičky v JSON formátu přímo na MQTT broker.
 * Zároveň naslouchá řídicím příkazům z webového rozhraní.
 */

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/time.h"
#include "pico/cyw43_arch.h"
#include "hardware/gpio.h"
#include "hardware/sync.h"
#include "hardware/structs/io_qspi.h"
#include "hardware/structs/sio.h"

#include "lwip/apps/mqtt.h"
#include "lwip/dns.h"
#include "lwip/dhcp.h"
#include "lwip/ip_addr.h"

#include "config.h"

/* ========================================================================== */
/* Konfigurace pinů a parametrů                                               */
/* ========================================================================== */
#define TELEMETRY_INTERVAL_MS   1000UL      /**< Perioda odesílání telemetrie v ms */
#define JSON_BUFFER_SIZE        200         /**< Velikost bufferu pro JSON řetězec */
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
/* Globální proměnné a stav síťového zásobníku                                */
/* ========================================================================== */

static drybox_telemetry_t g_telemetry;
static mqtt_client_t *g_mqtt_client = NULL;
static ip_addr_t g_broker_ip;
static bool g_wifi_connected = false;
static bool g_dns_resolved = false;
static bool g_mqtt_connected = false;
static char g_material_type[16] = "PLA";
static char g_incoming_topic[128];

/* Prototypy pro přepínání stavu */
static void toggle_drying_state(void);

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
    // Uživatelské tlačítko na USER_BUTTON_PIN (GPIO 15)
    gpio_init(USER_BUTTON_PIN);
    gpio_set_dir(USER_BUTTON_PIN, GPIO_IN);
    gpio_pull_up(USER_BUTTON_PIN);
}

/**
 * @brief Kontrola požadavku na změnu stavu tlačítek nebo USB sériové linky
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

    // 2. Kontrola příkazu ze sériové linky (USB CDC)
    int c = getchar_timeout_us(0);
    if (c >= 0) {
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
        /* Vypnuto / Zastaveno: Komora chladne */
        if (data->temp > AMBIENT_TEMP_C) {
            data->temp -= (data->temp - AMBIENT_TEMP_C) * (0.05f * dt_s);
        }
        if (data->hum < AMBIENT_HUMIDITY_PCT) {
            data->hum += (AMBIENT_HUMIDITY_PCT - data->hum) * (0.03f * dt_s);
        }
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

    /* 2. Pokles vlhkosti */
    if (data->hum > SIM_MIN_HUMIDITY_PCT) {
        float hum_decay = (data->temp / SIM_TARGET_TEMP_C) * 0.35f * dt_s;
        data->hum -= hum_decay;
        if (data->hum < SIM_MIN_HUMIDITY_PCT) {
            data->hum = SIM_MIN_HUMIDITY_PCT;
        }
    } else {
        data->hum = SIM_MIN_HUMIDITY_PCT + (cosf(time_us_64() / 3000000.0f) * 0.15f);
    }

    /* 3. Úbytek hmotnosti evaporací */
    if (data->weight > 441.50f && data->temp > 35.0f) {
        data->weight -= 0.004f * dt_s;
    }
}

static void toggle_drying_state(void) {
    if (g_telemetry.dry_state == DRY_STATE_STANDBY) {
        g_telemetry.dry_state = DRY_STATE_HEATING;
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
        printf("[STAV] Sušení SPUŠTĚNO.\n");
    } else {
        g_telemetry.dry_state = DRY_STATE_STANDBY;
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
        printf("[STAV] Sušení ZASTAVENO.\n");
    }
}

/* ========================================================================== */
/* Serializace a Publikace Telemetrie                                         */
/* ========================================================================== */

static bool drybox_serialize_json(const drybox_telemetry_t *data, char *out_buf, size_t max_len) {
    if (!data || !out_buf || max_len == 0) return false;

    const char *status_str = (data->dry_state == DRY_STATE_STANDBY) ? "idle" : "drying";

    int written = snprintf(
        out_buf,
        max_len,
        "{\"id\": %lu, \"weight\": %.2f, \"temp\": %.1f, \"hum\": %.1f, \"dry_state\": %d, \"status\": \"%s\", \"type\": \"%s\"}",
        (unsigned long)data->id,
        data->weight,
        data->temp,
        data->hum,
        (int)data->dry_state,
        status_str,
        g_material_type
    );

    return (written > 0 && (size_t)written < max_len);
}

static void mqtt_pub_request_cb(void *arg, err_t err) {
    if (err == ERR_OK) {
        // Zpráva byla doručena
    } else {
        printf("[MQTT CHYBA] Publikace selhala, err: %d\n", err);
    }
}

static void drybox_transport_publish(const char *json_payload) {
    // 1. Výpis na USB sériovou linku
    printf("[TELEMETRY] %s\n", json_payload);

    // 2. Publikace přes MQTT rozhraní na broker
    if (g_mqtt_client && mqtt_client_is_connected(g_mqtt_client)) {
        char status_topic[64];
        snprintf(status_topic, sizeof(status_topic), "drybox/status/%lu", (unsigned long)g_telemetry.id);

        cyw43_arch_lwip_begin();
        err_t err = mqtt_publish(
            g_mqtt_client,
            status_topic,
            json_payload,
            strlen(json_payload),
            0, // QoS 0
            0, // Retain 0
            mqtt_pub_request_cb,
            NULL
        );
        cyw43_arch_lwip_end();

        if (err != ERR_OK) {
            printf("[MQTT CHYBA] Chyba při volání mqtt_publish: %d\n", err);
        }
    }
}

/* ========================================================================== */
/* MQTT Callbacky a Komunikace (lwIP MQTT Stack)                               */
/* ========================================================================== */

static void mqtt_incoming_publish_cb(void *arg, const char *topic, u32_t tot_len) {
    snprintf(g_incoming_topic, sizeof(g_incoming_topic), "%s", topic);
}

static void mqtt_incoming_data_cb(void *arg, const u8_t *data, u16_t len, u8_t flags) {
    char payload_str[256];
    if (len >= sizeof(payload_str)) len = sizeof(payload_str) - 1;
    memcpy(payload_str, data, len);
    payload_str[len] = '\0';

    printf("[MQTT IN] Topic: %s | Payload: %s\n", g_incoming_topic, payload_str);

    // Zpracování příkazů z webu
    if (strstr(payload_str, "\"cmd\": \"stop\"") || strstr(payload_str, "\"cmd\":\"stop\"") ||
        strstr(payload_str, "\"cmd\": \"toggle\"") || strstr(payload_str, "\"cmd\":\"toggle\"")) {
        printf("[MQTT CMD] Přijat příkaz k zastavení/přepnutí sušení!\n");
        toggle_drying_state();
    }

    // Změna typu materiálu z webu
    char *mat_ptr = strstr(payload_str, "\"type\":");
    if (mat_ptr) {
        char mat_val[16] = {0};
        if (sscanf(mat_ptr, "\"type\": \"%15[^\"]\"", mat_val) == 1 ||
            sscanf(mat_ptr, "\"type\":\"%15[^\"]\"", mat_val) == 1) {
            strncpy(g_material_type, mat_val, sizeof(g_material_type) - 1);
            printf("[MQTT CMD] Nastaven nový typ materiálu: %s\n", g_material_type);
        }
    }
}

static void mqtt_sub_request_cb(void *arg, err_t err) {
    if (err == ERR_OK) {
        printf("[MQTT] Úspěšně přihlášeno k odběru topicu: %s\n", MQTT_TOPIC_CMD);
    } else {
        printf("[MQTT CHYBA] Přihlášení k topicu %s selhalo (%d)\n", MQTT_TOPIC_CMD, err);
    }
}

static void mqtt_connection_cb(mqtt_client_t *client, void *arg, mqtt_connection_status_t status) {
    if (status == MQTT_CONNECT_ACCEPTED) {
        printf("[MQTT] Úspěšně připojeno k brokeru!\n");
        g_mqtt_connected = true;

        // Nastavení callbacků pro příchozí zprávy
        mqtt_set_inpub_callback(client, mqtt_incoming_publish_cb, mqtt_incoming_data_cb, NULL);

        // Odběr řídicích příkazů z webu
        mqtt_subscribe(client, MQTT_TOPIC_CMD, 0, mqtt_sub_request_cb, NULL);
    } else {
        printf("[MQTT CHYBA] Připojení k brokeru odmítnuto, kód: %d\n", status);
        g_mqtt_connected = false;
        if (g_mqtt_client) {
            mqtt_client_free(g_mqtt_client);
            g_mqtt_client = NULL;
        }
    }
}

static void dns_found_cb(const char *name, const ip_addr_t *ipaddr, void *arg) {
    if (ipaddr) {
        g_broker_ip = *ipaddr;
        g_dns_resolved = true;
        printf("[DNS] Broker '%s' přeložen na IP: %s\n", name, ipaddr_ntoa(ipaddr));
    } else {
        printf("[DNS CHYBA] Nelze přeložit doménové jméno brokeru '%s'\n", name);
    }
}

/* ========================================================================== */
/* Inicializace Wi-Fi a Sítě                                                  */
/* ========================================================================== */

static bool wifi_init_and_connect(void) {
    printf("[WIFI] Inicializace Wi-Fi modulu CYW43439 (CZ kód země)...\n");
    if (cyw43_arch_init_with_country(CYW43_COUNTRY('C', 'Z', 0))) {
        printf("[WIFI CHYBA] Nelze inicializovat cyw43_arch!\n");
        return false;
    }

    cyw43_arch_enable_sta_mode();
    cyw43_wifi_pm(&cyw43_state, CYW43_NO_POWERSAVE_MODE);
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);

    uint8_t mac[6];
    cyw43_wifi_get_mac(&cyw43_state, CYW43_ITF_STA, mac);
    printf("[WIFI] MAC adresa vašeho Pico W: %02X:%02X:%02X:%02X:%02X:%02X\n",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

    // Automatické přiřazení unikátního ID sušicího boxu podle HW MAC adresy (1 až 8)
    g_telemetry.id = (mac[5] % 8) + 1;
    printf("[SYSTEM] Automaticky generované ID Boxu z HW: %lu\n", (unsigned long)g_telemetry.id);

    printf("[WIFI] Připojování k AP: '%s' ...\n", WIFI_SSID);

    int req_res = -1;
    for (int retry = 0; retry < 3; retry++) {
        if (retry > 0) {
            printf("[WIFI] Opakuji pokus o připojení k Wi-Fi (%d/3)...\n", retry + 1);
            sleep_ms(2000);
        }
        req_res = cyw43_arch_wifi_connect_timeout_ms(
            WIFI_SSID,
            WIFI_PASSWORD,
            CYW43_AUTH_WPA2_AES_PSK,
            30000
        );
        if (req_res == 0) break;
    }

    struct netif *netif = &cyw43_state.netif[CYW43_ITF_STA];
    int link_status = cyw43_tcpip_link_status(&cyw43_state, CYW43_ITF_STA);

    // Pokud je Wi-Fi fyzicky spojená (JOIN/UP), nastartujeme / vyčkáme na DHCP vyjednání IP
    if (netif_ip4_addr(netif)->addr == 0 && (link_status == CYW43_LINK_JOIN || link_status == CYW43_LINK_UP)) {
        printf("[WIFI] Wi-Fi spojitost OK, zahajuji DHCP požadavek o IP adresu...\n");
        cyw43_arch_lwip_begin();
        dhcp_stop(netif);
        dhcp_start(netif);
        cyw43_arch_lwip_end();

        for (int i = 0; i < 30; i++) {
            cyw43_arch_poll();
            sleep_ms(500);
            if (netif_ip4_addr(netif)->addr != 0) {
                req_res = 0;
                break;
            }
        }
    }

    if (req_res != 0 && netif_ip4_addr(netif)->addr == 0) {
        printf("[WIFI CHYBA] Připojení k Wi-Fi selhalo, kód: %d (link status: %d)\n", req_res, link_status);
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
        return false;
    }

    printf("[WIFI] Připojeno k Wi-Fi síti '%s'!\n", WIFI_SSID);
    printf("[WIFI] Přidělená IP adresa: %s\n", ip4addr_ntoa(netif_ip4_addr(netif)));
    g_wifi_connected = true;
    return true;
}

static void start_mqtt_connection(void) {
    if (!g_wifi_connected) return;

    if (!g_dns_resolved) {
        if (ipaddr_aton(MQTT_BROKER_HOST, &g_broker_ip)) {
            g_dns_resolved = true;
            printf("[DNS] Používám přímou IP adresu brokeru: %s\n", ip4addr_ntoa(&g_broker_ip));
        } else {
            printf("[DNS] Překládám doménu brokeru '%s'...\n", MQTT_BROKER_HOST);
            cyw43_arch_lwip_begin();
            err_t err = dns_gethostbyname(MQTT_BROKER_HOST, &g_broker_ip, dns_found_cb, NULL);
            cyw43_arch_lwip_end();

            if (err == ERR_OK) {
                g_dns_resolved = true;
                printf("[DNS] IP adresa již získána z cache: %s\n", ip4addr_ntoa(&g_broker_ip));
            } else if (err != ERR_INPROGRESS) {
                printf("[DNS CHYBA] Chyba zahájení DNS dotazu: %d\n", err);
                return;
            }
        }
    }

    if (g_dns_resolved && !g_mqtt_connected && g_mqtt_client == NULL) {
        printf("[MQTT] Připojování k MQTT brokeru %s:%d ...\n", ip4addr_ntoa(&g_broker_ip), MQTT_BROKER_PORT);

        g_mqtt_client = mqtt_client_new();
        if (!g_mqtt_client) {
            printf("[MQTT CHYBA] Nelze alokovat paměť pro MQTT klienta!\n");
            return;
        }

        char client_id_buf[32];
        uint8_t mac[6];
        cyw43_wifi_get_mac(&cyw43_state, CYW43_ITF_STA, mac);
        snprintf(client_id_buf, sizeof(client_id_buf), "drybox_pico_%02X%02X%02X", mac[3], mac[4], mac[5]);

        struct mqtt_connect_client_info_t client_info = {0};
        client_info.client_id = client_id_buf;
        client_info.keep_alive = 60;

        cyw43_arch_lwip_begin();
        err_t err = mqtt_client_connect(
            g_mqtt_client,
            &g_broker_ip,
            MQTT_BROKER_PORT,
            mqtt_connection_cb,
            NULL,
            &client_info
        );
        cyw43_arch_lwip_end();

        if (err != ERR_OK) {
            printf("[MQTT CHYBA] Příkaz mqtt_client_connect selhal (%d)\n", err);
            if (g_mqtt_client) {
                mqtt_client_free(g_mqtt_client);
                g_mqtt_client = NULL;
            }
        }
    }
}

/* ========================================================================== */
/* Hlavní program (Main Entry Point)                                          */
/* ========================================================================== */

int main(void) {
    stdio_init_all();
    hw_controls_init();

    // Čekání na USB CDC (max 3 sekundy pro ladicí konzoli)
    uint32_t wait_start = to_ms_since_boot(get_absolute_time());
    while (!stdio_usb_connected()) {
        if ((to_ms_since_boot(get_absolute_time()) - wait_start) > 3000) break;
        sleep_ms(50);
    }

    printf("\n======================================================\n");
    printf("  MULTI-BOX FILAMENT DRYBOX - MASTER NODE (PICO 2 W)\n");
    printf("======================================================\n");

    // Inicializace simulace senzorů
    sim_sensors_init(&g_telemetry);

    // Inicializace Wi-Fi
    wifi_init_and_connect();

    char json_buffer[JSON_BUFFER_SIZE];
    uint64_t last_telemetry_time_us = time_us_64();
    uint64_t last_sim_step_time_us = time_us_64();

    while (true) {
        // cyw43_arch_poll() nebo background handling pro lwIP
        cyw43_arch_poll();

        uint64_t current_time_us = time_us_64();

        // 1. Zajištění síťového spojení s MQTT brokerem
        if (g_wifi_connected && !g_mqtt_connected) {
            start_mqtt_connection();
        }

        // 2. Obsluha tlačítka nebo sériového příkazu
        if (check_toggle_request()) {
            toggle_drying_state();

            // Okamžité odeslání telemetrie při změně stavu
            if (drybox_serialize_json(&g_telemetry, json_buffer, sizeof(json_buffer))) {
                drybox_transport_publish(json_buffer);
            }
        }

        // 3. Fyzikální model sušičky (každých 100 ms)
        if ((current_time_us - last_sim_step_time_us) >= 100000ULL) {
            float dt_s = (float)(current_time_us - last_sim_step_time_us) / 1000000.0f;
            sim_sensors_update(&g_telemetry, dt_s);
            last_sim_step_time_us = current_time_us;
        }

        // 4. Pravidelná periodická telemetrie (každou sekundu)
        if ((current_time_us - last_telemetry_time_us) >= (TELEMETRY_INTERVAL_MS * 1000ULL)) {
            last_telemetry_time_us = current_time_us;

            if (drybox_serialize_json(&g_telemetry, json_buffer, sizeof(json_buffer))) {
                drybox_transport_publish(json_buffer);
            }
        }

        sleep_ms(10);
    }

    return 0;
}
