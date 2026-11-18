"""Tram lines of the 1913 plan of Tiflis (legend: 'линия трамвая' = a thin red line, 'остановки' = small red circles).
The warped plan (data/warped/tbilisi_1913.webp, the same image as on the site) is used, so the lines are as exact as the plan fit (about 45 m).

Method (semi-automatic, checked by eye on overlays):
1. redness = R - (G+B)/2; a white top-hat keeps thin red features; thick red (police-district boundaries) is removed by an opening;
2. the stop circles (a small red ring, radius about 4 px) are found by template matching;
3. the thin red pixels are thinned to a skeleton; every stop is linked to the neighbouring stops along the skeleton (path length <= 1.6 x straight
   distance, at most MAXD px); the union of these paths is the network;
4. the paths are simplified and converted to lon/lat with the corners of data/warped/tbilisi_1913.json (Web Mercator rows).
Manual corrections: EXCLUDE (boxes in pixels where false links, e.g. along the railway, are cut) and EXTRA (waypoint chains added by hand,
snapped to the thin red skeleton).
Output: data/boundaries/tram_1913.geojson (committed copy: site/data/tram_1913.json) and a preview PNG in data/cache.
Usage: python -P tools/trace_tram_1913.py
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, os.path.dirname(__file__))
import trace_streets_auto as T  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAXD = 360
TH = 11
STOP_THR = 0.60
EXCLUDE = []            # [x0, y0, x1, y1] boxes: links with a point inside are dropped
EXTRA = []              # [[x, y], [x, y], ...] hand-placed waypoint chains


def load():
    rgb = np.array(Image.open(os.path.join(ROOT, "data", "warped", "tbilisi_1913.webp")).convert("RGB"))
    r = np.clip(rgb[..., 0].astype(np.int16) - (rgb[..., 1].astype(np.int16) + rgb[..., 2].astype(np.int16)) // 2, 0, 255).astype(np.uint8)
    th = cv2.morphologyEx(r, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    return rgb, r, th


def find_stops(th):
    R = 4
    t = np.zeros((2 * R + 5, 2 * R + 5), np.float32)
    cv2.circle(t, (R + 2, R + 2), R, 1.0, 1)
    t = cv2.GaussianBlur(t, (3, 3), 0)
    res = cv2.matchTemplate(th.astype(np.float32), t, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.nonzero(res > STOP_THR)
    order = np.argsort(-res[ys, xs])
    used = np.zeros(th.shape, bool)
    pts = []
    for i in order:
        x, y = int(xs[i]) + R + 2, int(ys[i]) + R + 2
        if used[max(0, y - 8):y + 9, max(0, x - 8):x + 9].any():
            continue
        used[y, x] = True
        pts.append((x, y))
    return pts


def main():
    rgb, r, th = load()
    H, W = th.shape
    stops = find_stops(th)
    print("stops", len(stops))
    thick = cv2.morphologyEx((r >= 95).astype(np.uint8), cv2.MORPH_OPEN, np.ones((4, 4), np.uint8))
    thick = cv2.dilate(thick, np.ones((7, 7), np.uint8))
    thin = ((th >= TH) & (thick == 0)).astype(np.uint8)
    thin = cv2.morphologyEx(thin, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    thin = cv2.morphologyEx(thin, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    sk = T.thin(thin.astype(bool))
    ys, xs = np.nonzero(sk)
    idx = -np.ones(sk.shape, np.int32)
    idx[ys, xs] = np.arange(len(ys))
    rows, cols, w = [], [], []
    for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
        x2, y2 = xs + dx, ys + dy
        ok = (x2 >= 0) & (x2 < W) & (y2 >= 0) & (y2 < H)
        a = np.nonzero(ok)[0]
        b = idx[y2[a], x2[a]]
        m = b >= 0
        rows += [a[m]]
        cols += [b[m]]
        w += [np.full(int(m.sum()), math.hypot(dx, dy))]
    rows, cols, w = np.concatenate(rows), np.concatenate(cols), np.concatenate(w)
    n = len(ys)
    G = coo_matrix((np.concatenate([w, w]), (np.concatenate([rows, cols]), np.concatenate([cols, rows]))), shape=(n, n)).tocsr()
    print("skeleton px", n)
    # snap every stop to the nearest skeleton pixel (within 7 px)
    tree_pts = np.stack([xs, ys], 1)
    snapped = []
    from scipy.spatial import cKDTree
    kd = cKDTree(tree_pts)
    for (x, y) in stops:
        d, i = kd.query([x, y])
        if d <= 7:
            snapped.append((i, x, y))
    print("stops on skeleton", len(snapped))
    sid = {i: k for k, (i, _, _) in enumerate(snapped)}
    segs = []
    seen = set()
    for k, (i, x, y) in enumerate(snapped):
        dist, pred = dijkstra(G, indices=i, limit=MAXD, return_predecessors=True)
        for k2, (j, x2, y2) in enumerate(snapped):
            if k2 <= k or not np.isfinite(dist[j]):
                continue
            eu = math.hypot(x - x2, y - y2)
            if dist[j] > 1.6 * eu + 20:
                continue
            path = []
            c = j
            while c != i and c >= 0:
                path.append((int(xs[c]), int(ys[c])))
                c = pred[c]
            path.append((int(xs[i]), int(ys[i])))
            segs.append(path[::-1])
    print("links", len(segs))
    boxes = EXCLUDE
    keep = []
    for p in segs:
        if any(any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for x, y in p[::6]) for b in boxes):
            continue
        keep.append(p)
    meta = json.load(open(os.path.join(ROOT, "data", "warped", "tbilisi_1913.json"), encoding="utf-8"))
    (lon0, lat0), (lon1, _), (_, lat1) = meta["corners"][0], meta["corners"][1], meta["corners"][2]
    sizeW, sizeH = meta["size"]

    def my(lat):
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    def ll(x, y):
        lon = lon0 + (lon1 - lon0) * x / sizeW
        lat = math.degrees(2 * math.atan(math.exp(my(lat0) + (my(lat1) - my(lat0)) * y / sizeH)) - math.pi / 2)
        return [round(lon, 5), round(lat, 5)]

    feats = []
    for p in keep:
        ap = cv2.approxPolyDP(np.array(p, np.int32).reshape(-1, 1, 2), 2.5, False).reshape(-1, 2)
        if len(ap) >= 2:
            feats.append({"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": [ll(int(x), int(y)) for x, y in ap]}})
    out = {"type": "FeatureCollection", "features": feats}
    os.makedirs(os.path.join(ROOT, "data", "boundaries"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "data", "boundaries", "tram_1913.geojson"), "w", encoding="utf-8"), separators=(",", ":"))
    prev = Image.fromarray(rgb).copy()
    arr = np.array(prev)
    for p in keep:
        for x, y in p:
            arr[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = (0, 200, 0)
    for (_, x, y) in snapped:
        cv2.circle(arr, (x, y), 7, (0, 90, 255), 2)
    Image.fromarray(arr).save(os.path.join(ROOT, "data", "cache", "tram1913_preview.png"))
    print("features", len(feats))


if __name__ == "__main__":
    main()
