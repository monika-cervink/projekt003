import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import re
from prettytable import PrettyTable


def stazeni_html(adresa_stranky: str):
    """Stáhne HTML a vytvoří BeautifulSoup objekt"""

    r = requests.get(adresa_stranky)
    if r.status_code != 200:
        raise RuntimeError(f"odkaz {adresa_stranky} vrátil status {r.status_code}")
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    return soup


def list_odkazy_obci(startovni_url_okresu: str) -> list:
    """Vytvoří seznam odkazů jednotlivých obcí pro daný okres"""

    soup = stazeni_html(startovni_url_okresu)
    td_cislo = soup.find_all("td", {"class": "cislo"})
    href_list = [(y.get("href")) for x in td_cislo for y in x.find_all("a")]
    spojene_url = map(lambda x: urljoin("https://volby.cz/pls/ps2017nss/", x), href_list)

    return list(spojene_url)


def kody_a_nazvy_obci(odkaz_okresu: str) -> dict:
    """Vytvoří slovník s kódy a názvy obcí pro daný okres"""

    soup = stazeni_html(odkaz_okresu)
    nazvy_obci = []
    kody_obci = []
    index = 0

    try:
        while index >= 0:
            obec = soup.find_all("td")[index + 1].text
            kod = soup.find_all("td")[index].text
            if len(nazev) > 1:
                nazvy_obci.append(obec)
                kody_obci.append(kod)
            index += 3
    except IndexError:
        pass

    vysledek = {
        "kód obce": kody_obci,
        "název obce": nazvy_obci,
    }

    return vysledek


def pocty_volicu_obalek_a_hlasu(odkaz_obce: str) -> dict:
    """Vrací počty voličů, vydaných obálek a platných hlasů pro danou obec"""

    soup = stazeni_html(odkaz_obce)
    tabulka = soup.find("table", {"class": "table"})

    pocty_volicu = tabulka.find_all("td")[3].text
    pocty_vydanych_obalek = tabulka.find_all("td")[4].text
    pocty_platnych_hlasu = tabulka.find_all("td")[7].text

    return {
        "pocty_volicu": uprav_nbsp(pocty_volicu),
        "pocty_vydanych_obalek": uprav_nbsp(pocty_vydanych_obalek),
        "pocty_platnych_hlasu": uprav_nbsp(pocty_platnych_hlasu)
    }


def uprav_nbsp(text: str) -> str:
    """Přepíše pevnou mezeru v textu na klasickou mezeru"""

    regex = re.compile(r"\xa0")
    upraveny_text = regex.sub(" ", text)

    return upraveny_text


def strany_v_cr() -> dict:
    """Vytvoří slovník, kde klíče jsou všechny kandidující strany v ČR
    a hodnoty (počty hlasů) jsou nula.
    Slouží jako příprava pro naplnění hodnotami z jednotl. obcí."""

    vysledky_cr = "https://volby.cz/pls/ps2017nss/ps2?xjazyk=CZ&xkraj=0"
    soup = stazeni_html(vysledky_cr)
    strany = []
    index = 10

    try:
        while index:
            strana = soup.find_all("td")[index].text
            if len(strana) > 1:
                strany.append(strana)
            index += 4

    except IndexError:
        vysledek = {}
        vysledek = vysledek.fromkeys(strany, 0)
        return vysledek


def strany_a_hlasy_v_obci(odkaz_obce: str) -> dict:
    """Vytvoří slovník, kde klíče jsou kandidující strany pro danou obec
    a hodnoty se rovnají počtu hlasů pro danou stranu"""

    soup = stazeni_html(odkaz_obce)
    index = 10
    vysledek = {}

    try:
        while index:
            strana = soup.find_all("td")[index].text
            pocet_hlasu = soup.find_all("td")[index + 1].text
            upraveny_pocet_hlasu = uprav_nbsp(pocet_hlasu)
            if len(strana) > 1:
                vysledek[strana] = upraveny_pocet_hlasu
            index += 5

    except IndexError:
        return vysledek


