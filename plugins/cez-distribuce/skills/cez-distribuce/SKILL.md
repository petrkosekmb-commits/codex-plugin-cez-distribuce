---
name: cez-distribuce
description: Čti naměřenou spotřebu a dodávku elektřiny v ČEZ Distribuce PND, stáhni CSV přes přihlášený Edge a zkontroluj nebo vyhodnoť export. Použij pro PND a hodnoty distribučního elektroměru; nastavení odběrných míst a aktivaci služeb tato dovednost neprovádí.
---

# ČEZ Distribuce – naměřená data

Pracuj přes existující přihlášenou relaci Edge na `https://pnd.cezdistribuce.cz/cezpnd2/external/dashboard/view`. Místní MCP `cez-distribuce` zpracovává exporty; sám nestahuje data ani neprovádí přihlášení. Stav možností zjisti přes `cez_status`. Neprezentuj místní MCP jako aktivované API ČEZ.

## Čtení a export

Použij dostupné browser nástroje a načti aktuální stránku. Ověř přihlášení, konkrétní EAN/elektroměr, sestavu, profil a období. Okna mohou měnit pořadí i ID. Označení ELM není EAN. Domácí název odběrného místa přiřaď jen podle doloženého propojení; tři okna nejsou důkaz tří různých adres.

Pro konkrétní kroky, názvy profilů a pozorovaný exportní endpoint čti [references/portal.md](references/portal.md). Souhrn viditelných dat poskytni přímo. Pro přesné intervaly a součty použij CSV, nejlépe úplné CSV se statusy. Stažení musí skutečně vrátit místní soubor. Při chybě připojení nebo přihlášení neoznačuj export za dokončený; zachovej původní stránku a uveď omezení. Po dvou neúspěšných pokusech stejné operace přestaň opakovat a pokračuj místním zpracováním dostupných dat.

Heslo, cookies ani přihlašovací tokeny neukládej do pluginu nebo exportu. Neměň registraci, upozornění, množiny zařízení ani sestavy kvůli čtení dat. Nové služby nebo automatizaci aktivuj pouze na odpovídající výslovný požadavek.

## Místní nástroje

- `inspect_csv(path, header_row=1, encoding?, delimiter?)`: zjistí formát, sloupce, úvodní řádky a SHA256. `header_row` je pořadí záznamu CSV od 1 včetně případného úvodu. Náhled má nejvýše 5 záznamů. Neznámé schéma vyhodnoť před výpočtem.
- `summarize_csv`: vyžaduje přesné názvy časového a hodnotového sloupce, formát času, význam veličiny a jednotku. Volitelně sloupec stavu a výslovný seznam přijatelných stavů nebo filtry jedné série/elektroměru. Nikdy nesčítej současně spotřebu, dodávku a registry. Chybějící hodnota není nula. Pro intervalovou energii sčítej kWh/Wh/MWh. Pro průměrný výkon kW/W/MW musí být známá skutečná délka intervalu. Kumulativní registr se nesčítá; nástroj vrací rozdíl první/poslední hodnoty a odmítá pokles registru. Data PND nepovažuj za fakturační doklad.
- `save_export(path, label)`: zkopíruje originál do finálního úložiště, ověří SHA256, zachová rozdílné existující soubory a vrátí skutečnou cestu. Použij až po ověření, že jde o požadovaný export.
- `list_exports`: ukáže soubory v určených složkách pluginu, nejvýše 100. Neskenuje ostatní NAS.

Nejdříve zkontroluj jednotku v exportu/hlavičce/profilu. Profil výroby `-A` distribučního elektroměru může znamenat dodávku do sítě, nikoli celkovou výrobu střídače. Bez významu časové značky a délky intervalu nepřeváděj výkon na energii. Duplicitní časy bez offsetu jsou nejednoznačné, zvláště při změně letního času; zachovej originál a součet v takovém případě neprezentuj jako ověřený. Časy s offsetem se pro denní přehled převádějí na Europe/Prague. Součet hodnot sám nepotvrzuje úplnost období; porovnej počet intervalů, krajní časy a požadovaný rozsah včetně změny času.

Proměnné `CEZ_OUTPUT_DIR` a `CEZ_PENDING_DIR` mohou změnit cílové složky; přesné cesty zjisti přes `cez_status`. Ve výchozím nastavení originály i finální přehledy patří do `Z:\ZALOHA\07_CODEX\outputs\cez-distribuce`, při výpadku do `%USERPROFILE%\Codex\pending-Z\outputs\cez-distribuce`. Průběžné soubory ukládej do `%USERPROFILE%\Codex\outputs\cez-distribuce`. Předání vždy uvádí skutečnou cestu a příznak `z_verified`; výstup v pending-Z dosud nemá ověřenou kopii na Z:. Aktivní běhové soubory ponech na C:.

## Oficiální API

Pro požadavek na přímé API čti [references/api.md](references/api.md). V první verzi není SOAP klient ani automatické přihlášení. Oficiální služba AZD má podmínky a samostatnou aktivaci; nepředpokládej, že heslo portálu znamená přístup k této službě. Nepoužívej vymyšlené REST endpointy. Způsob budoucího napojení odvoď až z přiděleného WSDL, autentizace a potvrzených oprávnění.
