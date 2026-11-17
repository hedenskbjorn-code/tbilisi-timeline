"""Water bodies that changed: the Tbilisi Sea (reservoir) and the three salt lakes it replaced.

Inputs : data/raw/admin/osm_water.json   (OpenStreetMap, ODbL); data/warped/tiflis_1911.webp (georeferenced sheet c.1911)
         data/raw/plans/1954_ams_nk38-8.jpg (U.S. Army Map Service sheet NK 38-8, 1:250 000, public domain)
Outputs: data/boundaries/tbilisi_lakes_1911.geojson   the blue lake fills traced from the 1954 sheet
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


def lakes_1911():
    """Blue lake fills on the georeferenced c.1911 topographic sheet (data/warped/tiflis_1911, 8 control points, LOO 56 m)."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = cv2.cvtColor(np.array(Image.open(os.path.join(ROOT, "data", "warped", "tiflis_1911.webp")).convert("RGB")), cv2.COLOR_RGB2BGR)
    j = json.load(open(os.path.join(ROOT, "data", "warped", "tiflis_1911.json"), encoding="utf-8"))
    (w0, n0), (w1, _), (_, s0) = j["corners"][0], j["corners"][1], j["corners"][3]
    H, W = im.shape[:2]
    my = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    imy = lambda y: math.degrees(2 * math.atan(math.exp(y)) - math.pi / 2)

    def ll(x, y):
        return w0 + x / W * (w1 - w0), imy(my(n0) + y / H * (my(s0) - my(n0)))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (100, 70, 150), (125, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    feats = []
    for c in cnts:
        ap = cv2.approxPolyDP(c, 1.5, True)[:, 0, :]
        if len(ap) < 4:
            continue
        ring = [[round(v, 5) for v in ll(x, y)] for x, y in ap]
        ring.append(ring[0])
        a = area_km2(ring)
        if a < 0.1:
            continue
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                      "properties": {"t": "lake54", "area_km2": round(a, 2)}})
    return feats


def main():
    lk = lakes_1911()
    out = os.path.join(ROOT, "data", "boundaries", "tbilisi_lakes_1911.geojson")
    json.dump({"type": "FeatureCollection", "features": lk,
               "properties": {"source": "blue lake fills on the topographic sheet of Tiflis environs c.1911 (1:42 000), georeferenced with 8 control points",
                              "accuracy_note": "8-point affine, leave-one-out 56 m; lake outline coincides with the OSM reservoir outline at Avlabari"}},
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
