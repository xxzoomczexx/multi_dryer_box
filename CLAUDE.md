# Modulární IoT sušička filamentu – maturitní projekt

@.claude/pamet.md

Maturitní práce (SPŠE a VOŠ Plzeň, obor Elektrotechnika – Internet věcí). Návrh HW, FW i cloudu
pro sušení, uchovávání a tisk z filamentových boxů s dohledem v reálném čase.
GitHub: https://github.com/xxzoomczexx/multi_dryer_box · Web: https://xxzoomczexx.github.io/multi_dryer_box/

## Struktura složek

Tahle složka je bare git repozitář (`.git`, `core.bare=true`) se třemi worktree:

| Složka | Větev | Obsah |
|---|---|---|
| `PCB/` | `PCB` | KiCad 9 projekt `susicka_filamentu.kicad_pro` |
| `FIRMWARE/` | `FIRMWARE` | C, Pico SDK 2.x, lwIP MQTT (`main.c`, `serial_mqtt_bridge.py`) |
| `WEB/` | `WEB` | single-file dashboard `index.html` (Tailwind, mqtt.js, Chart.js) |

Větev `main` není checkoutnutá (`git worktree add MAIN main`). Git příkazy spouštět uvnitř podsložek.
Subagenti v `.claude/agents/`: `hledac` (Haiku – jen hledání/čtení souborů), `pcb-navrhar` (Opus – PCB, schéma,
součástky, výpočty a vše náročné). Uživatel chce: jednoduché hledání → Haiku, těžké nebo PCB → Opus.
`soucastky.xlsx` (zde v kořeni, mimo git) = nákupní seznam hlavních součástek + tabulka zapojení RM2.

## Koncept

- Každý box je **samostatná deska**: RP2350A (jako Pico 2) + Wi-Fi modul RM2 (jako Pico 2 W),
  posílá telemetrii přímo přes Wi-Fi/MQTT. Box ID = výrobní číslo čipu (`pico_get_unique_board_id_string`,
  16 hex znaků, v JSON jako string) → web sám přidá kartu nového boxu
  (ověřeno: Pico 1 W se přihlásilo na web jako další box).
- Starší README zmiňují RP2040 sensor nody + Master Node přes CAN/RS-485/I2C – to je původní/výhledová
  kaskádová varianta, aktuální deska žádný transceiver nemá.
- MQTT: `drybox/status/{id}` (JSON: id, weight, temp, hum, dry_state, status, type; 1 Hz),
  `drybox/commands` (spínání ohřevu, materiálový profil). Broker `test.mosquitto.org`, web přes `wss://…:8081/mqtt`.
- Firmware zatím simuluje hodnoty senzorů; Wi-Fi + MQTT funguje.

## Hardware (PCB)

- RP2350A0A4 QFN-60 7×7, interní VREG + AOTA-B201610S3R3-101-T (0806), krystal 12 MHz ABM8-272-T3,
  flash W25Q128JVSIQ (SOIC-8 208 mil), RM2 na GPIO23 (WL_ON+BT_ON), 24 (data; DO přes 470 Ω, nIRQ přes 10 k), 25 (CS), 29 (CLK).
- Napájení 24 V (jack PJ-102AH) → AP63203WU-7 → 3,3 V.
- Topení: 24V PTC 30 W (Curie ~70 °C, náběh 3–5 A), N-MOSFET Q1 na GPIO14, pomalé PWM ~1 Hz (PID), svorkovnice J5.
- Senzory: SHT4x přes I2C (J6: 3V3, GND, SCL GPIO3, SDA GPIO2), HX711 + tenzometr (J7: 3V3, GND, SCK GPIO5, DT GPIO4).
- Výstupy a další vstupy (list `vystupy.kicad_sch`): GPIO13 = ventilátor (J8), GPIO14 = topení (J5),
  **GPIO12 = odtahový ventilátor** (J9), **GPIO8/9 = I2C0 pro druhý SHT40** (J11: 3V3, GND, SDA, SCL),
  **GPIO26 = NTC topení** (J10: ADC, GND), GPIO15 = tlačítko, RM2 GPIO0 = stavová LED.
