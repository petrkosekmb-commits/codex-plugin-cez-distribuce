# ČEZ Distribuce – naměřená data

[English](README.md) | Česky

Místní plugin pro Codex. Obsahuje postup čtení a exportu z přihlášeného PND v Edge a nástroje pro kontrolu, souhrn a uchování CSV. Neobsahuje hesla ani přihlašovací relaci. Oficiální SOAP služba AZD není připojena.

Komunitní projekt pro Windows, který není oficiálním produktem ČEZ Distribuce ani jí podporován.

Po instalaci otevřete nový chat a zadejte například: „Přečti dostupné elektroměry v ČEZ Distribuce“ nebo „Stáhni spotřebu a dodávku za září 2026“. Pro stahování je potřeba dostupný portál a platné přihlášení v Edge. Pro práci s již staženým CSV není přihlášení potřeba.

První přihlášené zobrazení a nabídka exportů byly ověřeny 7. 10. 2026. Samotné stažení skončilo chybou připojení. Živá zkouška skutečného CSV tedy zbývá při obnovení dostupnosti portálu. Souhrn CSV vyžaduje ověřené názvy sloupců, jednotku a význam veličiny; formát se neodhadne automaticky.

Nástroje: `cez_status`, `inspect_csv`, `summarize_csv`, `save_export`, `list_exports`. CSV parser a stdio server používají standardní knihovnu Pythonu 3.12. Spouštěč upřednostňuje Python z místního runtime Codexu, jinak hledá `python.exe` v PATH. Server lze spustit přes `scripts/start-server.ps1`; portál obsluhuje samostatně dovednost prostřednictvím připojeného prohlížeče. Pro časy s offsetem je potřeba databáze Europe/Prague (na Windows ji může poskytovat balíček `tzdata`); její dostupnost ukazuje `cez_status`. Bez ní se převod odmítne.

Výchozí finální exporty se ukládají do `Z:\ZALOHA\07_CODEX\outputs\cez-distribuce`, při nedostupnosti do `%USERPROFILE%\Codex\pending-Z\outputs\cez-distribuce`. Vlastní hlavní úložiště nastavte proměnnou prostředí `CEZ_OUTPUT_DIR` a záložní složku `CEZ_PENDING_DIR` před spuštěním Codexu. Zadejte absolutní cesty mimo OneDrive. Názvy výstupních příznaků `z_verified` a `stored_on_z` kvůli kompatibilitě označují hlavní úložiště i při jeho přenastavení. Kopie má ověřený SHA256. Odlišné existující soubory se nepřepisují. Plugin záložní složku sám nesynchronizuje.

Zdroj podmínek API: https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/sluzba-automatickeho-zasilani-namerenych-dat

## Podpora projektu

Pokud vám plugin pomáhá, můžete podpořit jeho další vývoj a údržbu na [Buy Me a Coffee](https://buymeacoffee.com/kojakcio). Děkuji za podporu.
