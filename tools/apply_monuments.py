"""Builds site/data/sculptures.json (monuments, sculptures, busts, memorials, reliefs) and site/data/plaques.json (memorial plaques): the lazy files of the two layers (loaded when a layer is switched on).
Input: data/cache/monuments_named.json (tools/build_monuments_names.py), data/cache/monuments_names_verified.json (tools/verify_monuments_names.py: the missing languages of the names),
data/cache/monument_photos.json (tools/fetch_monument_photos.py), tools/monuments_ui.json (the strings of the cards in ru/en/ka; tools/build_monuments_ui.py).
Format of a file: {"items": [...], "streets": {key: {ka, ru, en}} (only the streets that the items use), "photos": {title: {thumb, page, author, license}}, "ui": {...}}.
Monument: {"id", "k": kind, "lon", "lat", "n": {ka, ru, en} (an empty language stays ""), "y": year|null, "sc", "ar" (as in the source), "mat", "ph": title|"", "w": {lang: url}, "st": key of the street|""}.
Plaque: {"id", "lon", "lat", "n", "y": the first year of the life named in the inscription | null, "ins": the inscription (to 400 characters), "ph", "w", "st"}.
Usage: python -P tools/apply_monuments.py
"""
import collections
import json
import os
import sys
import urllib.parse

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(R, "site", "data")


def ph_title(u):
    p = "https://commons.wikimedia.org/wiki/"
    if u and u.startswith(p):
        t = urllib.parse.unquote(u[len(p):]).replace("_", " ")
        return t if t.startswith("File:") else ""
    return ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "data", "cache", "monuments_named.json"), encoding="utf-8"))
    nv = json.load(open(os.path.join(R, "data", "cache", "monuments_names_verified.json"), encoding="utf-8")) if os.path.exists(os.path.join(R, "data", "cache", "monuments_names_verified.json")) else {}
    photos = json.load(open(os.path.join(R, "data", "cache", "monument_photos.json"), encoding="utf-8"))
    up = os.path.join(R, "tools", "monuments_ui.json")
    ui = json.load(open(up, encoding="utf-8"))["ui"] if os.path.exists(up) else {}
    sn = json.load(open(os.path.join(D, "street_names.json"), encoding="utf-8"))["streets"]
    street = {(s.get("geom") or s["now"]["en"]): s["now"] for s in sn}
    fixp = os.path.join(R, "tools", "monuments_names_fix.json")
    fix = {k: v for k, v in json.load(open(fixp, encoding="utf-8")).items() if k != "note"} if os.path.exists(fixp) else {}
    nv.update(fix)                                                  # corrections of typos of OSM (decision of the owner)
    out = {}
    for fn, key, pre in (("sculptures.json", "monuments", "m:"), ("plaques.json", "plaques", "p:")):
        items, used, ph = [], set(), {}
        for x in d[key]:
            n = dict(nv.get(pre + x["id"], x["n"]))
            if x["id"].startswith("ENC_"):              # the "name" of an object taken from the encyclopedia is a torn piece of a sentence of the OCR text ("where a bust was set in 2007"): the object is labelled by its type and street
                n = {"ka": "", "ru": "", "en": ""}
            t = ph_title(x["image"])
            if t and photos.get(t) and photos[t]["thumb"]:
                ph[t] = {k: photos[t][k] for k in ("thumb", "page", "author", "license")}
            else:
                t = ""
            it = {"id": x["id"], "lon": x["lon"], "lat": x["lat"], "n": n, "y": x["year"], "ph": t, "w": x["wiki"], "st": x["st"] or ""}
            if key == "monuments":
                it.update({"k": x["kind"], "sc": x["sculptor"], "ar": x["architect"], "mat": x.get("mat", "")})
            else:
                it["ins"] = (x["inscription"] or "").replace("\\n", "\n").strip()[:400]
            if it["st"]:
                used.add(it["st"])
            items.append(it)
        data = {"items": items, "streets": {k: street[k] for k in sorted(used) if k in street}, "photos": ph, "ui": ui}
        open(os.path.join(D, fn), "wb").write(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        miss = collections.Counter(lg for it in items for lg in ("ka", "ru", "en") if not it["n"][lg] and any(it["n"].values()))
        print(fn, len(items), "| bytes:", os.path.getsize(os.path.join(D, fn)), "| photos:", len(ph), "| streets:", len(data["streets"]), "| partial names left:", dict(miss), "| unnamed:", sum(1 for it in items if not any(it["n"].values())))


if __name__ == "__main__":
    main()
