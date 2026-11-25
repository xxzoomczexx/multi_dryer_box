# Oživení desky – checklist

Postup od holé desky po první běžící firmware. Každý krok dělej, až předchozí prošel.
Když něco nesedí, **nepokračuj** – vypni zdroj a hledej příčinu.

Testovací firmware: větev FIRMWARE, složka `test_desky/` (přepínače částí nahoře v `test_desky.c`).

Potřeba: laboratorní zdroj s proudovým limitem, multimetr, lupa, Debug Probe, zástrčka 5,5/2,1.

---

## 0. Holá deska (před osazením)

- [ ] **Zkraty mezi napájecími sítěmi** (multimetr na Ω, holá deska → musí být rozpojeno / OL):
  - [ ] TP1 (24V) – GND (TP4/TP5)
  - [ ] TP2 (3V3) – GND
  - [ ] 1V1 – GND (TP3 na desce není → měřit na plošce L1 pin 1 nebo C5)
  - [ ] TP1 (24V) – TP2 (3V3)
- [ ] **Průchodnost GND**: TP4 ↔ TP5 ↔ TP12 ↔ J3 pin 3 ↔ J2 pin 3 (~0 Ω)
- [ ] Lupou okolí U1 a RM2: žádné můstky v mědi, maska mezi ploškami QFN
- [ ] **Footprinty nasucho** (položit díl na plošky): SW1 (vlastní tlačítko!), J4, svorkovnice 5,0 mm,
      lišty, Keystone 5001, Q1 PowerPAK, Q3 DPAK, L1, L2, RM2
- [ ] Stencil přiložený na desku – otvory sedí na U1 a termální plošku
- [ ] **Zástrčka od zdroje**: plus na **středovém kolíku** (změřit multimetrem)

## 1. Po osazení – vizuálně (bez napájení)

- [ ] Lupou: žádné můstky na U1 (QFN 0,4 mm), U3, U4 (TSOT-23-6), RM2
- [ ] Žádné „náhrobky“ (postavené 0402) – hlavně kolem VREG (C4, C5, C6, R7)
- [ ] **Orientace**:
  - [ ] U1 – tečka / pin 1
  - [ ] U3 flash – pin 1
  - [ ] U4 – pin 1
  - [ ] L1 – tečka k +1V1 (podle reference)
  - [ ] D2 (SMA), D3, D7 (SOD-123) – proužek = katoda
  - [ ] D4 (zenerka BZT52C15) – proužek = katoda
  - [ ] D6 LED – katoda na GND
  - [ ] C25 (elektrolyt 100 µF/50 V) – polarita
  - [ ] Q1, Q3 – správně otočené (pouzdra se dají položit jen jedním způsobem, ale zkontrolovat)
  - D5 (SMBJ24CA) je obousměrná – polarita nevadí
- [ ] F1 osazená (bez ní deska nedostane 24 V)

## 2. Multimetr bez napájení (osazená deska)

Hodnoty se při měření mění (nabíjí se kondenzátory) – čti ustálenou hodnotu.
**< 10 Ω = zkrat**, stovky Ω až MΩ = v pořádku. Při pochybnosti porovnat s druhou deskou.

| Měření | Výsledek | OK? |
|---|---|---|
| TP1 24V – GND | | |
| TP2 3V3 – GND | | |
| 1V1 (L1 pin 1 / C5) – GND | | |
| TP1 24V – TP2 3V3 | | |

## 3. První zapnutí – napájení

Zdroj: **24,0 V** (ne víc – D5 SMBJ24CA začíná vést nad ~26,7 V), **proudový limit 50–100 mA**.
Nic nepřipojeno na J5, J8, J9, J13. Napájet přes J4 (otestuje se i F1 a ochrana Q3).

- [ ] Po zapnutí zdroj **nejede v proudovém limitu** (jinak hned vypnout → zkrat)
- [ ] Odběr z 24 V: orientačně jednotky mA (prázdná flash, RM2 vypnutý přes R11) – zapsat: ______ mA
- [ ] TP1 = 24 V (o pár desetin méně kvůli Q3): ______ V
- [ ] TP2 = **3,3 V** (3,25–3,35 V): ______ V
- [ ] 1V1 na L1 / C5 = **~1,1 V**: ______ V
- [ ] Prstem / teploměrem: U4, L2, U1, Q3 jsou studené (po ~1 min)
- [ ] (volitelně) osciloskopem zvlnění 3V3 a uzel SW u L2 – spínání ~1,1 MHz bez divokých zákmitů

Když 3V3 nesedí, ale 24V ano → U4 / L2 / C21–C24. Když nesedí 1V1 → VREG (L1, C4–C6, R7).

## 4. SWD – spojení s čipem

Probe konektor **D** → J3: žlutý = **pin 1 SWDIO**, oranžový = **pin 2 SWCLK**, černý = **pin 3 GND** (pin 4 RUN volný).
Deska napájená z 24 V.

- [ ] OpenOCD: `openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000"`
- [ ] Výpis obsahuje `SWD DPIDR` a `Listening on port 3333` (čip žije, krystal ještě netestovaný)
- [ ] Když `cannot read IDR`: zkontrolovat zapojení (SWDIO/SWCLK prohozené?), 3V3, 1V1, snížit rychlost na 1000 kHz

