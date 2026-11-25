# Nákup – prototyp sušičky

Stav k 2026-11-25. Deska osazená a oživená (2026-11-18), zbývá dokoupit díly mimo desku a mechaniku.

## Zbývá koupit

### Elektronika

| Díl | Parametry | Ks | Kde | Poznámka |
|---|---|---|---|---|
| **Topení** (J5) | výkonový rezistor **Arcol HS50 10R J** (10 Ω, 50 W, hliníkové pouzdro, 72,5 × 29,7 × 14,8 mm) | 2 | **TME** | místo PTC (RS 336-739 = drahá doprava). Při 24 V 2,4 A / 57,6 W → firmware omezí střídu na ~85 % (≈ 49 W). Není samoomezující → **TCO na J13 povinná**, NTC na chladiči. Na desce se nic nemění. |
| Teplovodivá pasta | na rezistor, TCO a NTC (do ~150 °C) | 1 | TME / Laskakit | HS50 má 50 W jen na chladiči |
| **Čidlo T/RH** (J6, J11) | modul **SHT40** (I2C, 3,3 V) | 2 (+1) | Laskakit / Adafruit 4885 | J6 v komoře, J11 venku; pull-upy jsou na desce. Bez nich nejde test I2C. |
| **Převodník váhy** (J7) | modul **HX711** | 1–2 | Laskakit / AliExpress | zelený modul s RATE na GND = 10 Hz |
| **Pull-up NTC** | odpor **22 kΩ** (vývodový stačí) | 1 | TME / cokoli | mezi J12 pin 1 (3V3) a pin 13 (GP28); R25 na desce se nekupoval (DNP) |
| **Napájecí adaptér** | **24 V DC, 4 A (96 W)**, koncovka 5,5/2,1 mm, + uprostřed | 1 | TME / Alza | zatím stačí laboratorní zdroj → koupit později. PTC 50 W ≈ 2,1 A trvale + ventilátory ≈ 0,2 A + náběh PTC |

### Mechanika

| Díl | Parametry | Ks | Poznámka |
|---|---|---|---|
| **Chladič k topení** | **Fischer Elektronik SK 100 100 AL** (přírodní hliník) nebo **SK 100 100 SA** (černě eloxovaný) – TME; 100 × 64–66 × 40 mm, základna 10 mm | 1 | profil se žebry podél délky → proudění z 5015 po délce; základna 10 mm = slepé závity M3 pro HS50 a sloupky. Pasivně 1,5–3 K/W (RS / TME se liší), s ventilátorem výrazně míň. Model `mechanika/topny_modul` upravený na tyto rozměry. |
| Ložiska | **608** | 2 | kolébka cívky |
| Hřídelky | k ložiskům 608 (Ø 8 mm) | 2 | |
| Sloupek váhy | ocel nebo karbon | 1 | **ne PETG** (creep při 65 °C) |
| Tepelný izolant | FR4 nebo PTFE, kousek | 1 | na konec sloupku u tenzometru |
| Šrouby | M3 (+ matice, podložky) | | |
| Zalisovací matice | M3 do plastu (heat-set inserts) | ~40 | box je větší než tisk A1 (256³) → díly se šroubují k sobě |
| Izolace boxu | XPS/EPS **10 mm** | | podle simulace max. ~63 °C → ~76 °C |
| Větrání | drát Ø 1,5 mm (čepy žaluzie), fólie 0,6 mm (kotouček zpětného ventilu) | | |
| Filament | **PETG** (ideálně PETG FR, UL94 V-0) na box, přepážku a kolébku; **ASA** na kanál/rukáv kolem topení a držák rezistoru | | tisk na Bambu Lab A1: ABS/ASA na A1 výrobce nedoporučuje (otevřená tiskárna, kroucení) → ASA jen malé díly, větrat. Vzduch u topení ~90 °C, PETG by měklo. |

**Tenzometr** uživatel má – ověřit rozsah **2–5 kg** (1 kg nestačí, plná cívka ~1,25 kg). Když ne → TAL220B.

## Už koupeno

| Co | Kdy / kde | Poznámka |
|---|---|---|
| Deska 4 vrstvy, 5 ks, OSP + šablona 0,10 mm | JLCPCB, objednáno 2026-10-27 | [gerber/OBJEDNAVKA_JLCPCB.md](gerber/OBJEDNAVKA_JLCPCB.md) |
| Součástky na desku | Mouser 2026-10-27 (38 položek), TME (AO3422, AOD4185) | [jlcpcb/BOM_JLCPCB.csv](jlcpcb/BOM_JLCPCB.csv) |
| Pasta Chip Quik TS391SNL50, tavidlo SMD291NL | Mouser 2026-10-27 | |
| Raspberry Pi Debug Probe | 2026-11-03 | otestovaná 2026-11-18 |
| Ventilátory 24 V (J8 cirkulace, J9 odtah) | do 2026-11-14 | odzkoušené na desce |
| NTC 100k (B 3950) | do 2026-11-14 | na GP28 (J12), ne na J10 |
| Tepelná pojistka (J13) | 3× SCHOTT SF129R0 (Tf 133 °C, Th 118 °C), 3× AUPO A2-5A-F (115 °C) | použít **SF129R0** na chladiči, ne přímo na PTC |
| Kabelová zástrčka 5,5/2,1 | RS 487-820 (5 A) | |
| Kabely | | lanko k topení, dupont/JST k lištám |
| Tenzometr | | viz výše – ověřit rozsah |

Nekupuje se: H1–H4, ploškové TP (vyrobí JLC), SW1 (vlastní), USB (J1, D1, R2–R6, C3 – DNP), J10, R25, C26 (NTC jde na J12).
