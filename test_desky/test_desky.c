/*
 * Testovaci firmware pro oziveni desky susicky (RP2350A + RM2).
 *
 * Vystup a ovladani: UART0 na liste J2 (GPIO0 TX, GPIO1 RX), 115200 8N1.
 * Debug Probe: konektor U -> J2, konektor D -> J3 (SWD).
 *
 * Po startu vypise: cip (pouzdro, revize, ID), takty (krystal 12 MHz), flash JEDEC ID,
 * inicializaci RM2 (gSPI) a pak kazde 2 s stav senzoru. Prikazy jsou jednotlive znaky (h = napoveda).
 *
 * Vsechny vystupy (ventilatory, topeni) jsou po startu VYPNUTE. Topeni se zapina jen na 10 s
 * a vypne se samo; watchdog 2 s -> pri zaseknuti reset, R15 pak drzi gate Q1 dole.
 */
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "pico/cyw43_arch.h"
#include "hardware/adc.h"
#include "hardware/clocks.h"
#include "hardware/flash.h"
#include "hardware/i2c.h"
#include "hardware/pwm.h"
#include "hardware/sync.h"
#include "hardware/watchdog.h"
#include "hardware/structs/sysinfo.h"

// ---- Piny podle schematu ----
#define PIN_I2C1_SDA   2   // J6 SHT4x (komora)
#define PIN_I2C1_SCL   3
#define PIN_HX_DT      4   // J7 HX711 DOUT
#define PIN_HX_SCK     5   // J7 HX711 SCK
#define PIN_I2C0_SDA   8   // J11 SHT40 #2 (venku / elektronika)
#define PIN_I2C0_SCL   9
#define PIN_EXH        12  // J9 odtahovy ventilator (Q4)
#define PIN_FAN        13  // J8 ventilator (Q2)
#define PIN_HEAT       14  // J5 topeni (Q1)
#define PIN_BTN        15  // SW1 proti GND, interni pull-up
#define PIN_NTC_J10    26  // ADC0, J10 (na prototypu neosazeno)
#define PIN_NTC        28  // ADC2, lista J12 - NTC 100k, pull-up 22k k 3V3 mimo desku

#define SHT4X_ADDR     0x44
#define NTC_PULLUP     22000.0f
#define NTC_R25        100000.0f
#define NTC_B          3950.0f

#define FAN_PWM_WRAP   5999u         // 150 MHz / 6000 = 25 kHz
#define HEAT_LIMIT_MS  10000u        // topeni max 10 s na jeden prikaz
#define HEAT_MAX_NTC_C 100.0f        // nad touto teplotou NTC topeni nepusti

static bool wifi_ok = false;
static bool periodic = true;
static uint8_t fan_pct = 0, exh_pct = 0;
static bool heat_on = false;
static absolute_time_t heat_off_at;

// ------------------------------------------------------------------ vystupy
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

static void heat_set(bool on) {
    heat_on = on;
    gpio_put(PIN_HEAT, on);
    if (on) heat_off_at = make_timeout_time_ms(HEAT_LIMIT_MS);
}

static void all_off(void) {
    fan_pct = exh_pct = 0;
    pwm_pin_set(PIN_FAN, 0);
    pwm_pin_set(PIN_EXH, 0);
    heat_set(false);
}

static uint8_t next_duty(uint8_t pct) {
    return pct == 0 ? 50 : (pct == 50 ? 100 : 0);
}

// ------------------------------------------------------------------ informace o cipu
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

// ------------------------------------------------------------------ I2C a SHT4x
static void i2c_scan(i2c_inst_t *bus, const char *name) {
    printf("I2C scan %s:", name);
    int found = 0;
    for (uint8_t a = 0x08; a < 0x78; a++) {
        uint8_t dummy;
        if (i2c_read_timeout_us(bus, a, &dummy, 1, false, 2000) >= 0) {
            printf(" 0x%02X", a);
            found++;
        }
    }
    printf(found ? "\n" : " nic\n");
}

