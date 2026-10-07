# Ověření portálu dne 7. 10. 2026

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

Jde o pozorovaný endpoint webového exportu, nikoli dokumentované veřejné REST API. Stažení 7. 10. 2026 skončilo chybou připojení ERR_CONNECTION_TIMED_OUT a nebyl získán vzorový soubor. Skutečné schéma CSV tedy dosud není ověřené. Parser záměrně vyžaduje explicitní mapování sloupců; generická syntetická zkouška není ověření schématu ČEZ.

Browser workflow: načti správnou existující Edge kartu, vyber konkrétní okno podle viditelného elektroměru, nastav požadované období/profil, vyhledej data, otevři exportní nabídku, před kliknutím na CSV zahaj čekání na download a převezmi jeho místní cestu. Pokud export naviguje na chybu, vrať se na původní dashboard. Při expiraci přihlášení umožni běžné přihlášení uživatele; nezískávej cookies z profilu prohlížeče.

Veřejný popis PND: https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/portal-namerenych-dat
