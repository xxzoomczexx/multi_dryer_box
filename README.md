# 🛠️ Multi-Box Filament Dryer - Hardware & 4-Layer PCB Design

Hardwarový návrh plošného spoje (PCB) pro řídicí desku sušičky filamentu s mikrokontrolérem **Raspberry Pi RP2350A** a Wi-Fi modulem **Raspberry Pi RM2**.

---

## 🎛️ 4-Vrstvý PCB Stackup (Maturitní Standard)

Návrh využívá **4vrstvou desku plošných spojů (4-Layer PCB)** o rozměrech **85 × 65 mm** pro zajištění vynikající elektromagnetické kompatibility (EMC), nízkého šumu pro 24-bitový ADC převodník váhy HX711 a stabilního chodu Wi-Fi modulu.

| Vrstva | Název v KiCad | Typ | Popis / Využití |
| :--- | :--- | :--- | :--- |
| **L1 (Top)** | `F.Cu` | **Signal & Power** | Hlavní signálové vodiče (I2C, HX711, SWD, SPI pro Flash a RM2), součástky a silové 24V trasy. |
| **L2 (Inner 1)** | `In1.Cu` | **GND Plane** | **Plná souvislá zemní plocha (GND)** pod všemi čipy, napájecím zdrojem i RF částí. |
| **L3 (Inner 2)** | `In2.Cu` | **Power Plane** | Rozlitá napájecí zóna (**+3.3V** pro logiku, mikrokontrolér, Flash i Wi-Fi modul). |
| **L4 (Bottom)**| `B.Cu` | **Signal / GND**| Propojovací signálové vodiče a spodní stínění zemí. |

---

## ⚡ Dimenzování napájení a dynamika PTC ohřevu (3–5 A)

- 🔌 **Vstup 24 V DC:** Přes jack `PJ-102AH` dimenzovaný na trvalý proud 5 A.
- 🔥 **PTC topné články:** Nominální příkon 30 W při 24 V (1.25 A), avšak **startovací proud za studena dosahuje 3 až 5 A**.
- 📏 **Silové spoje na PCB:**
  - Hlavní trasa 24V (`J4` pin 1 $\to$ svorkovnice `J5` pin 1) má šířku **1.5 mm** s odbočkou 0.8 mm k buck měniči `U4`.
  - Spínaná větev (`J5` pin 2 $\to$ MOSFET `Q1` Drain $\to$ Schottky dioda `D2`) má šířku **1.5 mm / 1.2 mm**.
  - Návratový uzel MOSFETu `Q1` (Source $\to$ GND) je posílen **3 paralelními prokovy** (vrtání 0.4 mm, mezikruží 0.8 mm) přímo do celistvé L2 GND roviny.
  - Sběrnice váhy HX711 (`GPIO4`, `GPIO5`) je důsledně trasována mimo silové spínací pole pro nulové rušení měření.

---

## 🧩 Přehled pasivních pouzder (0402 & 0603, větší jen kde je nutné)

Základ je **0402 / 0603** (pájení v peci + pinzeta). Větší pouzdro jen tam, kde to vyžaduje napětí 24 V nebo DC bias velkých keramických kondenzátorů.

| Pouzdro | Součástky | Proč |
| :--- | :--- | :--- |
| **0402** (1005 Metric) | `C7–C18, C20` (100 nF, 10–16 V X7R), `C1, C2` (15 pF C0G) | Blokovací kondenzátory musí sedět co nejblíž pinům RP2350 / RM2 / flash, krystalové kondenzátory těsně u Y1. |
| **0603** (1608 Metric) | všechny rezistory `R1–R15`; `C4, C5, C6` (4,7 µF, 10 V X5R), `C19` (10 µF, 10 V X5R), `C3` (4,7 nF, DNP), `C22` (100 nF, **50 V**, bootstrap) | Rezistory jsou na 3,3 V a ztrácejí ≪ 0,1 W. C22 je mezi SW a BST: napětí na něm je jen ~5 V, ale kvůli 24V uzlu SW se volí 50 V. |
| **0805** (2012 Metric) | `C23, C24` (22 µF, **16 V** X5R/X7R) | Výstup měniče 3,3 V. 22 µF v 0603 ztratí při 3,3 V DC biasu víc než polovinu kapacity. |
| **1210** (3225 Metric) | `C21` (10 µF, **50 V** X7R) | Vstupní kondenzátor měniče na **24 V**. Napětí ≥ 2× pracovní, při 24 V zůstane ~3–4 µF. |
| **2016** (`rp2350A_QFN60:L_Abracon_AOTA-B201610`) | `L1` (3,3 µH, Abracon AOTA-B201610S3R3-101-T) | Cívka interního VREG RP2350. Footprint převzatý z RP2350A Minimal R4. **Tečka = pin 1 = +1V1, orientace je kritická** (viz Hardware design with RP2350, kap. 2.1). |
| **4×4 mm** (Würth WE-MAPI 4020) | `L2` (4,7 µH, 74438356047, I<sub>R</sub> 2,9 A) | Cívka buck měniče AP63203 (2 A). Pouzdro 0805 je na to výrazně poddimenzované. |

