"""Author, licence and a thumbnail of the Wikimedia Commons photographs that the tables name for the monuments and plaques (the field "image" of data/cache/monuments_clean.json is the address of a file page of Commons).
Output: data/cache/monument_photos.json ({"File:Name.jpg": {thumb, page, author, license, license_url, w, h}}), the same format as the photographs of the other layers (tools/fetch_photos.py, whose
request function is used here). Only public read-only Commons API calls with the generic User-Agent. Resumable. Usage: python -P tools/fetch_monument_photos.py
"""
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_photos import call, strip  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import re
EMAIL = re.compile(r",?\s*[\w.+-]+@[\w-]+(\.[\w-]+)+")
PREFIX = "https://commons.wikimedia.org/wiki/"


def title(u):
    if not u or not u.startswith(PREFIX):
        return None
    t = urllib.parse.unquote(u[len(PREFIX):]).replace("_", " ")
    return t if t.startswith("File:") else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "data", "cache", "monuments_named.json"), encoding="utf-8"))
    titles = {title(x["image"]) for k in ("monuments", "plaques") for x in d[k]}
    gp = os.path.join(R, "data", "cache", "monument_photos_geo.json")                    # the files found by coordinates (tools/fetch_monument_photos_geo.py)
    if os.path.exists(gp):
        titles |= {v["title"] for v in json.load(open(gp, encoding="utf-8")).values() if v}
    titles = sorted(titles - {None})
    path = os.path.join(R, "data", "cache", "monument_photos.json")
    info = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    todo = [t for t in titles if t not in info]
    print("files:", len(titles), "| to describe:", len(todo), flush=True)
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        r = call({"action": "query", "titles": "|".join(chunk), "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 400, "format": "json"})
        norm = {n["to"]: n["from"] for n in r.get("query", {}).get("normalized", [])}
        for p in r.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            tt = norm.get(p["title"], p["title"])
            if not ii:
                info[tt] = None                                   # the file does not exist (any more)
                continue
            md = ii.get("extmetadata", {})
            info[tt] = {"thumb": (ii.get("thumburl") or "").split("?")[0] or None, "page": ii.get("descriptionurl"), "author": EMAIL.sub("", strip(md.get("Artist", {}).get("value")) or "").strip() or None,                  # an e-mail address that a photographer prints in the credit is not copied to the site
                        
                        "license": strip(md.get("LicenseShortName", {}).get("value")) or None, "license_url": strip(md.get("LicenseUrl", {}).get("value")) or None, "w": ii.get("thumbwidth"), "h": ii.get("thumbheight")}
        json.dump(info, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        print("  described", min(i + 50, len(todo)), "/", len(todo), flush=True)
        time.sleep(1.5)
    ok = sum(1 for v in info.values() if v and v["thumb"])
    print("with a thumbnail:", ok, "| missing:", sum(1 for v in info.values() if not v), "| no licence:", sum(1 for v in info.values() if v and not v["license"]))


if __name__ == "__main__":
    main()
