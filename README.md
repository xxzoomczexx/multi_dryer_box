# 📦 Multi-Box Filament Dryer System

Škálovatelný IoT systém pro monitorování a řízení více filamentových sušiček současně. Nabízí real-time přehled o stavu materiálu (váha, teplota, vlhkost) v přehledném dashboardu s možností přímé integrace do systémů chytré domácnosti a 3D tiskových serverů.

---

##  Live Demo

**Prohlédněte si běžící webový dashboard zde:**  
 **[https://xxzoomczexx.github.io/multi_dryer_box/](https://xxzoomczexx.github.io/multi_dryer_box/)**

*(Dashboard funguje jako statická vizualizace MQTT dat. Pro ukázku zobrazení je naplněn simulovanými testovacími daty do chvíle, než začne naslouchat reálnému hardwaru).*

---

##  Architektura Systému (Data Flow)

Systém je navržen s důrazem na modularitu a stabilitu komunikace. Skládá se z několika vrstev:

1. **Sensor Nodes (RP2040):** Každý sušicí box obsahuje vlastní mikrokontrolér, který sbírá data z lokálních senzorů a stará se o topná tělesa.
2. **RS-485 Sběrnice:** Spolehlivá industriální drátová komunikace propojuje všechny Sensor Nody do topologie daisy-chain.
3. **Master Node (RP2350):** Centrální mozek systému. Přijímá data přes RS-485 od jednotlivých boxů.
4. **Mongoose MQTT (TLS):** Master Node využívá knihovnu Mongoose pro bezpečné odeslání agregovaných dat přes internet k MQTT brokeru za použití silného TLS šifrování.
5. **Cloud Broker:** Zprostředkovatel zpráv (např. HiveMQ Cloud nebo lokální Mosquitto).
6. **Frontend (GitHub Pages):** Koncový klient přistupující k datům přes Secure WebSockets (wss) a vizualizující je v reálném čase.

---

##  Klíčové Vlastnosti (Key Features)

-  **Globální přístup odkudkoliv:** Systém využívá MQTT a nevyžaduje žádný složitý port-forwarding na routeru ani pevnou veřejnou IP adresu.
-  **Modulární design:** Automatická detekce připojených boxů. Pokud připojíte další Sensor Node na RS-485 sběrnici, webový dashboard si pro něj automaticky vygeneruje novou dlaždici.
-  **Vysoká bezpečnost:** Veškerá cloudová komunikace probíhá přes zabezpečený TLS kanál pomocí robustního síťového stacku Mongoose.
-  **Integrace a API:** Architektura otevírá jednoduché cesty pro integrace do systémů **Home Assistant** a API endpointů tiskových platforem, jako je **Prusa Connect**.

---

##  Hardware Details

- **Raspberry Pi RP2350:** Superrychlý mikrokontrolér pro Master Node zajišťující orchestraci dat a cloudové spojení.
- **RM2 Wi-Fi Modul:** Zajišťuje bezdrátovou konektivitu pro Master Node.
- **Raspberry Pi RP2040:** Cenově dostupné a spolehlivé mikrokontroléry pro jednotlivé podřízené uzly (Sensor Nodes).
- **SHT4x:** Precizní digitální senzory pro měření teploty a relativní vlhkosti uvnitř filamentových boxů.
- **HX711:** 24bitový A/D převodník a tenzometry pro přesné měření hmotnosti a úbytku filamentu.
- **RS-485 Transceivery:** Čipy pro stabilní obousměrnou průmyslovou komunikaci bez ohledu na rušení a vzdálenost vodičů.

---

##  Software Stack

| Vrstva | Použitá Technologie | Popis |
| :--- | :--- | :--- |
| **Firmware** | C / C++ (Pico SDK 2.0) | Nízkoúrovňový kód pro sběr dat z I2C senzorů, RS-485 komunikaci a řízení výkonových prvků. |
| **Networking** | Mongoose Embedded Web Server | Odlehčený framework starající se o stabilní MQTT připojení, socket management a TLS šifrování. |
| **Frontend** | HTML5, Vanilla JavaScript | Plně statická single-file aplikace (SPA) hostovaná bez nutnosti serveru na GitHub Pages. |
| **Styling & UI** | Tailwind CSS (CDN) | Moderní Dark Mode designový systém pro esteticky čisté a plně responzivní UI prvky. |
| **Vizualizace** | Chart.js | Real-time grafy uchovávající a plynule vykreslující historii úbytku hmotnosti v čase. |
| **Cloud Bridge** | MQTT.js | WebSockets klient pro čtení telemetrie v prohlížeči a odesílání kontrolních příkazů (např. stop). |

---

##  Instalace a Nasazení

### 1. Kompilace Firmware (Master Node & Sensor Nodes)
1. Ujistěte se, že máte nainstalované a nakonfigurované **Raspberry Pi Pico SDK 2.0**.
2. Naklonujte si tento repozitář včetně submodulů (pro stažení knihovny Mongoose):
   ```bash
   git clone --recursive https://github.com/xxzoomczexx/multi_dryer_box.git
   ```
3. Vytvořte build adresář, nakonfigurujte CMake a spusťte kompilaci:
   ```bash
   mkdir build && cd build
   cmake ..
   make -j4
   ```
4. Nakopírujte zkompilované `.uf2` soubory na příslušné desky (v BootROM režimu připojené jako mass-storage přes USB).

### 2. Spuštění Webového Dashboardu
1. Žádný build proces (Node.js, Webpack) není pro klientskou část potřeba.
2. Stačí otevřít soubor `index.html` v lokálním prohlížeči nebo nahrát větev na GitHub a aktivovat **GitHub Pages**.
3. Pomocí ikony ozubeného kola přímo v dashboardu zadejte MQTT konfiguraci a přihlašovací údaje ke svému brokeru.
