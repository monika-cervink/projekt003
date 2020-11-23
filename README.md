# projekt003
## Election scraper

### Úvod
Tento skript stahuje volební výsledky zvoleného okresu ze stránky [www.volby.cz](https://volby.cz/pls/ps2017nss/ps3?xjazyk=CZ) a ukládá je do csv souboru.

Výsledný soubor obsahuje na jednotlivých řádcích postupně všechny obce daného okresu s konkrétními čísly (počet voličů, vydané obálky, platné hlasy, počty hlasů pro jednotlivé strany).

### Spuštění
Skript lze spustit přímo z příkazové řádky v terminálu -> python3 election_scraper.py

Po spuštění vypíše tabulku s jednotlivými okresy a vyzve uživatele k volbě okresu a názvu souboru, do kterého chce výsledky uložit: např. pro okres Plzeň město je volba č. 44.

Název souboru musí být jednoslovný a složen pouze z písmen (např. Plzenmesto).

### Výstup
Jakmile vše proběhne, program vypíše "Soubor uložen" a csv soubor je k nalezení ve složce s uloženým skriptem.

### Poznámka
Pro správný běh programu je potřeba nainstalovat moduly prettytable, requests a bs4.
