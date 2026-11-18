/*
 * Testovaci firmware pro oziveni desky susicky (RP2350A + RM2).
 *
 * Vystup a ovladani: UART0 na liste J2 (GPIO0 TX, GPIO1 RX), 115200 8N1.
 * Debug Probe: konektor U -> J2, konektor D -> J3 (SWD).
 *
 * Testuje se po castech - kazdou cast zapnes prepinacem nize (1 = zapnuto, 0 = vypnuto)
 * a firmware znovu prelozis. Zaklad (cip, krystal, flash, RM2 + LED, tlacitko) bezi vzdy.
 *
 * Vsechny vystupy (ventilatory, topeni) jsou po startu VYPNUTE a vypnute cast drzi svuj pin v 0.
 * Watchdog 2 s -> pri zaseknuti reset, gate tranzistoru pak drzi dole R15/R18/R24.
 */

// ================= PREPINACE CASTI TESTU =================
#define TEST_VENTILATORY  1   // J8 ventilator (GPIO13) + J9 odtah (GPIO12), prikazy f / e
#define TEST_TOPENI       0   // J5 topeni (GPIO14) na 10 s, prikaz t  - az bude topne teleso + TCO na J13
#define TEST_NTC          1   // NTC 100k na GP28 (J12), pull-up 22k k 3V3 mimo desku
#define TEST_HX711        0   // HX711 na J7 (GPIO4 DT, GPIO5 SCK)
// (I2C / SHT40 se doplni, az budou moduly)
// =========================================================

#include <stdio.h>
#include <string.h>
#include <math.h>

#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "pico/cyw43_arch.h"
#include "hardware/adc.h"
#include "hardware/clocks.h"
#include "hardware/flash.h"
#include "hardware/pwm.h"
#include "hardware/sync.h"
#include "hardware/watchdog.h"
#include "hardware/structs/sysinfo.h"

// ---- Piny podle schematu ----
#define PIN_HX_DT      4   // J7 HX711 DOUT
#define PIN_HX_SCK     5   // J7 HX711 SCK
#define PIN_EXH        12  // J9 odtahovy ventilator (Q4)
#define PIN_FAN        13  // J8 ventilator (Q2)
#define PIN_HEAT       14  // J5 topeni (Q1)
#define PIN_BTN        15  // SW1 proti GND, interni pull-up
#define PIN_NTC        28  // ADC2, lista J12
#define ADC_CH_NTC     2

#define NTC_PULLUP     22000.0f
#define NTC_R25        100000.0f
#define NTC_B          3950.0f

#define FAN_PWM_WRAP   5999u         // 150 MHz / 6000 = 25 kHz
#define HEAT_LIMIT_MS  10000u        // topeni max 10 s na jeden prikaz
#define HEAT_MAX_NTC_C 100.0f        // nad touto teplotou NTC topeni nepusti

static bool wifi_ok = false;
static bool periodic = true;

static void out_low(uint pin) {
    gpio_init(pin);
    gpio_set_dir(pin, GPIO_OUT);
    gpio_put(pin, 0);
}

// ================================================================== ZAKLAD: cip, takty, flash
static void print_chip_info(void) {
    char id[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];
    pico_get_unique_board_id_string(id, sizeof id);
    uint32_t pkg = sysinfo_hw->package_sel & SYSINFO_PACKAGE_SEL_BITS;
    printf("Cip:      RP2350%s (package_sel=%lu), revize A%u, chip_id 0x%08lx\n",
           pkg ? "A (QFN-60)" : "B (QFN-80)", (unsigned long)pkg,
           rp2350_chip_version(), (unsigned long)sysinfo_hw->chip_id);
    printf("Box ID:   %s\n", id);
    printf("Reset:    %s\n", watchdog_caused_reboot() ? "WATCHDOG (zaseknuti nebo prikaz r)" : "normalni zapnuti / RUN");

    uint32_t xosc = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_XOSC_CLKSRC);
    uint32_t sys  = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_SYS);
    printf("Takty:    krystal %lu kHz (ma byt ~12000) %s, clk_sys %lu kHz\n",
           (unsigned long)xosc, (xosc > 11900 && xosc < 12100) ? "OK" : "!! CHYBA",
           (unsigned long)sys);

    // JEDEC ID flash: W25Q128JV = EF 40 18
    uint8_t tx[4] = {0x9F, 0, 0, 0}, rx[4] = {0};
    uint32_t irq = save_and_disable_interrupts();
    flash_do_cmd(tx, rx, 4);
    restore_interrupts(irq);
    bool flash_ok = rx[1] == 0xEF && rx[2] == 0x40 && rx[3] == 0x18;
    printf("Flash:    JEDEC %02X %02X %02X %s\n", rx[1], rx[2], rx[3],
           flash_ok ? "OK (Winbond W25Q128JV, 16 MB)" : "!! neocekavane (ceka se EF 40 18)");
}

