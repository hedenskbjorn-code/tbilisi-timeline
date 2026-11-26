"""Experiment: automatic tracing of the STREET NETWORK from a georeferenced city plan (the 1913 plan: blocks are pink or black, streets are
the pale strips between them).

Steps: (1) colour classes -> "not street" (pink blocks, black buildings, green parks, blue water, red police-district lines);
(2) the remaining pale pixels are cut into wide places (squares, gardens, open land: removed by a morphological opening) and narrow
strips (streets); (3) the narrow strips are thinned to a centre line (Zhang-Suen thinning, numpy); (4) the pixel skeleton is traced into
polylines, simplified and converted to lon/lat with the corners of data/warped/<plan>.json (Web Mercator rows).
Quality is measured against the present-day OSM road network (tools/eval_streets.py), not by eye alone.

Usage: python -P tools/trace_streets_auto.py [plan_id] [x0 y0 x1 y1]     (pixel window in the warped image; default: the whole city area)
Output: data/boundaries/streets_<plan>_auto.geojson
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WMAX = 8                                       # half-width (px) above which a pale area is not a street (1913 plan: about 1.5 m per px)


def classes(rgb):
    """Pale street pixels: low saturation (blocks are pink, S >= ~95; streets are cream, S ~ 45-60), light, yellowish hue.
    Dark outlines, green parks, blue water and red lines are excluded by the value / hue tests."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int), hsv[:, :, 2].astype(int)
    return (s < 78) & (v >= 170) & (h >= 13) & (h <= 30)


