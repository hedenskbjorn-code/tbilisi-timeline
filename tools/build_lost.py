"""Build site/data/lost.json (lost = demolished / destroyed buildings) from data/lost_buildings_gemini.json.

The source list was compiled by an external AI (Gemini) from Wikidata, Wikipedia (ka/ru/en), encyclopaedias and the legends of
the old plans; it is NOT authoritative. This script:
  * takes coordinates as given where the source is a Wikidata/OSM coordinate, otherwise converts the pixel the AI read on a plan
    to lon/lat with the project's own georeferencing of that plan (data/georef/<plan>_gcp.json, affine fit, same excluded points
    as tools/warp.py); positional accuracy is the plan's accuracy plus pixel-reading error (see ACC);
  * drops Wikidata links that point to the wrong item (checked by hand: Q4273295 is a truck, Q1975743 an alga);
  * marks per record whether a cited page contains the claimed year of loss (data/lost_check.json, made by a simple text check;
    "year found in a source page" is a weak confirmation, not proof).
Output properties: names, kind, built/lost ranges, reason, replaced, sources, checked, acc (m), pos ("coord"|"plan").
"""
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = 6371000.0
LAT0 = np.radians(41.69)
PLAN = {"1879_bnf.jpg": "tiflis_1879", "1782_cgvia.jpg": "tiflis_1782", "1802_plan.gif": "tiflis_1802",
        "tbilisi_1913_full.jpg": "tbilisi_1913", "1800_chuiko.jpg": "tiflis_1800"}
ACC = {"tiflis_1782": 80, "tiflis_1802": 55, "tiflis_1879": 85, "tbilisi_1913": 60, "tiflis_1800": 60}
BAD_WIKIDATA = {"Q4273295", "Q1975743"}          # wrong items (truck, alga) cited by the AI for a church and a station


def fits():
    out = {}
    for pid in set(PLAN.values()):
        g = json.load(open(os.path.join(ROOT, "data", "georef", pid + "_gcp.json"), encoding="utf-8"))
        ex = {0} if pid == "tbilisi_1913" else set(g.get("excluded_default", []))
        pts = [p for i, p in enumerate(g["gcps"]) if i not in ex]
        px = np.array([p["px"] for p in pts], float)
        w = np.array([[np.radians(p["lnglat"][0]) * R * np.cos(LAT0), np.radians(p["lnglat"][1]) * R] for p in pts])
        out[pid] = np.linalg.lstsq(np.c_[px, np.ones(len(px))], w, rcond=None)[0]
    return out


def main():
    F = fits()
    src = json.load(open(os.path.join(ROOT, "data", "lost_buildings_gemini.json"), encoding="utf-8"))
    chk_path = os.path.join(ROOT, "data", "lost_check.json")
    chk = json.load(open(chk_path, encoding="utf-8")) if os.path.exists(chk_path) else {}
    feats = []
    for x in src:
        pl = x.get("plan") or {}
        if x.get("lat") is not None and x.get("lng") is not None:
            lat, lng, acc, pos = x["lat"], x["lng"], 40, "coord"
        elif pl.get("file") in PLAN:
            pid = PLAN[pl["file"]]
            e, n = np.array([pl["x"], pl["y"], 1.0]) @ F[pid]
            lat, lng, acc, pos = float(np.degrees(n / R)), float(np.degrees(e / (R * np.cos(LAT0)))), ACC[pid], "plan"
        else:
            continue
        srcs = [u for u in (x.get("sources") or []) if not any(q in u for q in BAD_WIKIDATA)]
        c = chk.get(x.get("name_ru"), {})
        feats.append({"type": "Feature", "id": len(feats), "geometry": {"type": "Point", "coordinates": [round(lng, 5), round(lat, 5)]},
                      "properties": {"name_ka": x.get("name_ka"), "name_en": x.get("name_en"), "name_ru": x.get("name_ru"),
                                     "kind": x.get("kind"), "b0": x.get("built_from"), "b1": x.get("built_to"),
                                     "l0": x.get("lost_from"), "l1": x.get("lost_to"), "why": x.get("lost_reason"),
                                     "repl": x.get("what_replaced"), "src": srcs, "chk": bool(c.get("year_in_source")),
                                     "acc": acc, "pos": pos}})
    out = os.path.join(ROOT, "site", "data", "lost.json")
    json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("lost buildings:", len(feats), "with a source page containing the year:", sum(1 for f in feats if f["properties"]["chk"]))


if __name__ == "__main__":
    main()
