# Nákup – prototyp sušičky

Stav k 2026-11-25. Deska osazená a oživená (2026-11-18), zbývá dokoupit díly mimo desku a mechaniku.

## Zbývá koupit

### Elektronika

| Díl | Parametry | Ks | Kde | Poznámka |
|---|---|---|---|---|
| **PTC topení** (J5) | **24 V, 40–60 W, konstantní teplota ~120 °C**, hliníkové pouzdro s ouškem na šrouby | 2 | AliExpress | místo RS PRO 336-739 (drahá doprava z RS). Model `mechanika/topny_modul` počítá s 76×63×7 mm. **Ne nad ~60 W** (F1 = 4 A, náběh PTC 2–3× jmenovitého proudu), **ne 70 °C** (slabé) ani 220 °C (TCO SF129R0 by vypínala v provozu). Po doručení změřit proud na laboratorním zdroji. |
| **Čidlo T/RH** (J6, J11) | modul **SHT40** (I2C, 3,3 V) | 2 (+1) | Laskakit / Adafruit 4885 | J6 v komoře, J11 venku; pull-upy jsou na desce. Bez nich nejde test I2C. |
| **Převodník váhy** (J7) | modul **HX711** | 1–2 | Laskakit / AliExpress | zelený modul s RATE na GND = 10 Hz |
| **Pull-up NTC** | odpor **22 kΩ** (vývodový stačí) | 1 | TME / cokoli | mezi J12 pin 1 (3V3) a pin 13 (GP28); R25 na desce se nekupoval (DNP) |
| **Napájecí adaptér** | **24 V DC, 4 A (96 W)**, koncovka 5,5/2,1 mm, + uprostřed | 1 | TME / Alza | zatím stačí laboratorní zdroj → koupit později. PTC 50 W ≈ 2,1 A trvale + ventilátory ≈ 0,2 A + náběh PTC |

### Mechanika

| Díl | Parametry | Ks | Poznámka |
|---|---|---|---|
| **Chladič k PTC** | podle finální verze modelu | | simulace: 2× 60×60×10 v sendviči; skript `mechanika/topny_modul`: 100×69×36 |
| Ložiska | **608** | 2 | kolébka cívky |
| Hřídelky | k ložiskům 608 (Ø 8 mm) | 2 | |
| Sloupek váhy | ocel nebo karbon | 1 | **ne PETG** (creep při 65 °C) |
| Tepelný izolant | FR4 nebo PTFE, kousek | 1 | na konec sloupku u tenzometru |
| Šrouby | M3 (+ matice, podložky) | | |
| Izolace boxu | XPS/EPS **10 mm** | | podle simulace max. ~63 °C → ~76 °C |
| Větrání | drát Ø 1,5 mm (čepy žaluzie), fólie 0,6 mm (kotouček zpětného ventilu) | | |
| Filament | **ASA/ABS** na topný modul a kanál, **PETG FR** (UL94 V-0) na box | | vzduch u topení ~90 °C, PETG by měklo |

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