static uint8_t sht_crc(const uint8_t *d) {
    uint8_t crc = 0xFF;
    for (int i = 0; i < 2; i++) {
        crc ^= d[i];
        for (int b = 0; b < 8; b++) crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x31) : (uint8_t)(crc << 1);
    }
    return crc;
}

// Mereni s vysokou presnosti (0xFD). Vraci false, kdyz cidlo neodpovi nebo nesedi CRC.
static bool sht4x_read(i2c_inst_t *bus, float *t, float *rh) {
    uint8_t cmd = 0xFD, d[6];
    if (i2c_write_timeout_us(bus, SHT4X_ADDR, &cmd, 1, false, 5000) != 1) return false;
    sleep_ms(10);
    if (i2c_read_timeout_us(bus, SHT4X_ADDR, d, 6, false, 5000) != 6) return false;
    if (sht_crc(d) != d[2] || sht_crc(d + 3) != d[5]) return false;
    *t  = -45.0f + 175.0f * (float)((d[0] << 8) | d[1]) / 65535.0f;
    *rh = -6.0f + 125.0f * (float)((d[3] << 8) | d[4]) / 65535.0f;
    if (*rh < 0) *rh = 0;
    if (*rh > 100) *rh = 100;
    return true;
}

// ------------------------------------------------------------------ HX711
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

// ------------------------------------------------------------------ ADC
static uint16_t adc_avg(uint ch) {
    adc_select_input(ch);
    uint32_t s = 0;
    for (int i = 0; i < 16; i++) s += adc_read();
    return (uint16_t)(s / 16);
}

// NTC proti GND, pull-up k 3V3. Vraci NAN pri rozpojeni / zkratu.
static float ntc_temp_c(uint16_t raw, float *r_out) {
    if (raw >= 4080 || raw <= 15) { *r_out = NAN; return NAN; }
    float r = NTC_PULLUP * (float)raw / (4095.0f - (float)raw);
    *r_out = r;
    return 1.0f / (1.0f / 298.15f + logf(r / NTC_R25) / NTC_B) - 273.15f;
}

static float chip_temp_c(void) {
    float v = adc_avg(ADC_TEMPERATURE_CHANNEL_NUM) * 3.3f / 4096.0f;
    return 27.0f - (v - 0.706f) / 0.001721f;
}

// ------------------------------------------------------------------ Wi-Fi scan
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

// ------------------------------------------------------------------ vypisy
static void print_status(void) {
    float t, rh, r;
    printf("---\n");
    if (sht4x_read(i2c1, &t, &rh)) printf("SHT J6  (I2C1): %6.2f C  %5.1f %%RH\n", t, rh);
    else                           printf("SHT J6  (I2C1): neodpovida\n");
    if (sht4x_read(i2c0, &t, &rh)) printf("SHT J11 (I2C0): %6.2f C  %5.1f %%RH\n", t, rh);
    else                           printf("SHT J11 (I2C0): neodpovida\n");

    int32_t hx;
    if (hx711_read(&hx)) printf("HX711 J7: %ld\n", (long)hx);
    else                 printf("HX711 J7: neni pripraveny (DT=1)\n");

    uint16_t raw = adc_avg(2);
    float tn = ntc_temp_c(raw, &r);
    if (isnan(tn)) printf("NTC GP28: ADC %4u -> %s\n", raw, raw >= 4080 ? "rozpojeno" : "zkrat");
    else           printf("NTC GP28: ADC %4u -> %.0f ohm -> %.1f C\n", raw, r, tn);
    printf("ADC0 GP26 (J10, neosazeno): %u   cip: %.1f C\n", adc_avg(0), chip_temp_c());

    printf("Vystupy: ventilator J8 %u %%, odtah J9 %u %%, topeni J5 %s   tlacitko %s\n",
           fan_pct, exh_pct, heat_on ? "ZAP" : "vyp", gpio_get(PIN_BTN) ? "pusteno" : "STISKNUTO");
}

