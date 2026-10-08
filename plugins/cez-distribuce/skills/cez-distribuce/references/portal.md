# Ověření portálu a exportu dne 8. 10. 2026

V existující relaci Edge byla načtena přihlášená stránka PND verze 2.6.1. Zobrazovala tři okna, sestavu „Rychlá sestava“, množiny označené „ELM …“ a období „Minulý měsíc“. Čísla elektroměrů a ID oken se do opakovatelného postupu nezapisují; zjisti je z aktuálního DOM. Spárování s adresami nebylo provedeno.

Každé okno obsahuje volbu sestavy, množiny zařízení, období a vlastního období, tlačítko „VYHLEDAT DATA“, profily a „EXPORTOVAT DATA“. Všechna nastavení cílového okna ověř před stažením, protože jiná okna mají stejné názvy ovládacích prvků.

Pozorované profily:

| Profil | Popis v portálu |
| --- | --- |
| 00 | Profil spotřeby a výroby + Rv |
| 01 | Profil spotřeby (+A) |
| 02 | Profil výroby (-A) |
| 03 | Profily spotřeby (+A, +Ri, -Rc) |
| 04 | Profily výroby (-A, -Ri, +Rc) |
| 07 | Profil spotřeby za den (+A) |
| 08 | Profil výroby za den (-A) |
| 18 | Registry za měsíc (+E, -E) |

Význam Rv a statusů se bez aktuální nápovědy nevykládá. Profily 07/08 a 01/02 jsou různé agregace, nesmí se započítat dvakrát.

Exportní nabídka obsahovala Zjednodušené CSV, XLS, XLSX a úplné CSV, XLS, XLSX, PDF. Pro zkoušku bylo zvoleno úplné CSV. Prohlížeč se pokusil otevřít tuto strukturu URL:

```text
https://pnd.cezdistribuce.cz/cezpnd2/external/data/export
?format=csv
&idAssembly=<sestava>
&idDeviceSet=<množina>
&intervalFrom=<dd.MM.yyyy HH:mm>
&intervalTo=<dd.MM.yyyy HH:mm>
&compareFrom=
&opmId=<místo>
&electrometerId=<elektroměr>
&splitStrategy=
```

Jde o pozorovaný endpoint webového exportu, nikoli dokumentované veřejné REST API. Úplné CSV bylo úspěšně staženo 8. 10. 2026 v existující přihlášené relaci. Ověřen byl jeden elektroměr a profil +A/-A/Rv v kW za září 2026, ne všechny formáty a profily.

## Pozorované úplné CSV

Soubor má kódování CP1250, středníkový oddělovač, desetinnou čárku a opakované bloky po třech sloupcích. Poslední středník vytváří prázdný sloupec. Pořadí ověř přes `inspect_csv`; nespoléhej na toto pořadí u jiného profilu.

| Pozice | Ověřený profil | Volba pro výpočet |
| --- | --- | --- |
| #1 / #2 / #3 | Datum / +A\/<elektroměr> [kW] / Status | čas / odběr / status |
| #4 / #5 / #6 | Datum / -A\/<elektroměr> [kW] / Status | čas / dodávka do sítě / status |
| #7 / #8 / #9 | Datum / Rv\/<elektroměr> [kW] / Status | samostatná referenční řada |

Pro výpočet energie použij `quantity="mean_power"`, `unit="kW"`, `interval_minutes=15`, `time_format="%d.%m.%Y %H:%M:%S"` a `timestamp_position="interval_end"`. Parser převede `dd.MM.yyyy 24:00:00` na půlnoc následujícího dne; energii intervalu přiřadí předchozímu dni. Počáteční značka byla 1. 9. 00:15:00 a poslední 30. 9. 24:00:00. Ověření zjistilo 2 880 intervalů, žádné mezery ani duplicity, 30 úplných dnů a shodu obou součtů se statistikou portálu na tři desetinná místa.

Statusy odběru a dodávky měly 2 879 hodnot `naměřená data OK` a jednu hodnotu `naměřená data, výpadek napětí`. Pro porovnání se statistikou portálu byly zahrnuty obě hodnoty seznamu; výpadek musí být uveden ve výsledku. Výběr pouze `naměřená data OK` vrací částečný součet a jeden chybějící interval. Nepovoluj automaticky všechny statusy jiného souboru. Živý export přes změnu letního času zatím není ověřen.

Nástroj `cez_status` uvádí historické ověření a jeho rozsah. Neověřuje nynější přihlášení ani dostupnost webu. Originální soubor není součástí veřejného pluginu.

Browser workflow: načti správnou existující Edge kartu, vyber konkrétní okno podle viditelného elektroměru, nastav požadované období/profil, vyhledej data, otevři exportní nabídku, před kliknutím na CSV zahaj čekání na download a převezmi jeho místní cestu. Pokud export naviguje na chybu, vrať se na původní dashboard. Při expiraci přihlášení umožni běžné přihlášení uživatele; nezískávej cookies z profilu prohlížeče.

Veřejný popis PND: https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/portal-namerenych-dat
