"""Tram lines of the 1913 plan of Tiflis (legend: 'линия трамвая' = a thin red line, 'остановки' = small red circles).
The warped plan (data/warped/tbilisi_1913.webp, the same image as on the site) is used, so the lines are as exact as the plan fit (about 45 m).

Method (semi-automatic, checked by eye on overlays):
1. redness = R - (G+B)/2; a white top-hat keeps thin red features; thick red (police-district boundaries) is removed by an opening;
2. the stop circles (a small red ring, radius about 4 px) are found by template matching;
3. every stop is linked to the stops within MAXD px by a cheapest path over the image where thin red pixels cost 1 and everything else 9 (so the
   path follows the red line and may cross small gaps); a link is kept if at least MINRATIO of its pixels lie on thin red and its length is
   at most 1.5 x the straight distance;
4. the links are simplified and converted to lon/lat with the corners of data/warped/tbilisi_1913.json (Web Mercator rows).
EXCLUDE (pixel boxes where false links are cut) is for manual corrections.
Output: data/boundaries/tram_1913.geojson (not committed) and a preview PNG in data/cache.   Usage: python -P tools/trace_tram_1913.py
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
from scipy.spatial import cKDTree

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAXD = 260
TH = 9
STOP_THR = 0.60
MINRATIO = 0.72
EXCLUDE = []


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


def grid_graph(cost):
    h, w = cost.shape
    idx = np.arange(h * w).reshape(h, w)
    rows, cols, wts = [], [], []
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a = idx[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
        b = idx[max(0, dy):h - max(0, -dy) or None, max(0, dx):w - max(0, -dx) or None]
        a = a[:b.shape[0], :b.shape[1]]
        ca = cost.reshape(-1)[a.reshape(-1)]
        cb = cost.reshape(-1)[b.reshape(-1)]
        rows.append(a.reshape(-1))
        cols.append(b.reshape(-1))
        wts.append((ca + cb) / 2 * math.hypot(dx, dy))
    r = np.concatenate(rows)
    c = np.concatenate(cols)
    wv = np.concatenate(wts)
    return coo_matrix((wv, (r, c)), shape=(h * w, h * w)).tocsr()


def main():
    rgb, r, th = load()
    H, W = th.shape
    stops = find_stops(th)
    print("stops", len(stops), flush=True)
    thick = cv2.morphologyEx((r >= 95).astype(np.uint8), cv2.MORPH_OPEN, np.ones((4, 4), np.uint8))
    thick = cv2.dilate(thick, np.ones((7, 7), np.uint8))
    thin = ((th >= TH) & (thick == 0)).astype(np.uint8)
    thin = cv2.dilate(thin, np.ones((2, 2), np.uint8))
    cost = np.where(thin > 0, 1.0, 9.0).astype(np.float32)
    kd = cKDTree(np.array(stops, float))
    links = []
    done = set()
    for a, (x, y) in enumerate(stops):
        for b in kd.query_ball_point([x, y], MAXD):
            if b <= a or (a, b) in done:
                continue
            x2, y2 = stops[b]
            eu = math.hypot(x - x2, y - y2)
            if eu < 14:
                continue
            m = 30
            xa, xb = max(0, min(x, x2) - m), min(W, max(x, x2) + m + 1)
            ya, yb = max(0, min(y, y2) - m), min(H, max(y, y2) + m + 1)
            sub = cost[ya:yb, xa:xb]
            h, w = sub.shape
            G = grid_graph(sub)
            s = (y - ya) * w + (x - xa)
            t = (y2 - ya) * w + (x2 - xa)
            dist, pred = dijkstra(G, indices=s, return_predecessors=True)
            if not np.isfinite(dist[t]):
                continue
            path = []
            c = t
            while c != s and c >= 0:
                path.append((c % w + xa, c // w + ya))
                c = pred[c]
            path.append((x, y))
            path = path[::-1]
            ratio = float(np.mean([thin[py, px] for px, py in path]))
            ln = sum(math.hypot(path[i][0] - path[i + 1][0], path[i][1] - path[i + 1][1]) for i in range(len(path) - 1))
            if ratio >= MINRATIO and ln <= 1.5 * eu + 10:
                links.append(path)
            done.add((a, b))
        if a % 100 == 0:
            print(a, len(links), flush=True)
    print("links", len(links))
    keep = [p for p in links if not any(any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for x, y in p[::6]) for b in EXCLUDE)]
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
    os.makedirs(os.path.join(ROOT, "data", "boundaries"), exist_ok=True)
    json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(ROOT, "data", "boundaries", "tram_1913.geojson"), "w", encoding="utf-8"), separators=(",", ":"))
    arr = rgb.copy()
    for p in keep:
        for x, y in p:
            arr[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = (0, 200, 0)
    for (x, y) in stops:
        cv2.circle(arr, (x, y), 7, (0, 90, 255), 1)
    Image.fromarray(arr).save(os.path.join(ROOT, "data", "cache", "tram1913_preview.png"))
    print("features", len(feats))


if __name__ == "__main__":
    main()
