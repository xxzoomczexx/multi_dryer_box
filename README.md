# 🛠️ Multi-Box Filament Dryer - Hardware & 4-Layer PCB Design

Hardwarový návrh plošného spoje (PCB) pro řídicí desku sušičky filamentu s mikrokontrolérem **Raspberry Pi RP2350A** a Wi-Fi modulem **Raspberry Pi RM2**.

---

## 🎛️ 4-Vrstvý PCB Stackup (Maturitní Standard)

Návrh využívá **4vrstvou desku plošných spojů (4-Layer PCB)** pro zajištění vynikající elektromagnetické kompatibility (EMC), nízkého šumu pro 24-bitový ADC převodník váhy HX711 a stabilního chodu Wi-Fi modulu.

| Vrstva | Název v KiCad | Typ | Popis / Využití |
| :--- | :--- | :--- | :--- |
| **L1 (Top)** | `F.Cu` | **Signal** | Hlavní signálové vodiče (I2C, HX711, SWD, SPI pro Flash a RM2, spínání MOSFETu). |
| **L2 (Inner 1)** | `In1.Cu` | **GND Plane** | **Plná souvislá zemní plocha (GND)** pod všemi čipy, napájecím zdrojem i RF částí. |
| **L3 (Inner 2)** | `In2.Cu` | **Power Plane** | Rozlitá napájecí zóna (**+3.3V** a rozvod **+5V / +12V** pro topná tělesa). |
| **L4 (Bottom)**| `B.Cu` | **Signal / GND**| Propojovací signálové vodiče a spodní stínění zemí. |

---

## 🧩 Hlavní Hardwarové Bloky (Hierarchická Schémata)

- ⚡ **`pwr.kicad_sch` (Napájecí zdroj):** Spínaný DC-DC buck měnič **AP63203WU** (vstup 3.8 V až 32 V přes jack `PJ-102AH`, výstup **+3.3 V / 2 A** pro RP2350, Flash i RM2).
- 📡 **`RM2.kicad_sch` (Wi-Fi / BT modul):** Modul **Raspberry Pi RM2** (čip CYW43439) připojený přes rozhraní SPI.
- 💾 **`flash.kicad_sch` (Flash paměť):** 16 MB QSPI Flash paměť **W25Q128JVS** pro uložení firmwaru.
- 🔌 **`susicka_filamentu.kicad_sch` (Mikrokontrolér a konektory):**
  - **Čip:** RP2350A (QFN-60).
  - **Programování:** **SWD Konektor** (`J2` - 3-pin / 4-pin Header: `SWCLK`, `SWDIO`, `GND`, `+3V3`). *(USB větev je vynechána - DNP)*.
  - **I2C Senzor teploty a vlhkosti:** Rozhraní pro senzor SHT40 (`SDA`, `SCL` s 4.7kΩ pull-up rezistory).
  - **Tenzometr váhy (HX711):** 4-pin konektor pro HX711 (`VCC`, `SCK`, `DT`, `GND`).
  - **MOSFET Spínač topení:** N-kanálový MOSFET (**AO3400A** / **IRLML6344TRPBF** v pouzdře SOT-23) s 10kΩ pulldown rezistorem na gate a ochrannou flyback diodou.

---

## 📏 Návod pro Layout a DRC v KiCad

1. **Keepout zóna pro Wi-Fi anténu:** Pod anténní částí modulu RM2 odstraňte měděné zóny ze všech 4 vrstev pro zachování plného dosahu Wi-Fi.
2. **GND Vrstva (In1.Cu):** Narušovat souvislou zemní plochu L2 co nejméně. Všechny piny GND připojovat krátkými prokovy (vias) přímo na L2.
3. **Filtrační kondenzátory:** Blokovací kondenzátory 100 nF a 10 µF umístit těsně k napájecím pinům RP2350A, W25Q128, AP63203 i RM2.

---