static void print_help(void) {
    printf("\nPrikazy:\n"
           "  h  napoveda           i  info o cipu        s  stav senzoru ted\n"
           "  p  periodicky vypis zap/vyp (2 s)          c  I2C scan obou sbernic\n"
           "  w  Wi-Fi scan (test RM2 a anteny)\n"
           "  f  ventilator J8   0 -> 50 -> 100 %%      e  odtah J9   0 -> 50 -> 100 %%\n"
           "  t  topeni J5 na %u s (znovu t = vypnout)   x  vse vypnout\n"
           "  r  restart (watchdog)\n\n", HEAT_LIMIT_MS / 1000);
}

// ------------------------------------------------------------------ main
int main(void) {
    // Vystupy co nejdriv do 0 (gate drzi R15/R18/R24, ale at je to jiste)
    gpio_init(PIN_HEAT);
    gpio_set_dir(PIN_HEAT, GPIO_OUT);
    gpio_put(PIN_HEAT, 0);
    pwm_pin_init(PIN_FAN);
    pwm_pin_init(PIN_EXH);

    stdio_init_all();
    sleep_ms(1500);   // cas na otevreni terminalu

    printf("\n\n===== Susicka filamentu - test desky =====\n");
    print_chip_info();

    gpio_init(PIN_BTN);
    gpio_set_dir(PIN_BTN, GPIO_IN);
    gpio_pull_up(PIN_BTN);

    gpio_init(PIN_HX_SCK);
    gpio_set_dir(PIN_HX_SCK, GPIO_OUT);
    gpio_put(PIN_HX_SCK, 0);
    gpio_init(PIN_HX_DT);
    gpio_set_dir(PIN_HX_DT, GPIO_IN);

    // I2C 100 kHz, pull-upy 4k7 jsou na desce (R21/R22, R26/R27)
    i2c_init(i2c1, 100 * 1000);
    gpio_set_function(PIN_I2C1_SDA, GPIO_FUNC_I2C);
    gpio_set_function(PIN_I2C1_SCL, GPIO_FUNC_I2C);
    i2c_init(i2c0, 100 * 1000);
    gpio_set_function(PIN_I2C0_SDA, GPIO_FUNC_I2C);
    gpio_set_function(PIN_I2C0_SCL, GPIO_FUNC_I2C);

    adc_init();
    adc_gpio_init(PIN_NTC_J10);
    adc_gpio_init(PIN_NTC);
    adc_set_temp_sensor_enabled(true);

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

    i2c_scan(i2c1, "I2C1 (J6, GPIO2/3)");
    i2c_scan(i2c0, "I2C0 (J11, GPIO8/9)");
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
            case 'c': i2c_scan(i2c1, "I2C1 (J6)"); i2c_scan(i2c0, "I2C0 (J11)"); break;
            case 'w': wifi_scan(); break;
            case 'f': fan_pct = next_duty(fan_pct); pwm_pin_set(PIN_FAN, fan_pct);
                      printf("Ventilator J8: %u %%\n", fan_pct); break;
            case 'e': exh_pct = next_duty(exh_pct); pwm_pin_set(PIN_EXH, exh_pct);
                      printf("Odtah J9: %u %%\n", exh_pct); break;
            case 't':
                if (heat_on) { heat_set(false); printf("Topeni VYP\n"); break; }
                {
                    float r, tn = ntc_temp_c(adc_avg(2), &r);
                    if (!isnan(tn) && tn > HEAT_MAX_NTC_C) {
                        printf("Topeni odmitnuto: NTC %.1f C > %.0f C\n", tn, HEAT_MAX_NTC_C);
                        break;
                    }
                }
                heat_set(true);
                printf("Topeni ZAP na %u s (jisti F1 4 A, TCO na J13 musi byt zapojena)\n", HEAT_LIMIT_MS / 1000);
                break;
            case 'x': all_off(); printf("Vse vypnuto\n"); break;
            case 'r': printf("Restart...\n"); all_off(); watchdog_reboot(0, 0, 10); while (1) tight_loop_contents();
            default: break;
        }

        if (heat_on && time_reached(heat_off_at)) {
            heat_set(false);
            printf("Topeni VYP (casovy limit)\n");
        }

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
