"""Cut the Tbilisi administrative boundary out of the OCHA COD-AB Georgia dataset (HDX, CC BY-IGO).

Dataset: "Georgia - Subnational Administrative Boundaries" (COD-AB v01, valid 2019-10-18, reviewed 2024-01-31),
source: National Statistics Office of Georgia; https://data.humdata.org/dataset/cod-ab-geo
Input : data/raw/admin/hdx/geo_admin_boundaries.geojson.zip (admin level 1, feature "Tbilisi", area_sqkm 502.5)
Output: data/boundaries/tbilisi_admin_2019.geojson  (simplified to about 30 m)
Run in isolated mode (downloaded data):  python -I tools/extract_admin.py
"""
import json
import math
import os
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EPS = 3.0     # in units of 1e-4 degrees (~30 m)


def rdp(pts, eps):
    n = len(pts)
    if n < 5:
        return pts
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for k in range(i + 1, j):
            x, y = pts[k]
            d = abs(dy * (x - x1) - dx * (y - y1)) / norm if norm else math.hypot(x - x1, y - y1)
            if d > best:
                best, bi = d, k
        if best > eps:
            keep[bi] = True
            stack += [(i, bi), (bi, j)]
    return [p for p, k in zip(pts, keep) if k]


def simplify(ring):
    pts = [(x * 1e4, y * 1e4) for x, y in ring[:-1]]
    i0 = min(range(len(pts)), key=lambda k: pts[k][0])
    i1 = max(range(len(pts)), key=lambda k: pts[k][0])
    if i0 > i1:
        i0, i1 = i1, i0
    out = rdp(pts[i0:i1 + 1], EPS)[:-1] + rdp(pts[i1:] + pts[:i0 + 1], EPS)[:-1]
    out = [[round(x / 1e4, 5), round(y / 1e4, 5)] for x, y in out]
    return out + [out[0]]


def main():
    z = zipfile.ZipFile(os.path.join(ROOT, "data", "raw", "admin", "hdx", "geo_admin_boundaries.geojson.zip"))
    d = json.load(z.open("geo_admin1.geojson"))
    f = [x for x in d["features"] if x["properties"].get("adm1_name") == "Tbilisi"][0]
    g = f["geometry"]
    rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
    feats = [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [simplify(r)]},
              "properties": {"name": "Tbilisi", "level": "admin1", "valid_on": f["properties"].get("valid_on"),
                             "area_sqkm": round(f["properties"].get("area_sqkm") or 0, 1)}} for r in rings]
    out = {"type": "FeatureCollection", "features": feats,
           "properties": {"source": "OCHA COD-AB Georgia v01 (HDX), source: National Statistics Office of Georgia; CC BY-IGO",
                          "valid_on": f["properties"].get("valid_on")}}
    path = os.path.join(ROOT, "data", "boundaries", "tbilisi_admin_2019.geojson")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print("rings:", len(feats), "vertices:", sum(len(x["geometry"]["coordinates"][0]) for x in feats), "bytes:", os.path.getsize(path))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
