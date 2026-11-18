# Simulace ohřevu a proudění (2026-11-14)

Model podle sestavy `susicka_celek_v2` ve Fusionu: PTC RS PRO 336-739 v sendviči mezi 2× chladičem 60×60×10,
ventilátor 5015, komora 266 × 110 × 230 mm, stěny PETG 3 mm, cívka 1 kg.
Výsledky jsou odhad (katalogové a odhadnuté parametry), ověří se měřením na prototypu.

| Skript | Co dělá | Výstup |
|---|---|---|
| `termika_0d.py` | tepelný model v čase (PTC → chladiče → vzduch → stěny, cívka), regulace PI | `vystupy/termika_0d.png` |
| `varianty_0d.py` | porovnání chladičů, izolace a otáček ventilátoru | text |
| `proudeni_2d.py` | 2D řez komorou (Navier–Stokes + vztlak, efektivní turbulentní viskozita) | `vystupy/proudeni_2d.png` |

Spuštění: `python termika_0d.py` (numpy, scipy, matplotlib). 2D simulace běží ~5 min.

## Hlavní výsledky
- Bez izolace se komora dostane max. na **~63 °C** (PTC dává ~37 W, samo se omezí). PETG 65 °C na hraně, ABS 80 °C ne.
- **Izolace 10 mm** (XPS/EPS zvenku) → **~76 °C**. Větší chladiče pomohou jen o 1–2 °C, rozhoduje izolace a průtok vzduchu.
- Chladiče (místo TCO) ~88 °C, keramika PTC ~103 °C → SF129R0 (holding 118 °C) má rezervu ~30 K.
- Průměrná stěna ~43 °C, vzduch u stěny za topením ~76 °C → vnitřní povrch PETG ~50 °C (OK).
- Náběh: vzduch 55 °C za ~50 min, cívka dobíhá o 1–2 h později. Proudový náraz omezí zdroj (3,5 A).
- 2D: horký proud stoupá u pravé stěny, vede pod stropem doleva a dolů; **vlevo dole za cívkou je o ~25 K chladněji**
  než vpravo nahoře. SHT40 nahoře uprostřed měří o ~6 K víc, než je průměr. (2D přehání – ve 3D obtéká vzduch cívku
  i zepředu a zezadu.)
- 2D řez má o něco menší ztráty než skutečný box (chybí netěsnosti, část ploch) → absolutní teploty z 2D jsou
  vyšší než z tepelného modelu; 2D slouží k **porovnání variant**, absolutní hodnoty brát z `termika_0d.py`.

## Vedení vzduchu – rukáv + šachta + kanál pod strop (`python proudeni_2d.py kanal`)
Ve Fusionu (`susicka_celek_v2`) díl „Vedení vzduchu“: rukáv kolem sendviče (Z 76–136, navazuje na kryt 5015),
šachta nahoru a vodorovný kanál pod stropem s tryskou 70 × 22 mm u X = 65 mm (nad cívkou 10 mm vůle),
díry pro sloupky a průchodka kabelů v rukávu. Materiál ASA/ABS (vzduch ~90 °C, PETG by měklo).
SHT40 přesunutý dolů ke vstupu ventilátoru (X 100, Z 46).

| (stejný výkon 37 W) | bez kanálu | s kanálem |
|---|---|---|
| průtok žebry chladičů | 1,1 l/s (zbytek obtéká) | **1,78 l/s** (rukáv) |
| vzduch kolem obvodu cívky – rozptyl max−min | 36 K (σ 10,8 K) | **23 K (σ 6,1 K)** |
| rychlost kolem cívky | 0,15 m/s | **0,23 m/s** |
| SHT40 proti průměru komory | +7,5 K (nahoře) | **+0,3 K** (u vstupu 5015) |
| vzduch u pravé stěny za topením | 85 °C | **34 °C** |
