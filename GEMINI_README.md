# 🧠 Multi-Box Filament Dryer System – Gemini AI Knowledge Base & Context README
> **Účel dokumentu:** Tento dokument slouží jako kompletní systémová a technická znalostní báze (Knowledge Base) pro **Google Gemini AI** (Gemini Sešity / Gems / Google NotebookLM). Poskytuje detailní přehled o celém projektu, jeho architektuře, hardwaru, firmwaru, webovém rozhraní a přesném rozdělení do jednotlivých Git větví (branches).

---

## 📌 1. Základní informace o projektu

* **Název projektu:** Multi-Box Filament Dryer System (IoT Sušička filamentu)
* **Typ práce:** Maturitní práce (Střední průmyslová škola – IoT, Embedded Hardware & Software)
* **Autor:** Míra Černý ([@xxzoomczexx](https://github.com/xxzoomczexx))
* **GitHub repozitář:** `xxzoomczexx/multi_dryer_box`
* **Živý webový dashboard (GitHub Pages):** [https://xxzoomczexx.github.io/multi_dryer_box/](https://xxzoomczexx.github.io/multi_dryer_box/)

### Řešený problém
3D tiskové struny (filamenty jako PLA, PETG, ABS, Nylon/PA, TPU) jsou silně hygroskopické – absorbují vzdušnou vlhkost. Vlhký filament při tisku v trysce vře, způsobuje mikrovýbuchy páry, defekty povrchu (*stringing*, *blobs*), ztrátu pevnosti mezi vrstvami a ucpávání trysky.

### Cíl a řešení systému
Modulární systém pro monitorování a řízení více filamentových sušiček současně:
1. **Měření v reálném čase:** Teplota (°C), relativní vlhkost (% RH) a hmotnost cívky (g) pomocí tenzometru. Sledováním úbytku hmotnosti v čase se přímo měří rychlost odpařování vody.
2. **Přímá konektivita do cloudu:** Master Node (RP2350 / RP2040) se přes Wi-Fi a protokol MQTT (lwIP stack) připojuje přímo k brokeru bez nutnosti mít spuštěný mezilehlý počítač nebo skript.
3. **Automatická škálovatelnost (Multi-Box):** Plug & Play architektura – každý box si odvodí unikátní ID z hardwarové MAC adresy. Jeden firmware funguje na libovolném počtu sušiček.
4. **Cloudový dashboard:** Statická Single-Page aplikace na GitHub Pages komunikující přes Secure WebSockets (`wss://`) s živými grafy úbytku hmotnosti a vzdáleným řízením (výběr materiálu, spuštění/zastavení).

---

## 🏗️ 2. Celková systémová architektura & Tok dat

```text
  ┌────────────────────────────────────────────────────────┐
  │                 SUŠICÍ BOX (Hardware)                  │
  │  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐ │
  │  │  SHT40 Temp  │   │ HX711 Váha   │   │ Topné těleso│ │
  │  │   & Humidity │   │  (Tenzometr) │   │  + MOSFET   │ │
  │  └──────┬───────┘   └──────┬───────┘   └──────▲──────┘ │
  └─────────┼──────────────────┼──────────────────┼────────┘
            │ I2C              │ Data/Clock       │ PWM/GPIO
  ┌─────────▼──────────────────▼──────────────────┴────────┐
  │         ŘÍDICÍ JEDNOTKA (Master Node)                  │
  │   Raspberry Pi RP2350A / Pico 2 W + RM2 Wi-Fi modul    │
  │   - Čtení senzorů a PID/hysterezní řízení ohřevu       │
  │   - Serializace telemetrie do JSON                     │
  │   - lwIP Network Stack + CYW43439 Wi-Fi driver         │
  └────────────────────────┬───────────────────────────────┘
                           │ Wi-Fi 2.4 GHz (WPA2-PSK)
                           │ MQTT Protokol (Port 1883)
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │                 CLOUD MQTT BROKER                      │
  │   Host: test.mosquitto.org / 54.36.178.49              │
  │   - Topic stavu: drybox/status/{id}                    │
  │   - Topic příkazů: drybox/commands                     │
  └───────────┬────────────────────────────────▲───────────┘
              │ WebSockets (WSS Port 8081)    │ Odesílání příkazů
              ▼                                │ (Start/Stop, Materiál)
  ┌────────────────────────────────────────────┴───────────┐
  │             WEB DASHBOARD (Frontend SPA)               │
  │   GitHub Pages (HTML5, Tailwind CSS, Chart.js, MQTT.js)│
  │   - Automatické generování karet podle Box ID          │
  │   - Real-time grafy odpařování vlhkosti v čase         │
  │   - Výběr filamentu (PLA, PETG, ABS, ASA, TPU, PA...) │
  └────────────────────────────────────────────────────────┘
```

---

## 🌿 3. Detailní přehled všech Git větví (Branches)

Repozitář projektu je rozdělen do 4 klíčových větví, které oddělují jednotlivé domény:

| Větev (Branch) | Hlavní zaměření | Klíčové technologie a soubory |
| :--- | :--- | :--- |
| **`main`** | Hlavní integrační větev | Globální dokumentace, architektura, starter soubory |
| **`PCB`** | Návrh hardware a plošného spoje | KiCad 9, 4vrstvá DPS, RP2350A, RM2, Kusovník BOM |
| **`FIRMWARE`** | C/C++ vestavěný kód pro mikrokontrolér | Pico SDK 2.3, lwIP, CYW43, Wi-Fi, MQTT klient, FreeRTOS/bare-metal |
| **`WEB`** | Webový frontend a uživatelské rozhraní | Single-file SPA, Tailwind CSS, Chart.js, MQTT.js přes WSS |

---

### 🌿 Větev 1: `main` (Integrační & Dokumentační základ)
* **Účel:** Slouží jako stabilní základna a centrální dokumentační rozcestník projektu pro GitHub.
* **Obsah:**
  * `README.md` – Hlavní prezentace projektu, popis architektury, návod na sestavení pro Pico W / Pico 2 W, odkaz na živé demo.
  * `.vscode/` – Nastavení editoru VS Code pro Pico SDK (C/C++ properties, CMake kits, úlohy pro nahrávání).
  * `CMakeLists.txt` a `pico_sdk_import.cmake` – Základní skripty pro inicializaci sestavení Pico SDK.

---

### 🌿 Větev 2: `PCB` (Hardware & Návrh plošného spoje v KiCad 9)
* **Účel:** Kompletní návrh schématu a 4vrstvé desky plošných spojů (DPS) pro sériovou výrobu na míru.
* **Rozměry desky:** **85 × 65 mm** se zaoblenými rohy a montážními otvory M3.
* **Vrstvy (4-layer stackup):**
  1. **Top Layer (F.Cu):** Signálové cesty, součástky, **RF Keepout zóna** pod anténou modulu RM2.
  2. **Inner Layer 1 (In1.Cu):** Souvislá zemní plocha (**GND plane**) pro minimalizaci šumu a zpětné proudy.
  3. **Inner Layer 2 (In2.Cu):** Napájecí rozvod (**+3V3 power plane**).
  4. **Bottom Layer (B.Cu):** Pomocné signály a spodní měděné polygony.
* **Stav DRC (Design Rule Check):** **0 chyb, 0 nepropojených spojů (0 DRC violations)**.
* **Klíčové soubory větve:**
  * `susicka_filamentu.kicad_sch` – Hlavní hierarchické schéma.
  * `pwr.kicad_sch` – Napájecí sekce: Vstup 24V DC Jack (`PJ-102AH`), svorkovnice `MKDS 1,5`, Step-Down měnič **AP63203WU-7** (24V $\to$ 3,3V, 2A).
  * `flash.kicad_sch` – Externí paměť **W25Q128JVS** (128 Mbit QSPI Flash) pro kód a data.
  * `surge_protect_D.kicad_sch` – USB-C konektor s ESD ochranou **USBLC6-2SC6** a CC1/CC2 pull-down rezistory (5,1 k$\Omega$).
  * `susicka_filamentu.kicad_pcb` – Vyladěný layout desky plošných spojů.
  * `BOM.md` – Kompletní kusovník součástek spárovaný s tabulkou `soucastky.xlsx`. Všechny pasivní součástky (rezistory, kondenzátory) jsou sjednoceny na pouzdro **SMD 0805** pro snadné ruční pájení.
  * `pcb_top_render.png`, `pcb_bottom_render.png` – Fotorealistické 3D rendery osazené desky.
  * `sandbox/` – Tréninková podsložka s čistými a nepřeroutovanými verzemi desek pro cvičné routování.

#### Seznam klíčových integrovaných obvodů na PCB:
1. **U1 – RP2350A:** Dual-core ARM Cortex-M33 / Hazard3 RISC-V mikrokontrolér (pouzdro QFN-60, 7×7 mm, pitch 0,4 mm).
2. **U2 – Raspberry Pi RM2 (RMC20452T):** Certifikovaný rádiový modul Wi-Fi 4 + Bluetooth 5.2.
3. **U3 – Winbond W25Q128JVS:** 128 Mbit QSPI NOR Flash paměť (SOIC-8).
4. **U4 – Diodes Inc AP63203WU-7:** Synchronní snižující DC-DC měnič 24V na 3,3V / 2A (TSOT-23-6).
5. **Q1 – N-MOSFET (AO3400A / Si2302DS):** Logický spínač pro 24V topný element s ochrannou diodou D2 (SS14 Schottky).
6. **Senzory:** Tenzometrický převodník **HX711** (váha) + digitální teplotní/vlhkostní senzor **SHT40** (I2C).

---

### 🌿 Větev 3: `FIRMWARE` (Vestavěný C/C++ kód)
* **Účel:** Programové vybavení pro Master Node běžící na **Raspberry Pi Pico W / Pico 2 W** (kompatibilní s RP2040 i RP2350).
* **Vývojové prostředí:** Raspberry Pi Pico SDK verze 2.3+, C11/C++17, GCC ARM Embedded, CMake.
* **Klíčové soubory větve:**
  * `main.c` – Hlavní program: inicializace hardware, Wi-Fi, DHCP vyjednání, MQTT klient, obsluha stavového automatu, simulace senzorů a odesílání telemetrie.
  * `config.h.example` – Vzorová šablona konfigurace Wi-Fi sítě a MQTT brokeru.
  * `config.h` – **Ignorovaný soubor (`.gitignore`)** s reálnými přihlašovacími údaji:
    ```c
    #define WIFI_SSID       "Womp"
    #define WIFI_PASSWORD   "csbv2529"
    #define MQTT_BROKER_HOST "54.36.178.49" // nebo test.mosquitto.org
    #define MQTT_BROKER_PORT 1883
    #define MQTT_TOPIC_CMD  "drybox/commands"
    ```
  * `lwipopts.h` – Nízkoúrovňová konfigurace zásobníku lwIP pro RTOS/bare-metal Wi-Fi s podporou MQTT klienta a DHCP.
  * `serial_mqtt_bridge.py` – Záložní Python bridge skript pro ladění přes USB CDC sériový port.

#### Klíčové funkce firmwaru v `main.c`:
* **Dynamické generování Box ID:** Box ID se generuje automaticky z posledního bajtu hardwarové MAC adresy:  
  `g_telemetry.id = (mac[5] % 8) + 1;` $\to$ Umožňuje nahrát stejný binární soubor `.uf2` na libovolný počet desek bez přeprogramování!
* **JSON Telemetrie:** Pravidelné odesílání stavu každou sekundu na topic `drybox/status/{id}`:
  ```json
  {
    "id": 1,
    "weight": 448.32,
    "temp": 54.8,
    "hum": 15.2,
    "dry_state": 2,
    "status": "drying",
    "type": "PLA"
  }
  ```
* **Příjem vzdálených příkazů:** Odběr z topicu `drybox/commands`. Podporuje příkazy:
  * `{"cmd": "stop"}` / `{"cmd": "toggle"}` – Zapnutí nebo vypnutí topného cyklu.
  * `{"type": "PETG"}` – Nastavení nového profilu filamentu.
* **Fyzické ovládání:**
  * Čtení tlačítka **BOOTSEL** za běhu programu bezpečně bez resetu čipu (přes přímý přístup k QSPI registru).
  * Uživatelské tlačítko na **GPIO 15** s interním pull-upem.
  * Vizuální signalizace přes palubní LED na pinu `CYW43_WL_GPIO_LED_PIN`.

---

### 🌿 Větev 4: `WEB` (Webový Dashboard & Frontend)
* **Účel:** Živé, plně responzivní uživatelské rozhraní běžící v prohlížeči.
* **Hosting:** GitHub Pages ([Live Demo](https://xxzoomczexx.github.io/multi_dryer_box/)).
* **Architektura:** **Zero-build Single-Page Application (SPA)** – veškerý kód je v jednom souboru `index.html`, bez nutnosti Node.js, Webpacku nebo npm instalací.
* **Použitý Tech Stack:**
  * **HTML5 & ES6 JavaScript:** Aplikační logika a správa DOMu.
  * **Tailwind CSS (CDN):** Moderní Dark Mode designový systém.
  * **Chart.js (CDN):** Vykreslování vyhlazených křivek úbytku váhy v reálném čase.
  * **MQTT.js (CDN):** WebSockets klient pro přímou komunikaci s brokerem na `wss://test.mosquitto.org:8081/mqtt`.

#### Vlastnosti a funkce webu:
1. **Automatické vytváření karet (Multi-Box Grid):** Když dojde zpráva na `drybox/status/X`, aplikace zkontroluje, zda již existuje karta pro ID `X`. Pokud ne, dynamicky naklonuje HTML šablonu `<template id="dryboxTemplate">` a inicializuje pro ni vlastní Chart.js instanci.
2. **Rolling History Chart:** Graf uchovává data o hmotnosti přesně za **posledních 5 minut**. Starší body automaticky odmazává pro udržení vysokého výkonu.
3. **Předvolby materiálů (Presets):** Rozbalovací menu s profily pro filamenty:
   * **PLA:** Cílová teplota cca 45–50 °C
   * **PETG:** Cílová teplota cca 60–65 °C
   * **ABS / ASA:** Cílová teplota cca 70–80 °C
   * **TPU / Flex:** Cílová teplota cca 50–55 °C
   * **PA (Nylon) / PC:** Cílová teplota cca 80–90 °C
   * **PVA / HIPS:** Speciální podpůrné materiály
4. **Možnost rekonfigurace v UI:** Uživatel si může v horním nastavení změnit adresu MQTT brokeru, WSS port i sledované topicy bez zásahu do zdrojového kódu.

---

## 🔌 4. Přehled mapování pinů (Pinout & Hardware Interfacing)

| Signál / Funkce | Čip / Součástka | Pin na RP2350A | Popis zapojení |
| :--- | :--- | :--- | :--- |
| **I2C SDA** | SHT40 | `GPIO 2` | I2C datová linka se senzorem teploty/vlhkosti |
| **I2C SCL** | SHT40 | `GPIO 3` | I2C hodinová linka |
| **HX711 DOUT** | HX711 | `GPIO 4` | Sériový datový výstup z 24bit A/D převodníku váhy |
| **HX711 SCK** | HX711 | `GPIO 5` | Hodinový puls pro vyčtení váhy |
| **HEATER GATE** | MOSFET Q1 | `GPIO 14` | Řízení spínání 24V topného elementu (PWM / Hystereze) |
| **USER BUTTON** | Hmatník / Tlačítko | `GPIO 15` | Uživatelské tlačítko s pull-up odporem proti GND |
| **STATUS LED** | Wi-Fi modul RM2 | `WL_GPIO 0` | Indikační LED provozu a stavu Wi-Fi |
| **USB D+ / D-** | USB-C J1 | Vyhrazené USB piny | Programování, BOOTSEL, sériový terminál s ESD ochranou |
| **QSPI Flash** | W25Q128JVS | Vyhrazené QSPI piny | Externí rychlá 16MB Flash paměť pro mikrokontrolér |

---

## 📊 5. MQTT Komunikační protokol a formát zpráv

### 1. Telemetrie sušičky (Publikuje Master Node)
* **Topic:** `drybox/status/{id}` *(např. `drybox/status/1`)*
* **Frekvence:** 1 Hz (každých 1000 ms)
* **QoS:** 0
* **Příklad JSON zprávy:**
```json
{
  "id": 1,
  "weight": 449.15,
  "temp": 50.2,
  "hum": 18.4,
  "dry_state": 1,
  "status": "drying",
  "type": "PLA"
}
```
* **Význam hodnot:**
  * `id` *(int)*: Unikátní číslo sušicího boxu (1–8).
  * `weight` *(float)*: Aktuální hmotnost cívky v gramech (2 desetinná místa).
  * `temp` *(float)*: Teplota uvnitř boxu ve stupních Celsia.
  * `hum` *(float)*: Relativní vlhkost v procentech.
  * `dry_state` *(int)*: Stavový kód (0 = Standby/Idle, 1 = Heating, 2 = Target Reached, 3 = Error).
  * `status` *(string)*: `"idle"` nebo `"drying"`.
  * `type` *(string)*: Zvolený profil filamentu (např. `"PLA"`, `"PETG"`).

### 2. Řídicí příkazy (Odesílá Web Dashboard)
* **Topic:** `drybox/commands`
* **QoS:** 0
* **Příklady JSON zpráv:**
  * Zastavení / přepnutí procesu sušení:
    ```json
    { "cmd": "stop", "id": 1 }
    ```
  * Změna typu sušeného materiálu:
    ```json
    { "type": "PETG", "id": 1 }
    ```

---

## 🛠️ 6. Návod k sestavení a spuštění (Cheat Sheet pro vývojáře)

### A. Sestavení firmwaru (Pico C/C++ SDK)
1. Zkontrolujte přítomnost souboru `config.h` (vytvořte kopií z `config.h.example`):
   ```bash
   cp config.h.example config.h
   ```
2. Vyplňte přihlašovací údaje k Wi-Fi síti (`WIFI_SSID` a `WIFI_PASSWORD`).
3. Vytvořte build adresář a zkompilujte projekt:
   ```bash
   cmake -B build -S . -DPICO_BOARD=pico2_w   # nebo pico_w pro starší desku
   cmake --build build
   ```
4. Soubor `build/drybox_firmware.uf2` nahrajte do Pico přepnutého do režimu BOOTSEL.

### B. Prohlížení a editace hardwaru (KiCad 9)
1. Přepněte se na větev `PCB`:
   ```bash
   git checkout PCB
   ```
2. Otevřete projektový soubor `susicka_filamentu.kicad_pro` v **KiCad 9**.
3. Spusťte kontrolu návrhových pravidel (DRC) v PCB Editoru – ověříte nulový počet chyb.

### C. Lokální spuštění webového dashboardu
1. Přepněte se na větev `WEB`:
   ```bash
   git checkout WEB
   ```
2. Otevřete soubor `index.html` v libovolném moderním webovém prohlížeči (nebo přes VS Code rozšíření *Live Server*). Aplikace se ihned připojí k brokeru `test.mosquitto.org` přes WebSockets.

---

## 🎯 7. Shrnutí a role pro Gemini AI

Pokud s tímto projektem pracujete v **Google Gemini / NotebookLM / Gems**:
* **Jste technický expert:** Chápete projekt v plné šíři od nízkoúrovňového návrhu hardware (výběr komponent, impedanční přizpůsobení, RF Keepout, napájení DC-DC měničem), přes embedded firmware v jazyce C pro mikrokontroléry Raspberry Pi (RP2040/RP2350, lwIP síťový zásobník, MQTT callbacky, neblokující architektura), až po klientský webový frontend s WebSockets a real-time vizualizací.
* **Respektujete větvení repozitáře:** Víte, že schéma a deska patří do větve `PCB`, zdrojové kódy v C do `FIRMWARE`, webové rozhraní do `WEB` a integrační materiály do `main`.
* **Pomáháte autorovi:** Autor připravuje projekt jako maturitní práci. Vaším úkolem je asistovat s psaním technické dokumentace, vysvětlováním zapojení, optimalizací firmwaru, laděním komunikace a přípravou na maturitní obhajobu.

