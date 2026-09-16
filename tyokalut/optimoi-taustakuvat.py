#!/usr/bin/env python3
"""Pienentää CSS:n taustakuvat ja pakkaa ne uudelleen.

MIKSI: kaikki taustakuvat olivat 1800 px leveitä, mutta ne ovat koristekuvia
tumman gradientin alla (.hero, .page-hero, .image-band, .site-footer). Selain
skaalaa taustan näkyvän alueen leveyteen, joten 1800 px hyödyttää vain yli
1800 px levyistä ikkunaa -- ja siellä kuva on gradientin alla.

Pelkkä uudelleenpakkaus EI auta: 1800 px:ssä q75 tuotti footer-suosta 220 kt
kun nykyinen oli 182 kt. Pikselimäärä on se mikä maksaa, ei laatuasetus.

LAATU SEURAA GRADIENTTIA. Mitä tummemman peiton alla kuva on, sitä vähemmän
pakkausartefaktit näkyvät, joten LAADUT-taulukko on sidottu style.css:n
gradienttien läpinäkymättömyyteen. Jos gradienttia vaalennetaan, nosta laatua.

Kuvakortit (acc-*, ref-*) eivät ole listassa: ne ovat terävää sisältöä ilman
gradienttia, ja 800-1500 px vastaa niiden todellista näyttökokoa.

Lähteenä on .jpg, koska se on repon tarkin versio. Tiedostoa ei korvata jos
tulos kasvaisi -- hero-heinavesi.webp on jo tiukemmin pakattu kuin tämä saa
siitä (17 kt), joten se jää ennalleen.

Ajetaan repon juuresta: python3 tyokalut/optimoi-taustakuvat.py
"""

from pathlib import Path

from PIL import Image

MAKS_LEVEYS = 1400
JPG_LAATU = 78  # vain vanhojen selainten varafallback, ei kriittinen

# nimi -> webp-laatu. Perustelu = gradientin peitto style.css:ssä.
LAADUT = {
    # .site-footer: 0,68-0,80 tumma peitto -> artefaktit eivät näy
    "footer-suo": 60,
    # .page-hero: var(--hero-tint) 0,60-0,70
    "hero-suo-aamu": 64,
    "hero-syysranta": 64,
    "hero-kalliosaari": 66,
    "hero-suokasvit": 66,
    "hero-usvaranta": 66,
    "hero-usva-jarvi": 66,
    "hero-kuusikko": 66,
    "hero-kaislikko": 66,
    "hero-heinavesi": 66,
    # .image-band: vain 0,45-0,60 -> kuva näkyy selvemmin
    "band-soutaja": 72,
    # .hero: gradientti haipuu 0,72 -> 0,14, eli alaosa on lähes paljas.
    # Sama tiedosto on myös .site-header.scrolled -taustana joka sivulla.
    "hero-jarvi": 74,
}

juuri = Path(__file__).resolve().parent.parent


def kt(polku: Path) -> int:
    return polku.stat().st_size // 1024


def main() -> None:
    ennen = jalkeen = 0

    for nimi, laatu in LAADUT.items():
        jpg = juuri / f"{nimi}.jpg"
        webp = juuri / f"{nimi}.webp"
        if not jpg.exists():
            print(f"  OHITETAAN {nimi}: {jpg.name} puuttuu")
            continue

        ennen += kt(jpg) + (kt(webp) if webp.exists() else 0)

        with Image.open(jpg) as src:
            kuva = src.convert("RGB")
            if kuva.width > MAKS_LEVEYS:
                korkeus = round(kuva.height * MAKS_LEVEYS / kuva.width)
                kuva = kuva.resize((MAKS_LEVEYS, korkeus), Image.LANCZOS)

            # method=6 on hitain ja tiukin WebP-haku; kuvat ajetaan harvoin.
            for kohde, asetukset in (
                (webp, {"quality": laatu, "method": 6}),
                (jpg, {"quality": JPG_LAATU, "progressive": True, "optimize": True}),
            ):
                vanha_koko = kt(kohde) if kohde.exists() else None
                tmp = kohde.with_suffix(kohde.suffix + ".uusi")
                kuva.save(tmp, format=kohde.suffix[1:].replace("jpg", "jpeg"), **asetukset)

                if vanha_koko is not None and kt(tmp) >= vanha_koko:
                    tmp.unlink()
                    print(f"  {nimi + kohde.suffix:<24} {vanha_koko} kt  EI PIENENNY, jää ennalleen")
                else:
                    tmp.replace(kohde)

        jalkeen += kt(jpg) + kt(webp)
        print(f"  {nimi:<18} q{laatu}  {kuva.width}x{kuva.height}  webp {kt(webp)} kt  jpg {kt(jpg)} kt")

    print(f"\nYhteensä (webp+jpg) {ennen} kt -> {jalkeen} kt  (-{ennen - jalkeen} kt)")


if __name__ == "__main__":
    main()
