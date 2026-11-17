"""Download the 10 district boundaries of Tbilisi from OpenStreetMap (Overpass API) with their names.

Licence: (c) OpenStreetMap contributors, ODbL 1.0. The file written here is a derived database and must carry the same
attribution and ODbL terms wherever it is republished (see README and the "About" section of the site).

Output: data/boundaries/tbilisi_districts_osm.geojson - a polygon (outer rings only, holes ignored) per district with
name_ka / name_en / name_ru, osm relation id and a label point (area centroid of the largest ring).
"""
import json
import math
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project)"
IDS = [11300436, 11300438, 11300445, 11300446, 11300449, 13438808, 13438809, 13438810, 13438811, 13438812]


def overpass(ql):
    data = urllib.parse.urlencode({"data": ql}).encode()
    for k in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": UA}), timeout=180))
        except Exception as e:
            print("retry:", e, flush=True)
            time.sleep(15 * (k + 1))
    raise SystemExit("overpass failed")


def assemble(ways):
    """Join way geometries (lists of (lon, lat)) into closed rings by matching end points."""
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


def signed_area(r):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:])) / 2


def centroid(r):
    a = signed_area(r)
    cx = sum((x1 + x2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in zip(r, r[1:])) / (6 * a)
    cy = sum((y1 + y2) * (x1 * y2 - x2 * y1) for (x1, y1), (x2, y2) in zip(r, r[1:])) / (6 * a)
    return cx, cy


def inside(pt, ring):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def main():
    r = overpass("[out:json][timeout:120];relation(id:%s);out geom;" % ",".join(map(str, IDS)))
    feats = []
    for e in r["elements"]:
        outer = [[(p["lon"], p["lat"]) for p in m["geometry"]] for m in e["members"] if m["type"] == "way" and m.get("role") == "outer" and m.get("geometry")]
        rings = assemble(outer)
        if not rings:
            print("no ring for", e["id"])
            continue
        big = max(rings, key=lambda q: abs(signed_area(q)))
        c = centroid(big)
        if not inside(c, big):                       # concave district: fall back to the ring's bbox centre
            xs, ys = [p[0] for p in big], [p[1] for p in big]
            c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        t = e["tags"]
        feats.append({"type": "Feature",
                      "geometry": {"type": "MultiPolygon", "coordinates": [[[[round(x, 5), round(y, 5)] for x, y in q]] for q in rings]},
                      "properties": {"osm_relation": e["id"], "name_ka": t.get("name:ka") or t.get("name"), "name_en": t.get("name:en"),
                                     "name_ru": t.get("name:ru"), "label": [round(c[0], 5), round(c[1], 5)]}})
    out = {"type": "FeatureCollection", "features": feats,
           "properties": {"source": "OpenStreetMap contributors, ODbL 1.0", "fetched": time.strftime("%Y-%m-%d")}}
    path = os.path.join(ROOT, "data", "boundaries", "tbilisi_districts_osm.geojson")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print("districts:", len(feats), [f["properties"]["name_en"] for f in feats], "bytes", os.path.getsize(path))


if __name__ == "__main__":
    main()
