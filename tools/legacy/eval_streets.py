"""Measure the automatic street trace against the present-day OSM road network (data/raw/osm_roads/roads_center.json).

precision: share of traced length lying within D metres of a present-day road (streets that no longer exist, text and other noise lower it);
recall:    share of present-day road length (roads of the classes that existed in 1913: not service/footway/path) within D metres of the trace
           (roads built after the plan lower it, so it is a lower bound).
Usage: python -P tools/eval_streets.py streets_tbilisi_1913_auto.geojson [lon0 lat0 lon1 lat1]
"""
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
K = 111320 * math.cos(math.radians(41.7))


def dens(coords, step=3.0):
    out = []
    for a, b in zip(coords, coords[1:]):
        x0, y0, x1, y1 = a[0] * K, a[1] * 111190, b[0] * K, b[1] * 111190
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) // step))
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append((coords[-1][0] * K, coords[-1][1] * 111190))
    return out


def main():
    trace = json.load(open(os.path.join(ROOT, "data", "boundaries", sys.argv[1]), encoding="utf-8"))["features"]
    box = [float(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else [44.7715, 41.667, 44.8634, 41.7374]
    inbox = lambda p: box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
    T = []
    for f in trace:
        T += [p for p in dens(f["geometry"]["coordinates"]) if inbox((p[0] / K, p[1] / 111190))]
    roads = json.load(open(os.path.join(ROOT, "data", "raw", "osm_roads", "roads_center.json"), encoding="utf-8"))["elements"]
    ALL, OLD = [], []
    for w in roads:
        pts = [[g["lon"], g["lat"]] for g in w["geometry"]]
        d = [p for p in dens(pts) if inbox((p[0] / K, p[1] / 111190))]
        ALL += d
        if w["tags"].get("highway") in ("primary", "secondary", "tertiary", "trunk", "unclassified", "residential", "living_street", "pedestrian", "steps", "motorway"):
            OLD += d
    # recall only inside the city outline of the plan (+ margin 40 m): the rest of the modern road network did not exist or is outside the plan
    import cv2
    ob = os.path.join(ROOT, "data", "boundaries", "tbilisi_1913.geojson")
    cell = 5.0
    gx0, gy0 = box[0] * K, box[1] * 111190
    msk = np.zeros((int((box[3] - box[1]) * 111190 / cell) + 2, int((box[2] - box[0]) * K / cell) + 2), np.uint8)
    for f in json.load(open(ob, encoding="utf-8"))["features"]:
        g = f["geometry"]
        rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        for r in rings:
            cv2.fillPoly(msk, [np.array([[(x * K - gx0) / cell, (y * 111190 - gy0) / cell] for x, y in r], np.int32)], 1)
    msk = cv2.dilate(msk, np.ones((17, 17), np.uint8))
    OLD = np.array(OLD)
    ix, iy = ((OLD[:, 0] - gx0) / cell).astype(int), ((OLD[:, 1] - gy0) / cell).astype(int)
    OLD_IN = OLD[msk[np.clip(iy, 0, msk.shape[0] - 1), np.clip(ix, 0, msk.shape[1] - 1)] > 0]
    T, ALL = np.array(T), np.array(ALL)
    print("present-day street points inside the 1913 outline:", len(OLD_IN), "of", len(OLD))
    OLD = OLD_IN
    tt, ta, to = cKDTree(T), cKDTree(ALL), cKDTree(OLD)
    print("trace points (3 m step):", len(T), " OSM road points:", len(ALL))
    for D in (10, 15, 25):
        pr = float(np.mean(ta.query(T)[0] <= D))
        rc = float(np.mean(tt.query(OLD)[0] <= D))
        print("within %2d m: precision %.0f%%   recall (roads of street classes) %.0f%%" % (D, pr * 100, rc * 100))


if __name__ == "__main__":
    main()
