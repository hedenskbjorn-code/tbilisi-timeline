"""Building density of Tbilisi today: the share of ground covered by building footprints in ~100 x 100 m cells.

Data: OpenStreetMap buildings (Overpass API, (c) OpenStreetMap contributors, ODbL), downloaded in 3 x 3 tiles to
data/raw/osm_buildings/ (not committed). The OSM data have no construction years, so this is a picture of the present state only.
Output: site/data/density.png (RGBA overlay, Web Mercator rows) and site/data/density.json (corner coordinates, cell size, stats).
Run: python -P tools/build_density.py
"""
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "raw", "osm_buildings")
OUT = os.path.join(ROOT, "site", "data")
S, W, N, E = 41.60, 44.66, 41.86, 45.02
R = 6378137.0
CELL = 134.0                                    # Web Mercator metres, about 100 m on the ground at this latitude
K2 = 1.0 / (1.0 / math.cos(math.radians(41.73))) ** 2        # mercator area -> ground area factor


def merc(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def fetch(i, j, s, w, n, e):
    path = os.path.join(RAW, "tile_%d_%d.json" % (i, j))
    if os.path.exists(path):
        return path
    q = '[out:json][timeout:180];way["building"](%.5f,%.5f,%.5f,%.5f);out skel geom qt;' % (s, w, n, e)
    for k in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(),
                                          headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=300).read()
            json.loads(data)                                  # must be valid JSON
            open(path, "wb").write(data)
            print("tile", i, j, "%.1f MB" % (len(data) / 1e6), flush=True)
            return path
        except (urllib.error.URLError, ValueError, TimeoutError) as ex:
            print("tile", i, j, "retry", k, ex, flush=True)
            time.sleep(30 * (k + 1))
    sys.exit("giving up on tile %d,%d" % (i, j))


def main():
    os.makedirs(RAW, exist_ok=True)
    lons = np.linspace(W, E, 4)
    lats = np.linspace(S, N, 4)
    x0, y0 = merc(W, S)
    x1, y1 = merc(E, N)
    nx, ny = int(math.ceil((x1 - x0) / CELL)), int(math.ceil((y1 - y0) / CELL))
    area = np.zeros((ny, nx), np.float64)
    seen = set()
    for i in range(3):
        for j in range(3):
            p = fetch(i, j, lats[j], lons[i], lats[j + 1], lons[i + 1])
            for el in json.load(open(p, encoding="utf-8"))["elements"]:
                if el["id"] in seen or "geometry" not in el:
                    continue
                seen.add(el["id"])
                pts = [merc(g["lon"], g["lat"]) for g in el["geometry"]]
                if len(pts) < 4:
                    continue
                a = abs(sum(pts[k][0] * pts[k + 1][1] - pts[k + 1][0] * pts[k][1] for k in range(len(pts) - 1))) / 2
                cx = sum(p_[0] for p_ in pts) / len(pts)
                cy = sum(p_[1] for p_ in pts) / len(pts)
                ci, cj = int((cx - x0) // CELL), int((y1 - cy) // CELL)
                if 0 <= ci < nx and 0 <= cj < ny:
                    area[cj, ci] += a * K2                    # the footprint goes to the cell that holds its centre
    frac = area / (CELL * CELL * K2)
    print("buildings:", len(seen), "cells:", nx, "x", ny, "max share %.2f, median of non-empty %.3f" % (frac.max(), np.median(frac[frac > 0])))
    # blur a little so single plots do not look like confetti, then colour
    sm = cv2.GaussianBlur(np.clip(frac, 0, 1).astype(np.float32), (0, 0), 1.2)
    stops = [(0.02, (255, 255, 178, 0)), (0.06, (254, 217, 118, 150)), (0.12, (253, 141, 60, 190)), (0.20, (240, 59, 32, 215)), (0.32, (189, 0, 38, 235)), (0.45, (110, 0, 40, 245))]
    rgba = np.zeros((ny, nx, 4), np.uint8)
    for c in range(4):
        rgba[:, :, c] = np.interp(sm, [s_[0] for s_ in stops], [s_[1][c] for s_ in stops]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "density.png"), optimize=True)
    lon_of = lambda x: math.degrees(x / R)
    lat_of = lambda y: math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
    meta = {"coordinates": [[lon_of(x0), lat_of(y1)], [lon_of(x0 + nx * CELL), lat_of(y1)], [lon_of(x0 + nx * CELL), lat_of(y1 - ny * CELL)], [lon_of(x0), lat_of(y1 - ny * CELL)]],
            "cell_m": 100, "buildings": len(seen), "source": "OpenStreetMap contributors, ODbL (Overpass API)", "ramp_share": [s_[0] for s_ in stops]}
    json.dump(meta, open(os.path.join(OUT, "density.json"), "w"), indent=1)
    print("png KB", os.path.getsize(os.path.join(OUT, "density.png")) // 1024)


if __name__ == "__main__":
    main()
