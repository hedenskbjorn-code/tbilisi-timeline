"""Put the city outlines of 1924 and 1934 (digitised from the maps of the thesis of N. Kharebava by tools/digitize_thesis_maps.py,
data/boundaries/khar_<year>.geojson) into site/data/urban.json without a full rebuild of site/data (build_site_data.py does the same when it rebuilds the file).
The outlines are the boundary of the city of that year taken from the map (with gardens and planned built-up land), about 30 m per pixel: shown as approximate.
Usage: python -X utf8 -P tools/add_khar_outlines.py
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
YEARS = (1924, 1934)
ACC = 150


def _round(c):
    return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [_round(x) for x in c]


p = os.path.join(ROOT, "site", "data", "urban.json")
d = json.load(open(p, encoding="utf-8"))
d["features"] = [f for f in d["features"] if f["properties"].get("src") != "khar"]
add = []
for y in YEARS:
    g = json.load(open(os.path.join(ROOT, "data", "boundaries", "khar_%d.geojson" % y), encoding="utf-8"))
    for f in g["features"]:
        add.append({"type": "Feature", "geometry": {"type": f["geometry"]["type"], "coordinates": _round(f["geometry"]["coordinates"])},
                    "properties": {"snap": y, "src": "khar", "kind": "city", "partial": False, "acc": ACC}})
# keep the order of the file by snapshot year: the new ones go before the first snapshot that is later than theirs
feats = d["features"]
for f in add:
    i = next((k for k, x in enumerate(feats) if x["properties"]["snap"] > f["properties"]["snap"]), len(feats))
    feats.insert(i, f)
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("snapshots:", sorted({f["properties"]["snap"] for f in feats}))
