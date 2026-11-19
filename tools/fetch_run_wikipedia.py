"""Descriptions and lead photos for the sights of the route (data/run_trc2026.json): the introduction of the Wikipedia article in ru, en and ka (up to 3 sentences, the text of
Wikipedia, CC BY-SA 4.0, the page says so and links the article) and the lead image of the article (a Commons file name, its licence is checked by build_run_details.py).
An article is taken when it is linked from the register data of the site (the titles of the sight), or when a search by the name finds an article whose coordinates are within
350 m of the sight (so that an article about another object or a whole district is not taken). Output: data/run_descriptions.json (read by build_run_details.py).
Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT. Usage: python -X utf8 -P tools/fetch_run_wikipedia.py
"""
import json
import math
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_contact = os.environ.get("WIKIMEDIA_CONTACT")
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; Wikipedia API client%s)" % ("; contact: " + _contact if _contact else "")
LANGS = ("ru", "en", "ka")
MAX_M = 350


_fails = 0


def api(lang, **params):
    global _fails
    params.update(format="json", formatversion=2)
    url = "https://%s.wikipedia.org/w/api.php?%s" % (lang, urllib.parse.urlencode(params))
    for k in range(2):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read())
            time.sleep(0.2)
            _fails = 0
            return d
        except Exception as e:
            _fails += 1
            if _fails >= 6:                      # the server refuses (for example 429 Too Many Requests): stop, do not hammer it
                raise SystemExit("stopped: 6 failed requests in a row, last: %s (set WIKIMEDIA_CONTACT?)" % str(e)[:80])
            time.sleep(3 * (k + 1))
    return {}


def hav(a, b):
    k = math.cos(math.radians(a[0]))
    return math.hypot((a[1] - b[1]) * k * 111320, (a[0] - b[0]) * 111320)


def page_info(lang, title):
    """{title, extract, lat, lon, image, disambig} of one article, or None"""
    d = api(lang, action="query", titles=title, redirects=1, prop="extracts|coordinates|pageimages|pageprops", exintro=1, explaintext=1, exsentences=3, piprop="name", ppprop="disambiguation")
    pgs = (d.get("query") or {}).get("pages") or []
    if not pgs or pgs[0].get("missing"):
        return None
    pg = pgs[0]
    c = (pg.get("coordinates") or [None])[0]
    return {"title": pg["title"], "extract": re.sub(r"\s+", " ", pg.get("extract") or "").strip(), "lat": c and c["lat"], "lon": c and c["lon"], "image": pg.get("pageimage"),
            "disambig": "disambiguation" in (pg.get("pageprops") or {})}


def find(lang, s, known):
    cands = []
    if known:
        cands.append((known, True))
    name = re.sub(r"\s*\(.*?\)", "", s["name"].get(lang) or "")
    if name:
        d = api(lang, action="query", list="search", srsearch=name + (" Tbilisi" if lang == "en" else ""), srlimit=4, srnamespace=0)
        for r in (d.get("query") or {}).get("search") or []:
            cands.append((r["title"], False))
    seen = set()
    for title, trusted in cands:
        if title in seen:
            continue
        seen.add(title)
        pi = page_info(lang, title)
        if not pi or pi["disambig"] or not pi["extract"]:
            continue
        if trusted:
            return pi
        if pi["lat"] is not None and hav((s["lat"], s["lon"]), (pi["lat"], pi["lon"])) <= MAX_M:
            return pi
    return None


def main():
    run = json.load(open(os.path.join(ROOT, "site", "data", "run_trc2026.json"), encoding="utf-8"))
    out = []
    for s in run["sights"]:
        item = {"n": s["n"], "wp": {}, "desc": {}, "sources": [], "photos": [], "src_by_lang": {}}
        for lang in LANGS:
            pi = find(lang, s, (s.get("wp") or {}).get(lang))
            if not pi:
                continue
            item["wp"][lang] = pi["title"]
            item["desc"][lang] = pi["extract"]
            url = "https://%s.wikipedia.org/wiki/%s" % (lang, urllib.parse.quote(pi["title"].replace(" ", "_"), safe="_(),'"))
            item["sources"].append(url)
            item["src_by_lang"][lang] = url
            if pi["image"] and all(p["file"] != "File:" + pi["image"] for p in item["photos"]):
                item["photos"].append({"file": "File:" + pi["image"], "why": "lead image of the %s article" % lang})
        print(s["n"], s["name"]["en"][:40].ljust(40), "|", ",".join(item["wp"].keys()) or "NO ARTICLE", "|", len(item["photos"]), "photo(s)")
        out.append(item)
    open(os.path.join(ROOT, "data", "run_descriptions.json"), "wb").write(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print("articles:", {l: sum(1 for i in out if l in i["desc"]) for l in LANGS}, "| sights without any article:", [i["n"] for i in out if not i["desc"]])


if __name__ == "__main__":
    main()
