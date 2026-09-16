#!/usr/bin/env python3
"""Pienentää sivuston kuvat mittaamalla todettuihin mittoihin.

Kaksi eri tapausta, jotka vaativat eri logiikan:

TAUSTAKUVAT (CSS:n background-image gradientin alla)
  Kaikki olivat alun perin 1800 px leveitä. Pelkkä uudelleenpakkaus KASVATTAA
  tiedostoja (footer-suo 182 -> 220 kt q75:llä) -- hukka on pikselimäärässä.
  Laatu seuraa gradientin peittävyyttä: mitä tummemman peiton alla kuva on,
  sitä vähemmän artefaktit näkyvät. Jos gradienttia vaalennetaan, nosta laatua.

  Leveys on kuvakohtainen, koska tarve on mitattu selaimesta. Kuva PIENENNETÄÄN,
  ei rajata: rajaaminen muuttaisi sommittelua puhelimessa, koska cover näyttää
  kapeassa ruudussa kuvan koko korkeuden. Pienentäminen säilyttää kuvasuhteen,
  joten background-position pysyy samana eikä CSS:ää tarvitse koskea.

KORTTIKUVAT (<img> kortin kuvapinnassa, ei gradienttia)
  Näissä ei ole peittoa, joten laatua ei voi laskea yhtä paljon. Sen sijaan
  tiedosto rajataan siihen kuvasuhteeseen jossa se NÄYTETÄÄN: CSS antaa
  kuvapinnalle aspect-ratio-arvon ja object-fit: cover rajaa lopun pois, joten
  ylimääräiset reunapikselit eivät näy koskaan. Rajaus on ilmainen voitto.

Lähteenä on .jpg, koska se on repon tarkin versio. Tiedostoa ei korvata jos
tulos kasvaisi, joten skriptin voi ajaa uudelleen turvallisesti -- esimerkiksi
hero-heinavesi.webp on jo tiukemmin pakattu kuin tämä saa siitä.

Ajetaan repon juuresta: python3 tyokalut/optimoi-kuvat.py
"""

from pathlib import Path

from PIL import Image

JPG_LAATU = 78  # vain vanhojen selainten varafallback, ei kriittinen

# nimi -> (maksimileveys, webp-laatu)
# Leveydet on mitattu selaimesta: hero-laatikko on työpöydällä vain ~310 px
# korkea, joten 1920 px ikkunassa kuvasta näkyy 29 % pikseleistä ja se
# venytetään joka tapauksessa. Laatu perustuu gradientin peittoon style.css:ssä.
TAUSTAKUVAT = {
    # .site-footer: 0,68-0,80 tumma peitto -> artefaktit eivät näy
    "footer-suo": (1400, 60),
    # .page-hero: var(--hero-tint) 0,60-0,70.
    # hero-suo-aamu oli sivuston raskain tiedosto (165 kt 1400 px:ssä): usva ja
    # heinikko ovat kalliita pakata. 1100 px venyttää 1440 px ikkunassa 1,31x,
    # mutta mitattu ero renderöinnin JÄLKEEN on 1,8 / 255 eli näkymätön.
    "hero-suo-aamu": (1100, 58),
    "hero-syysranta": (1400, 64),
    "hero-kalliosaari": (1400, 66),
    "hero-suokasvit": (1400, 66),
    "hero-usvaranta": (1400, 66),
    "hero-usva-jarvi": (1400, 66),
    "hero-kuusikko": (1400, 66),
    "hero-kaislikko": (1400, 66),
    "hero-heinavesi": (1400, 66),
    # .image-band: vain 0,45-0,60 -> kuva näkyy selvemmin
    "band-soutaja": (1400, 72),
    # .hero: gradientti haipuu 0,72 -> 0,14, eli alaosa on lähes paljas.
    # Sama tiedosto on myös .site-header.scrolled -taustana joka sivulla.
    "hero-jarvi": (1400, 74),
}

