"""A Wikimedia Commons photograph for the monuments that have none (the table and OSM name no file for 450 of 630): the files with a geotag within 30 m of the monument (tools/fetch_photos.py, geosearch).
A file is taken when its title carries a word of a monument (statue, bust, monument, memorial, sculpture, relief ...) or a word of the name of the object (then it is "named"); otherwise the nearest file within 12 m
is taken and the card says "photo near this point (may show a neighbouring building)" ("near": true). Output: data/cache/monument_photos_geo.json ({id: {"title": "File:...", "near": bool}}).
Resumable; read-only requests, a generic User-Agent. Usage: python -P tools/fetch_monument_photos_geo.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_photos import geosearch  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORDS = re.compile(r"monument|statue|bust|memorial|sculpture|relief|obelisk|stele|fountain|ძეგლ|ბიუსტ|ქანდაკ|памятник|статуя|бюст|мемориал|скульптур", re.I)


def tokens(n):
    out = set()
    for v in n.values():
        for w in re.findall(r"[^\W\d_]{4,}", v or ""):
            out.add(w.lower())
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "data", "cache", "monuments_named.json"), encoding="utf-8"))
    path = os.path.join(R, "data", "cache", "monument_photos_geo.json")
    out = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    todo = [x for x in d["monuments"] if not x["image"] and x["id"] not in out]
    print("monuments without a photo:", len(todo), flush=True)
    for i, x in enumerate(todo, 1):
        hits = geosearch(x["lat"], x["lon"], 30)
        tk, pick = tokens(x["n"]), None
        for h in sorted(hits, key=lambda h: h["dist"]):
            t = h["title"][5:].lower()
            if any(w in t for w in tk):
                pick = {"title": h["title"], "near": False}
                break
        if not pick:
            for h in sorted(hits, key=lambda h: h["dist"]):
                t = h["title"][5:].lower()
                if WORDS.search(t):
                    pick = {"title": h["title"], "near": True}
                    break
        if not pick and hits:
            h = min(hits, key=lambda h: h["dist"])
            if h["dist"] <= 12:
                pick = {"title": h["title"], "near": True}
        out[x["id"]] = pick
        if i % 50 == 0:
            json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            print("  checked", i, "| photos", sum(1 for v in out.values() if v), flush=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print("photos found:", sum(1 for v in out.values() if v), "of", len(out), "| named:", sum(1 for v in out.values() if v and not v["near"]), "| near only:", sum(1 for v in out.values() if v and v["near"]))


if __name__ == "__main__":
    main()