static float chip_temp_c(void) {
    adc_select_input(ADC_TEMPERATURE_CHANNEL_NUM);
    uint32_t s = 0;
    for (int i = 0; i < 16; i++) s += adc_read();
    float v = (s / 16.0f) * 3.3f / 4096.0f;
    return 27.0f - (v - 0.706f) / 0.001721f;
}

// ================================================================== ZAKLAD: Wi-Fi scan (RM2)
static int scan_cb(void *env, const cyw43_ev_scan_result_t *r) {
    (void)env;
    if (r) {
        char ssid[33];
        memcpy(ssid, r->ssid, r->ssid_len);
        ssid[r->ssid_len] = 0;
        printf("  %-32s  RSSI %4d dBm  kanal %2u  %02x:%02x:%02x:%02x:%02x:%02x\n",
               ssid[0] ? ssid : "(skryta)", r->rssi, r->channel,
               r->bssid[0], r->bssid[1], r->bssid[2], r->bssid[3], r->bssid[4], r->bssid[5]);
    }
    return 0;
}

static void wifi_scan(void) {
    if (!wifi_ok) { printf("Wi-Fi: RM2 neni inicializovany\n"); return; }
    cyw43_wifi_scan_options_t opts = {0};
    if (cyw43_wifi_scan(&cyw43_state, &opts, NULL, scan_cb) != 0) {
        printf("Wi-Fi scan: nepodarilo se spustit\n");
        return;
    }
    printf("Wi-Fi scan (nekolik s, site se mohou opakovat):\n");
    absolute_time_t end = make_timeout_time_ms(10000);
    while (cyw43_wifi_scan_active(&cyw43_state) && !time_reached(end)) {
        watchdog_update();
        sleep_ms(50);
    }
    printf("Wi-Fi scan hotovo\n");
}

// ================================================================== CAST: ventilatory
#if TEST_VENTILATORY
static uint8_t fan_pct = 0, exh_pct = 0;

static void pwm_pin_init(uint pin) {
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(pin);
    pwm_set_wrap(slice, FAN_PWM_WRAP);
    pwm_set_clkdiv(slice, 1.0f);
    pwm_set_gpio_level(pin, 0);
    pwm_set_enabled(slice, true);
}

static void pwm_pin_set(uint pin, uint8_t pct) {
    pwm_set_gpio_level(pin, (uint32_t)(FAN_PWM_WRAP + 1) * pct / 100u);
}

static uint8_t next_duty(uint8_t pct) {
    return pct == 0 ? 50 : (pct == 50 ? 100 : 0);
}

static void fans_init(void) {
    pwm_pin_init(PIN_FAN);
    pwm_pin_init(PIN_EXH);
}

static void fans_off(void) {
    fan_pct = exh_pct = 0;
    pwm_pin_set(PIN_FAN, 0);
    pwm_pin_set(PIN_EXH, 0);
}
#endif

// ================================================================== CAST: NTC
#if TEST_NTC
// NTC proti GND, pull-up k 3V3. Vraci NAN pri rozpojeni / zkratu.
static float ntc_temp_c(uint16_t *raw_out, float *r_out) {
    adc_select_input(ADC_CH_NTC);
    uint32_t s = 0;
    for (int i = 0; i < 16; i++) s += adc_read();
    uint16_t raw = (uint16_t)(s / 16);
    *raw_out = raw;
    if (raw >= 4080 || raw <= 15) { *r_out = NAN; return NAN; }
    float r = NTC_PULLUP * (float)raw / (4095.0f - (float)raw);
    *r_out = r;
    return 1.0f / (1.0f / 298.15f + logf(r / NTC_R25) / NTC_B) - 273.15f;
}
#endif

