"""Cut Tbilisi out of the global GUSV urban-boundary shapefiles (Zenodo 14523232, CC BY 4.0).

Reads the .shp straight from each downloaded zip (data/raw/urban/GUSVyyyy.zip) with a minimal pure-Python reader
(polygon type 5, WGS84 lon/lat), keeps the polygons that touch the Tbilisi frame, drops interior holes, simplifies
to about 15 m and writes data/boundaries/tbilisi_urban_gusv.geojson (one feature per outer ring, property "year").

Citation: "Mapping of 30 m global urban boundaries from 1972 to 2021 based on multi-source geographic information
fusion", Zenodo, doi:10.5281/zenodo.14523232 (CC BY 4.0).
Run with isolated mode (the zips are downloaded data):  python -I tools/extract_urban.py
"""
import glob
import json
import math
import os
import struct
import zipfile


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRAME = (44.60, 41.55, 45.10, 41.90)       # lon0, lat0, lon1, lat1: records whose bbox touches this are read
CENTRE = (44.80, 41.70)                    # the polygon containing this point is "city"
SIMPLIFY = 1.5                             # in units of 1e-4 degrees (~15 m)
MIN_AREA_KM2 = 0.1


def ring_area_km2(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    la = math.radians(41.7)
    return abs(a) / 2 * (111.32 * math.cos(la)) * 111.19


def signed(pts):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))


def inside(pt, ring):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def records(zf, name):
    f = zf.open(name)
    f.read(100)
    while True:
        r = f.read(8)
        if len(r) < 8:
            return
        num, clen = struct.unpack(">ii", r)
        body = f.read(clen * 2)
        st, xmin, ymin, xmax, ymax = struct.unpack("<i4d", body[:36])
        if st == 5 and xmin <= FRAME[2] and xmax >= FRAME[0] and ymin <= FRAME[3] and ymax >= FRAME[1]:
            nparts, npts = struct.unpack("<ii", body[36:44])
            parts = struct.unpack("<%di" % nparts, body[44:44 + 4 * nparts])
            off = 44 + 4 * nparts
            xy = struct.unpack("<%dd" % (2 * npts), body[off:off + 16 * npts])
            pts = [(xy[2 * i], xy[2 * i + 1]) for i in range(npts)]
            rings = [pts[parts[i]:(parts[i + 1] if i + 1 < nparts else npts)] for i in range(nparts)]
            yield num, rings


def rdp(pts, eps):
    """Douglas-Peucker (iterative) on a closed ring given as [(x, y)]; coordinates in 1e-4 degrees."""
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
            stack.append((i, bi))
            stack.append((bi, j))
    return [p for p, k in zip(pts, keep) if k]


def simplify(ring):
    pts = [(x * 1e4, y * 1e4) for x, y in ring[:-1]]
    # split the closed ring at its two farthest-apart extreme points so that RDP has two open chains
    i0 = min(range(len(pts)), key=lambda k: pts[k][0])
    i1 = max(range(len(pts)), key=lambda k: pts[k][0])
    if i0 > i1:
        i0, i1 = i1, i0
    c1 = pts[i0:i1 + 1]
    c2 = pts[i1:] + pts[:i0 + 1]
    out = rdp(c1, SIMPLIFY)[:-1] + rdp(c2, SIMPLIFY)[:-1]
    return [[round(x / 1e4, 6), round(y / 1e4, 6)] for x, y in out]


def main():
    feats = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "raw", "urban", "GUSV*.zip"))):
        year = int(os.path.basename(path)[4:8])
        with zipfile.ZipFile(path) as zf:
            name = [n for n in zf.namelist() if n.lower().endswith(".shp") and "/" not in n and ".." not in n][0]
            n_city = n_other = 0
            for num, rings in records(zf, name):
                for ring in rings:
                    if len(ring) < 4 or signed(ring) >= 0:        # outer rings are clockwise: skip holes
                        continue
                    area = ring_area_km2(ring)
                    if area < MIN_AREA_KM2:
                        continue
                    sr = simplify(ring)
                    if len(sr) < 4:
                        continue
                    kind = "city" if inside(CENTRE, ring) else "other"
                    n_city += kind == "city"
                    n_other += kind == "other"
                    sr.append(sr[0])
                    feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [sr]},
                                  "properties": {"year": year, "kind": kind, "area_km2": round(area, 2), "confidence": "satellite"}})
            print(year, "city rings:", n_city, "other rings:", n_other, flush=True)
    out = {"type": "FeatureCollection", "features": feats,
           "properties": {"source": "GUSV, doi:10.5281/zenodo.14523232 (CC BY 4.0)",
                          "note": "satellite-derived built-up boundaries (Landsat, 30 m), holes dropped, simplified to ~15 m; not an administrative boundary"}}
    json.dump(out, open(os.path.join(ROOT, "data", "boundaries", "tbilisi_urban_gusv.geojson"), "w", encoding="utf-8"), ensure_ascii=False)
    print("features:", len(feats))


if __name__ == "__main__":
    main()
