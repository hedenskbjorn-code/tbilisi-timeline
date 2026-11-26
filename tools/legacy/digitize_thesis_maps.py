"""Vectorise the land-use maps of the thesis of N. Kharebava (2024) into outlines of the city for the years 1913, 1924, 1934.
On every map: grey = the boundary of Tbilisi of that year, green = green space, orange = built-up area, yellow = planned built-up area (not used for
the outline), cyan = planned green space. The city outline of a year = grey + green + orange (+ the planned parts that lie inside the grey boundary).
The maps are georeferenced by the white outline of the districts of 2021 (tools/georef_thesis_map.py).
Input : PNG files of the pictures extracted from the PDF of the thesis (arguments: year file [year file ...]).
Output: data/boundaries/khar_<year>.geojson (properties: year, area_km2, fit_px, m_per_px) and a control picture next to the input.
Usage : python -X utf8 tools/digitize_thesis_maps.py 1913 p69_0.png 1924 p70_0.png 1934 p74_0.png
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import georef_thesis_map as gm

ROOT = gm.ROOT
# rectangles (x0, y0, x1, y1) of the enlarged inset maps that lie over the main map: cut out
INSET = {1913: (0, 0, 345, 270), 1924: (680, 0, 1264, 428), 1934: (680, 0, 1258, 428)}


def masks(bgr):
    b, g, r = [bgr[:, :, i].astype(int) for i in range(3)]
    grey = (abs(r - 128) < 14) & (abs(g - 128) < 14) & (abs(b - 128) < 14)
    orange = (r > 220) & (abs(g - 165) < 35) & (b < 90)
    green = (abs(r - 112) < 30) & (abs(g - 173) < 30) & (abs(b - 112) < 30)
    yellow = (r > 230) & (g > 230) & (b < 90)
    cyan = (r < 60) & (g > 220) & (b > 160)
    return grey, orange, green, yellow, cyan


def vectorise(year, path):
    bgr = cv2.imread(path)
    h, w = bgr.shape[:2]
    geo, cost, rings = gm.make_geo(bgr)
    # inside the modern boundary only (this drops the legend, the swatches and the labels outside), and not under the inset
    inside = np.zeros((h, w), np.uint8)
    for r in rings:
        p = np.array([geo.m_to_px(x, y) for x, y in r]).astype(np.int32)
        cv2.fillPoly(inside, [p], 1)
    x0, y0, x1, y1 = INSET[year]
    inside[y0:y1, x0:x1] = 0
    grey, orange, green, yellow, cyan = masks(bgr)
    terr = (grey | orange | green | yellow | cyan) & (inside > 0)
    terr = terr.astype(np.uint8)
    terr = cv2.morphologyEx(terr, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))   # joins the pieces cut by black outlines of houses
    n, lab, stats, _ = cv2.connectedComponentsWithStats(terr)
    keep = np.zeros_like(terr)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 300:                        # about 0.3 km2: the grey edges of the letters of the labels are dropped
            keep[lab == i] = 1
    cs, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)       # outer outlines only: the black outlines of houses leave false holes
    keep = np.zeros_like(keep)
    cv2.drawContours(keep, cs, -1, 1, -1)
    ll = lambda c: [list(gm.to_lonlat(*geo.px_to_m(float(px), float(py)))) for px, py in c.reshape(-1, 2)]
    polys = []
    for c in cs:
        c = cv2.approxPolyDP(c, 1.0, True)
        if len(c) < 4:
            continue
        ring = ll(c); ring.append(ring[0])
        polys.append([ring])
    m2 = (1.0 / geo.s) ** 2
    area = keep.sum() * m2 / 1e6
    feat = {"type": "Feature", "properties": {"year": year, "area_km2": round(float(area), 1),
                                              "fit_px": round(float(cost), 2), "m_per_px": round(1 / geo.s, 1)},
            "geometry": {"type": "MultiPolygon", "coordinates": polys}}
    out = os.path.join(ROOT, "data", "boundaries", "khar_%d.geojson" % year)
    json.dump({"type": "FeatureCollection", "features": [feat]}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    ov = bgr.copy()
    cv2.drawContours(ov, cs, -1, (0, 0, 255), 1)
    cv2.imwrite(path.replace(".png", "_out.png"), ov)
    print(year, feat["properties"], len(polys), "polygons ->", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    for y, p in zip(a[0::2], a[1::2]):
        vectorise(int(y), p)
