"""Turn an outline given in pixels of the ORIGINAL plan scan into lon/lat with the plan's own affine control-point fit.

Used for tiflis_1884, whose outline vertices were read by an external AI (Gemini) from gridded tiles of the scan
(work/gemini/archive/outbox/outline_1884.json) and then checked by overlay by Claude. The fit is the same as tools/warp.py (affine,
excluded_default honoured), so the result equals tracing on the warped image.
Usage: python tools/outline_from_original_pixels.py <plan_id> <vertices.json> <year>
vertices.json: {"rings":[{"name":..., "vertices":[[x,y],...]}]}
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = 6378137.0


def main(pid, src, year):
    g = json.load(open(os.path.join(ROOT, "data", "georef", pid + "_gcp.json"), encoding="utf-8"))
    ex = set(g.get("excluded_default", []))
    pts = [p for i, p in enumerate(g["gcps"]) if i not in ex]
    px = np.array([p["px"] for p in pts], float)
    mx = np.array([[R * math.radians(p["lnglat"][0]), R * math.log(math.tan(math.pi / 4 + math.radians(p["lnglat"][1]) / 2))] for p in pts])
    M = np.linalg.lstsq(np.c_[px, np.ones(len(px))], mx, rcond=None)[0]
    meta = json.load(open(os.path.join(ROOT, "data", "warped", pid + ".json"), encoding="utf-8"))
    d = json.load(open(src, encoding="utf-8"))
    feats = []
    for r in d["rings"]:
        ll = []
        for x, y in r["vertices"]:
            X, Y = np.array([x, y, 1.0]) @ M
            ll.append([round(math.degrees(X / R), 6), round(math.degrees(2 * math.atan(math.exp(Y / R)) - math.pi / 2), 6)])
        if ll[0] != ll[-1]:
            ll.append(ll[0])
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ll]},
                      "properties": {"plan_id": pid, "name": r["name"], "kind": "built_up", "confidence": "approximate",
                                     "source": "vertices read from the plan scan (LOO %s m)" % round(meta.get("loo_rms_m") or 0)}})
    path = os.path.join(ROOT, "data", "boundaries", pid + ".geojson")
    json.dump({"type": "FeatureCollection", "features": feats, "properties": {"year": int(year)}}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(pid, "rings:", len(feats), "->", path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
