#!/usr/bin/env python3
"""Koostaa etusivun herokuvan: taivas lehden vasemmalla puolella.

MIKSI KOOSTE: sininen CSS-liukuväri logon takana näytti keinotekoiselta, ja
taivaan häivyttäminen tummaan taustaan näytti kollaasilta. Nyt taivas on
täysin kirkas lehden vasempaan reunaan asti, ja RAJAN MUODOSTAA LEHDEN OMA
ÄÄRIVIIVA -- kuin lehti olisi kuvattu taivasta vasten. Oikealla puolella
lehtikuvan tumma tausta säilyy, koska valikon valkoinen teksti on siellä.

Lehden tunnistus (värin ja reunan perusteella, ei käsin piirrettyä maskia):
  * lehti on oranssi, tausta harmaanruskea -> R-B-ero erottaa ne
  * lehden yläpuolella on lehdenväristä sumeaa taustaa. Se erotetaan
    reunan terävyydellä: lehden reuna on terävä (sobel 28-153), sumean
    taustan pehmeä (2-4)
  * lehden ylä- ja alapuolella raja jatkuu lehden kärjestä ja pehmenee
    asteittain, ettei synny pystysaumaa

Geometria on mitoitettu 1440 px ruudulle (kerrotaan 4/3 -> 1920 px):
lehtikuva alkaa x=200, joten lehdet ovat oikealla eivätkä osu logoon.
CSS:ssä kuva on `left 33% / cover`: kapeassa ruudussa vasen reuna (taivas)
jää logon taakse ja oikea reuna rajautuu pois.

Lähteet (eivät repossa, alkuperäinen on 3,9 Mt):
  /home/markus/lahtodata/plandisain-kuvat/syyslehdet-alkuperainen.jpg (5472x3080)
  /home/markus/lahtodata/plandisain-kuvat/taivas.png (kuvakaappaus, 882x341)

Ajetaan repon juuresta: python3 tyokalut/koosta-etusivun-hero.py
"""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

LAHDE = Path("/home/markus/lahtodata/plandisain-kuvat")
juuri = Path(__file__).resolve().parent.parent

K = 4 / 3            # 1440 -> 1920
LEVEYS = 1920
SIIRTO = 200         # lehtikuvan vasen reuna (1440-mitoissa)
LEHDEN_PISTE = (300, 950)   # (y, x) varmasti vasemman lehden sisällä, 1920-kuvassa
ALA_LEHDEN_PISTE = (640, 1470)  # (y, x) alemman lehden sisällä
TERAVYYS = 15        # lehden reunan sobel-raja; sumea tausta jää alle


def main() -> None:
    lehti = Image.open(LAHDE / "syyslehdet-alkuperainen.jpg").convert("RGB")
    taivas = Image.open(LAHDE / "taivas.png").convert("RGB")

    siirto = round(SIIRTO * K)
    lw = LEVEYS - siirto
    H = round(lehti.height * lw / lehti.width)

    pohja = Image.new("RGB", (LEVEYS, H))
    pohja.paste(lehti.resize((lw, H), Image.LANCZOS), (siirto, 0))
    # Vasen kaista lehtikuvan omalla reunalla peilattuna; jää taivaan alle.
    pohja.paste(pohja.crop((siirto, 0, siirto * 2, H)).transpose(Image.FLIP_LEFT_RIGHT), (0, 0))
    P = np.asarray(pohja, float)
    r, b = P[..., 0], P[..., 2]

    # Pehmeä lehtimaski reunojen sekoitukseen, tiukka maski muodon hakuun.
    pehmea = np.clip((r - b - 25) / 30, 0, 1)
    tiukka = ndimage.binary_opening((r - b > 45) & (r > 75), iterations=4)
    osat, _ = ndimage.label(tiukka)
    vasen_lehti = osat == osat[LEHDEN_PISTE]
    vasen_lehti = ndimage.binary_fill_holes(ndimage.binary_closing(vasen_lehti, iterations=5))

    # Rivikohtainen vasen reuna; mukaan vain rivit joilla reuna on terävä.
    reuna = np.where(vasen_lehti.any(1), np.argmax(vasen_lehti, 1), LEVEYS)
    harmaa = ndimage.gaussian_filter(P.mean(2), 1)
    gx = np.abs(ndimage.sobel(harmaa, 1))
    rivit = np.where(reuna < LEVEYS)[0]
    terava = np.array([gx[y, max(reuna[y] - 6, 0):reuna[y] + 6].max() for y in rivit])
    rivit = rivit[terava > TERAVYYS]
    ylin, alin = rivit[0], rivit[-1]

    # Alempi lehti: sen vasen reuna on rajana vasemman lehden alapuolella.
    ala = osat == osat[ALA_LEHDEN_PISTE]
    ala = ndimage.binary_fill_holes(ndimage.binary_closing(ala, iterations=5))
    ala_reuna = np.where(ala.any(1), np.argmax(ala, 1), LEVEYS).astype(float)
    ala_rivit = np.where(ala_reuna < LEVEYS)[0]
    ala_reuna[ala_rivit[-1] + 1:] = ala_reuna[ala_rivit[-1]]

    raja = np.empty(H)
    raja[ylin:alin + 1] = reuna[ylin:alin + 1]
    raja[:ylin] = raja[ylin]
    # Vasemman lehden kärjestä raja kaartuu pehmeästi alemman lehden reunaan
    # (ei vaakasaumaa kärjestä suoraan sivulle).
    y = np.arange(H)
    kaari = np.clip((y - alin) / 160, 0, 1)
    kaari = kaari * kaari * (3 - 2 * kaari)
    raja[alin + 1:] = (raja[alin] + (ala_reuna - raja[alin]) * kaari)[alin + 1:]

    # Lehtien kohdalla raja on terävä (lehti peittää sen), muualla pehmeämpi.
    etaisyys = np.where(y < ylin, ylin - y, 0)
    pehmennys = np.where(y > alin, 40, 6 + np.minimum(etaisyys, 120) * 2.5)[:, None]
    taivasosuus = np.clip((raja[:, None] - np.arange(LEVEYS)[None, :]) / pehmennys, 0, 1)

    lehdet = vasen_lehti | ala
    etuala = np.where(lehdet, 1.0, pehmea * ndimage.binary_dilation(lehdet, iterations=8))
    etuala[:max(ylin - 4, 0)] = 0   # lehden yläpuolinen lehdenvärinen tausta ei ole lehteä

    s = H / taivas.height
    T = np.asarray(taivas.resize((round(taivas.width * s), H), Image.LANCZOS), float)[:, :LEVEYS]
    T = np.pad(T, ((0, 0), (0, LEVEYS - T.shape[1]), (0, 0)), mode="edge")

    t, e = taivasosuus[..., None], etuala[..., None]
    kuva = Image.fromarray((e * P + (1 - e) * (t * T + (1 - t) * P)).astype("uint8"))

    # Laatu kuten optimoi-kuvat.py:n hero-syyslehdet-rivillä.
    kuva.save(juuri / "hero-syyslehdet.webp", quality=76, method=6)
    kuva.save(juuri / "hero-syyslehdet.jpg", quality=78, progressive=True, optimize=True)
    print(f"hero-syyslehdet {kuva.width}x{kuva.height}, lehden rivit {ylin}-{alin}")


if __name__ == "__main__":
    main()