**U1 (RP2350A)** používá footprint `rp2350A_QFN60:RP2350A_QFN-60_RPi_Minimal` převzatý z oficiálního návrhu Raspberry Pi RP2350A Minimal R4 (licence MIT). EP 3,4 × 3,4 mm má 9 prokovů (vrták 0,25 mm, ploška 0,6 mm) a rozdělenou pastu. **Y1** = Abracon ABM8-272-T3 (12 MHz), doporučený krystal podle design guide.

Silové díly na 24 V, které nejsou pasivní: `D2` SS14 (SMA, 40 V / 1 A) vyhovuje; `Q1` = SiS434DN v PowerPAK 1212-8 (viz tabulka vybraných součástek níže).

---

## 🔌 Výstupy, ochrana vstupu a periferie

Topení, ventilátor, ochrana vstupu, LED, tlačítko a I2C pull-upy jsou na listu `vystupy.kicad_sch`. S hlavním listem je propojují globální labely (`HEAT_PWM`, `FAN_PWM`, `BTN`, `SDA`, `SCL`, `WL_GPIO0`, `24V`, `24V_IN`).

Oba výstupy mají stejné zapojení a stejnou svorkovnici: **pin 1 = spínaná zem (−), pin 2 = +24 V**.

| Blok | Součástky | Zapojení |
| :--- | :--- | :--- |
| **Topení** (PTC 24 V / 30 W) | `J5` svorkovnice 5 mm, `Q1` N-MOSFET, `R16` 100 Ω do gate, `R15` 100 k pull-down, `D2` SS14 (SMA) | GPIO14 (`HEAT_PWM`) → R16 → gate Q1, low-side spínání, pomalé PWM ~1 Hz |
| **Ventilátor** (24 V, 2pin) | `J8` svorkovnice 5 mm, `Q2` N-MOSFET SOT-23, `R17` 100 Ω, `R18` 100 k, `D3` B5819W | GPIO13 (`FAN_PWM`) → R17 → gate Q2, low-side, D3 = nulová dioda motoru |
| **Ochrana vstupu** | `F1` 4 A T (Nano2), `Q3` P-MOSFET DPAK, `D4` BZT52C15, `R19` 10 k, `D5` SMBJ24CA, `C25` 100 µF/50 V | J4 (`24V_IN`) → F1 → Q3 (ochrana proti přepólování, D na vstupu, S na výstupu) → `24V`. D4 omezí V<sub>GS</sub> Q3 na 15 V. |
| **Odtahový ventilátor** (24 V, 2pin) | `J9` svorkovnice 5 mm, `Q4` N-MOSFET SOT-23 (jako Q2), `R23` 100 Ω, `R24` 100 k, `D7` B5819W | GPIO12 (`EXH_PWM`, PWM 6A) → R23 → gate Q4, řízené větrání komory |
| **NTC topení** | `J10` lišta 1×2 (1 = ADC, 2 = GND), `R25` 22k 1 % (Yageo RC0603FR-0722KL), `C26` 100 nF 0402 | 3V3 → R25 → GPIO26/ADC0 (`NTC_ADC`) → NTC 100k B3950 (mimo desku) → GND. C26 umístit u pinu U1. |
| **Druhý SHT40** (I2C0) | `J11` lišta 1×4 (3V3, GND, SDA, SCL jako J6), `R26`/`R27` 4k7, `C27` 100 nF | GPIO8 = `SDA0`, GPIO9 = `SCL0`. Samostatná sběrnice, takže oba SHT40 můžou mít stejnou adresu 0x44. |
| **Tepelná pojistka topení** | `J13` svorkovnice 5 mm | 24V → J13 (TCO mimo desku, na tělese topení) → `HEAT_V` → J5 pin 2. D2 zůstává přímo přes topení. |
| **Lišta GPIO** (list `rozsireni`) | `J12` 2×7, 2,54 mm | 1 = 3V3, 2 a 14 = GND, 3–13 = GP10, GP11, GP16–GP22, GP27, GP28 (přímo z RP2350, bez ochrany) |
| **Testovací body** (list `rozsireni`) | `TP1`–`TP5` | TP1 24V, TP2 3V3, TP3 1V1 (ploška Ø 1,5 mm), TP4/TP5 GND (drátěné očko pro krokosvorku) |
| **Testovací body – komunikace** (list `rozsireni`) | `TP6`–`TP19` ploška Ø 1 mm, `TP12` GND očko | TP6/7 SDA/SCL (I2C1), TP8/9 SDA0/SCL0 (I2C0), TP10/11 HX711_DT/SCK (GPIO4/5), TP13/14/15 WL_CLK/WL_CS/WL_DATA (RM2 gSPI, GPIO29/25/24), TP16/17/18 HEAT/FAN/EXH_PWM, TP19 NTC_ADC. Pro logický analyzátor a osciloskop; QSPI flash záměrně bez TP (rychlá, ladí se přes SWD). V layoutu dávat plošky přímo na cestu, bez odboček. |
| **Montážní otvory** (list `rozsireni`) | `H1`–`H4` M3 | `MountingHole_3.2mm_M3` bez mědi (box z plastu). Pozice podle layoutu; pro uzemnění změnit na `MountingHole_3.2mm_M3_Pad_Via`. |
| **Stavová LED** | `D6` LED 0603, `R20` 1 k | GPIO0 modulu RM2 (`WL_GPIO0`), stejně jako LED na Pico 2 W. Firmware ji ovládá přes `CYW43_WL_GPIO_LED_PIN`. |
| **Tlačítko** | `SW1` 6 × 6 mm THT | GPIO15 (`BTN`) proti GND, interní pull-up |
| **I2C pull-upy** | `R21`, `R22` 4k7 | GPIO2 = SDA, GPIO3 = SCL. Neosazovat, pokud má modul SHT4x vlastní pull-upy. |

