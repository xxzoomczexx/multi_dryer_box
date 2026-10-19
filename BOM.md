# Kusovník součástek (Bill of Materials – BOM)
**Projekt:** IoT Sušička filamentu (*Maturitní práce*)  
**Deska:** 4vrstvá DPS (85 × 65 mm)  
**Datum revize:** 19. 9. 2026  

Tento kusovník obsahuje kompletní seznam všech součástek osazených na desce plošných spojů, včetně přesných katalogových čísel a odkazů z tabulky `C:\Users\mirac\Desktop\soucastky.xlsx`. Běžná signálová a blokovací pasiva jsou standardizována na **SMD 0603 (1608 Metric)** dle doporučení a preferencí, zatímco výkonové prvky zachovávají dimenzovaná pouzdra (0805 pro 24V keramiku a cívky).

---

## 1. Souhrnná nákupní tabulka (Sdruženo podle typu součástky)

| Označení | Hodnota / Typ | Pouzdro | Počet | Reference na desce | Výrobce / Objednací kód | Odkaz na nákup |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **U1** | **RP2350A** (MCU Dual ARM/RISC-V) | QFN-60 (7×7 mm, pitch 0,4 mm) | 1 ks | `U1` | Raspberry Pi `RP2350A0A4` | [TME](https://www.tme.eu/cz/details/sc1509-a4/raspberry-pi-vestavene-systemy/raspberry-pi/raspberry-pi-rp2350a0a4-7-reel/) |
| **U2** | **RM2** (Wi-Fi 4 / BLE 5.2 modul) | LGA / Castellated | 1 ks | `U2` | Raspberry Pi `RPI-RMC20452T` | [RPiShop](https://rpishop.cz/602192/raspberry-pi-radio-module-rmc20452t/) |
| **U3** | **W25Q128JVS** (128 Mbit QSPI Flash) | SOIC-8 (208 mil, 5,3×5,3 mm) | 1 ks | `U3` | Winbond `W25Q128JVSIQ-TR` | [Mouser](https://cz.mouser.com/ProductDetail/Winbond/W25Q128JVSIQ-TR?qs=qSfuJ%252Bfl%2Fd7vTyLA9kNdGw%3D%3D) |
| **U4** | **AP63203WU-7** (Step-down 24V $\to$ 3,3V 2A) | TSOT-23-6 | 1 ks | `U4` | Diodes Inc `AP63203WU-7` | [Mouser](https://cz.mouser.com/ProductDetail/Diodes-Incorporated/AP63203WU-7?qs=u16ybLDytRZ1JqxbuLkMJw%3D%3D) |
| **Y1** | **ABM8-272-T3** (Krystal 12.000 MHz) | SMD 3225-4Pin (3,2×2,5 mm) | 1 ks | `Y1` | Abracon `ABM8-272-T3` | [TME](https://www.tme.eu/cz/details/abm8-272-t3/resonators-and-generators/abracon/) |
| **L1** | **3,3 $\mu$H** (Power Inductor, VREG Core) | SMD 2016 / 0805 | 1 ks | `L1` | Abracon `AOTA-B201610S3R3-101-T` | [TME](https://www.tme.eu/cz/details/aota-b201610s3r3-1/tlumivky/abracon/aota-b201610s3r3-101-t/) |
| **L2** | **3,9 $\mu$H** (Power Inductor, Buck 3.3V) | SMD 2016 / 0805 | 1 ks | `L2` | Würth / Bourns (proud $\ge 2\text{ A}$) | Běžný SMD induktor |
| **Q1** | **N-MOSFET** (Spínač topení, 30V $\ge 5\text{A}$) | SOT-23 | 1 ks | `Q1` | např. `AO3400A` nebo `Si2302DS` | Běžný N-FET logická úroveň |
| **D1** | **USBLC6-2SC6** (ESD ochrana USB, DNP) | SOT-23-6 | 1 ks | `D1` | STMicroelectronics `USBLC6-2SC6` | TME / Mouser |
| **D2** | **SS14** (Schottky dioda 40V 1A / 30A špička) | SMA (DO-214AC) | 1 ks | `D2` | Běžná Schottky dioda `SS14` | TME / Mouser |
| **J4** | **PJ-102AH** (DC Jack 2,1×5,5 mm, 5A) | THT | 1 ks | `J4` | Same Sky (CUI) `PJ-102AH` | [Mouser](https://cz.mouser.com/ProductDetail/Same-Sky/PJ-102AH?qs=WyjlAZoYn50Yq4CrVLCXLw%3D%3D) |
| **J5** | **MKDS 1,5/ 2-5,00** (Šroubová svorkovnice 2p) | THT, rozteč 5,00 mm | 1 ks | `J5` | Phoenix Contact `1715721` | TME / Mouser |
| **J2** | **PinHeader 1×03** (SWD, rozteč 2,54 mm) | THT Vertical | 1 ks | `J2` | Lámací kolíková lišta 2,54 mm | Běžná lišta |
| **J3, J6, J7** | **PinHeader 1×04** (Rozteč 2,54 mm / JST-XH) | THT Vertical | 3 ks | `J3, J6, J7` | Lámací kolíková lišta / JST-XH | Běžná lišta |

---

## 2. Pasivní součástky – Kondenzátory

| Hodnota | Pouzdro | Dielektrikum / Napětí | Počet | Označení na desce | Funkce v zapojení |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **15 pF** | **SMD 0603** | C0G/NP0, 50V | 2 ks | `C1, C2` | Zátěžové kondenzátory 12MHz krystalu Y1 |
| **4,7 nF** | **SMD 0603** | X7R, 50V | 1 ks | `C3` | Vysokofrekvenční filtr na vstupu napájení USB |
| **100 nF** ($0{,}1\,\mu\text{F}$) | **SMD 0603** | X7R, 25V / 50V | 13 ks | `C7, C8, C9, C10, C11, C12, C13, C14, C15, C17, C18, C20, C22` | Blokování VDD/IO pinů MCU, Flashky, RM2 a Bootstrap pro U4 |
| **4,7 $\mu$F** | **SMD 0603** | X5R/X7R, 10V / 16V | 4 ks | `C4, C5, C6, C16` | Filtrace VREG_AVDD, Core 1.1V a lokální zásoba 3.3V |
| **10 $\mu$F** | **SMD 0603** | X5R, 10V | 1 ks | `C19` | Filtrace napájení modulu RM2 (3.3V větev) |
| **10 $\mu$F** | **SMD 0805** | X5R/X7R, 35V / 50V | 1 ks | `C21` | Vstupní filtrace 24V u měniče U4 (*0805 nutné pro zachování kapacity při DC bias*) |
| **22 $\mu$F** | **SMD 0805** | X5R/X7R, 10V / 16V | 2 ks | `C23, C24` | Výstupní filtrace 3,3V měniče AP63203 (*0805 pro nízký ESR a proudové zatížení*) |

---

## 3. Pasivní součástky – Rezistory (všechny SMD 0603)

| Hodnota | Pouzdro | Tolerance | Počet | Označení na desce | Funkce v zapojení |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **27 $\Omega$** | **SMD 0603** | 1 %, 0603 | 2 ks | `R4, R5` | Sériové zakončení diferenciálních linek USB D+ / D- |
| **33 $\Omega$** | **SMD 0603** | 1 %, 0603 | 1 ks | `R7` | Filtrační odpor pro interní lineární regulátor (VREG_AVDD) |
| **220 $\Omega$** | **SMD 0603** | 1 %, 0603 | 2 ks | `R8, R9` | Sériové tlumicí rezistory pro SPI signály modulu RM2 |
| **470 $\Omega$** | **SMD 0603** | 1 %, 0603 | 1 ks | `R14` | Tlumení datové linky modulu RM2 |
| **1 k$\Omega$** | **SMD 0603** | 1 %, 0603 | 1 ks | `R1` | Sériový tlumicí rezistor oscilátoru Y1 (XOUT) |
| **5,1 k$\Omega$** | **SMD 0603** | 1 %, 0603 | 2 ks | `R2, R3` | Konfigurační pull-down rezistory USB-C (CC1 / CC2) |
| **10 k$\Omega$** | **SMD 0603** | 1 %, 0603 | 4 ks | `R10, R11, R12, R13` | Pull-up pro RUN/Reset tlačítko a řídicí linky RM2 |
| **100 k$\Omega$** | **SMD 0603** | 5 %, 0603 | 1 ks | `R15` | Pull-down Gate rezistor pro MOSFET topení Q1 |
| **1 M$\Omega$** | **SMD 0603** | 5 %, 0603 | 1 ks | `R6` | Paralelní zpětnovazební rezistor krystalu Y1 |

*Celkem rezistorů:* **15 ks** (všechny v pouzdru SMD 0603 / 1608Metric).
