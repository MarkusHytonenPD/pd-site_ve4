#!/usr/bin/env python3
"""Tekee markus-hytonen.html:n Profiili-osion kuvan.

Kuva rajataan hartioista ylöspäin, ja sen reunat häivytetään läpinäkyviksi
soikealla maskilla, jotta tausta (taivas, puut) sulautuu sivun valkoiseen
pohjaan ilman suorakulmion reunoja. Häivytys on leivottu tiedostoon eikä
CSS:n mask-imagena, jotta varakuva näyttää samalta kaikissa selaimissa.

Lähde on markus-hytonen.jpg (480 x 676). Ajetaan repon juuresta:
    python3 tyokalut/tee-profiilikuva.py
"""

import numpy as np
from PIL import Image

LAHDE = "markus-hytonen.jpg"
KOHDE = "markus-hytonen-profiili"
# (vasen, ylä, oikea, ala): pää keskelle, alareuna hartioiden alapuolelle
RAJAUS = (30, 0, 430, 350)
# Maski on superellipsi |x|^P + |y|^P = 1: P = 2 olisi soikio, jonka muoto
# erottui valkoisella pohjalla; 3 on pyöristetty suorakulmio, joka seuraa
# hartioiden leveyttä. Sisäosa (SISA säteestä) on täysin peittävä, reuna
# häipyy siitä nollaan.
P = 3
SISA = 0.3

kuva = Image.open(LAHDE).convert("RGB").crop(RAJAUS)
w, h = kuva.size

x = (np.arange(w) + 0.5) / w * 2 - 1
y = (np.arange(h) + 0.5) / h * 2 - 1
d = (np.abs(x[None, :]) ** P + np.abs(y[:, None]) ** P) ** (1 / P)
t = np.clip((1 - d) / (1 - SISA), 0, 1)
alfa = t * t * (3 - 2 * t)
kuva.putalpha(Image.fromarray((alfa * 255).round().astype("uint8")))

kuva.save(KOHDE + ".webp", quality=85, method=6)
kuva.save(KOHDE + ".png", optimize=True)  # varakuva selaimille ilman WebP-tukea
print("ok", kuva.size)
