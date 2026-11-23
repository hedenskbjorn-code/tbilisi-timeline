"""Builds site/data/modernism.json (the layer "Soviet modernism"; lazy, loaded when the layer is switched on, a card format of the monuments layer).
Input: data/cache/modernism_verified.json (tools/verify_modernism.py: every quote stands on its page), data/cache/modernism_geo.json (tools/geocode_modernism.py + tools/modernism_points.py: the point and its origin),
data/cache/modernism_photos.json + modernism_photo_info.json (tools/fetch_modernism_photos.py), data/cache/folk_verified.json (the folk name of the Palace of Rituals), tools/folk_mod_ui.json ("modernism": the strings).
Item: {id, lon, lat, n: {ru,en,ka}, y (the year of the end of the building), k: "modernism", ar: [architects as the sources write them], ft / fn: the function then / now {ru,en,ka}, st: status,
d: the description {ru,en,ka}, ph: the file of Commons (or ""), w: {lang: url of a Wikipedia article} when a source is Wikipedia, wd: Wikidata id, g: {how, ref} the origin of the point,
s: [{u (url), l (language), q (quote), f (what the quote confirms)}], f: the folk names}. "photos" is the same dictionary as in the monuments layer.
Usage: python -P tools/build_modernism.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(R, "data", "cache")


def load(p):
    return json.load(open(os.path.join(CACHE, p), encoding="utf-8"))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = load("modernism_verified.json")["ok"]
    geo, ph, info = load("modernism_geo.json"), load("modernism_photos.json"), load("modernism_photo_info.json")
    folk = [r for r in json.load(open(os.path.join(R, "for_gemini", "from_desktop", "folk_result.json"), encoding="utf-8")) if r["adult"] == "none"]
    ui = json.load(open(os.path.join(R, "tools", "folk_mod_ui.json"), encoding="utf-8"))["modernism"]
    for v in ui.values():
        if not v.get("ka"):
            v["pending_ka"] = True                                      # the Georgian text is still to come from Gemini: tests/check_data.mjs does not let it be published
    items, photos, skipped = [], {}, []
    for i, b in enumerate(rows):
        g = geo.get(str(i))
        if not g:
            skipped.append(b["name"]["en"])
            continue
        c = {"id": "md-" + slug(b["name"]["en"].split(" (")[0]), "lon": round(g["lon"], 6), "lat": round(g["lat"], 6), "n": b["name"], "y": b["year"], "k": "modernism",
             "ar": b["architects"], "ft": b["function_then"], "fn": b["function_now"], "st": b["status"], "d": b["description"], "wd": b.get("wikidata") or "",
             "g": {"how": g["how"], "ref": g["ref"]}, "s": [{"u": s["url"], "l": s["lang"], "q": s["quote"], "f": s["fact"]} for s in b["sources"]]}
        w = {}
        for s in b["sources"]:
            m = re.match(r"https://(ka|ru|en)\.wikipedia\.org/wiki/", s["url"])
            if m and m.group(1) not in w:
                w[m.group(1)] = s["url"]
        if w:
            c["w"] = w
        p = ph.get(str(i))
        c["ph"] = p["title"] if p and info.get(p["title"]) else ""
        if c["ph"]:
            photos[c["ph"]] = info[c["ph"]]
        if "Palace of Rituals" in b["name"]["en"]:                      # the folk name from the answer about the folk names (row about the Palace of Rituals)
            f = [x for x in folk if x["folk"].get("ka") == "რიტუალების სასახლე"]
            c["f"] = [{"n": {k: v for k, v in x["folk"].items() if v}, "s": [{"u": s["url"], "l": s["lang"], "q": s["quote"]} for s in x["sources"]], **({"m": x["meaning"]} if x["meaning"] else {})} for x in f]
        items.append(c)
    items.sort(key=lambda c: (c["y"] or 0, c["id"]))
    out = {"items": items, "photos": photos, "ui": ui}
    json.dump(out, open(os.path.join(R, "site", "data", "modernism.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("buildings:", len(items), "| with a photo:", sum(1 for c in items if c["ph"]), "| without a point:", skipped)


if __name__ == "__main__":
    main()
