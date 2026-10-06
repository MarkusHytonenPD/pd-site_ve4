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
  - taivaan sävytys pään ja hartioiden korkeudella: taivas on kirkkaimmillaan
    puiden latvojen yläpuolella ja näkyi herossa vaaleana vaakakaistana kasvojen
    kohdalla. Taivas sävytetään kohti heron taivaan sinistä. Kohdistuu vain
    kirkkaisiin pikseleihin (luminanssi 150-215), joten kasvot (~95) ja puut
    eivät muutu. Vaikutus loppuu hartioiden alapuolella, jottei lumi tummu.

Lähde on markus-hytonen.jpg (480 x 676). Ajetaan repon juuresta:
    python3 tyokalut/tee-heron-profiilikuva.py
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

LAHDE = "markus-hytonen.jpg"
KOHDE = "markus-hytonen-hero"


def ramppi(n, alku, loppu):
    """0 -> 1 ensimmäisen `alku`-osuuden matkalla, 1 -> 0 viimeisen `loppu`-osuuden."""
    t = (np.arange(n) + 0.5) / n
    return np.clip(np.minimum(t / alku, (1 - t) / loppu), 0, 1)


kuva = Image.open(LAHDE).convert("RGB")

lahto = np.asarray(kuva, dtype=float)
lum = np.asarray(kuva.convert("L"), dtype=float)
taivas = np.clip((lum - 150) / (215 - 150), 0, 1)
taivas = taivas * taivas * (3 - 2 * taivas)
rivit = np.arange(lahto.shape[0])[:, None]
alue = np.clip((340 - rivit) / (340 - 300), 0, 1)   # y < 300 täysi, 340 -> 0
# Sumennettu maski, jottei puiden latvoihin jää teräviä vaaleita reunoja.
# MaxFilter laajentaa maskia muutaman pikselin ääriviivoja kohti: muuten pään ja
# hartioiden ympärille jäi ohut sävyttämätön, vaalea reunus.
maski = (Image.fromarray((taivas * alue * 255).astype("uint8"))
         .filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(3)))
# 0,4: alkuperäistä taivasta jää 60 %. 0,7 teki pään sivuista liian tummat.
paino = 0.4 * np.asarray(maski, dtype=float)[..., None] / 255
# Kohti heron taivaan sävyä (mitattu herosta 66,78,86 ja jaettu alla olevalla
# himmennyksellä 0,72); pelkkä tummennus teki harmaanpunertavasta taivaasta ruskean.
TAIVAAN_SAVY = np.array([92, 108, 120], dtype=float)
kuva = Image.fromarray((lahto * (1 - paino) + TAIVAAN_SAVY * paino).round().astype("uint8"))
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
