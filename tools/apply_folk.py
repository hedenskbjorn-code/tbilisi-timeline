"""Adds the folk (slang) names to data/places.json: run it AFTER tools/apply_places.py (that script writes places.json anew). Input: data/cache/folk_verified.json (tools/verify_folk.py: the quotes stand on their pages),
data/cache/folk_points.json (tools/folk_points.py), tools/folk_mod_ui.json (the strings of the interface, "places" part: the Georgian text from Gemini).
The folk name is a field "f" of a place that exists (a list: a place can have several folk names), or a new place of its own (id "folk-<OSM object>", name = the official name of the object, no description of its own;
the card shows the folk names). A name that the check calls rude or obscene is NOT added (the owner decided: no 18+ layer). The folk name of the Palace of Rituals goes to the layer of modernism (tools/build_modernism.py).
f = [{"n": {ru, en, ka} (the folk name in the languages where it exists), "m": {ru, en, ka} (what it means), "s": [{"u", "l", "q"}]}]. Idempotent. Usage: python -P tools/apply_folk.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from folk_points import PLACE, TO_PLACE  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(R, "site", "data", "places.json")


def entry(r):
    """a folk name as it goes to the card; "m" (the meaning) is absent when the answer gives none (the sources name the name but do not explain it).
    One fix of the answer: a Russian abbreviation in brackets inside a Georgian sentence "(КГБ)" is cut out (the check allows no Cyrillic in the Georgian text); nothing is added."""
    e = {"n": {k: v for k, v in r["folk"].items() if v}, "s": [{"u": s["url"], "l": s["lang"], "q": s["quote"]} for s in r["sources"]]}
    if r["meaning"]:
        e["m"] = {k: v.replace(" (КГБ)", "") if k == "ka" else v for k, v in r["meaning"].items()}
    return e


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ver = json.load(open(os.path.join(R, "data", "cache", "folk_verified.json"), encoding="utf-8"))["ok"]
    rows = json.load(open(os.path.join(R, "for_gemini", "from_desktop", "folk_result.json"), encoding="utf-8"))
    ok = {json.dumps(v["folk"], sort_keys=True) for v in ver}
    pts = json.load(open(os.path.join(R, "data", "cache", "folk_points.json"), encoding="utf-8"))["points"]
    ui = json.load(open(os.path.join(R, "tools", "folk_mod_ui.json"), encoding="utf-8"))["places"]
    d = json.load(open(OUT, encoding="utf-8"))
    d["items"] = [c for c in d["items"] if not c["id"].startswith("folk-")]
    for c in d["items"]:
        c.pop("f", None)
    byid = {c["id"]: c for c in d["items"]}
    added = attached = 0
    new = {}
    for i, r in enumerate(rows):
        if r["adult"] != "none" or json.dumps(r["folk"], sort_keys=True) not in ok:
            continue                                                   # rude, or not verified
        if i in TO_PLACE:
            byid[TO_PLACE[i]].setdefault("f", []).append(entry(r))
            attached += 1
        elif i in PLACE:
            oid, kind = PLACE[i]
            p = pts[oid]
            c = new.setdefault(oid, {"id": "folk-" + oid.lower(), "k": kind, "lon": round(p["lon"], 6), "lat": round(p["lat"], 6), "n": r["official"], "ne": 1,
                                     "s": {"u": r["sources"][0]["url"], "l": r["sources"][0]["lang"], "aq": r["sources"][0]["quote"]}, "f": []})
            c["f"].append(entry(r))
            added += 1
    d["items"] += list(new.values())
    for v in ui.values():
        if not v.get("ka"):
            v["pending_ka"] = True                                      # the Georgian text is still to come from Gemini: tests/check_data.mjs does not let it be published
    d["ui"].update(ui)
    json.dump(d, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("folk names attached to existing places:", attached, "| new places:", len(new), "with", added, "names | places:", len(d["items"]))


if __name__ == "__main__":
    main()
