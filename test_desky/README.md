# Testovací firmware desky (oživení)

Samostatný projekt pro první zapnutí osazené desky (RP2350A + RM2). Nepotřebuje Wi-Fi heslo ani MQTT.
Sestavuje se jako `pico2_w` (stejný krystal 12 MHz a zapojení RM2 jako Pico 2 W), flash 16 MB.

## Testování po částech

Nahoře v `test_desky.c` jsou přepínače – část, kterou zrovna máš připojenou, dej na `1` a přelož znovu.
**Základ** (čip, krystal, flash, RM2 + LED, Wi-Fi scan, tlačítko SW1, teplota čipu) běží vždy.

| Přepínač | Výchozí | Co testuje |
|---|---|---|
| `TEST_VENTILATORY` | 1 | J8 ventilátor (GPIO13) + J9 odtah (GPIO12), příkazy `f` / `e` |
| `TEST_TOPENI` | 0 | J5 topení (GPIO14) na 10 s, příkaz `t` – až bude topné těleso a TCO na J13 |
| `TEST_NTC` | 0 | NTC 100k na GP28 (J12), pull-up 22k k 3V3 mimo desku |
| `TEST_HX711` | 0 | HX711 na J7 (GPIO4 DT, GPIO5 SCK) |

I2C (SHT40 na J6/J11) se doplní, až budou moduly. Vypnuté části drží své výstupní piny v 0.

## Zapojení Debug Probe

| Probe | Deska |
|---|---|
| D – oranžový | J3 SWCLK |
| D – černý | J3 GND |
| D – žlutý | J3 SWDIO |
| U – oranžový (TX probe) | J2 GPIO1 (RX) |
| U – žlutý (RX probe) | J2 GPIO0 (TX) |
| U – černý | J2 GND |

Terminál: COM port probe, 115200 8N1 (PuTTY / Serial Monitor ve VS Code). Pokud nic nechodí, zapnout DTR.

## Sestavení a nahrání

VS Code: otevřít **složku `test_desky`** → Pico rozšíření → Compile, pak „Flash Project (SWD)“.

Ručně (Git Bash, cesty k `~/.pico-sdk`):

```
cmake -G Ninja -S . -B build && ninja -C build
openocd -s <openocd>/scripts -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000" \
        -c "program build/test_desky.elf verify reset exit"
```

## Co vypíše po startu

- čip (RP2350A, revize, ID boxu), důvod resetu
- **krystal** změřený frekvenčním čítačem (má být ~12 000 kHz) a clk_sys (150 MHz)
- **flash JEDEC ID** (W25Q128JV = `EF 40 18`)
- **RM2**: inicializace gSPI a MAC adresa; LED D6 bliká 1 Hz (při stisku SW1 svítí)
- pak každé 2 s stav zapnutých částí, teplota čipu a tlačítko

## Příkazy (jeden znak v terminálu)

| Znak | Akce |
|---|---|
| `h` | nápověda |
| `i` | info o čipu znovu |
| `s` | stav senzorů hned |
| `p` | periodický výpis zap/vyp |
| `w` | Wi-Fi scan – test RM2 a antény bez hesla |
| `f` / `e` (ventilátory) | ventilátor J8 / odtah J9: 0 → 50 → 100 % (PWM 25 kHz) |
| `t` (topení) | topení J5 na 10 s, pak se samo vypne (odmítne, když NTC > 100 °C) |
| `x` | vše vypnout |
| `r` | restart |

Po startu je všechno vypnuté. Watchdog 2 s – při zaseknutí reset, gate Q1 pak drží dole R15.
