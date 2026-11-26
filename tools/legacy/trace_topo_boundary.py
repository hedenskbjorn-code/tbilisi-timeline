"""Outline the built-up area of Tbilisi from the Soviet General Staff 1:50 000 map (topo500 tiles from nakarte.me).

Built-up blocks are filled orange on that map, so the outline is found by colour (HSV threshold), cleaned with
morphological operations and converted from tile pixels to lon/lat (Web Mercator tile grid, zoom 14, ~7 m/px).
Only the traced OUTLINE is written (data/boundaries/tbilisi_1980_topo.geojson); the map tiles are not republished.

Input : data/raw/nakarte/topo500.mbtiles (not in the repository; see sources.md)
Needs : opencv-python, numpy, Pillow
Quality: approximate. Hillside hatching can leave small false patches; thin roads are removed on purpose; interior
holes are ignored. The survey year of the sheet was not read from the sheet itself (see year_note).
"""
import io
import json
import math
import os
import sqlite3

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MBTILES = os.path.join(ROOT, "data", "raw", "nakarte", "topo500.mbtiles")
OUT = os.path.join(ROOT, "data", "boundaries", "tbilisi_1980_topo.geojson")
Z = 14
BBOX = (44.68, 41.60, 44.98, 41.80)    # lon0, lat0, lon1, lat1
MIN_AREA_PX = 2500                     # ~0.12 km2 at 7.1 m/px
MAIN_AREA_PX = 100000                  # components above this are the continuous city, below: separate settlements


def tile_xy(lon, lat, z):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


def pix_to_lonlat(px, py, x0, y0, z):
    n = 2 ** z * 256.0
    X, Y = x0 * 256 + px, y0 * 256 + py
    lon = X / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * Y / n))))
    return lon, lat


def mosaic():
    con = sqlite3.connect("file:%s?mode=ro" % MBTILES, uri=True)
    cur = con.cursor()
    n = 2 ** Z
    x0, y1 = tile_xy(BBOX[0], BBOX[1], Z)
    x1, y0 = tile_xy(BBOX[2], BBOX[3], Z)
    im = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256), (255, 255, 255))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            r = cur.execute("select tile_data from tiles where zoom_level=? and tile_column=? and tile_row=?",
                            (Z, x, n - 1 - y)).fetchone()          # MBTiles rows are TMS (flipped)
            if r:
                im.paste(Image.open(io.BytesIO(r[0])).convert("RGB"), ((x - x0) * 256, (y - y0) * 256))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), x0, y0


def ellipse(k):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


def main():
    img, x0, y0 = mosaic()
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (4, 160, 90), (15, 255, 235))
    c = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ellipse(15))        # merge buildings and streets inside blocks
    c = cv2.morphologyEx(c, cv2.MORPH_OPEN, ellipse(19))         # drop thin red roads, contour hatching, speckle
    c = cv2.morphologyEx(c, cv2.MORPH_CLOSE, ellipse(25))        # smooth the outline
    n, lab, st, _ = cv2.connectedComponentsWithStats(c)
    keep = np.zeros_like(c)
    for i in range(1, n):
        if st[i, 4] >= MIN_AREA_PX:
            keep[lab == i] = 255
    cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    feats = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        ap = cv2.approxPolyDP(cnt, 2.0, True)[:, 0, :]
        if len(ap) < 4:
            continue
        ring = [list(pix_to_lonlat(float(px), float(py), x0, y0, Z)) for px, py in ap]
        ring = [[round(a, 6), round(b, 6)] for a, b in ring]
        ring.append(ring[0])
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                      "properties": {"plan_id": "tbilisi_1980_topo", "name": "built_up_area",
                                     "kind": "city" if area >= MAIN_AREA_PX else "settlement",
                                     "area_km2": round(area * (7.1 ** 2) / 1e6, 2), "confidence": "approximate"}})
    out = {"type": "FeatureCollection", "features": feats,
           "properties": {"year": 1980,
                          "year_note": "late Soviet period (1970s-1980s); the survey year of the sheet was not read from the sheet",
                          "source": "Soviet General Staff 1:50 000 topographic map (tiles from nakarte.me); only the traced outline is published",
                          "method": "HSV colour threshold of the orange built-up fill + morphology; checked by eye; small false patches possible on hillsides",
                          "partial": False}}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    big = [f for f in feats if f["properties"]["kind"] == "city"]
    print("polygons: %d (city %d, settlements %d); city area %.1f km2" % (
        len(feats), len(big), len(feats) - len(big), sum(f["properties"]["area_km2"] for f in big)))


if __name__ == "__main__":
    main()