# nimi -> (kuvapinnan kuvasuhde CSS:ssä, webp-laatu)
# HUOM: jos style.css:n aspect-ratio muuttuu, muuta sama arvo tästä -- muuten
# rajaus leikkaa pois jotain mikä pitäisi näkyä.
KORTTIKUVAT = {
    # .ref-category.card--media .card-media img { aspect-ratio: 16 / 10 }
    # ref-sarakasvi on korttikuvista kallein (79 kt kun sisarkuvat ovat 20-26
    # kt): tuhansia ohuita korsia kirjavaa heijastusta vasten on pakkaukselle
    # pahin mahdollinen sisältö. Leveys 800 px on mitattu oikeaksi -- 900 px
    # taitekohdassa kortti on yksipalstainen ja kuva 826 px leveä.
    "ref-sarakasvi": (16 / 10, 58),
}

juuri = Path(__file__).resolve().parent.parent


def kt(polku: Path) -> int:
    return polku.stat().st_size // 1024


def kirjoita(kuva: Image.Image, kohde: Path, **asetukset) -> str:
    """Kirjoittaa vain jos tulos pienenee. Palauttaa selosteen."""
    vanha = kt(kohde) if kohde.exists() else None
    tmp = kohde.with_suffix(kohde.suffix + ".uusi")
    muoto = "JPEG" if kohde.suffix == ".jpg" else "WEBP"
    kuva.save(tmp, format=muoto, **asetukset)

    if vanha is not None and kt(tmp) >= vanha:
        tmp.unlink()
        return f"{vanha} kt (ei pienene, ennallaan)"
    tmp.replace(kohde)
    return f"{kt(kohde)} kt" + (f" (oli {vanha})" if vanha else "")


def aja(nimi: str, muokkaa, laatu: int) -> tuple[int, int]:
    jpg = juuri / f"{nimi}.jpg"
    webp = juuri / f"{nimi}.webp"
    if not jpg.exists():
        print(f"  OHITETAAN {nimi}: {jpg.name} puuttuu")
        return 0, 0

    ennen = kt(jpg) + (kt(webp) if webp.exists() else 0)
    with Image.open(jpg) as src:
        kuva = muokkaa(src.convert("RGB"))
        # method=6 on hitain ja tiukin WebP-haku; kuvat ajetaan harvoin.
        w = kirjoita(kuva, webp, quality=laatu, method=6)
        j = kirjoita(kuva, jpg, quality=JPG_LAATU, progressive=True, optimize=True)
    print(f"  {nimi:<18} {kuva.width}x{kuva.height} q{laatu}   webp {w:<26} jpg {j}")
    return ennen, kt(jpg) + kt(webp)


def main() -> None:
    ennen = jalkeen = 0

    print("Taustakuvat (pienennys, laatu gradientin mukaan):")
    for nimi, (maks_leveys, laatu) in TAUSTAKUVAT.items():
        def pienenna(kuva, maks_leveys=maks_leveys):
            if kuva.width <= maks_leveys:
                return kuva
            korkeus = round(kuva.height * maks_leveys / kuva.width)
            return kuva.resize((maks_leveys, korkeus), Image.LANCZOS)

        a, b = aja(nimi, pienenna, laatu)
        ennen += a
        jalkeen += b

    print("\nKorttikuvat (rajaus näytettyyn kuvasuhteeseen):")
    for nimi, (suhde, laatu) in KORTTIKUVAT.items():
        def rajaa(kuva, suhde=suhde):
            if abs(kuva.width / kuva.height - suhde) < 0.01:
                return kuva          # jo oikeassa suhteessa, ei rajata uudelleen
            if kuva.width / kuva.height > suhde:
                # liian leveä -> cover rajaa leveyttä, keskitettynä
                uusi = round(kuva.height * suhde)
                reuna = (kuva.width - uusi) // 2
                return kuva.crop((reuna, 0, reuna + uusi, kuva.height))
            uusi = round(kuva.width / suhde)
            reuna = (kuva.height - uusi) // 2
            return kuva.crop((0, reuna, kuva.width, reuna + uusi))

        a, b = aja(nimi, rajaa, laatu)
        ennen += a
        jalkeen += b

    print(f"\nYhteensä (webp+jpg) {ennen} kt -> {jalkeen} kt  (-{ennen - jalkeen} kt)")


if __name__ == "__main__":
    main()