- Tepelná pojistka topení: svorkovnice J13 v sérii (24V → J13 → `HEAT_V` → J5.2), TCO je mimo desku na tělese topení.
- List `rozsireni.kicad_sch`: lišta J12 2×7 s volnými GPIO (GP10, 11, 16–22, 27, 28 + 3V3 + 2× GND) a testovací body
  TP1 24V, TP2 3V3, TP3 1V1 (ploška 1,5 mm), TP4/TP5 GND (očko pro krokosvorku).
  GPIO6/7 nejsou vyvedené – na hlavním listu jim v cestě vede propojení J7 (GPIO4/5).
  Montážní otvory H1–H4 (M3, `MountingHole_3.2mm_M3`, bez mědi) – pozice se volí až v layoutu.
  Testovací body komunikace TP6–TP19 (plošky Ø 1 mm) + TP12 GND očko: I2C1, I2C0, HX711, RM2 gSPI, 3× PWM, NTC_ADC.
  HX711: **GPIO4 = DT (DOUT), GPIO5 = SCK** (sítě `HX711_DT`, `HX711_SCK`). RM2 sítě: `WL_CLK` GPIO29, `WL_CS` GPIO25, `WL_DATA` GPIO24.
  Na hlavním listu jsou GPIO2–5 → J6/J7 a GPIO24/25/29 → RM2 propojené globálními labely (ne dráty); J6 posunutá níž.
- Ladění: SWD (J3: SWDIO, SWCLK, GND, RUN) + UART0 (J2: GPIO0/1 přes 220 Ω, GND).
- **USB-C (J1, D1, R2–R6, C3) je záměrně DNP** – programuje se přes SWD; USB zůstává v návrhu jako záloha.
- 4 vrstvy: Top signál / In1 GND / In2 +3V3 / Bottom silové trasy; keepout pod anténou RM2 35,5 × 18,5 mm ve všech vrstvách.
- Součástky se kupují po 5 ks jako rezerva na poškození při osazování (deska je jedna).

## Rozhodnutí (2026-10-19)

- Teď se dělá **jeden testovací box**, rozšíření až potom. Zatím bez CAN/RS-485/I2C mezi boxy.
- Napájení: 24V DC jack (adaptér jako k notebooku / PC zdroj), USB-C PD zamítnuto (složité).
- Testovací materiály: PETG, ABS, TPU; vyšší teploty / těžší materiály později.
- Programování přes SWD, USB DNP. Každé rozhraní má vlastní lištu (SWD, UART, I2C, HX711).
- Pasiva preferovat **0402 / 0603** (pájení v peci + pinzeta), větší jen kde je nutné (C21 1210/50 V,
  C23/C24 0805, L2 4×4 mm). Rozpis v `PCB/README.md`. VREG (C4, C5, C6 4,7 µF 6,3 V X5R + R7 33 Ω) je v 0402
  jako v referenci, aby šel layout okopírovat 1:1 (pozice vůči U1 v `PCB/README.md`).
  Layout VREG je HOTOVÝ (2026-10-19, skriptem přes pcbnew API podle reference): C5/C6 mají footprint
  `susicka:C_0402_1005Metric_RPi` (plošky 0,47×0,55 na ±0,515 → mezera 0,56 mm pro LX pod tělem), zóny F.Cu
  +3V3/VIN prio 7, +1V1 prio 6, VREG_LX prio 5, GND prio 4 (solid, clearance 0,15, min. šířka 0,15), GND cesta
  pin 47 → C6 (jinak LX zóna odřízne PGND), prokovy GND (3,1;−4,9)(3,1;−5,5)(3,85;−3,85), +1V1 (0,5;−5,2)(0,5;−5,8)
  pro rozvod k DVDD pinům 6/23/39, +3V3 prokov pod pouzdrem (1,6;−2,45) napájí VIN z In2. Souřadnice vůči středu U1.
- U1 a L1 mají footprinty převzaté z oficiálního RP2350A Minimal R4 (MIT) v `rp2350A_QFN60.pretty`.
  Rozmístění VREG (L1 tečkou k +1V1, C5, C6, C4/R7) kopírovat podle Pico 2 / Minimal – design guide to vyžaduje.
