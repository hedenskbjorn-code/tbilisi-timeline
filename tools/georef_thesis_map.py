"""Georeference a land-use map of the thesis of N. Kharebava (2024; the maps 'land use in the modern boundaries of Tbilisi' for 1735, 1800, 1913, 1924, 1934)
by the white outline of the districts of 2021 that is drawn on every map. The maps are north-up; the scale and the shift are found by matching the dark
lines of the picture with the district borders of data/boundaries/tbilisi_districts_osm.geojson (chamfer matching, no rotation).
Library:  load_lines(), fit(img_gray) -> (px_per_m, x0, y0)  where pixel = ((x - X0) * s, (Y0 - y) * s) with x, y metres from the reference point.
Usage:    python -X utf8 tools/georef_thesis_map.py <image.png> [out_overlay.png]
"""
import json
import math
import os
import sys

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LON0, LAT0 = 44.80, 41.72
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0


def to_m(lon, lat):
    return (lon - LON0) * KX, (lat - LAT0) * KY


def to_lonlat(x, y):
    return LON0 + x / KX, LAT0 + y / KY


def load_rings():
    d = json.load(open(os.path.join(ROOT, "data", "boundaries", "tbilisi_districts_osm.geojson"), encoding="utf-8"))
    rings = []
    for f in d["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for r in poly:
                rings.append(np.array([to_m(p[0], p[1]) for p in r]))
    return rings


def densify(rings, step=60.0):
    pts = []
    for r in rings:
        for a, b in zip(r[:-1], r[1:]):
            n = max(1, int(np.hypot(*(b - a)) // step))
            for k in range(n):
                pts.append(a + (b - a) * k / n)
    return np.array(pts)


def dark_mask(bgr):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    b, gg, r = [bgr[:, :, i].astype(int) for i in range(3)]
    colored = (np.abs(r - gg) > 25) | (np.abs(gg - b) > 25)
    return ((g < 80) & ~colored).astype(np.uint8)


def fit(bgr, pts):
    h, w = bgr.shape[:2]
    dm = dark_mask(bgr)
    dt = cv2.distanceTransform(1 - dm, cv2.DIST_L2, 3)
    dt = np.minimum(dt, 25.0).astype(np.float32)
    ext = pts.max(axis=0) - pts.min(axis=0)
    best = None
    for s in np.linspace(0.016, 0.040, 49):                       # px per metre
        tw, th = int(ext[0] * s) + 3, int(ext[1] * s) + 3
        if tw >= w or th >= h:
            continue
        tpl = np.zeros((th, tw), np.float32)
        px = ((pts[:, 0] - pts[:, 0].min()) * s).astype(int)
        py = ((pts[:, 1].max() - pts[:, 1]) * s).astype(int)
        tpl[py, px] = 1.0
        res = cv2.matchTemplate(dt, tpl, cv2.TM_CCORR)
        cost = res / tpl.sum()
        yy, xx = np.unravel_index(np.argmin(cost), cost.shape)
        if best is None or cost[yy, xx] < best[0]:
            best = (cost[yy, xx], s, xx, yy)
    cost, s, xx, yy = best
    # refine the scale and the shift
    def cost_at(s, x0, y0):
        px = (pts[:, 0] - pts[:, 0].min()) * s + x0
        py = (pts[:, 1].max() - pts[:, 1]) * s + y0
        ok = (px >= 0) & (px < w - 1) & (py >= 0) & (py < h - 1)
        return dt[py[ok].astype(int), px[ok].astype(int)].mean() + 25.0 * (1 - ok.mean())
    cur = (s, float(xx), float(yy)); cc = cost_at(*cur)
    for step_s, step_p in ((0.0008, 2.0), (0.0003, 1.0), (0.0001, 0.5)):
        improved = True
        while improved:
            improved = False
            for ds in (-step_s, 0, step_s):
                for dx in (-step_p, 0, step_p):
                    for dy in (-step_p, 0, step_p):
                        c = cost_at(cur[0] + ds, cur[1] + dx, cur[2] + dy)
                        if c < cc - 1e-6:
                            cc, cur, improved = c, (cur[0] + ds, cur[1] + dx, cur[2] + dy), True
    return cur, cc


class Geo:
    """pixel <-> metres/lonlat for a fitted map"""
    def __init__(self, s, x0, y0, xmin, ymax):
        self.s, self.x0, self.y0, self.xmin, self.ymax = s, x0, y0, xmin, ymax

    def px_to_m(self, px, py):
        return (px - self.x0) / self.s + self.xmin, self.ymax - (py - self.y0) / self.s

    def m_to_px(self, x, y):
        return (x - self.xmin) * self.s + self.x0, (self.ymax - y) * self.s + self.y0


def make_geo(bgr):
    rings = load_rings()
    pts = densify(rings)
    (s, x0, y0), cost = fit(bgr, pts)
    return Geo(s, x0, y0, pts[:, 0].min(), pts[:, 1].max()), cost, rings


if __name__ == "__main__":
    img = cv2.imread(sys.argv[1])
    geo, cost, rings = make_geo(img)
    print("px per metre %.5f (%.1f m per pixel), mean distance %.2f px" % (geo.s, 1 / geo.s, cost))
    if len(sys.argv) > 2:
        ov = img.copy()
        for r in rings:
            p = np.array([geo.m_to_px(x, y) for x, y in r]).astype(np.int32)
            cv2.polylines(ov, [p], True, (0, 0, 255), 1)
        cv2.imwrite(sys.argv[2], ov)
