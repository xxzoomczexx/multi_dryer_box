# 🌐 Multi-Box Filament Dryer - Web Dashboard (Frontend)

Webový dashboard pro zobrazení real-time telemetrie a vzdálené řízení více filamentových sušiček současně.

---

## 🚀 Živá Aplikace (GitHub Pages)

Dashboard je nasazen jako plně statická single-file aplikace:  
👉 **[https://xxzoomczexx.github.io/multi_dryer_box/](https://xxzoomczexx.github.io/multi_dryer_box/)**

---

## ✨ Vlastnosti Webového Rozhraní

- 📊 **Real-time Grafy (Chart.js):** Vykreslování historie úbytku hmotnosti v čase (posledních 5 minut) pro každý box.
- ⚡ **Plug & Play Multi-Box:** Karty pro nové sušičky se generují automaticky při přijetí zprávy z nového ID.
- 🎛️ **Vzdálené Řízení:** Tlačítko pro zastavení sušení a rozevírací nabídka pro výběr materiálu (PLA, PETG, ABS, ASA, TPU, PA, PC, PVA, HIPS).
- ⚙️ **Konfigurace MQTT Brokeru:** Možnost změnit URL brokeru (přednastaveno `wss://test.mosquitto.org:8081/mqtt`), topicy i přihlašovací údaje přímo v UI.
- 🎨 **Moderní Dark Mode:** Responzivní UI postavené na **Tailwind CSS**.

---

## 🛠️ Použitý Tech Stack

| Komponenta | Použitá Technologie | Popis |
| :--- | :--- | :--- |
| **Frontend Framework** | Vanilla HTML5 / ES6 JavaScript | Single-file SPA aplikace bez nutnosti Node.js build kroku. |
| **Styling** | Tailwind CSS (CDN) | Moderní tmavé UI. |
| **MQTT Client** | MQTT.js (CDN) | WebSockets komunikace s brokerem. |
| **Vizualizace** | Chart.js (CDN) | Plynulé vyhlazené grafy váhy. |

---