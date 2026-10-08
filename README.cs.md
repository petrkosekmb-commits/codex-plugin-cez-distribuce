# ČEZ Distribuce pro Codex

[English](README.md) | Česky

Komunitní plugin pro čtení naměřené spotřeby a dodávky elektřiny z Portálu naměřených dat ČEZ Distribuce (PND).

Obsahuje opakovatelný postup exportu přes přihlášený Edge a místní MCP nástroje pro kontrolu CSV, denní přehledy a uchování originálů s ověřením SHA256. Přímé API ČEZ ani automatické přihlášení nejsou připojeny. Projekt není oficiálně spojen s ČEZ Distribuce ani jí podporován.

## Instalace

Pro místní Codex na Windows:

```powershell
codex plugin marketplace add petrkosekmb-commits/codex-plugin-cez-distribuce
codex plugin add cez-distribuce@cez-distribuce-community
```

Po instalaci otevřete nový chat. Pro práci s portálem je potřeba připojené ovládání Edge a platné přihlášení do PND. Místní práce s CSV vyžaduje Python 3.12; spouštěč upřednostňuje runtime Codexu, jinak použije Python v PATH. Pro časy s offsetem potřebuje Python databázi Europe/Prague; na Windows ji může poskytovat `tzdata`.

Příklady zadání: „Přečti dostupné elektroměry v ČEZ Distribuce“, „Stáhni spotřebu a dodávku za minulý měsíc“ nebo „Zkontroluj tento export CSV a spočítej denní součty“.

## Nástroje a nastavení

- `cez_status`: stav a dostupnost místního prostředí.
- `inspect_csv`: sloupce, kódování, oddělovač, malý náhled a SHA256.
- `summarize_csv`: explicitně zvolená série, jednotky, filtry a statusy.
- `save_export`: uchování originálu s ověřením kopie.
- `list_exports`: seznam exportů v cílových složkách.

Vlastní hlavní úložiště nastavte proměnnou `CEZ_OUTPUT_DIR`, záložní složku `CEZ_PENDING_DIR` před spuštěním Codexu. Výchozí cesty jsou `Z:\ZALOHA\07_CODEX\outputs\cez-distribuce` a `%USERPROFILE%\Codex\pending-Z\outputs\cez-distribuce`. Použijte absolutní cesty mimo OneDrive. Plugin záložní složku sám nesynchronizuje a neobsahuje plánovač. Příznaky `z_verified` a `stored_on_z` označují hlavní úložiště i při jeho přenastavení.

Podrobnosti: [návod pluginu](plugins/cez-distribuce/README.cs.md), [postup pro portál](plugins/cez-distribuce/skills/cez-distribuce/references/portal.md), [možnosti API](plugins/cez-distribuce/skills/cez-distribuce/references/api.md).

## Stav ověření

Verze 0.1.3 byla ověřena 8. 10. 2026 na skutečně staženém úplném CSV jednoho elektroměru, profilu +A/-A/Rv v kW za září 2026. Soubor obsahoval všech 2 880 čtvrthodinových intervalů a součty odběru i dodávky odpovídaly statistice portálu po zaokrouhlení na tři desetinná místa. Jeden interval měl status naměřených dat s výpadkem napětí; byl výslovně zahrnut pro shodu se součtem portálu. Skutečná naměřená data zůstávají mimo repozitář.

Parser podporuje opakované názvy `Datum`/`Status` pomocí pozic sloupců od jedné (`#1`, `#2` atd.), CP1250, desetinné čárky a zápis konce dne `24:00:00`. Pro přiřazení půlnoční hodnoty předchozímu dni nastavte `timestamp_position="interval_end"` a délku intervalu. Ostatní profily, formáty a živé exporty přes změnu letního času nejsou ověřeny. Mapování sloupců, význam veličiny, jednotky a přijatelné statusy se stále zadávají výslovně; `cez_status` uvádí rozsah historické zkoušky, nikoli aktuální přihlášení nebo dostupnost portálu.

Oficiální služba AZD podle [podmínek ČEZ](https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/sluzba-automatickeho-zasilani-namerenych-dat) vyžaduje samostatnou aktivaci a alespoň 30 odběrných míst typu A/B. Tato verze SOAP klienta neobsahuje.

## Vývoj a soukromí

```powershell
python -B -m unittest discover -s plugins/cez-distribuce/tests -v
```

Testy používají syntetické CSV a dočasné složky. Do repozitáře neukládejte hesla, cookies, tokeny, EAN, skutečné exporty ani místní konfiguraci. Naměřená data zpracovávejte ve vlastním úložišti.

## Podpora projektu

Pokud vám plugin pomáhá, můžete podpořit jeho další vývoj a údržbu na [Buy Me a Coffee](https://buymeacoffee.com/kojakcio). Děkuji za podporu.

## Licence

MIT. Viz [LICENSE](LICENSE).
