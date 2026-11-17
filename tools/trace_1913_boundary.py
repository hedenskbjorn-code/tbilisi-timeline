"""Partial city-limit line from the 1913 plan (green line "границы города" in the legend).

Vertices were read by eye from half-resolution crops of data/raw/maps/tbilisi_1913.jpg (HALF coordinates, x2 = full pixels).
Only the stretches that are clearly visible are included; the line is hidden under park fills and tables elsewhere,
so the west and south parts are NOT traced. Pixel -> lng/lat uses the same affine model as tools/warp.py
(14 control points, outliers 0,2,15 excluded).
Writes data/boundaries/tbilisi_1913.geojson  (LineString features, partial=true, confidence=approximate).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from warp import Warp, merc, unmerc, ROOT  # noqa: E402

EXCLUDE = {0, 2, 15}
gcps = [g for i, g in enumerate(json.load(open(os.path.join(ROOT, "data/georef/tbilisi_1913_gcp.json")))["gcps"]) if i not in EXCLUDE]
P = np.array([g["px"] for g in gcps], float)
M = np.array([merc(*g["lnglat"]) for g in gcps], float)
fwd = Warp(P, M, None)

# global half-resolution coordinates (see q_NW / q_NE / q_SE crops)
SEGMENTS = {
    "north_and_east_arc": [
        (62, 60), (350, 100), (560, 138), (770, 175), (1060, 138), (1090, 172),   # top edge of the plan area
        (1275, 400), (1491, 665), (1656, 870),                                     # north-east diagonal
        (1836, 1100), (1861, 1160), (1871, 1225), (1856, 1290), (1916, 1340),      # Avlabar side (bits hidden under the table are joined straight)
        (2016, 1510), (2146, 1683), (2286, 1833), (2366, 1943), (2416, 2023),      # east / south-east diagonal
        (2516, 2163), (2576, 2223), (2706, 2383), (2816, 2513),
    ],
}

feats = []
for name, pts in SEGMENTS.items():
    px = np.array(pts, float) * 2.0
    ll = [unmerc(*xy) for xy in fwd(px)]
    feats.append({
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[round(a, 6), round(b, 6)] for a, b in ll]},
        "properties": {
            "year": 1913, "plan_id": "tbilisi_1913", "type": "city_limit", "confidence": "approximate", "partial": True, "name": name,
            "source": "green 'city limit' line on the 1913 plan, vertices read by eye; hidden stretches joined straight; west and south not traced",
        },
    })
out = os.path.join(ROOT, "data", "boundaries", "tbilisi_1913.geojson")
json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", out, [len(f["geometry"]["coordinates"]) for f in feats])
# also dump the pixel polyline for the overlay check
json.dump({k: [(x * 2, y * 2) for x, y in v] for k, v in SEGMENTS.items()}, open(os.path.join(os.environ.get("SCRATCH", "."), "seg_px.json"), "w"))