def thin(img):
    """Zhang-Suen thinning of a boolean image (vectorised)."""
    im = np.pad(img.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p = [im[0:-2, 1:-1], im[0:-2, 2:], im[1:-1, 2:], im[2:, 2:], im[2:, 1:-1], im[2:, 0:-2], im[1:-1, 0:-2], im[0:-2, 0:-2]]   # P2..P9
            c = im[1:-1, 1:-1]
            b = sum(q.astype(np.int16) for q in p)
            a = sum(((p[i] == 0) & (p[(i + 1) % 8] == 1)).astype(np.int16) for i in range(8))
            if step == 0:
                cond = (p[0] * p[2] * p[4] == 0) & (p[2] * p[4] * p[6] == 0)
            else:
                cond = (p[0] * p[2] * p[6] == 0) & (p[0] * p[4] * p[6] == 0)
            rm = (c == 1) & (b >= 2) & (b <= 6) & (a == 1) & cond
            if rm.any():
                im[1:-1, 1:-1][rm] = 0
                changed = True
        if not changed:
            break
    return im[1:-1, 1:-1].astype(bool)


def trace(sk):
    """Skeleton pixels -> polylines (lists of (x, y)); junctions split the lines."""
    ys, xs = np.nonzero(sk)
    pts = set(zip(xs.tolist(), ys.tolist()))
    nb = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    deg = {p: sum(((p[0] + dx, p[1] + dy) in pts) for dx, dy in nb) for p in pts}
    seen_edges = set()
    lines = []
    nodes = [p for p, d in deg.items() if d != 2]
    for start in nodes:
        for dx, dy in nb:
            q = (start[0] + dx, start[1] + dy)
            if q not in pts or (start, q) in seen_edges:
                continue
            path = [start, q]
            seen_edges.add((start, q))
            prev, cur = start, q
            while deg[cur] == 2:
                nxt = None
                for ex, ey in nb:
                    r = (cur[0] + ex, cur[1] + ey)
                    if r in pts and r != prev and r not in path[-3:]:
                        nxt = r
                        break
                if nxt is None:
                    break
                seen_edges.add((cur, nxt))
                path.append(nxt)
                prev, cur = cur, nxt
            seen_edges.add((path[-1], path[-2]))
            lines.append(path)
    # closed loops without junctions are skipped (rare)
    return lines


def main():
    pid = sys.argv[1] if len(sys.argv) > 1 else "tbilisi_1913"
    meta = json.load(open(os.path.join(ROOT, "data", "warped", pid + ".json"), encoding="utf-8"))
    im = np.array(Image.open(os.path.join(ROOT, "data", "warped", pid + ".webp")).convert("RGB"))
    H, W = im.shape[:2]
    x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6]) if len(sys.argv) >= 6 else (0, 0, W, H)
    rgb = im[y0:y1, x0:x1]
    pale = classes(rgb)
    pale = cv2.morphologyEx(pale.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * WMAX + 1, 2 * WMAX + 1))
    wide = cv2.dilate(cv2.morphologyEx(pale, cv2.MORPH_OPEN, k), np.ones((3, 3), np.uint8))
    narrow = (pale > 0) & (wide == 0)
    narrow = cv2.morphologyEx(narrow.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0
    n, lab, stats, _ = cv2.connectedComponentsWithStats(narrow.astype(np.uint8), connectivity=8)
    keep = np.isin(lab, [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= 60])
    # only inside the city outline of the plan (plus a margin): outside it the plan shows hills, text and open land
    ob = os.path.join(ROOT, "data", "boundaries", pid + ".geojson")
    if os.path.exists(ob):
        (lng0_, lat0_), (lng1_, _), (_, lat1_) = meta["corners"][0], meta["corners"][1], meta["corners"][3]
        my_ = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
        area = np.zeros(keep.shape, np.uint8)
        for f in json.load(open(ob, encoding="utf-8"))["features"]:
            g = f["geometry"]
            rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
            for r in rings:
                pxy = np.array([[(x - lng0_) / (lng1_ - lng0_) * W - x0, (my_(y) - my_(lat0_)) / (my_(lat1_) - my_(lat0_)) * H - y0] for x, y in r], np.int32)
                cv2.fillPoly(area, [pxy], 1)
        area = cv2.dilate(area, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (81, 81)))
        keep &= area > 0
    sk = thin(keep)
    for _ in range(4):                                         # prune short spurs (4 px)
        ys_, xs_ = np.nonzero(sk)
        pad = np.pad(sk, 1).astype(np.uint8)
        nbs = sum(np.roll(np.roll(pad, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - pad
        ends = (pad == 1) & (nbs <= 1)
        sk = sk & ~ends[1:-1, 1:-1]
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(sk.astype(np.uint8), connectivity=8)
    sk = np.isin(lab2, [i for i in range(1, n2) if st2[i, cv2.CC_STAT_AREA] >= 30])
    lines = trace(sk)
    (lng0, lat0), (lng1, _), (_, lat1) = meta["corners"][0], meta["corners"][1], meta["corners"][3]
    R = 6378137.0
    my = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    imy = lambda v: math.degrees(2 * math.atan(math.exp(v)) - math.pi / 2)

    def ll(x, y):
        X, Y = x + x0, y + y0
        return [round(lng0 + X / W * (lng1 - lng0), 6), round(imy(my(lat0) + Y / H * (my(lat1) - my(lat0))), 6)]
    feats = []
    total = 0.0
    for p in lines:
        if len(p) < 3:
            continue
        ap = cv2.approxPolyDP(np.array(p, np.int32).reshape(-1, 1, 2), 1.6, False)[:, 0, :]
        if len(ap) < 2:
            continue
        feats.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": [ll(x, y) for x, y in ap]}, "properties": {}})
        total += float(np.sum(np.hypot(*np.diff(ap, axis=0).T)))
    out = os.path.join(ROOT, "data", "boundaries", "streets_%s_auto.geojson" % pid)
    json.dump({"type": "FeatureCollection", "features": feats, "properties": {"plan": pid, "method": "colour classes + opening + Zhang-Suen thinning"}}, open(out, "w"), separators=(",", ":"))
    m_per_px = (lng1 - lng0) * 111320 * math.cos(math.radians(41.7)) / W
    print("polylines:", len(feats), "total length ~ %.1f km" % (total * m_per_px / 1000), "px size %.2f m" % m_per_px, "->", out)



if __name__ == "__main__":
    main()