- Pull-up na QSPI_SS není potřeba (v referenci DNF, s W25Q128JV zbytečný).
- L1 = AOTA-B201610S3R3-101-T (doporučení RPi). Vybráno 2026-10-19 (MPN v poli `MPN` ve schématu, rozpis v `PCB/README.md`):
  Q1 SiS434DN (PowerPAK 1212-8, footprint `susicka:Vishay_PowerPAK_1212-8_Single_GSD` = stock s pady 1=G 2=S 3=D),
  Q2/Q4 AO3422 (SOT-23), Q3 AOD4185 (DPAK), L2 Würth 74438356047 (4,7 µH, WE-MAPI 4020; 3,9 µH z datasheetu
  ve 4×4 se neshání, 4,7 µH má SparkFun BabyBuck), F1 Littelfuse 0454004.MR, R25 (NTC pull-up) 22k Yageo RC0603FR-0722KL.
  Q1 při 3,3 V na gate není v datasheetu garantovaný → na prototypu změřit U_DS při náběhu topení (< ~0,2 V = OK).
  D5 = SMBJ24CA (místo SMBJ26CA), aby TVS omezovala špičky pod 40 V tranzistoru Q1 (V_C 38,9 V).
  Alternativa Q1 zvažovaná a zamítnutá: Rohm RQ5H030TN (45 V, garantovaný při 2,5 V, sedí na SOT-23), ale jen 3 A
  trvale – náběh PTC 3–5 A by ho přetěžoval. 40V+ MOSFET s garantovaným 2,5V buzením a ≥ 5 A se nenašel.
- **BOM.md a PCB/README.md nejsou spolehlivé** (generované Gemini pro jeho layout, cca 50 % špatně) – nebrat jako zdroj pravdy.
- Firmware/web na GitHubu je testovací verze pro Pico W; nesoulady se opraví v kódu.
  ID z výrobního čísla je znovu implementované (FIRMWARE `42b6fb4`); původní verze byla možná na jiném PC.
  Projekt používá Pico SDK 2.3.1 / toolchain 15_2_Rel1; ve VS Code otevírat přímo složku `FIRMWARE`, ne kořen.

## Princip fungování

Značení: ✅ rozhodnuto · 💡 návrh (zatím nerozhodnuto).

### Konstrukce boxu
- ✅ Box z PETG FR (UL94 V-0), později ABS FR. Hliník topení nesmí přímo na plast (izolační podložky).
- ✅ Dva oddíly oddělené izolovanou přepážkou: **sušicí komora** (cívka, PTC, ventilátor, SHT40)
  a **oddíl elektroniky** (deska, tenzometr) – teplo se k elektronice a tenzometru nedostane.
- 💡 Komora nad elektronikou; přepážka dvojitá se vzduchovou mezerou nebo s pěnou/korkem,
  oddíl elektroniky větraný ven (ne do komory).

### Vážení (HX711 + tenzometr)
- ✅ Cívka leží na kolébce (💡 2 hřídelky s ložisky 608), kolébka tlačí sloupkem přes přepážku na tenzometr.
- 💡 Tenzometr: hliníkový nosník (straight bar) **2 kg** (3–5 kg s rezervou; 1 kg ne – plná cívka ~1,25 kg).
  Uživatel už má nějaký tenzometr, později výměna za lepší levný (např. TAL220B).
- Pravidla:
  - sloupek se **nesmí dotýkat přepážky** – otvor o 2–3 mm větší, těsnění měkkou membránou/labyrintem,
    které nenese sílu (jinak část váhy jde mimo tenzometr);
  - sloupek **ne z PETG** (creep při 65 °C pod stálou zátěží) – ocel nebo karbon, na konci u tenzometru
    tepelný izolant FR4 nebo PTFE;
  - tenzometr pevně jedním koncem přes podložky (střed volný), šipka ve směru síly, pod volným koncem
    šroub jako **doraz proti přetížení** (~0,5 mm);
  - nic jiného než cívka nesmí ležet na kolébce (např. silikagel by svým přírůstkem vody kazil měření úbytku).
- Firmware: průměrovat 10–30 s (při tisku filament cívku tahá → kolísání), úbytek hodnotit z trendu;
  tára s prázdnou kolébkou, odečet hmotnosti prázdné cívky.

### Ohřev a cirkulace
- ✅ PTC 24 V ohřívá vzduch, ventilátor (24 V, PWM na GPIO13) ho rozhání po komoře a cirkuluje.
- 💡 Ventilátor radiální 5015 (lépe překoná odpor tělesa) nebo axiální 4010.
- 💡 PTC 30 W / Curie 70 °C je bezpečné, ale vzduch nejspíš jen ~55–60 °C (PETG na hraně, ABS ne);
  případně PTC s ventilátorem 50–100 W s vyšší povrchovou teplotou a regulací ve firmwaru.
- Horký vzduch nesmí foukat přímo na sloupek váhy.

