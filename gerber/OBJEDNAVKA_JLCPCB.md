# Objednávka desky u JLCPCB

Deska `susicka_filamentu` v1.0 (prototyp), export 2026-10-26 z KiCadu 9.0.8.
Objednává se **jen deska** (bez osazení) + doporučená šablona na pastu. Součástky se osazují ručně a pájí v peci.

## 1. Co nahrát

Soubor **`susicka_filamentu_JLCPCB_2026-10-26.zip`** (11 vrstev Gerber + 2 vrtací soubory Excellon).

1. [jlcpcb.com](https://jlcpcb.com) → **Order now** → **Add gerber file** → vybrat ZIP.
2. JLC sám načte počet vrstev (4) a rozměr (70 × 100 mm).
3. Otevřít **Gerber Viewer** a zkontrolovat:
   - pořadí vrstev: L1 = Top (`.gtl`), L2 = In1 – GND (`.g1`), L3 = In2 – 3V3/GND (`.g2`), L4 = Bottom (`.gbl`);
   - u horní hrany pod anténou RM2 není měď v žádné vrstvě;
   - díry: 4 montážní M3 bez mědi (NPTH), nejmenší díry 0,25 mm.

## 2. Parametry desky

| Parametr | Nastavit | Poznámka |
|---|---|---|
| Base Material | FR-4 | |
| Layers | 4 | doplní se samo |
| Dimensions | 70 × 100 mm | doplní se samo |
| PCB Qty | 5 | minimum; potřeba je 1, zbytek rezerva |
| Product Type | Industrial/Consumer electronics | |
| Different Design | 1 | |
| Delivery Format | Single PCB | panel není potřeba |
| PCB Thickness | 1.6 mm | |
| PCB Color | Green | nejlevnější a nejrychlejší, jiná barva nevadí |
| Silkscreen | White | |
| Material Type | výchozí FR-4 | elektronika je mimo sušicí komoru, vyšší Tg netřeba |
| Surface Finish | **ENIG** | rovné plošky pro QFN-60 s roztečí 0,4 mm a plošky RM2; HASL je nerovný a hůř se na něj tiskne pasta |
| Outer Copper Weight | 1 oz | |
| Inner Copper Weight | 0.5 oz (výchozí) | stačí |
| Impedance Control | No | |
| Layer Stackup | výchozí (JLC04161H-7628) | |
| Via Covering | Tented (výchozí) | |
| Min via hole size/diameter | 0.25 mm | 7 prokovů VREG + 9 děr v termální plošce RP2350 (oficiální footprint); případný příplatek uvidíš hned v ceně |
| Board Outline Tolerance | ±0.2 mm (Regular) | |
| Confirm Production File | No | Yes = před výrobou ti pošlou podklady ke schválení (zdrží) |
| Mark on PCB | výchozí, nebo Remove Mark | JLC jinak natiskne číslo objednávky na volné místo |
| Electrical Test | Flying Probe Fully Test | výchozí |
| Gold Fingers, Castellated Holes, Edge Plating | No | |
| ostatní | výchozí | |

## 3. Šablona na pastu (doporučená)

Na stejné stránce zapnout **SMT-Stencil**:

| Parametr | Nastavit | Poznámka |
|---|---|---|
| Stencil Type | Non-Framework | bez rámu, levnější, na jednu desku stačí |
| Stencil Side | Top | dole nejsou žádné SMD součástky |
| Thickness | **0.10 mm** | méně můstků na QFN 0,4 mm; poměr ploch otvorů 0,87 (min. 0,66) |
| Fiducials | None | deska fiduciály nemá |
| Electropolishing | No | volitelně Yes (pasta se lépe uvolňuje) |

## 4. Co v exportu záměrně není

- BOM a osazovací soubor (CPL) – osazuje se ručně.
- Spodní potisk je prázdný (soubor `.gbo` obsahuje jen vynechané oblasti masky).
- Nezapojené piny GP10, 11, 16, 18, 19, 20, 27 na J12, NTC (J10, R25, C26, TP19) a TP3 – záměr u prototypu,
  DRC to hlásí jako 7 nespojených položek + chybějící TP3.

## 5. Jak export zopakovat

Gerber (Soubor → Vykreslit): vrstvy F.Cu, In1.Cu, In2.Cu, B.Cu, F/B.Paste, F/B.Silkscreen, F/B.Mask, Edge.Cuts;
✓ Protel přípony, ✗ rozšířený formát X2, ✗ atributy netlistu, ✓ odečíst masku od potisku, přesnost 4.6 mm.
Vrtání: Excellon, mm, desetinný formát, absolutní počátek, oválné díry „alternate“, PTH a NPTH zvlášť.

Totéž z příkazové řádky (KiCad zavřený, ve složce `PCB/`):

```
kicad-cli pcb export gerbers -o gerber/ -l "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" --subtract-soldermask --no-x2 --no-netlist --precision 6 susicka_filamentu.kicad_pcb
kicad-cli pcb export drill -o gerber/ --format excellon --drill-origin absolute --excellon-zeros-format decimal --excellon-oval-format alternate --excellon-units mm --excellon-separate-th susicka_filamentu.kicad_pcb
```

Pak zabalit všechny `susicka_filamentu-*` soubory (Gerbery, `.drl`, `.gbrjob`) do ZIPu.
Před exportem vždy přepočítat zóny (B) a spustit DRC.