// ================================================================== CAST: topeni
#if TEST_TOPENI
static bool heat_on = false;
static absolute_time_t heat_off_at;

static void heat_set(bool on) {
    heat_on = on;
    gpio_put(PIN_HEAT, on);
    if (on) heat_off_at = make_timeout_time_ms(HEAT_LIMIT_MS);
}

static void heat_command(void) {
    if (heat_on) { heat_set(false); printf("Topeni VYP\n"); return; }
#if TEST_NTC
    uint16_t raw; float r, tn = ntc_temp_c(&raw, &r);
    if (!isnan(tn) && tn > HEAT_MAX_NTC_C) {
        printf("Topeni odmitnuto: NTC %.1f C > %.0f C\n", tn, HEAT_MAX_NTC_C);
        return;
    }
#endif
    heat_set(true);
    printf("Topeni ZAP na %u s (jisti F1 4 A, TCO na J13 musi byt zapojena)\n", HEAT_LIMIT_MS / 1000);
}
#endif

// ================================================================== CAST: HX711
#if TEST_HX711
// Vraci false, kdyz HX711 neni pripraveny (DT v 1 = chybi modul nebo jeste meri).
static bool hx711_read(int32_t *val) {
    if (gpio_get(PIN_HX_DT)) return false;
    uint32_t v = 0;
    uint32_t irq = save_and_disable_interrupts();   // SCK nesmi byt v 1 dele nez 60 us
    for (int i = 0; i < 24; i++) {
        gpio_put(PIN_HX_SCK, 1);
        busy_wait_us_32(1);
        v = (v << 1) | gpio_get(PIN_HX_DT);
        gpio_put(PIN_HX_SCK, 0);
        busy_wait_us_32(1);
    }
    gpio_put(PIN_HX_SCK, 1);   // 25. puls = kanal A, zisk 128
    busy_wait_us_32(1);
    gpio_put(PIN_HX_SCK, 0);
    restore_interrupts(irq);
    if (v & 0x800000) v |= 0xFF000000;   // znamenkove rozsireni 24 -> 32 bitu
    *val = (int32_t)v;
    return true;
}
#endif

// ================================================================== vypisy
static void all_off(void) {
#if TEST_VENTILATORY
    fans_off();
#endif
#if TEST_TOPENI
    heat_set(false);
#endif
}

static void print_status(void) {
    printf("---\n");
#if TEST_HX711
    int32_t hx;
    if (hx711_read(&hx)) printf("HX711 J7: %ld\n", (long)hx);
    else                 printf("HX711 J7: neni pripraveny (DT=1)\n");
#endif
#if TEST_NTC
    uint16_t raw; float r, tn = ntc_temp_c(&raw, &r);
    if (isnan(tn)) printf("NTC GP28: ADC %4u -> %s\n", raw, raw >= 4080 ? "rozpojeno" : "zkrat");
    else           printf("NTC GP28: ADC %4u -> %.0f ohm -> %.1f C\n", raw, r, tn);
#endif
#if TEST_VENTILATORY
    printf("Ventilator J8 %u %%, odtah J9 %u %%\n", fan_pct, exh_pct);
#endif
#if TEST_TOPENI
    printf("Topeni J5 %s\n", heat_on ? "ZAP" : "vyp");
#endif
    printf("Cip %.1f C, tlacitko SW1 %s, RM2 %s\n", chip_temp_c(),
           gpio_get(PIN_BTN) ? "pusteno" : "STISKNUTO", wifi_ok ? "OK" : "CHYBA");
}

static void print_help(void) {
    printf("\nZapnute casti testu: zaklad%s%s%s%s\n",
           TEST_VENTILATORY ? ", ventilatory" : "", TEST_TOPENI ? ", topeni" : "",
           TEST_NTC ? ", NTC" : "", TEST_HX711 ? ", HX711" : "");
    printf("Prikazy:\n"
           "  h  napoveda           i  info o cipu        s  stav ted\n"
           "  p  periodicky vypis zap/vyp (2 s)\n"
           "  w  Wi-Fi scan (test RM2 a anteny)\n");
#if TEST_VENTILATORY
    printf("  f  ventilator J8   0 -> 50 -> 100 %%      e  odtah J9   0 -> 50 -> 100 %%\n");
#endif
#if TEST_TOPENI
    printf("  t  topeni J5 na %u s (znovu t = vypnout)\n", HEAT_LIMIT_MS / 1000);
#endif
    printf("  x  vse vypnout        r  restart (watchdog)\n\n");
}

