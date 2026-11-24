"""Gives a line on the map to the streets of site/data/street_names.json that are marked "nogeom" (the card and the search only) when OpenStreetMap holds the street under the same Georgian name
(2026-11-24; the lead came from the checking of the project index: data/cache/street_points_candidates.json "direct_osm").
Rule (so that a namesake in another district is not drawn as the street of the book): the OSM ways of the project index (data/db/project.sqlite, raw_record, made from data/raw) with name:ka (or name) equal to
the Georgian name of the street today are joined into chains (ends within 60 m); the street is taken only when there is ONE chain; a name with several separate chains (a namesake, a gap in OpenStreetMap, a long avenue)
is listed and left as it was. Footpaths and steps are not taken; the lines are simplified (4 m) and a carriageway that repeats another within 15 m is not drawn again. Writes: site/data/street_geom.json (MultiLineString, the key = the geom key or the English name today) and takes "nogeom" off the entry in street_names.json.
OpenStreetMap data: (c) OpenStreetMap contributors, ODbL. Idempotent. Usage: python -P tools/apply_streets_osm.py [--dry-run]
"""
import collections
import json
import math
import os
import sqlite3
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(R, "site", "data")
SKIP = {"footway", "steps", "path", "cycleway", "bridleway", "corridor", "proposed", "construction"}


def hav(a, b):
    p = math.pi / 180
    h = math.sin((b[1] - a[1]) * p / 2) ** 2 + math.cos(a[1] * p) * math.cos(b[1] * p) * math.sin((b[0] - a[0]) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(h))


def simplify(line, tol_m=4.0):
    """Douglas-Peucker: the points that lie within tol_m of the straight line between their neighbours go (the first screen loads this file: its weight is counted by tests/e2e/perf.test.mjs)"""
    if len(line) < 3:
        return line
    ax, ay = line[0]
    bx, by = line[-1]
    k = math.cos(math.radians(ay))
    best, bi = 0.0, 0
    for i in range(1, len(line) - 1):
        px, py = line[i]
        dx, dy = (bx - ax) * k * 111000, (by - ay) * 111000
        n = math.hypot(dx, dy)
        d = math.hypot((px - ax) * k * 111000, (py - ay) * 111000) if n == 0 else abs(dx * (py - ay) * 111000 - dy * (px - ax) * k * 111000) / n
        if d > best:
            best, bi = d, i
    if best <= tol_m:
        return [line[0], line[-1]]
    return simplify(line[: bi + 1], tol_m)[:-1] + simplify(line[bi:], tol_m)


def _dist_m(pt, line):
    """the distance from a point to a polyline in metres (a flat approximation, enough at this size)"""
    k = math.cos(math.radians(pt[1]))
    best = 1e9
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        dx, dy = (bx - ax) * k, by - ay
        t = 0.0 if dx == 0 and dy == 0 else max(0.0, min(1.0, (((pt[0] - ax) * k) * dx + (pt[1] - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot((pt[0] - ax) * k - t * dx, pt[1] - ay - t * dy) * 111000)
    return best


def drop_parallel(ways, near_m=15, share=0.8):
    """a street drawn twice in OpenStreetMap (two carriageways): a way whose points lie (share) within near_m of the longer ways already kept is not drawn again"""
    length = lambda w: sum(hav(a, b) for a, b in zip(w, w[1:]))      # noqa: E731
    kept = []
    for w in sorted(ways, key=length, reverse=True):
        if kept and sum(1 for pt in w if min(_dist_m(pt, k) for k in kept) <= near_m) >= share * len(w):
            continue
        kept.append(w)
    return kept


def chains(ways, join_m=150):
    n = len(ways)
    par = list(range(n))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    ends = [(w[0], w[-1]) for w in ways]
    for i in range(n):
        for j in range(i + 1, n):
            if any(hav(a, b) <= join_m for a in ends[i] for b in ends[j]):
                par[f(i)] = f(j)
    out = collections.defaultdict(list)
    for i in range(n):
        out[f(i)].append(ways[i])
    return list(out.values())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    sn_p, sg_p = os.path.join(D, "street_names.json"), os.path.join(D, "street_geom.json")
    sn_raw, sg_raw = open(sn_p, "rb").read().decode("utf-8"), open(sg_p, "rb").read().decode("utf-8")
    sn, sg = json.loads(sn_raw), json.loads(sg_raw)
    db = sqlite3.connect("file:%s?mode=ro" % os.path.join(R, "data", "db", "project.sqlite").replace("\\", "/"), uri=True)
    byname = collections.defaultdict(list)
    byname_en = collections.defaultdict(list)
    for tags, geom in db.execute("SELECT tags, geom FROM raw_record WHERE source='osm' AND type='way' AND geom IS NOT NULL AND tags LIKE '%\"highway\"%'"):
        t = json.loads(tags)
        if t.get("highway") in SKIP:
            continue
        pts = [[round(x, 5), round(y, 5)] for x, y in json.loads(geom)]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        if not (44.71 <= cx <= 44.89 and 41.66 <= cy <= 41.82):
            continue
        for k in ("name:ka", "name"):
            if t.get(k):
                byname[t[k].strip()].append(pts)
                break
        if t.get("name:en"):
            byname_en[t["name:en"].strip().lower()].append(pts)
    taken, several, nothing = [], [], []
    for s in sn["streets"]:
        if not s.get("nogeom"):
            continue
        key = s.get("geom") or s["now"]["en"]
        ways = byname.get(s["now"]["ka"].strip()) or byname_en.get(s["now"]["en"].strip().lower())
        if not ways:
            nothing.append(key)
            continue
        ch = chains(ways)
        if len(ch) != 1:
            several.append((key, len(ch)))
            continue
        if key in sg:
            continue
        sg[key] = {"type": "MultiLineString", "coordinates": [simplify(w) for w in drop_parallel(ways)]}
        del s["nogeom"]
        taken.append(key)
    print("taken:", len(taken), "| several separate chains (left as they were):", len(several), "| no way of this name:", len(nothing), "| dry-run:", dry)
    print("some taken:", taken[:6])
    print("some with several chains:", several[:8])
    if taken and not dry:                                              # both files are written compact, as they are (checked: the same text comes back from json.dumps)
        for path, raw, doc in ((sg_p, sg_raw, sg), (sn_p, sn_raw, sn)):
            assert json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":")) == raw, "unexpected layout of " + path
        open(sg_p, "wb").write(json.dumps(sg, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        open(sn_p, "wb").write(json.dumps(sn, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

if __name__ == "__main__":
    main()
