#!/usr/bin/env python3
"""Tekee markus-hytonen.html:n heroon taustakerroksen profiilikuvasta.

Kuva on heron TAUSTAKERROS eikä <img>, koska yläpalkki (.site-header::before)
on heron taustan kopio: vain taustakerroksena kuva näkyy myös palkin kohdalla
ja voi ulottua valikkolinkkien taakse. Taustakerrokseen ei voi kohdistaa CSS:n
mask-imagea eikä filteriä, joten molemmat leivotaan tiedostoon:

  - himmennys heron tummennettuun sävyyn (brightness 0,72, saturaatio 0,9)
  - reunojen häivytys läpinäkyväksi: vaakasuunnassa 22 % kummastakin reunasta,
    pystysuunnassa ylhäältä 14 % ja alhaalta 20 % (sama kuin aiempi CSS-maski)
  - lisätummennus yläosaan, joka ulottuu valikkolinkkien taakse: kerroin 0,6
    yläreunassa, nousee 1:een 35 %:n korkeudella. Tummennus on kuvassa eikä
    erillisenä CSS-gradienttina, jotta se häivyy reunoilta kuvan mukana.

Lähde on markus-hytonen.jpg (480 x 676). Ajetaan repon juuresta:
    python3 tyokalut/tee-heron-profiilikuva.py
"""

import numpy as np
from PIL import Image, ImageEnhance

LAHDE = "markus-hytonen.jpg"
KOHDE = "markus-hytonen-hero"


def ramppi(n, alku, loppu):
    """0 -> 1 ensimmäisen `alku`-osuuden matkalla, 1 -> 0 viimeisen `loppu`-osuuden."""
    t = (np.arange(n) + 0.5) / n
    return np.clip(np.minimum(t / alku, (1 - t) / loppu), 0, 1)


kuva = Image.open(LAHDE).convert("RGB")
kuva = ImageEnhance.Brightness(kuva).enhance(0.72)
kuva = ImageEnhance.Color(kuva).enhance(0.9)

w, h = kuva.size
y = (np.arange(h) + 0.5) / h
s = np.clip(y / 0.35, 0, 1)
kerroin = 0.6 + 0.4 * s * s * (3 - 2 * s)
rgb = np.asarray(kuva, dtype=float) * kerroin[:, None, None]
kuva = Image.fromarray(rgb.round().astype("uint8"))
alfa = np.outer(ramppi(h, 0.14, 0.20), ramppi(w, 0.22, 0.22))
kuva.putalpha(Image.fromarray((alfa * 255).round().astype("uint8")))

kuva.save(KOHDE + ".webp", quality=82, method=6)
kuva.save(KOHDE + ".png", optimize=True)  # varakuva selaimille ilman image-set-tukea
print("ok", kuva.size)
