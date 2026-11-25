# Nákup – prototyp sušičky

Stav k 2026-11-25. Deska osazená a oživená (2026-11-18), objednané topení, chladič a adaptér (TME) a senzory (Laskakit).
Zbývá dokoupit mechaniku (železářství), izolaci a filament.

## Zbývá koupit

### Železářství / kamenný obchod

| Díl | Parametry | Ks | Kam |
|---|---|---|---|
| Šrouby | **M3×8, imbus (DIN 912), nerez A2** | ~60 | HS50 → chladič (2), sloupky chladiče přes stěnu rukávu (4), rukáv → pravá stěna boxu (4), svorka TCO (1–2), box do zalisovacích matic (~40) |
| Matice | M3 (DIN 934), nerez | ~10 | rezerva |
| Podložky | M3 (DIN 125), nerez | ~20 | pod hlavy šroubů |
| Distanční sloupky | **M3, 15 mm, vnější + vnitřní závit** | 4 | základna chladiče → zadní stěna rukávu z **ASA** (+ podložka PTFE; ne přímo do PETG – sloupek vede teplo ~100 °C) |
| Zalisovací matice | M3 do plastu (heat-set inserts) | ~40 | box je větší než tisk A1 (256³) → díly se šroubují k sobě |
| Podložky PTFE | M3, tl. 1 mm | 8 | 4× pod sloupky chladiče (u rukávu), 4× mezi bloky rukávu a pravou stěnu boxu – tepelná izolace ASA → PETG |
| Vrták 2,5 mm + závitník M3 | | | 6 slepých závitů v chladiči (2× HS50, 4× sloupky), vrtat ~7 mm, závit ~6 mm – nebo ve školní dílně |
| Pásek plechu (Al / Cu) | | 1 | svorka přitlačující TCO k chladiči (plast by u ~100 °C měkl) |
| Ložiska | **608** | 2 | kolébka cívky |
| Hřídelky | Ø 8 mm k ložiskům 608 | 2 | |
| Sloupek váhy | ocel nebo karbon | 1 | **ne PETG** (creep při 65 °C) |
| Tepelný izolant | FR4 nebo PTFE, kousek | 1 | na konec sloupku u tenzometru |
| Drát | Ø 1,5 mm | | čepy žaluzie odtahu |
| Fólie | 0,6 mm | | kotouček zpětného ventilu |

### Jinde

| Díl | Parametry | Kde | Poznámka |
|---|---|---|---|
| **Izolace boxu** | XPS/EPS **10 mm** | hobby market (OBI, Hornbach…) | **nutná** – s malým chladičem a ~49 W by bez ní byl ohřev pomalý; podle simulace max. ~63 → ~76 °C |
| Filament | **PETG** (ideálně PETG FR, UL94 V-0) na box, přepážku a kolébku; **ASA** na kanál/rukáv kolem topení, držák rezistoru a podstavec chladiče | e-shop s filamenty | tisk na Bambu Lab A1: ABS/ASA výrobce na A1 nedoporučuje → ASA jen malé díly, větrat. Vzduch u topení ~90 °C, PETG by měklo. |

## Už koupeno

| Co | Kdy / kde | Poznámka |
|---|---|---|
| Deska 4 vrstvy, 5 ks, OSP + šablona 0,10 mm | JLCPCB, objednáno 2026-10-27 | [gerber/OBJEDNAVKA_JLCPCB.md](gerber/OBJEDNAVKA_JLCPCB.md) |
| Součástky na desku | Mouser 2026-10-27 (38 položek), TME (AO3422, AOD4185) | [jlcpcb/BOM_JLCPCB.csv](jlcpcb/BOM_JLCPCB.csv) |
| Pasta Chip Quik TS391SNL50, tavidlo SMD291NL | Mouser 2026-10-27 | |
| Raspberry Pi Debug Probe | 2026-11-03 | otestovaná 2026-11-18 |
| Ventilátory 24 V (J8 cirkulace, J9 odtah) | do 2026-11-14 | odzkoušené na desce |
| NTC 100k (B 3950) | do 2026-11-14 | na GP28 (J12), ne na J10 |
| Tepelná pojistka (J13) | 3× SCHOTT SF129R0 (Tf 133 °C, Th 118 °C), 3× AUPO A2-5A-F (115 °C) | použít **SF129R0** na chladiči hned u rezistoru (A2-5A-F by vybavovala v provozu) |
| **Topení** – Arcol **HS50 10R J** (10 Ω, 50 W), 2 ks | **TME, objednáno 2026-11-25** | 24 V → 2,4 A / 57,6 W, firmware omezí střídu na ~85 % (≈ 49 W). Není samoomezující → TCO na J13 povinná, NTC na chladiči. Díry 2× Ø 3,2 úhlopříčně, rozteč 39,7 × 21,4 mm. |
| **Chladič** – Fischer **SK 189 100 AL** | **TME, objednáno 2026-11-25** | 100 × 41,5 × 34 mm, základna 8 mm, 6 žeber. TCO a NTC za rezistorem. Odhad ~1 K/W s 5015 → při plném výkonu ~110–120 °C, firmware stáhne výkon podle NTC. |
| **Teplovodivá pasta** AG Termopasty **ART.AGT-057** | **TME, objednáno 2026-11-25** | silikonová, nevodivá, ~0,88 W/mK, −50 až 200 °C, 100 g |
| **Pull-up NTC** 22 kΩ | **TME, objednáno 2026-11-25** | mezi J12 pin 1 (3V3) a pin 13 (GP28) |
| **Napájecí adaptér** ESPE **E90P-9024-211** | **TME, objednáno 2026-11-25** | 24 V / 3,75 A / 90 W, jack 2,1 × 5,5 mm **plus uprostřed**, vstup IEC C14, ochrany zkrat / nadproud / přepětí 38 V, CE, provoz −5 až 40 °C → **nechat mimo box**. Špička spotřeby ~2,6 A. |
| Kabelová zástrčka 5,5/2,1 | RS 487-820 (5 A) | pro laboratorní zdroj |
| Kabely | | lanko k topení, dupont/JST k lištám |
| **Čidlo T/RH** – LaskaKit **SHT40** (LA131037), 2 ks | **Laskakit, objednáno 2026-11-25** | J6 v komoře (vzduch u cívky, ne proud z topení), J11 venku. Zapojit podle popisků: J6 = 3V3, GND, SCL, SDA; J11 = 3V3, GND, SDA, SCL. |
| **Převodník váhy** – HX711 zelený modul (LA161036), 1 ks | **Laskakit, objednáno 2026-11-25** | J7 = 3V3, GND, SCK, DT (modul: GND, DT, SCK, VCC) – zapojit podle popisků |
| **Tenzometr** – GUANG CE **YZC-131, 5 kg** (LA131068B) | **Laskakit, objednáno 2026-11-25** | straight bar; rozměr závitů v koncích (M4/M5?) změřit a dokoupit šrouby |
| Síťový kabel IEC C13 | vlastní | k adaptéru E90P (vstup C14) |
| Tenzometr (původní) | vlastní | rozsah neznámý – záloha |

Nekupuje se: H1–H4, ploškové TP (vyrobí JLC), SW1 (vlastní), USB (J1, D1, R2–R6, C3 – DNP), J10, R25, C26 (NTC jde na J12).
