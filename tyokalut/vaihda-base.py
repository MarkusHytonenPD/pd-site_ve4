#!/usr/bin/env python3
"""Vaihtaa sivuston BASE-osoitteen kaikkiin absoluuttisiin viittauksiin.

MIKSI TÄMÄ ON SKRIPTI EIKÄ MUUTTUJA: absoluuttista osoitetta tarvitaan
paikoissa joita ei voi tehdä suhteellisiksi eikä koota selaimessa:

  * <link rel="canonical">      -- suhteellinen toimisi, mutta og-tagit eivät
  * <meta property="og:url">    -- Facebook/Slack/LinkedIn EIVÄT aja JS:ää,
  * <meta property="og:image">     joten site.js:llä kootut tagit eivät näy
  * JSON-LD @id / url / logo / image / item
  * sitemap.xml <loc>           -- vaatii täydet osoitteet
  * robots.txt Sitemap:

GitHub Pages ei aja palvelinpuolen koostamista (ei SSI:tä eikä templaatteja
ilman Jekyll-rakennetta), ja Jekyllin _includes-rakenne rikkoisi sivujen
avaamisen suoraan tiedostoina. Siksi keskitys = yksi komento joka kirjoittaa
kaikki 84 esiintymää kerralla, ei käsityö 14 tiedostossa.

KÄYTTÖ (kuivaharjoitus on oletus, mikään ei muutu ilman --kirjoita):

    python3 tyokalut/vaihda-base.py https://www.plandisain.fi/
    python3 tyokalut/vaihda-base.py https://www.plandisain.fi/ --kirjoita
"""

import re
import sys
from pathlib import Path

juuri = Path(__file__).resolve().parent.parent
TIEDOSTOT = sorted(juuri.glob("*.html")) + [juuri / "sitemap.xml", juuri / "robots.txt"]


def nykyinen_base() -> str:
    """Lukee nykyisen BASEn etusivun canonical-tagista — ei erillistä
    tilatiedostoa, joka voisi jäädä jälkeen todellisuudesta."""
    html = (juuri / "index.html").read_text(encoding="utf-8")
    osuma = re.search(r'<link rel="canonical" href="(https?://[^"]*?)"', html)
    if not osuma:
        sys.exit("VIRHE: index.html:stä ei löytynyt canonical-tagia.")
    return osuma.group(1).rstrip("/") + "/"


def main() -> None:
    argumentit = [a for a in sys.argv[1:] if not a.startswith("--")]
    kirjoita = "--kirjoita" in sys.argv[1:]

    if len(argumentit) != 1:
        sys.exit(__doc__)

    vanha = nykyinen_base()
    uusi = argumentit[0].rstrip("/") + "/"

    if not uusi.startswith(("http://", "https://")):
        sys.exit(f"VIRHE: BASE tarvitsee protokollan, sai '{uusi}'.")
    if uusi == vanha:
        sys.exit(f"BASE on jo {vanha} — ei muutettavaa.")

    print(f"vanha: {vanha}\nuusi:  {uusi}\n")

    # Törmäystarkistus. Alatunnisteessa on linkki www.plandisain.fi:hin, joka EI
    # ole BASE vaan viittaus viralliseen sivustoon. Jos BASEksi annetaan sama
    # osoite, seuraava ajo ei enää pysty erottamaan näitä toisistaan ja
    # rikkoisi alatunnisteen linkit. Varoitetaan nyt, ei vasta silloin.
    ennestaan = sum(
        t.read_text(encoding="utf-8").count(uusi) for t in TIEDOSTOT if t.exists()
    )
    if ennestaan:
        print(f"  VAROITUS: uusi BASE esiintyy jo {ennestaan} kertaa muuna kuin")
        print("  BASEna (esim. alatunnisteen linkki viralliselle sivustolle).")
        print("  Ne muuttuvat erottamattomiksi BASEsta — käy ne läpi käsin")
        print("  ennen seuraavaa vaihtoa.\n")

    yhteensa = 0
    for tiedosto in TIEDOSTOT:
        if not tiedosto.exists():
            continue
        sisalto = tiedosto.read_text(encoding="utf-8")
        maara = sisalto.count(vanha)
        # robots.txt:n selittävä kommentti viittaa isäntään ilman polkua
        maara += sisalto.count(vanha.split("://", 1)[1].rstrip("/"))
        if not maara:
            continue
        yhteensa += sisalto.count(vanha)
        print(f"  {tiedosto.name:<28} {sisalto.count(vanha):>2} kpl")
        if kirjoita:
            tiedosto.write_text(sisalto.replace(vanha, uusi), encoding="utf-8")

    print(f"\nYhteensä {yhteensa} esiintymää {len(TIEDOSTOT)} tiedostossa.")

    if not kirjoita:
        print("\nKUIVAHARJOITUS — mitään ei kirjoitettu. Lisää --kirjoita.")
        return

    print("\nKirjoitettu. Tarkista vielä käsin:")
    print("  * robots.txt: projektipolussa se ei tehoa, mutta oman")
    print("    verkkotunnuksen juuressa se ALKAA ohjata indeksointia.")
    print("  * GitHub Pages: Settings > Pages > Custom domain + CNAME-tiedosto.")
    print("  * Vanhat osoitteet: harkitse uudelleenohjausta, jotta")
    print("    jaetut linkit eivät kuole.")


if __name__ == "__main__":
    main()
