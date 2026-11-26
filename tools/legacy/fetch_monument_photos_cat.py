"""A Wikimedia Commons file for the monuments whose table entry names a Commons CATEGORY instead of a file ("image" = .../wiki/Category:Name; 50 objects).
The category is named after the object, so a file of it is taken: the first whose title shares a word with the category name (else the first file of the category, not a "cropped" one).
Output: the entries are added to data/cache/monument_photos_geo.json ({id: {"title": "File:...", "near": false}}), the file that tools/apply_monuments.py already reads.
Read-only public Commons API calls, a generic User-Agent. Usage: python -P tools/fetch_monument_photos_cat.py
"""
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_photos import call  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PREFIX = "https://commons.wikimedia.org/wiki/Category:"
IMG = re.compile(r"\.(jpe?g|png|webp)$", re.I)


STOP = {"tbilisi", "tbilissi", "georgia", "georgian", "statue", "statute", "monument", "memorial", "bust", "sculpture", "street", "square", "church", "grave", "gravestone", "panoramio", "saint", "settlement", "fountain", "cropped"}


def words(s):
    return {w.lower() for w in re.findall(r"[^\W\d_]{4,}", s)} - STOP


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "data", "cache", "monuments_named.json"), encoding="utf-8"))
    path = os.path.join(R, "data", "cache", "monument_photos_geo.json")
    out = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    todo = []
    for k in ("monuments",):
        for x in d[k]:
            u = urllib.parse.unquote(x["image"] or "")
            if u.startswith(PREFIX):
                todo.append((x["id"], u[len(PREFIX):].replace("_", " ")))
    print("categories to resolve:", len(todo), flush=True)
    for i, (oid, cat) in enumerate(todo, 1):
        r = call({"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat, "cmtype": "file", "cmlimit": 50, "format": "json"})
        files = [m["title"] for m in r.get("query", {}).get("categorymembers", []) if IMG.search(m["title"])]
        cw = words(cat)
        pick = next((f for f in files if cw & words(f[5:]) and "cropped" not in f), None)            # only a file that shares a meaningful word with the category (the first file of a category may show something else)
        out[oid] = {"title": pick, "near": False} if pick else None
        print(" ", i, cat, "->", pick, flush=True)
        time.sleep(0.5)
    man = json.load(open(os.path.join(R, "tools", "monuments_manual.json"), encoding="utf-8")).get("photo", {})
    for oid, title in man.items():                                                      # the files chosen by hand (tools/monuments_manual.json "photo")
        out[oid] = {"title": title, "near": False}
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print("resolved:", sum(1 for o, _c in todo if out.get(o)), "of", len(todo))


if __name__ == "__main__":
    main()
