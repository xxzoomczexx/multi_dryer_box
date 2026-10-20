# 📦 Multi-Box Filament Dryer System

IoT systém pro monitorování a řízení více filamentových sušiček současně. Real-time přehled o stavu materiálu (váha, teplota, vlhkost) v dashboardu s možností přímé integrace do systémů chytré domácnosti a 3D tiskových serverů.

---

## 🌐 Live Demo

**Prohlédněte si běžící webový dashboard zde:**  
👉 **[https://xxzoomczexx.github.io/multi_dryer_box/](https://xxzoomczexx.github.io/multi_dryer_box/)**

*(Dashboard funguje jako statická vizualizace MQTT dat z připojených hardwarových sušiček).*

---

## 🚀 Rychlý návod k sestavení pro Raspberry Pi Pico W / Pico 2 W

Master Node se připojuje přímo přes **Wi-Fi** a **MQTT protocol (lwIP)** na cloudový broker bez nutnosti mít spuštěný jakýkoliv skript na PC.

### 1. Konfigurace Wi-Fi přístupových údajů

Před kompilací zkontrolujte v kořenu projektu soubor `config.h` (můžete zkopírovat ze šablony `config.h.example`):

```bash
cp config.h.example config.h
```

Otevřete `config.h` a zadejte název a heslo k vaší Wi-Fi síti:

```c
#define WIFI_SSID       "NAZEV_VASI_WIFI"
#define WIFI_PASSWORD   "VASE_HESLO"
```

*(Soubor `config.h` je v `.gitignore`, vaše heslo se nedostane do Git repozitáře).*

### 2. Kompilace a nahrání firmwaru

1. Otevřete projekt ve VS Code s nainstalovaným **Raspberry Pi Pico extension** (Pico SDK 2.x).
2. Sestavte projekt pro **Pico W** (nebo `pico2_w` pro Pico 2 W):
   ```bash
   cmake -B build -S . -DPICO_BOARD=pico_w
   cmake --build build
   ```
3. Zapojte **Raspberry Pi Pico W** v BOOTSEL režimu (se stisknutým tlačítkem BOOTSEL) a nahrajte vygenerovaný soubor `build/drybox_firmware.uf2` přetažením na disk `RPI-RP2`.

---

## 🏗️ Architektura Systému (Data Flow)

Systém je navržen pro modularitu a stabilitu komunikace. Skládá se z několika vrstev:

1. **Sensor Nodes (RP2040):** Každý sušicí box obsahuje vlastní mikrokontrolér, který sbírá data z lokálních senzorů a stará se o topná tělesa.
2. **Master Node (Pico W / Pico 2 W):** Centrální mozek systému. Přijímá data přes CAN/I2C od jednotlivých boxů a posílá je přes Wi-Fi.
3. **Direct MQTT / Wi-Fi (lwIP):** Master Node využívá Wi-Fi stack CYW43439 pro bezpečné odeslání agregovaných dat přes internet k MQTT brokeru.
4. **Cloud Broker:** Zprostředkovatel zpráv (`test.mosquitto.org` / `54.36.178.49`).
5. **Frontend (GitHub Pages):** Koncový klient přistupující k datům přes Secure WebSockets (`wss://test.mosquitto.org:8081/mqtt`) a vizualizující je v reálném čase.

---

## ✨ Klíčové Vlastnosti (Key Features)

- 📡 **Přístup odkudkoliv:** Systém využívá MQTT a nevyžaduje žádný složitý port-forwarding na routeru ani pevnou veřejnou IP adresu.
- ⚡ **Plug & Play Multi-Box:** Automatické generování unikátního ID sušičky z HW MAC adresy. Můžete nahrát jeden `.uf2` soubor na libovolný počet Pico desek bez ručních změn kódu.
- 🔒 **Bezpečné uložení údajů:** Wi-Fi credentials uložené v ignorovaném `config.h`.
- 📊 **Integrace a API:** Architektura otevírá cesty pro integrace do systémů **Home Assistant** a API endpointů tiskových platforem, jako je **Prusa Connect**.

---

## 🛠️ Hardware Details

- **Raspberry Pi Pico W (RP2040) / Pico 2 W (RP2350):** Mikrokontrolér s integrovaným Wi-Fi modulem CYW43439 pro Master Node.
- **Raspberry Pi RP2040:** Cenově dostupné a spolehlivé mikrokontroléry pro jednotlivé podřízené uzly (Sensor Nodes).
- **SHT4x:** Digitální senzory pro měření teploty a relativní vlhkosti uvnitř filamentových boxů.
- **HX711:** 24bitový A/D převodník a tenzometry pro přesné měření hmotnosti a úbytku filamentu.

---

## 💻 Software Stack

| Vrstva | Použitá Technologie | Popis |
| :--- | :--- | :--- |
| **Firmware** | C / C++ (Pico SDK 2.3) | Nízkoúrovňový kód pro sběr dat ze senzorů, Wi-Fi a MQTT komunikaci. |
| **Networking** | lwIP / CYW43 Architecture | Integrovaný síťový stack pro Wi-Fi připojení a MQTT klienta. |
| **Frontend** | HTML5, Vanilla JavaScript | Plně statická single-file aplikace (SPA) hostovaná na GitHub Pages. |
| **Styling & UI** | Tailwind CSS (CDN) | Dark Mode designový systém pro esteticky čisté a responzivní UI prvky. |
| **Vizualizace** | Chart.js | Real-time grafy uchovávající a vykreslující historii úbytku hmotnosti v čase. |
| **Cloud Bridge** | MQTT.js | WebSockets klient pro čtení telemetrie v prohlížeči a odesílání kontrolních příkazů. |

---
