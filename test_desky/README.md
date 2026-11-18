# Testovací firmware desky (oživení)

Samostatný projekt pro první zapnutí osazené desky (RP2350A + RM2). Nepotřebuje Wi-Fi heslo ani MQTT.
Sestavuje se jako `pico2_w` (stejný krystal 12 MHz a zapojení RM2 jako Pico 2 W), flash 16 MB.

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
- I2C scan obou sběrnic (SHT40 = `0x44`)
- pak každé 2 s: oba SHT40, HX711, NTC na GP28 (22k pull-up mimo desku, B 3950), teplota čipu, tlačítko

## Příkazy (jeden znak v terminálu)

| Znak | Akce |
|---|---|
| `h` | nápověda |
| `i` | info o čipu znovu |
| `s` | stav senzorů hned |
| `p` | periodický výpis zap/vyp |
| `c` | I2C scan |
| `w` | Wi-Fi scan – test RM2 a antény bez hesla |
| `f` / `e` | ventilátor J8 / odtah J9: 0 → 50 → 100 % (PWM 25 kHz) |
| `t` | topení J5 na 10 s, pak se samo vypne (odmítne, když NTC > 100 °C) |
| `x` | vše vypnout |
| `r` | restart |

Po startu je všechno vypnuté. Watchdog 2 s – při zaseknutí reset, gate Q1 pak drží dole R15.
