# ČEZ Distribuce – naměřená data

[English](README.md) | Česky

Místní plugin pro Codex. Obsahuje postup čtení a exportu z přihlášeného PND v Edge a nástroje pro kontrolu, souhrn a uchování CSV. Neobsahuje hesla ani přihlašovací relaci. Oficiální SOAP služba AZD není připojena.

Komunitní projekt pro Windows, který není oficiálním produktem ČEZ Distribuce ani jí podporován.

Po instalaci otevřete nový chat a zadejte například: „Přečti dostupné elektroměry v ČEZ Distribuce“ nebo „Stáhni spotřebu a dodávku za září 2026“. Pro stahování je potřeba dostupný portál a platné přihlášení v Edge. Pro práci s již staženým CSV není přihlášení potřeba.

Verze 0.1.3 byla ověřena 8. 10. 2026 na skutečném úplném CSV profilu +A/-A/Rv v kW za září 2026: 2 880 čtvrthodinových intervalů se součty energie odpovídajícími statistice portálu na tři desetinná místa. Jeden interval označený jako naměřená data s výpadkem napětí byl výslovně zahrnut. Jde o historickou zkoušku tohoto formátu, nikoli o kontrolu aktuální relace nebo všech profilů. Soukromá naměřená data nejsou součástí pluginu.

Opakované názvy sloupců vybírejte podle pozice od jedné, např. `timestamp_column="#1"`, `value_column="#2"` a `status_column="#3"`, které uvádí `inspect_csv`. Druhá série ověřeného úplného profilu používá pozice `#4`/`#5`/`#6`. Vždy ověřte aktuální hlavičku a jednotky. Jen při potvrzeném významu nastavte `quantity="mean_power"`, `unit="kW"`, `interval_minutes=15`, `time_format="%d.%m.%Y %H:%M:%S"` a `timestamp_position="interval_end"`. Půlnoc PND `24:00:00` se převede na `00:00:00` následujícího dne; energie intervalu patří dni předchozímu. Přijatelné statusy vybírejte výslovně a uvádějte výpadky nebo vyloučená data. Ostatní formáty a živé exporty přes změnu letního času zatím nejsou ověřeny.

Nástroje: `cez_status`, `inspect_csv`, `summarize_csv`, `save_export`, `list_exports`. CSV parser a stdio server používají standardní knihovnu Pythonu 3.12. Spouštěč upřednostňuje Python z místního runtime Codexu, jinak hledá `python.exe` v PATH. Server lze spustit přes `scripts/start-server.ps1`; portál obsluhuje samostatně dovednost prostřednictvím připojeného prohlížeče. Pro časy s offsetem je potřeba databáze Europe/Prague (na Windows ji může poskytovat balíček `tzdata`); její dostupnost ukazuje `cez_status`. Bez ní se převod odmítne.

Výchozí finální exporty se ukládají do `Z:\ZALOHA\07_CODEX\outputs\cez-distribuce`, při nedostupnosti do `%USERPROFILE%\Codex\pending-Z\outputs\cez-distribuce`. Vlastní hlavní úložiště nastavte proměnnou prostředí `CEZ_OUTPUT_DIR` a záložní složku `CEZ_PENDING_DIR` před spuštěním Codexu. Zadejte absolutní cesty mimo OneDrive. Názvy výstupních příznaků `z_verified` a `stored_on_z` kvůli kompatibilitě označují hlavní úložiště i při jeho přenastavení. Kopie má ověřený SHA256. Odlišné existující soubory se nepřepisují. Plugin záložní složku sám nesynchronizuje.

Zdroj podmínek API: https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/sluzba-automatickeho-zasilani-namerenych-dat

## Podpora projektu

Pokud vám plugin pomáhá, můžete podpořit jeho další vývoj a údržbu na [Buy Me a Coffee](https://buymeacoffee.com/kojakcio). Děkuji za podporu.