### Odvod vlhkosti
Ohřátý vzduch vlhkost z filamentu přijme, ale v uzavřené komoře se absolutní vlhkost zvyšuje a sušení
se zpomalí – vlhkost musí z komory pryč. Uživatel zvažuje silikagel nebo krátké vyvětrání.
- **Silikagel** (kuličky, indikační oranžový → zelený, regenerace 110–120 °C v troubě):
  při 50–65 °C má výrazně nižší kapacitu (při vyšší teplotě vodu spíš uvolňuje) → při aktivním sušení
  pomáhá málo, hodí se hlavně na **skladování** za studena. Nesmí ležet na kolébce váhy.
- **Větrání**: komerční sušičky mají malé větrací otvory. ✅ Řízeně: odtahový ventilátor (GPIO12, J9)
  + druhý SHT40 v oddílu elektroniky/venku; firmware z T a RH spočítá **absolutní vlhkost** (Magnusův vzorec)
  a větrá jen když je uvnitř vyšší než venku (jinak by nasával vlhčí vzduch a ztrácel teplo).
  Dva SHT40 mají stejnou I2C adresu 0x44 → ✅ vyřešeno druhou sběrnicí I2C0 (GPIO8/9, J11).
- 💡 Doporučená kombinace: **sušení = ohřev + cirkulace + řízené větrání**, **skladování = uzavřeno + silikagel**,
  topení vypnuté nebo udržovací (~35 °C).

### Režimy (💡 návrh pro firmware)
| Režim | Topení | Ventilátor | Větrání | Konec |
|---|---|---|---|---|
| Sušení | PID na cílovou teplotu profilu | běží | když AH uvnitř > venku | váha i vlhkost se zploští (trend ~0) |
| Skladování | vypnuto / ~35 °C | občas | ne | – (silikagel) |
| Tisk z boxu | PLA 40–45 °C, jinak dle profilu | běží | dle potřeby | ruční |

Profily: PLA 45–50 °C (při tisku 40–45), PETG 60–65, TPU ~45–55, ABS/PA 70–80+.

### Bezpečnost
- ✅ Curie teplota PTC jako fyzický strop, R15 pull-down na gate (topení vypnuté při resetu).
- ✅ NTC 100k (jako v 3D tiskárnách) přímo u topení na ADC GPIO26 + 4,7 k pull-up: vypnout topení při
  přehřátí tělesa nebo když SHT40 přestane odpovídat. 💡 Watchdog ve firmwaru. ✅ Tepelná pojistka v obvodu topení (svorkovnice J13, TCO na tělese topení;
  vybavovací teplota musí být s rezervou nad provozní teplotou tělesa, protože holding temperature bývá jen ~75–85 °C u 98°C typů).
- Veřejný broker → před ostrým ovládáním topení přejít na broker s heslem.

## Stav layoutu (2026-10-20)

- Deska 70 × 100 mm (na výšku), obrys v Edge.Cuts, H1–H4 M3 v rozích. Zadní (spodní kratší) hrana = jack J4 + svorkovnice;
  RM2 na horní hraně anténou ven, rule area `nrf_keep_out` (všechny Cu vrstvy, x 204–239,5, y 23,05–43,05; zákaz
  footprintů vypnout – jinak DRC hlásí samotný U2).
- Hotovo: krystal (Y1 otočený, XIN/XOUT krátké), VREG podle reference (zóny + C5/C6 RPi footprint), blokování U1,
  RM2 (gSPI WL_CLK 16,5 mm, WL_DATA 14,4 mm, CLK bez prokovů, nic pod modulem), LED, TP12–TP15.
- Další: napájení u jacku (J4 → F1 → Q3 + D4/R19 → D5/C25, U4 + C21–C24/L2), silová část, zóny In1 GND / In2 +3V3,
  zbytek TP a lišt, DRC, popisky.
- Simulace SI: projekt `PCB/simulace/wl_clk.kicad_pro` (ngspice v KiCadu): WL_CLK jako TLINE Z0 ≈ 94 Ω, td ≈ 96 ps
  (0,2 mm, 16,5 mm, h 0,48 mm, FR4) → překmit 3 %, −3 dB na 901 MHz. Přeslech (vázané vedení) model nezahrnuje.
- Kontroly desky dělat přes `kicad-cli pcb drc --format json` a Python API KiCadu
  (`C:/Program Files/KiCad/9.0/bin/python.exe`, `import pcbnew`) – jen při uložené desce a zavřeném KiCadu.

## Generálka desky (2026-10-25, deska uložená 22. 10.)

