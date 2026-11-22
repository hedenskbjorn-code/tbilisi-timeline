"""Builds site/data/places.json (the layer "Local names"; loaded when the layer is switched on, not part of the first screen).
Input: data/cache/places_verified.json (tools/verify_places.py: the quotes stand in the articles), data/cache/places_candidates.json (the points), tools/places_manual.json (entries that do not come from
OSM + Wikipedia: the former hippodrome etc.; checked by tests/check_data.mjs), tools/places_ui.json (the strings of the layer in ru/en/ka; the Georgian text from Gemini).
Output: {"items": [{"id", "k": kind, "lon", "lat", "n": {ka, ru, en}, "a": {ru, en, ka} (what it is), "e": {ru, en, ka}|null (where the name comes from; null = the source does not say),
"s": {"l": language of the article, "u": url, "aq": quote, "eq": quote|null}, "x"?: {other fields of a manual entry}}], "ui": {...}}.
The same object that came in two pieces of OSM (the same Georgian name and kind) is taken once. Usage: python -P tools/apply_places.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    v = json.load(open(os.path.join(R, "data", "cache", "places_verified.json"), encoding="utf-8"))
    cand = {x["key"]: x for x in json.load(open(os.path.join(R, "data", "cache", "places_candidates.json"), encoding="utf-8"))}
    wiki = json.load(open(os.path.join(R, "data", "cache", "places_wiki.json"), encoding="utf-8"))
    items, seen = [], {}
    fixp = os.path.join(R, "tools", "places_names_fix.json")
    fix = json.load(open(fixp, encoding="utf-8")) if os.path.exists(fixp) else {}
    for r in v["ok"]:
        r["name"] = {**r["name"], **fix.get(r["key"], {})}
        c = cand[r["key"]]
        sig = (c["kind"], r["name"]["ka"])
        if sig in seen:
            continue
        seen[sig] = r["key"]
        lg = r["about_quote"]["lang"]
        e = r["etym"]
        s = {"l": lg, "u": wiki[r["key"]]["pages"][lg]["url"], "aq": r["about_quote"]["quote"], "eq": None}
        if e:
            lg2 = r["etym_quote"]["lang"]
            s["eq"] = {"l": lg2, "u": wiki[r["key"]]["pages"][lg2]["url"], "q": r["etym_quote"]["quote"]}
        items.append({"id": r["key"].replace(":", "-").replace("/", ""), "k": c["kind"], "lon": c["lon"], "lat": c["lat"], "n": r["name"], "a": r["about"], "e": e, "s": s})
    # the second search of the origin of the names (tools/verify_places_etym.py): the places that had no origin get it, with the quote of the page; "kind": "dictionary" = the meaning of the common word
    ep, xp = os.path.join(R, "data", "cache", "places_etym_verified.json"), os.path.join(R, "tools", "places_etym_exclude.json")
    if os.path.exists(ep):
        excl = {k for k in json.load(open(xp, encoding="utf-8")) if k != "note"} if os.path.exists(xp) else set()
        byid = {it["id"]: it for it in items}
        for r in json.load(open(ep, encoding="utf-8"))["ok"]:
            it = byid.get(r["key"].replace(":", "-").replace("/", ""))
            if it is None or it["e"] or r["key"] in excl:
                continue
            kind = "dictionary" if r.get("kind") == "dictionary" or "/ka/form/" in r["url"] else "origin"
            it["e"] = r["etym"]
            it["s"]["eq"] = {"l": r["lang"], "q": r["quote"], **({"u": r["url"]} if r["source"] == "web" else {"p": r["page"]}), **({"k": "dictionary"} if kind == "dictionary" else {})}
    mp = os.path.join(R, "tools", "places_manual.json")
    if os.path.exists(mp):
        items += json.load(open(mp, encoding="utf-8"))["items"]
    up = os.path.join(R, "tools", "places_ui.json")
    ui = json.load(open(up, encoding="utf-8"))["ui"] if os.path.exists(up) else {}
    items.sort(key=lambda x: (x["k"], x["n"]["en"]))
    p = os.path.join(R, "site", "data", "places.json")
    open(p, "wb").write(json.dumps({"items": items, "ui": ui}, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    import collections
    print("places:", len(items), dict(collections.Counter(x["k"] for x in items)), "| with etymology:", sum(1 for x in items if x["e"]), "| bytes:", os.path.getsize(p))


if __name__ == "__main__":
    main()
