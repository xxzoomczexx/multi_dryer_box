# Nákup – prototyp sušičky (2026-10-27)

Kontrola před objednáním (2026-10-27, díry zvětšeny na 0,3 mm, nové gerbery): DRC 0 chyb vzdáleností,
7 nespojených GPIO na J12 + chybějící TP3 = záměr. BOM proti desce: nic nechybí.

## 1. Deska – JLCPCB
Podle [gerber/OBJEDNAVKA_JLCPCB.md](gerber/OBJEDNAVKA_JLCPCB.md): ZIP `susicka_filamentu_JLCPCB_2026-10-27.zip`,
4 vrstvy, 5 ks, **OSP**, min. via **0,3 mm** (bez příplatku), 1,6 mm + **šablona** (Non-Framework, Top, 0,10 mm). Jen deska, bez osazení.

## 2. Součástky na desku – Mouser (OBJEDNÁNO 2026-10-27) + TME (AO3422, AOD4185)
Seznam s MPN a odkazy: [jlcpcb/BOM_JLCPCB.csv](jlcpcb/BOM_JLCPCB.csv). Doporučené počty k nákupu:

| Co | Na desku | Koupit |
|---|---|---|
| Pasiva 0402/0603 (R, C) | 1–14 | **max(5, 2× potřeba)**, 100 nF 0402 → 50 ks (cena za 50 je skoro stejná) |
| RP2350A0A4, W25Q128JVSIQ, AP63203WU-7, krystal, L1, L2 | 1 | 3 ks |
| RM2 (Raspberry Pi SC1169) | 1 | 2 ks – když není na Mouseru, Raspberry Pi prodejci (rpishop.cz, Kiwi) |
| MOSFETy, diody, F1, LED | 1–2 | 5 ks |
| C21, C25, J4, svorkovnice, lišty, GND očka | 1–4 | potřeba + 1–2 |

Nekupuje se: H1–H4, ploškové TP (vyrobí JLC), SW1 (vlastní), USB (J1, D1, R2–R6, C3 – DNP), NTC (J10, R25, C26 – na prototypu není).

## 3. Mimo desku

| Díl | Parametry | Ks | Kde | Poznámka |
|---|---|---|---|---|
| **Programátor** Raspberry Pi Debug Probe | SWD + UART | 1 | rpishop.cz / Mouser | USB je DNP → bez něj desku nenaprogramuješ (J3 SWD, J2 UART) |
| **Napájecí adaptér** | 24 V DC, ≥ 3 A (72 W), koncovka 5,5/2,1 mm, + uprostřed | 1 | TME / Alza | PTC 30 W + ventilátory ≈ 1,5 A, náběh PTC 3–5 A |
| **PTC topení** | 24 V, 30 W, Curie ~70 °C, hliníkové žebrování | 2 | AliExpress | 1 rezerva |
| **Tepelná pojistka (J13)** | bimetal **KSD301 NC 85 °C**, 10 A | 3 | AliExpress | **povinná** – NTC na prototypu není; samovratná, takže při testech nevadí, když vypne |
| Ventilátor cirkulace (J8) | radiální **5015, 24 V**, 2vodičový | 2 | AliExpress / 3D tisk shopy | spínaný low-side MOSFETem → 2 vodiče stačí |
| Odtahový ventilátor (J9) | axiální **4010, 24 V**, 2vodičový | 1 | dtto | |
| Čidlo T/RH ×2 (J6, J11) | modul **SHT40** (I2C, 3,3 V) | 2 (+1) | Laskakit / Adafruit 4885 | pull-upy jsou na desce |
| Převodník váhy (J7) | modul **HX711** | 2 | Laskakit / AliExpress | zelený modul s RATE na GND = 10 Hz |
| Tenzometr | hliníkový nosník (straight bar) 2–5 kg | 1 | Laskakit / AliExpress | uživatel jeden má; 1 kg nestačí |
| Kabely | lanko 0,5–0,75 mm² (topení), dupont/JST kabely k lištám | | | |
| Mechanika | 2× ložisko 608, hřídelky, ocelový/karbonový sloupek, izolant FR4/PTFE, šrouby M3 | | | viz CLAUDE.md – Vážení |
| Filament na box | PETG FR (UL94 V-0) | | | |

## 4. Na osazení
Pájecí pasta (bezolovnatá, typ 4 kvůli QFN 0,4 mm), tavidlo, knot, isopropylalkohol, kaptonová páska.
