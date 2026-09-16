#!/usr/bin/env python3
"""Hakee kaavan asiakirjat Weebly-sivustolta talteen ennen sen alasajoa.

MIKSI TÄMÄ ON KIIREELLINEN: viralliset kaava-asiakirjat (kaavakartat,
määräykset, selostukset, liiteselvitykset) ovat olemassa VAIN
www.plandisain.fi:n Weebly-tallennustilassa. Paikallisessa
/home/markus/lahtodata/heinlansi/ -kansiossa on 1,1 GB kenttäkuvia ja
QGIS-dataa, mutta ei yhtään PDF:ää. Jos Weebly-tilaus päättyy ennen kuin
tiedostot on kopioitu, ne ovat poissa -- ja osa niistä on lakisääteisiä
kaava-asiakirjoja joita ei voi tuottaa uudelleen.

Lataus menee REPOJEN ULKOPUOLELLE lahtodataan, koska:
  * 250 MB PDF:iä git-historiassa on pysyvä: poisto vaatisi historian
    uudelleenkirjoituksen, joka rikkoisi jo jaetut raw-osoitteet
  * julkaisutapa on vielä päättämättä (oma repo / Releases / CDN), ja
    talteenotto ei saa riippua siitä päätöksestä

Ajetaan: python3 tyokalut/hae-asiakirjat.py [--kohde POLKU]
Kartoituksen tekee erikseen kartoita-asiakirjat.py, joka kirjoittaa
asiakirjat.json-tiedoston tämän syötteeksi.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

OLETUSKOHDE = Path("/home/markus/lahtodata/plandisain-asiakirjat")


def lataa(url: str, kohde: Path) -> tuple[bool, int, str]:
    """Lataa tiedoston. Ohittaa jos koko täsmää jo -- skripti on turvallinen
    ajaa uudelleen keskeytyksen jälkeen."""
    kohde.parent.mkdir(parents=True, exist_ok=True)

    odotettu = 0
    paa = subprocess.run(["curl", "-sIL", "--max-time", "40", url],
                         capture_output=True, text=True)
    for rivi in paa.stdout.splitlines():
        if rivi.lower().startswith("content-length:"):
            odotettu = int(rivi.split(":", 1)[1].strip())

    if kohde.exists() and odotettu and kohde.stat().st_size == odotettu:
        return True, kohde.stat().st_size, "jo ladattu"

    tulos = subprocess.run(
        ["curl", "-sL", "--max-time", "600", "--retry", "3",
         "-o", str(kohde), "-w", "%{http_code}", url],
        capture_output=True, text=True)
    koodi = tulos.stdout.strip()

    if koodi != "200":
        if kohde.exists():
            kohde.unlink()
        return False, 0, f"HTTP {koodi}"

    koko = kohde.stat().st_size
    if odotettu and koko != odotettu:
        return False, koko, f"koko ei täsmää: {koko} != {odotettu}"
    return True, koko, "ok"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kohde", type=Path, default=OLETUSKOHDE)
    ap.add_argument("--kartoitus", type=Path,
                    default=Path(__file__).parent / "asiakirjat.json")
    args = ap.parse_args()

    if not args.kartoitus.exists():
        sys.exit(f"VIRHE: {args.kartoitus} puuttuu. Aja ensin "
                 f"kartoita-asiakirjat.py.")

    if str(args.kohde).find("/omat-apit/") != -1:
        sys.exit("VIRHE: kohde on repon sisällä. Asiakirjat kuuluvat "
                 "lahtodataan, ei git-historiaan.")

    tiedostot = [t for t in json.load(open(args.kartoitus)) if t["koodi"] == "200"]
    print(f"{len(tiedostot)} tiedostoa -> {args.kohde}\n")

    ok = virheita = 0
    tavuja = 0
    for t in tiedostot:
        # Projektikansio siitä sivusta joka tiedostoon viittaa; jos useampi,
        # ensimmäinen aakkosjärjestyksessä. Nimi säilyy alkuperäisenä.
        projekti = (t["sivut"][0].replace(".html", "") if t.get("sivut")
                    else "muut")
        nimi = unquote(Path(urlparse(t["url"]).path).name)
        kohde = args.kohde / projekti / nimi

        onnistui, koko, viesti = lataa(t["url"], kohde)
        if onnistui:
            ok += 1
            tavuja += koko
            print(f"  OK   {koko/1048576:7.1f} MB  {projekti}/{nimi}  ({viesti})")
        else:
            virheita += 1
            print(f"  !!   {viesti:26} {projekti}/{nimi}")

    print(f"\n{ok} ladattu ({tavuja/1048576:.1f} MB), {virheita} virhettä")
    print(f"Kohde: {args.kohde}")
    if virheita:
        sys.exit(1)


if __name__ == "__main__":
    main()