def uloz_data_do_csv(odkaz_okresu: str, nazev_souboru: str):
    """Hlavní funkce, která posbírá data z jednotlivých funkcí
    a uloží je do csv souboru"""

    nazev_souboru = (nazev_souboru + ".csv")
    print("Ukládám soubor...")

    with open(nazev_souboru, "w") as file:
        header = ["kód obce", "název obce", "voliči v seznamu", "vydané obálky", "platné hlasy", *strany_v_cr()]
        writer = csv.writer(file)
        writer.writerow(header)

        kody_obci = kody_a_nazvy_obci(odkaz_okresu)["kód obce"]
        nazvy_obci = kody_a_nazvy_obci(odkaz_okresu)["název obce"]

        index = 0
        try:
            for obec in list_odkazy_obci(odkaz_okresu):
                slovnik_vsech_stran = strany_v_cr()
                slovnik_vsech_stran.update(strany_a_hlasy_v_obci(obec))
                radek = {
                    "kód obce": kody_obci[index],
                    "název obce": nazvy_obci[index],
                    "voliči v seznamu": pocty_volicu_obalek_a_hlasu(obec)["pocty_volicu"],
                    "vydané obálky": pocty_volicu_obalek_a_hlasu(obec)["pocty_vydanych_obalek"],
                    "platné hlasy": pocty_volicu_obalek_a_hlasu(obec)["pocty_platnych_hlasu"],
                    **slovnik_vsech_stran
                }

                finalni_data = list(radek.values())
                writer.writerow(finalni_data)
                index += 1

        except IndexError:
            pass

    return nazev_souboru


def slovnik_okresy() -> dict:
    """Vytvoří slovník, kde klíče jsou názvy okresů a hodnoty jsou odkazy na daný okres.
    Slouží pro výběr okresu uživatelem a vybraný odkaz okresu pak vstupuje do hlavní funkce"""

    soup = stazeni_html("https://volby.cz/pls/ps2017nss/ps3?xjazyk=CZ#1")

    nazvy_okresu = []
    index = 1
    try:
        while index:
            nazev_okresu = soup.find_all("td")[index].text
            if nazev_okresu != "Zahraničí":
                nazvy_okresu.append(nazev_okresu)
            index += 4
    except IndexError:
        pass

    najdi_td_center = soup.find_all("td", {"class": "center"})
    href_list = [(y.get("href")) for x in najdi_td_center for y in x.find_all("a")]
    vyfiltrovane_odkazy = filter(lambda x: x.startswith("ps32"), href_list)
    spojene_odkazy = map(lambda x: urljoin("https://volby.cz/pls/ps2017nss/", x), vyfiltrovane_odkazy)

    return dict(zip(nazvy_okresu, list(spojene_odkazy)))


if __name__ == "__main__":                  # uživatelské rozhraní se vstupy

    ODDELOVAC = 200 * "="
    print(ODDELOVAC)
    print("Vítejte v aplikaci pro stahování volebních výsledků.")
    print(ODDELOVAC)
    print("V tabulce níže jsou uvedeny okresy, jejichž výsledky je možné stáhnout:")

    # tabulka s přehledem okresů k výběru
    okresy_dle_abc = sorted(slovnik_okresy().keys())
    ciselny_seznam_okresu = list(enumerate(okresy_dle_abc, 1))
    tab = PrettyTable()
    tab.field_names = ["Volba", "Okres"]
    tab.add_rows(ciselny_seznam_okresu)
    print(tab)
    print(ODDELOVAC)

    while True:
        try:
            volba_okres = int(input("Zvolte číslo okresu, který Vás zajímá: "))
            if 78 > volba_okres > 0:
                break
            else:
                print("Zadejte číslo od 1 do 77!")

        except ValueError:
            print("Zadejte číslo od 1 do 77!")

    while True:
        nazev = input("Zadejte název souboru, do kterého chcete výsledky uložit: ")
        if not nazev.isalpha() or " " in nazev:
            print("Název souboru musí být jednoslovný a musí obsahovat pouze písmena!")
        else:
            break

    print("Zvolený okres: ", ciselny_seznam_okresu[volba_okres-1][1])
    # vypíše vybraný okres

    zvoleny_okres = slovnik_okresy()[ciselny_seznam_okresu[volba_okres-1][1]]
    # vytáhne příslušnou URL

    uloz_data_do_csv(zvoleny_okres, nazev)
    # provede hlavní funkci

    print("Soubor uložen.")
