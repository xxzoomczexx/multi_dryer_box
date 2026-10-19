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

## 🧩 Přehled pasivních pouzder (0603 & 0805)

- **Běžná signálová a blokovací pasiva (0603 / 1608 Metric):** Všechny rezistory `R1` až `R15`, zátěžové kondenzátory 15 pF (`C1, C2`), filtr 4.7 nF (`C3`), blokovací kondenzátory 100 nF a lokální filtrace 4.7 µF jsou sjednoceny na pouzdro **0603**.
- **Výkonová pasiva (0805 / 2012 Metric):**
  - `C21` (10 µF, 50 V): Vstupní keramický kondenzátor buck měniče AP63203 (0805 nutné kvůli zachování kapacity při stejnosměrném DC biasu 24 V).
  - `C23, C24` (22 µF, 10 V): Výstupní filtrace měniče (0805 pro nízký ESR a zvlnění).
  - `L1` (3.3 µH VREG): 2016 metric / 0805 (Abracon AOTA-B201610).
  - `L2` (3.9 µH Buck): 0805 (saturační proud $\ge 2\text{ A}$).

---

## 📏 Návod pro Layout a DRC v KiCad 9

1. **Keepout zóna pro Wi-Fi anténu:** Pod anténní částí modulu RM2 je striktně dodržena zóna o rozměrech **35.5 × 18.5 mm** bez mědi na všech 4 vrstvách pro maximální dosah Wi-Fi.
2. **Výsledek DRC (Design Rule Check):** **0 porušení pravidel (0 DRC violations), 0 nepropojených spojů (0 unconnected items)**.