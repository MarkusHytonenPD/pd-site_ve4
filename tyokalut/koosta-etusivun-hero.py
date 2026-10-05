#!/usr/bin/env python3
"""Koostaa etusivun herokuvan: taivas vasemmalla, syyslehdet oikealla.

MIKSI KOOSTE EIKÄ CSS-LIUKUVÄRI: sininen liukuväri logon takana näytti
keinotekoiselta. Taivaskuva häivytetään lehtikuvaan, ja samalla taivas
tummuu asteittain kohti siirtymää, jotta kirkas taivas ei katkea jyrkästi
lehtikuvan tummaan taustaan.

Geometria on mitoitettu 1440 px ruudulle (kerrotaan 4/3 -> 1920 px):
  * lehtikuva alkaa x=200, joten lehdet ovat oikealla eivätkä osu logoon
  * taivas täysin näkyvä x=200 asti, häipyy kokonaan x=600 mennessä, eli
    ennen vasemman lehden reunaa (~600)
  * logo on 1440 px:ssä kohdassa 160-321, 1920 px:ssä 400-561 -> taivaalla
CSS:ssä kuva on `left 33% / cover`: leveissä ruuduissa kuva skaalautuu
leveyden mukaan, joten suhteet pysyvät; kapeissa vasen reuna (taivas) jää
logon taakse ja oikea reuna rajautuu pois.

Lähteet (eivät repossa, alkuperäinen on 3,9 Mt):
  /home/markus/lahtodata/plandisain-kuvat/syyslehdet-alkuperainen.jpg (5472x3080)
  /home/markus/lahtodata/plandisain-kuvat/taivas.png (kuvakaappaus, 882x341)

Ajetaan repon juuresta: python3 tyokalut/koosta-etusivun-hero.py
"""

from pathlib import Path

import numpy as np
from PIL import Image

LAHDE = Path("/home/markus/lahtodata/plandisain-kuvat")
juuri = Path(__file__).resolve().parent.parent

K = 4 / 3            # 1440 -> 1920
LEVEYS = 1920
SIIRTO = 200         # lehtikuvan vasen reuna (1440-mitoissa)
TAIVAS_TAYSI = 200   # taivas täysin näkyvä tähän asti
TAIVAS_LOPPU = 600   # taivas häipynyt kokonaan
TUMMUUS = 0.55       # taivaan kirkkaus siirtymän lopussa


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def main() -> None:
    lehti = Image.open(LAHDE / "syyslehdet-alkuperainen.jpg").convert("RGB")
    taivas = Image.open(LAHDE / "taivas.png").convert("RGB")

    siirto = round(SIIRTO * K)
    lw = LEVEYS - siirto
    korkeus = round(lehti.height * lw / lehti.width)

    pohja = Image.new("RGB", (LEVEYS, korkeus))
    pohja.paste(lehti.resize((lw, korkeus), Image.LANCZOS), (siirto, 0))
    # Vasen kaista lehtikuvan omalla reunalla peilattuna; jää taivaan alle.
    reuna = pohja.crop((siirto, 0, siirto * 2, korkeus)).transpose(Image.FLIP_LEFT_RIGHT)
    pohja.paste(reuna, (0, 0))

    s = korkeus / taivas.height
    taivas_kork = Image.new("RGB", (LEVEYS, korkeus))
    taivas_kork.paste(taivas.resize((round(taivas.width * s), korkeus), Image.LANCZOS), (0, 0))

    x = np.arange(LEVEYS) / K
    alfa = 1 - smoothstep(x, TAIVAS_TAYSI, TAIVAS_LOPPU)
    kirkkaus = 1 - (1 - TUMMUUS) * smoothstep(x, 0, TAIVAS_LOPPU)

    t = np.asarray(taivas_kork, float) * np.tile(kirkkaus, (korkeus, 1))[..., None]
    m = np.tile(alfa, (korkeus, 1))[..., None]
    kuva = Image.fromarray((t * m + np.asarray(pohja, float) * (1 - m)).astype("uint8"))

    # Laatu kuten optimoi-kuvat.py:n hero-syyslehdet-rivillä.
    kuva.save(juuri / "hero-syyslehdet.webp", quality=76, method=6)
    kuva.save(juuri / "hero-syyslehdet.jpg", quality=78, progressive=True, optimize=True)
    print(f"hero-syyslehdet {kuva.width}x{kuva.height}")


if __name__ == "__main__":
    main()