### Vybrané součástky (MPN je ve schématu v poli `MPN`)

| Pozice | Součástka | Footprint | Poznámka |
| :--- | :--- | :--- | :--- |
| `Q1` topení | Vishay **SiS434DN** (SIS434DN-T1-GE3) | `susicka:Vishay_PowerPAK_1212-8_Single_GSD` | 40 V, 9,2 mΩ @ 4,5 V, V<sub>GS(th)</sub> max 2,2 V. R<sub>DS(on)</sub> při 3,3 V není v datasheetu garantovaný – na prototypu změřit úbytek U<sub>DS</sub>. Footprint = stock PowerPAK s přečíslovanými pady (1 = G, 2 = S, 3 = D). |
| `Q2`, `Q4` ventilátory | AOS **AO3422** | SOT-23 | 55 V, 2,1 A, R<sub>DS(on)</sub> < 200 mΩ @ V<sub>GS</sub> 2,5 V. Kupovat originál AOS (klony MSKSEMI/JSMSEMI mají jiné parametry). |
| `Q3` přepólování | AOS **AOD4185** | TO-252-2 (DPAK) | −40 V, −40 A, 20 mΩ @ −4,5 V; V<sub>GS</sub> omezeno D4 na −15 V. |
| `L2` | Würth **74438356047** (WE-MAPI 4020, 4,7 µH), Mouser 710-74438356047 | `L_Wuerth_MAPI-4020` | I<sub>R</sub> 2,9 A, DCR 76 mΩ. Datasheet AP63203 uvádí 3,9 µH, ve 4×4 mm se ale shání špatně; 4,7 µH je ověřené na SparkFun BabyBuck (AP63203), EVM Diodes používá 6,8 µH. |
| `R25` (NTC pull-up) | Yageo **RC0603FR-0722KL** (22k 1 %) | 0603 | 22k ≈ odpor NTC 100k B3950 při ~65 °C → největší citlivost v pracovním rozsahu (25 → 90 °C: 2,70 → 0,98 V; se 4k7 jen 3,15 → 2,20 V). |
| `F1` | Littelfuse **0454004.MR** | `Fuse_Littelfuse-NANO2-451_453` | Nano2 454 Slo-Blo 4 A, stejné pouzdro 6,1 × 2,69 mm jako řada 453. |

TVS `D5` = Littelfuse **SMBJ24CA** (obousměrná, V<sub>R</sub> 24 V, V<sub>BR</sub> min 26,7 V, V<sub>C</sub> 38,9 V). Původní SMBJ26CA omezovala až na ~42 V, tedy nad V<sub>DS</sub> 40 V tranzistoru Q1; SMBJ24CA drží špičky pod 40 V. 24V adaptér ji neotevře (otevírá až od 26,7 V).

**Ověření Q1 na prototypu:** při náběhu topení změřit U<sub>DS</sub> na Q1. Pod ~0,2 V je tranzistor z 3,3 V sepnutý naplno; při vyšší hodnotě hledat jiný Q1 (záloha: Rohm RQ5H030TN – garantovaný při 2,5 V, ale jen 3 A trvale).

`D2` teď používá standardní symbol `Device:D_Schottky`, jehož piny odpovídají ploškám footprintu `D_SMA`. Původní symbol SS14 z knihovny Digi-Key měl piny A/K, ne 1/2, a dioda proto nebyla připojená.

## 📏 Návod pro Layout a DRC v KiCad 9

1. **Keepout zóna pro Wi-Fi anténu:** Pod anténní částí modulu RM2 je striktně dodržena zóna o rozměrech **35.5 × 18.5 mm** bez mědi na všech 4 vrstvách pro maximální dosah Wi-Fi.
2. **Výsledek DRC (Design Rule Check):** **0 porušení pravidel (0 DRC violations), 0 nepropojených spojů (0 unconnected items)**.