DRC: 0 chyb clearance, 7 nespojených (J12: GP10, 11, 16, 18, 19, 20, 27), TP3 (+1V1) chybí na desce. Zóny po přepočtu
každá v jednom kuse, cesty bez ostrých úhlů (jen 45°), schéma zapojené správně, footprinty sedí na MPN.
Rozhodnuto 2026-10-26 (deska = prototyp, počítá se s další verzí):
- J12: 7 nedotažených GPIO zůstává záměrně (DRC je bude hlásit). NTC (J10, R25, C26, TP19) na prototypu není –
  topení hlídá jen Curie PTC + TCO na J13 (musí být osazená). TP3 se nepoužije (zatím jen varování parity v DRC).
- J6 (3V3, GND, SCL, SDA) vs J11 (3V3, GND, SDA, SCL) – opačné pořadí záměrně kvůli routingu, popisky sedí.
- J4 přečnívá spodní hranu o ~5 mm záměrně; kolík 2,0 mm = koncovka 5,5/2,1 (pro 5,5/2,5 je PJ-102BH, stejný footprint).
- U JLCPCB se objednává jen deska (bez osazení) → LCSC čísla ani fiduciály netřeba.
- D6 (150060GS75000, U_F 3,2 V) → menší R20, doporučeno 220 Ω (stejný díl jako R8/R9).
- Hotovo: značky +/− u J5, J8, J9 přesunuté do pruhu u hrany desky (0,8 mm / 0,15 mm), popisek D4 vlevo od diody.
  R14 zůstává pod U2 (kolem není místo).
- Hotovo 2026-10-26: TP12 posunutý (3,75 mm od keepoutu antény), popisek TP13 nad ploškou, R20 = 220 Ω, J4 o 0,67 mm výš
  (přesah ~4,4 mm), na In2 GND zóna přes celou desku s prioritou 0 (3V3 zóny 2 a 14) → měď na vrstvách vyrovnaná.
- Stackup v KiCadu (3 × 0,48 mm) neodpovídá JLC JLC04161H-7628 (F.Cu–In1 0,21 mm, vnitřní Cu 0,5 oz) → Z0 WL_CLK
  reálně ≈ 67 Ω, ne 94 Ω; simulaci případně přepočítat.
- Výrobní data: `gerber/susicka_filamentu_JLCPCB_2026-10-26.zip` + návod a parametry objednávky
  `gerber/OBJEDNAVKA_JLCPCB.md`. 2026-10-27: 16 děr 0,25 mm (7 prokovů VREG + 9 v termální plošce U1) zvětšeno na 0,3 mm (kroužek 0,6 mm, DRC i zóny beze změny) kvůli ceně u JLC → nový ZIP `susicka_filamentu_JLCPCB_2026-10-27.zip`, povrch OSP místo ENIG, stencil 0,10 mm. **Deska OBJEDNÁNA 2026-10-27** u JLCPCB (5 ks, OSP, via plugged, stencil 0,1 mm, apertury 1:1 podle F.Paste, EuroPacket DDP, 5–9 prac. dnů). **Součástky OBJEDNÁNY 2026-10-27 na Mouseru** (38 položek, FedEx DDP; podle `jlcpcb/MOUSER_IMPORT.csv`, počty rezerv v košíku ručně snížené) + pasta Chip Quik TS391SNL50 (SAC305 T4, kelímek 50 g, bez lednice, peak ~245 °C) a tavidlo SMD291NL-5M. Náhrady proti původnímu BOM (stejná hodnota i pouzdro, zapsané jen v `BOM_JLCPCB.csv`, schéma beze změny): D3/D7 1N5819HW-7-F (B5819W-TP jen po cívce), C19 CL10A106KP8NQSC, C22 KEMET C0603C104K5RACTU, C23/C24 Taiyo Yuden MLASL21GBB5226MTNA01, U3 W25Q128JVSIQ TR, D5 SMBJ24CA od Semtech; U1 na Mouseru jako SC1509(13)-A4 (358-SC150913). Na TME zbývá AO3422 5 ks + AOD4185 3 ks (`jlcpcb/TME_IMPORT.csv`), Mouser je nevede. Debug Probe (SWD) – ověřit, jestli je koupený.
  `jlcpcb/BOM_JLCPCB.csv` = nákupní soupiska s MPN (ověřeno proti schématu 2026-10-26, R20 220 Ω): svorkovnice
  Phoenix 1715022 (MKDS 1,5/ 2, rozteč 5,0 mm – 1715721 je 5,08 mm!), lišty Würth WR-PHD 61300311121 / 61300411121 /
  61301421121, GND očka TP4/TP5/TP12 Keystone 5001 (díra 1,0 mm). Nekupuje se: H1–H4 a ploškové TP (vyrobí JLC).
  SW1 má uživatel vlastní. Sloupce Qty (ks na desku) + Mouser/TME = odkazy na vyhledávání podle MPN (RP2350A a RM2
  hledat jako „RP2350A“ / „SC1169“ – Raspberry Pi kódy; na TME je nejspíš nemají). `CPL_JLCPCB.csv` není v gitu.