## 5. Testovací firmware – základ

V `test_desky.c` všechny přepínače `TEST_…` na 0 (nejdřív jen základ). Přeložit a nahrát přes SWD.
Probe konektor **U** → J2: oranžový (TX probe) = **pin 2 GPIO1 RX**, žlutý (RX probe) = **pin 1 GPIO0 TX**,
černý = **pin 3 GND**. Terminál na COM portu probe, 115200 (příp. zapnout DTR).

- [ ] Nahrání proběhlo (`verify` OK)
- [ ] V terminálu se objeví `===== Susicka filamentu - test desky =====`
- [ ] `Cip: RP2350A (QFN-60)`, revize A2 nebo novější
- [ ] `Takty: krystal ~12000 kHz OK` → krystal Y1 kmitá
- [ ] `Flash: JEDEC EF 40 18 OK` → flash U3 komunikuje
- [ ] `RM2: OK, MAC …` → gSPI k RM2 funguje
- [ ] LED D6 bliká 1 Hz
- [ ] Tlačítko SW1: při stisku `STISKNUTO`, LED svítí trvale
- [ ] Teplota čipu rozumná (20–40 °C)
- [ ] Odběr z 24 V po startu RM2: ______ mA (orientačně do ~30 mA)
- [ ] `r` → restart, vypíše se znovu (důvod resetu WATCHDOG)
- [ ] Zapsat Box ID: ____________________ a MAC: ____________________

## 6. Wi-Fi a anténa

- [ ] `w` → seznam sítí, domácí síť je vidět
- [ ] RSSI domácí sítě srovnatelné s mobilem na stejném místě: ______ dBm
- [ ] Nic kovového ani ruka u antény během měření (keepout na horní hraně)

## 7. Ventilátory (J8, J9)

`TEST_VENTILATORY 1`, znovu nahrát. Zdroj: proudový limit **~0,5 A**.
Zapojení: **J8/J9 pin 2 = +24 V** (červený drát ventilátoru), **pin 1 = spínaná zem** (černý).

- [ ] Před zapnutím zdroje: ventilátor stojí (gate drží R18 / R24)
- [ ] `f` → J8 50 %, točí se pomaleji; `f` → 100 %; `f` → stojí
- [ ] Odběr ventilátoru při 100 %: ______ mA
- [ ] `e` → totéž pro J9
- [ ] Q2, Q4 a D3, D7 studené
- [ ] `x` vypne vše
- (Na 2drátovém ventilátoru může PWM 25 kHz při 50 % pískat nebo točit nerovnoměrně – pro test nevadí.)

## 8. NTC na GP28 (až bude pull-up)

Pull-up **22 kΩ mezi J12 pin 1 (3V3) a pin 13 (GP28)**, NTC mezi **pin 13 (GP28) a pin 2 (GND)**.
`TEST_NTC 1`.

- [ ] Bez NTC vypisuje `rozpojeno`
- [ ] S NTC při pokojové teplotě ~100 kΩ a teplota odpovídá teploměru (±2 °C): ______ °C
- [ ] Zahřátí prsty / horkou vodou → teplota roste

## 9. Topení (až bude rezistor HS50 a TCO)

`TEST_TOPENI 1` (+ ideálně `TEST_NTC 1`). Rezistor Arcol HS50 10R **přišroubovaný na chladiči s pastou**
(bez chladiče ho nezapínat), ventilátor, TCO SF129R0 na J13 na chladiči hned u rezistoru.
Zdroj: limit **3 A**. Zapojení J5: pin 2 = +24 V (přes J13), pin 1 = spínaná zem.

- [ ] Odpor rezistoru multimetrem (na J5, bez napájení): ______ Ω (čeká se ~10 Ω)
- [ ] Bez TCO na J13 topení nejde (obvod rozpojený) – ověřit, že to tak je
- [ ] Před zapnutím zdroje topení vypnuté (R15)
- [ ] `t` → topí 10 s a samo se vypne (`Topeni VYP (casovy limit)`)
- [ ] Proud během topení ______ A (čeká se stálých ~2,4 A, bez náběhového rázu)
- [ ] **U_DS Q1** během topení (měřit mezi J5 pin 1 a GND): ______ V (< ~0,2 V = OK, Q1 je při 3,3 V na hraně)
- [ ] Q1 po několika pulzech jen vlažný
- [ ] Teplota chladiče u TCO po delším provozu (cíl < ~110 °C) – změří se později s reálným firmwarem

## 10. HX711 (až bude modul)

`TEST_HX711 1`. Modul na J7: 3V3, GND, SCK (GPIO5), DT (GPIO4).

- [ ] Vypisuje číslo místo `neni pripraveny`
- [ ] Při zatížení tenzometru se hodnota mění, bez zátěže je stabilní (kolísání v řádu desítek až stovek)

## 11. Ochrana proti přepólování (volitelně)

Zdroj **limit 50 mA**, zástrčku zapojit obráceně (prohodit dráty na zdroji).

- [ ] Odběr ~0 mA, TP1 ~0 V (Q3 blokuje)
- [ ] Po vrácení polarity deska normálně běží

---

Hotovo → další krok je reálný firmware (I2C/SHT40, PID topení, MQTT).
