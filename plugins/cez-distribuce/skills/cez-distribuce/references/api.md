# Oficiální webové služby ČEZ

Ověřeno dne 7. 10. 2026 na stránce ČEZ Distribuce:
https://www.cezdistribuce.cz/cs/pro-zakazniky/potrebuji-vyresit/elektromery-a-odecty/sluzba-automatickeho-zasilani-namerenych-dat

ČEZ popisuje službu automatického zasílání naměřených dat (AZD) jako bezplatnou elektronickou výměnu strukturovaných zpráv prostřednictvím webových služeb. Stránka stanovuje alespoň 30 odběrných míst s dálkovou komunikací, typu měření A/B. Aktivace se žádá podepsanou žádostí. Podmínky nejsou odvozeny z počtu oken na dashboardu; způsobilost tohoto účtu nebyla potvrzena.

Stránka odkazuje na podmínky poskytování služby, definice zpráv, WSDL, XSD, XML příklady a návod SOAP UI. Pro budoucí připojení si z aktuální stránky vyžádej přesné dokumenty a potvrzení aktivace. Před implementací urči, které operace skutečně vracejí data a které vytvářejí úlohy, a ověř autentizaci, certifikáty, síťový přístup a jednotky zpráv. První verze pluginu na tyto služby nevolá a nemá k nim přihlašovací údaje.

Alternativou pro jednotlivá místa je export přihlášeného portálu PND. Exportní endpoint byl pozorován v prohlížeči, ale stažení při úvodní zkoušce selhalo připojením. Pro budoucí neoficiální klient je nutné nejprve ověřit funkční export a podporovaný způsob přihlášení. Nevydávej interní endpoint ani komunitní skript za oficiálně podporované API.
