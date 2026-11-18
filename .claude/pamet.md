# Sdílená paměť pro Clauda (v gitu, funguje na PC i na notebooku)

## Uživatel
- Student SPŠE a VOŠ Plzeň (Elektrotechnika – IoT), maturitní projekt IoT sušička filamentu. Píše česky (často bez
  diakritiky), odpovídat česky. Má za sebou jednu ročníkovou práci s PCB, v KiCadu se orientuje.
- Pracuje na dvou počítačích (domácí PC, školní notebook) → na konci práce commit + push, na začátku `git pull`.
  Důležité nové poznatky zapisovat sem nebo do `CLAUDE.md`, ne jen do lokální paměti.
- Složky se na PC liší: na jednom je `multi_dryer_box_PCB` bare repo se třemi worktree (PCB/FIRMWARE/WEB, viz `CLAUDE.md`),
  na druhém je `multi_dryer_box_PCB` obyčejný klon jen větve PCB (fetch refspec jen PCB) a FIRMWARE je vedle
  v `../multi_dryer_box`. Před pullem/pushem ověřit `git worktree list` a `git branch -vv`.

## Jak pracovat s KiCadem
- KiCad soubory upravovat jen když KiCad **neběží**; nejdřív na kopii, pak zkontrolovat, že se originál nezměnil.
- Po každé změně ověřit: netlist (`kicad-cli sch export netlist`), ERC, pin↔ploška, DRC (`kicad-cli pcb drc`)
  a **vizuálně** (`kicad-cli … export pdf` + Poppler `pdftoppm`, obrázek prohlédnout – překryté labely).
- Desku analyzovat přes Python API KiCadu (`C:/Program Files/KiCad/9.0/bin/python.exe`, `import pcbnew`),
  jen z **uložené** desky (screenshot bývá novější než soubor – zkontrolovat čas změny).
- U zón kontrolovat, že každá síť je po vyplnění v jednom kuse (LX zóna jednou odřízla PGND).
- `pcbnew.LoadBoard` načítat jen ze složky, kde je **stejnojmenný `.kicad_pro`** – jinak chybí třídy sítí (Power 0,3 mm),
  přepočet zón dá špatné mezery a `SaveBoard` přepíše `.kicad_pro` výchozím. Kopie: `X.kicad_pcb` + `X.kicad_pro`.
- **KiCad IPC API** je zapnuté (Nastavení → Pluginy → Povolit KiCad API, od 2026-10-22 na domácím PC).
  Knihovna `kicad-python` (`pip install kicad-python`, import `kipy`) v systémovém Pythonu, ne v KiCadím.
  `KiCad().get_board()` = živá deska v otevřeném editoru DPS (i neuložená, změny jdou vrátit Ctrl+Z,
  `get_selection()` = co uživatel označil). Jen editor DPS – schéma dál přes soubory při zavřeném KiCadu;
  DRC a rendery dál přes `kicad-cli` z uloženého souboru. Na notebooku se API musí zapnout zvlášť.

## Fusion (mechanika)
- Oficiální místní **Fusion MCP server**: ve Fusionu Preferences → General → API → „Fusion MCP Server (runs locally
  on this device)“, endpoint `http://127.0.0.1:27182/mcp` (Streamable HTTP, bez přihlášení, jen když Fusion běží).
  V repu je `.mcp.json` → po restartu Claude Code schválit server `autodesk-fusion`. Na každém PC zapnout zvlášť.
- Model celé sušičky je v cloudu Fusionu: projekt **Default Project** → `susicka_celek_proto` (obal 272×116×292,
  cívka, kolébka, tenzometr, přepážka, elektronika s deskou z KiCadu, topný modul, 5015, odtah 4010, SHT40),
  dále `deska` a `cirkulace_teploty`. Otevírá se z Data Panelu (stejný účet na každém PC).
- Bez MCP: skripty v `mechanika/` (Shift+S → Scripts → + → složka → Run); topny_modul ukládá `nahled*.png` a `rozmery.txt`.

## Součástky
- Jen ověřené díly (datasheet) dostupné na **Mouseru nebo TME**; čísla dílů nevymýšlet. Do schématu pole
  Manufacturer + MPN, rozpis do `PCB/README.md`. Pasiva 0402/0603, větší jen kvůli napětí/DC biasu.
- Když uživatel neví, co je lepší, dát **jedno doporučení** se zdůvodněním.

## Modely
- Jednoduché hledání/čtení → subagent `hledac` (Haiku). PCB, schéma, součástky, výpočty → `pcb-navrhar` (Opus).
