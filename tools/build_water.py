"""Water bodies that changed: the Tbilisi Sea (reservoir) and the three salt lakes it replaced.

Inputs : data/raw/admin/osm_water.json   (OpenStreetMap, ODbL; Overpass export of water polygons)
         data/raw/plans/1954_ams_nk38-8.jpg (U.S. Army Map Service sheet NK 38-8, 1:250 000, public domain)
Outputs: data/boundaries/tbilisi_lakes_1954.geojson   the blue lake fills traced from the 1954 sheet
         site/data/water.json                          reservoir (OSM) + 1954 lakes, for the page

How the lakes are placed: the sheet is georeferenced with the five points used for the 1954 built-up outline; the check is Lisi
Lake (blob at 41.7430, 44.7364, 0.39 km2) against its OpenStreetMap polygon (41.7437, 44.7351, 0.40 km2): a position
difference of about 15 m and the same area. Lakes nearer to the edge of the sheet may be off by more; the page says ~300 m.
The sheet was compiled in 1951 from surveys of the 1920s-40s, so the lakes show the state before the reservoir.
"""
import json
import math
import os

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = 6371000.0
LAT0 = np.radians(41.7)


def assemble(ways):
    segs = [list(w) for w in ways if len(w) >= 2]
    rings = []
    while segs:
        cur = segs.pop(0)
        changed = True
        while changed and cur[0] != cur[-1]:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == cur[-1]:
                    cur += s[1:]
                elif s[-1] == cur[-1]:
                    cur += s[::-1][1:]
                elif s[-1] == cur[0]:
                    cur = s[:-1] + cur
                elif s[0] == cur[0]:
                    cur = s[::-1][:-1] + cur
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        if cur[0] == cur[-1] and len(cur) >= 4:
            rings.append(cur)
    return rings


def area_km2(r):
    a = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:])) / 2
    return abs(a) * 111.32 * math.cos(LAT0) * 111.19


def inside(pt, ring):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def reservoir():
    els = json.load(open(os.path.join(ROOT, "data", "raw", "admin", "osm_water.json"), encoding="utf-8"))
    rel = [e for e in els if e["type"] == "relation" and e["id"] == 19423317][0]
    outer = [[(p["lon"], p["lat"]) for p in m["geometry"]] for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer" and m.get("geometry")]
    rings = [r for r in assemble(outer) if area_km2(r) > 0.05]
    return [[[round(x, 5), round(y, 5)] for x, y in r] for r in rings]


def lakes_1954():
    pts = [(2335, 1322, 44.75, 41.75), (1882, 932, 44.5768, 41.8492), (2277, 1016, 44.7235, 41.8385), (2468, 1444, 44.798, 41.7211), (2632, 1568, 44.855, 41.6852)]
    px = np.array([[p[0], p[1]] for p in pts], float)
    w = np.array([[np.radians(p[2]) * R * np.cos(LAT0), np.radians(p[3]) * R] for p in pts])
    M, *_ = np.linalg.lstsq(np.c_[px, np.ones(5)], w, rcond=None)

    def ll(x, y):
        e, n = np.array([x, y, 1.0]) @ M
        return float(np.degrees(e / (R * np.cos(LAT0)))), float(np.degrees(n / R))
    im = cv2.imread(os.path.join(ROOT, "data", "raw", "plans", "1954_ams_nk38-8.jpg"))
    x0, y0, x1, y1 = 2450, 1230, 2800, 1480                      # window around the three salt lakes (Kukia, Ilguniani, Avlabari)
    hsv = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (95, 60, 120), (125, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    feats = []
    for c in cnts:
        if cv2.contourArea(c) < 30:
            continue
        (_, _), (rw, rh), _ = cv2.minAreaRect(c)
        if min(rw, rh) < 1 or max(rw, rh) / max(min(rw, rh), 1e-6) > 5:       # thin lines (the blue UTM grid), not lakes
            continue
        ap = cv2.approxPolyDP(c, 0.8, True)[:, 0, :]
        if len(ap) < 4:
            continue
        ring = [[round(v, 5) for v in ll(x0 + x, y0 + y)] for x, y in ap]
        ring.append(ring[0])
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                      "properties": {"t": "lake54", "area_km2": round(area_km2(ring), 2)}})
    return feats


def main():
    lk = lakes_1954()
    out = os.path.join(ROOT, "data", "boundaries", "tbilisi_lakes_1954.geojson")
    json.dump({"type": "FeatureCollection", "features": lk,
               "properties": {"source": "blue lake fills on U.S. Army Map Service sheet NK 38-8 (1:250 000, ed. 1954, compiled 1951)",
                              "accuracy_note": "five-point georeferencing; Lisi Lake check ~15 m, edge of sheet up to ~300 m"}},
              open(out, "w", encoding="utf-8"), ensure_ascii=False)
    res = reservoir()
    pts_res = np.array([p for r in res for p in r])

    def near_reservoir(f, km=1.5):
        c = np.mean(np.array(f["geometry"]["coordinates"][0]), axis=0)
        d = np.hypot((pts_res[:, 0] - c[0]) * 111.32 * math.cos(LAT0), (pts_res[:, 1] - c[1]) * 111.19)
        return d.min() <= km
    lk = [f for f in lk if near_reservoir(f)]           # keep the lakes at the reservoir (Kukia, Ilguniani, Avlabari)
    feats = [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [r]}, "properties": {"t": "res"}} for r in res] + lk
    # which 1954 lakes lie inside the reservoir (the claim "built on the site of salt lakes")
    for f in lk:
        c = np.mean(np.array(f["geometry"]["coordinates"][0]), axis=0)
        f["properties"]["in_res"] = any(inside((c[0], c[1]), r) for r in res)
    json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(ROOT, "site", "data", "water.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("reservoir rings:", len(res), "area km2: %.1f" % sum(area_km2(r) for r in res), "| 1954 lakes:",
          [(f["properties"]["area_km2"], f["properties"]["in_res"]) for f in lk])


if __name__ == "__main__":
    main()