## Harmonogram

Říjen 2026 schválení konceptu · listopad–prosinec KiCad + 3D model · leden 2027 osazení a oživení ·
únor firmware a MQTT · březen–duben web a testy sušení · odevzdání duben 2027.

## Otevřené body z revize schématu (2026-10-19)

- Tepelná pojistka (TCO na J13) zatím nevybraná – nejdřív na prototypu změřit teplotu tělesa topení.
- ERC zatím neřešit (53 porušení: hlavně neshoda symbolů s knihovnou, chybějící knihovna vlastních symbolů,
  PWR_FLAG, nezapojené GPIO6/7, R4/R5 a footprint J1). USB (J1…) zůstává v návrhu.
- USB se nebude používat (DNP) → jeho chyby (prohozené D+/D-, R4/R5) se neřeší.
- BOOTSEL tlačítko (1 k na QSPI_SS) zatím ne – programuje se přes SWD.

Hotovo 2026-10-19: list `vystupy.kicad_sch` – topení (přesunuto z hlavního listu, J5/Q1/R16 100 Ω/R15 100 k/D2),
ventilátor 24 V na GPIO13 (J8/Q2/R17/R18/D3), ochrana vstupu F1/Q3/D4/R19/D5/C25, LED na RM2 GPIO0, tlačítko GPIO15,
I2C pull-upy. Svorkovnice J5/J8: pin 1 = spínaná zem, pin 2 = +24 V. D2 = `Device:D_Schottky` (oprava A/K vs 1/2).
Schéma se generovalo skriptem – vizuálně zkontrolováno přes `kicad-cli sch export pdf` + Poppler (`pdftoppm`, nainstalován přes winget).
Hotovo 2026-10-19 (2. kolo, list `vystupy`): odtahový ventilátor na GPIO12 (J9, Q4, R23 100 Ω, R24 100 k, D7 B5819W;
kopie bloku Q2, J9 pin 1 = spínaná zem, pin 2 = +24 V), NTC topení na GPIO26 (R25 4k7 pull-up na 3V3, C26 100 nF 0402
na GND – umístit u U1, J10: 1 = ADC, 2 = GND), druhý SHT40 na I2C0 GPIO8/9 (J11 3V3/GND/SDA/SCL jako J6,
R26/R27 4k7 pull-upy, C27 100 nF u lišty). ERC 69 → 65, žádné nové chyby.
Hotovo 2026-10-19 (3. kolo): tepelná pojistka J13 v obvodu topení (`HEAT_V`), nový list `rozsireni` (J12 GPIO lišta,
TP1–TP5), viditelné hodnoty +3V3/+1V1 u napájecích šipek. ERC 65 → 54, žádné nové chyby.
Hotovo 2026-10-19 (4. kolo): vybrané součástky Q1–Q4, L2, F1 s footprinty a poli Manufacturer/MPN, nová knihovna
`susicka.pretty` (PowerPAK GSD), odstraněn duplicitní pull-down R12 na BT_ON (zůstává R11 na WL_ON). ERC 54 → 53.
Firmware musí doplnit: ventilátor na GPIO13 (PWM), topení na GPIO14, I2C1 na GPIO2/3, HX711 na GPIO4/5,
PWM odtahového ventilátoru na GPIO12, I2C0 na GPIO8/9 (druhý SHT40), ADC0 (GPIO26) s převodem NTC na °C
(Steinhart–Hart / B rovnice, B = 3950, R25 = 22 k – změněno z 4,7 k kvůli citlivosti v rozsahu 25–90 °C) a vypnutí topení při přehřátí nebo chybě čidla (NTC rozpojené/zkrat).
- `config.h` s Wi-Fi heslem odebrán z gitu v PCB (`203bbed`) i WEB (`d374922`), ale heslo zůstává
  v historii na GitHubu → heslo k Wi-Fi změnit.
