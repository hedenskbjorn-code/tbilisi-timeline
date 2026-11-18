"""Snap the hand-read tram lines of the 1913 plan (for_gemini/outbox/tram1913.json: points in the pixel coordinates of the warped plan, read by Gemini from
gridded tiles) to the thin red line printed on the plan: between two consecutive points the cheapest path over the image is taken, where thin red pixels
(white top-hat of the redness channel, thick red boundaries removed) cost 1 and everything else 6, with a penalty for leaving a corridor of 30 px
around the straight segment. Output: data/boundaries/tram_1913_snapped.json (pixel and lon/lat), a preview PNG and per-line statistics.
Usage: python -P tools/snap_tram_1913.py
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

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MARGIN = 40


def grid_graph(cost):
    h, w = cost.shape
    idx = np.arange(h * w).reshape(h, w)
    rows, cols, wts = [], [], []
    flat = cost.reshape(-1)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        if dx >= 0:
            a = idx[: h - dy, : w - dx]
            b = idx[dy:, dx:]
        else:
            a = idx[: h - dy, -dx:]
            b = idx[dy:, : w + dx]
        rows.append(a.reshape(-1))
        cols.append(b.reshape(-1))
        wts.append((flat[a.reshape(-1)] + flat[b.reshape(-1)]) / 2 * math.hypot(dx, dy))
    return coo_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(h * w, h * w)).tocsr()


def main():
    g = json.load(open(os.path.join(ROOT, "for_gemini", "outbox", "tram1913.json"), encoding="utf-8"))
    rgb = np.array(Image.open(os.path.join(ROOT, "data", "warped", "tbilisi_1913.webp")).convert("RGB"))
    H, W = rgb.shape[:2]
    r = np.clip(rgb[..., 0].astype(np.int16) - (rgb[..., 1].astype(np.int16) + rgb[..., 2].astype(np.int16)) // 2, 0, 255).astype(np.uint8)
    th = cv2.morphologyEx(r, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    thick = cv2.dilate(cv2.morphologyEx((r >= 95).astype(np.uint8), cv2.MORPH_OPEN, np.ones((4, 4), np.uint8)), np.ones((7, 7), np.uint8))
    thin = cv2.dilate(((th >= 10) & (thick == 0)).astype(np.uint8), np.ones((2, 2), np.uint8))
    out = []
    for t in g["tiles"]:
        for l in t.get("lines", []):
            pts = [tuple(p) for p in l["points"]]
            path_all = []
            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
                xa, xb = max(0, min(x0, x1) - MARGIN), min(W, max(x0, x1) + MARGIN + 1)
                ya, yb = max(0, min(y0, y1) - MARGIN), min(H, max(y0, y1) + MARGIN + 1)
                sub = np.where(thin[ya:yb, xa:xb] > 0, 1.0, 6.0).astype(np.float32)
                h, w = sub.shape
                yy, xx = np.mgrid[ya:yb, xa:xb]
                d = np.abs((x1 - x0) * (y0 - yy) - (x0 - xx) * (y1 - y0)) / max(1.0, math.hypot(x1 - x0, y1 - y0))
                sub = sub + np.where(d > 30, (d - 30) * 0.5, 0).astype(np.float32)
                G = grid_graph(sub)
                s = min(max(y0 - ya, 0), h - 1) * w + min(max(x0 - xa, 0), w - 1)
                e = min(max(y1 - ya, 0), h - 1) * w + min(max(x1 - xa, 0), w - 1)
                dist, pred = dijkstra(G, indices=s, return_predecessors=True)
                seg = []
                c = e
                while c != s and c >= 0:
                    seg.append((c % w + xa, c // w + ya))
                    c = pred[c]
                seg.append((x0, y0))
                path_all += seg[::-1]
            ratio = float(np.mean([thin[y, x] for x, y in path_all])) if path_all else 0
            ap = cv2.approxPolyDP(np.array(path_all, np.int32).reshape(-1, 1, 2), 2.0, False).reshape(-1, 2).tolist()
            out.append({"id": l["id"], "tile": t["tile"], "streets": l.get("streets_on_plan"), "ratio": round(ratio, 2), "path": ap, "orig": pts, "stops": l.get("stops", [])})
            print(l["id"], len(pts), "->", len(ap), "on thin red:", round(ratio, 2), flush=True)
    json.dump(out, open(os.path.join(ROOT, "data", "boundaries", "tram_1913_snapped.json"), "w"), separators=(",", ":"))
    arr = rgb.copy()
    for o in out:
        col = (0, 200, 0) if o["ratio"] >= 0.6 else (255, 140, 0)
        cv2.polylines(arr, [np.array(o["path"], np.int32).reshape(-1, 1, 2)], False, col, 3)
        cv2.polylines(arr, [np.array(o["orig"], np.int32).reshape(-1, 1, 2)], False, (200, 0, 200), 1)
    Image.fromarray(arr).save(os.path.join(ROOT, "data", "cache", "tram1913_snapped.png"))


if __name__ == "__main__":
    main()