// ================================================================== main
int main(void) {
    // Vystupy co nejdriv do 0 (gate drzi i pull-downy na desce, ale at je to jiste)
    out_low(PIN_HEAT);
    out_low(PIN_FAN);
    out_low(PIN_EXH);
#if TEST_VENTILATORY
    fans_init();
#endif

    stdio_init_all();
    sleep_ms(1500);   // cas na otevreni terminalu

    printf("\n\n===== Susicka filamentu - test desky =====\n");
    print_chip_info();

    gpio_init(PIN_BTN);
    gpio_set_dir(PIN_BTN, GPIO_IN);
    gpio_pull_up(PIN_BTN);

    adc_init();
    adc_set_temp_sensor_enabled(true);
#if TEST_NTC
    adc_gpio_init(PIN_NTC);
#endif
#if TEST_HX711
    out_low(PIN_HX_SCK);
    gpio_init(PIN_HX_DT);
    gpio_set_dir(PIN_HX_DT, GPIO_IN);
#endif

    printf("RM2:      inicializace gSPI...\n");
    if (cyw43_arch_init() == 0) {
        wifi_ok = true;
        cyw43_arch_enable_sta_mode();
        uint8_t mac[6];
        cyw43_hal_get_mac(0, mac);
        printf("RM2:      OK, MAC %02x:%02x:%02x:%02x:%02x:%02x\n",
               mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    } else {
        printf("RM2:      !! CHYBA inicializace (gSPI GPIO24/25/29, WL_ON GPIO23, napajeni modulu)\n");
    }

    print_help();
    watchdog_enable(2000, true);

    absolute_time_t next_print = get_absolute_time();
    absolute_time_t next_led = get_absolute_time();
    bool led = false, btn_prev = true;

    while (true) {
        watchdog_update();

        int c = getchar_timeout_us(0);
        switch (c) {
            case 'h': case '?': print_help(); break;
            case 'i': print_chip_info(); break;
            case 's': print_status(); break;
            case 'p': periodic = !periodic; printf("Periodicky vypis %s\n", periodic ? "ZAP" : "VYP"); break;
            case 'w': wifi_scan(); break;
#if TEST_VENTILATORY
            case 'f': fan_pct = next_duty(fan_pct); pwm_pin_set(PIN_FAN, fan_pct);
                      printf("Ventilator J8: %u %%\n", fan_pct); break;
            case 'e': exh_pct = next_duty(exh_pct); pwm_pin_set(PIN_EXH, exh_pct);
                      printf("Odtah J9: %u %%\n", exh_pct); break;
#endif
#if TEST_TOPENI
            case 't': heat_command(); break;
#endif
            case 'x': all_off(); printf("Vse vypnuto\n"); break;
            case 'r': printf("Restart...\n"); all_off(); watchdog_reboot(0, 0, 10); while (1) tight_loop_contents();
            default: break;
        }

#if TEST_TOPENI
        if (heat_on && time_reached(heat_off_at)) {
            heat_set(false);
            printf("Topeni VYP (casovy limit)\n");
        }
#endif

        bool btn = gpio_get(PIN_BTN);
        if (btn != btn_prev) {
            sleep_ms(20);   // jednoduche odruseni zakmitu
            if (gpio_get(PIN_BTN) == btn) {
                printf("Tlacitko SW1: %s\n", btn ? "pusteno" : "STISKNUTO");
                btn_prev = btn;
            }
        }

        // LED na RM2 GPIO0: 1 Hz = vse bezi; pri stisknutem tlacitku sviti trvale
        if (wifi_ok && time_reached(next_led)) {
            led = !btn_prev ? true : !led;
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, led);
            next_led = make_timeout_time_ms(500);
        }

        if (periodic && time_reached(next_print)) {
            print_status();
            next_print = make_timeout_time_ms(2000);
        }

        sleep_ms(5);
    }
}
