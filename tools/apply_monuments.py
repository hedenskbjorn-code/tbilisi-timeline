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


INTRO = json.load(open(os.path.join(R, "data", "cache", "wiki_intros.json"), encoding="utf-8")) if os.path.exists(os.path.join(R, "data", "cache", "wiki_intros.json")) else {}


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
    labels = json.load(open(os.path.join(R, "data", "cache", "monument_labels.json"), encoding="utf-8")) if os.path.exists(os.path.join(R, "data", "cache", "monument_labels.json")) else {}
    gp = os.path.join(R, "data", "cache", "monument_photos_geo.json")
    geo = json.load(open(gp, encoding="utf-8")) if os.path.exists(gp) else {}
    vp = os.path.join(R, "data", "cache", "monuments_verified.json")           # the descriptions found by a search and checked by tools/verify_search.py (quotations stand on their pages)
    ver = {r["id"]: r for r in json.load(open(vp, encoding="utf-8"))["ok"]} if os.path.exists(vp) else {}
    out = {}
    for fn, key, pre in (("sculptures.json", "monuments", "m:"), ("plaques.json", "plaques", "p:")):
        items, used, ph = [], set(), {}
        for x in d[key]:
            n = dict(nv.get(pre + x["id"], x["n"]))
            if x["id"].startswith("ENC_"):              # the "name" of an object taken from the encyclopedia is a torn piece of a sentence of the OCR text ("where a bust was set in 2007"): the object is labelled by its type and street
                n = {"ka": "", "ru": "", "en": ""}
            t = ph_title(x["image"])
            near = False
            if not t and key == "monuments" and geo.get(x["id"]):                         # no file named by the table: the file found by coordinates (marked when only the nearness says that it is the monument)
                t, near = geo[x["id"]]["title"], geo[x["id"]]["near"]
            if t and photos.get(t) and photos[t]["thumb"]:
                ph[t] = {k: photos[t][k] for k in ("thumb", "page", "author", "license", "w", "h")}
            else:
                t, near = "", False
            it = {"id": x["id"], "lon": x["lon"], "lat": x["lat"], "n": n, "y": x["year"], "ph": t, "w": x["wiki"], "st": x["st"] or ""}
            if near and t:
                it["phn"] = 1
            if key == "monuments":
                it.update({"k": x["kind"], "sc": x["sculptor"], "ar": x["architect"], "mat": x.get("mat", "")})
                lb = labels.get(x.get("sc_qid", ""))
                if lb and all(lb[k] for k in ("ka", "ru", "en")):
                    it["sc"] = lb                                      # the artist named by Wikidata: the name in three languages
                if x.get("d"):
                    it["d"] = x["d"]
                v = ver.get(x["id"])
                if v and not it.get("d"):                              # a description from a search: ru / en (ka only when it exists: the Georgian text waits for Gemini), the quotations for the details
                    it["d"] = {l: t for l, t in v["description"].items() if t}
                    it["dq"] = [{"u": s["url"], "l": s["lang"], "q": s["quote"]} for s in v["sources"]]
                    w = dict(it["w"] or {})
                    for s in v["sources"]:
                        mm = __import__("re").match(r"https://(ka|ru|en)[.]wikipedia[.]org/", s["url"])
                        if mm and mm.group(1) not in w:
                            w[mm.group(1)] = s["url"]
                    it["w"] = w
                if any(n.values()) and not all(n.values()):
                    it["pend"] = 1                                     # a new object whose name waits for the translation (tools/build_monuments_names.py makes the table for Gemini): the page shows the name that exists
            else:
                it["ins"] = (x["inscription"] or "").replace("\\n", "\n").strip()[:400]
            wi = INTRO.get(key, {}).get(x["id"])                       # the first sentences of the Wikipedia article that the object is linked to (data/cache/wiki_intros.json: written by hand into the files on 2026-11-24, kept here so that a rebuild keeps them); a description found by a search wins
            if wi and not it.get("d"):
                it["d"] = {l: t.replace("́", "") for l, t in wi.items()}      # the stress marks of the Russian article (a combining acute) are not kept
                it["dw"] = 1                                                      # a description from Wikipedia: the card says so
            if it["st"]:
                used.add(it["st"])
            items.append(it)
        data = {"items": items, "streets": {k: street[k] for k in sorted(used) if k in street}, "photos": ph, "ui": ui}
        open(os.path.join(D, fn), "wb").write(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        miss = collections.Counter(lg for it in items for lg in ("ka", "ru", "en") if not it["n"][lg] and any(it["n"].values()))
        print(fn, len(items), "| bytes:", os.path.getsize(os.path.join(D, fn)), "| photos:", len(ph), "| streets:", len(data["streets"]), "| partial names left:", dict(miss), "| unnamed:", sum(1 for it in items if not any(it["n"].values())))


if __name__ == "__main__":
    main()
