"""The text of the Wikipedia articles of the candidates of the layer "Local names" (data/cache/places_candidates.json): for every candidate the articles in ka / ru / en (found by the Wikidata sitelinks
and by the OSM tag "wikipedia") as plain text. Output: data/cache/places_wiki.json ({key: {"qid", "labels": {ka, ru, en}, "pages": {lang: {"title", "url", "text"}}}}). The text is the base for the
quotes that tools/verify_places.py checks. Sequential, with pauses; Retry-After is respected; a generic User-Agent (an optional contact only from the environment variable WIKIMEDIA_CONTACT).
Usage: python -P tools/fetch_places_wiki.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % ("; contact: " + os.environ["WIKIMEDIA_CONTACT"] if os.environ.get("WIKIMEDIA_CONTACT") else "")
LANGS = ("ka", "ru", "en")
MAXCH = 12000


def get(url):
    for k in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60))
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After")
            time.sleep(int(ra) if ra and ra.isdigit() else 10 * (k + 1))
        except Exception:
            time.sleep(5 * (k + 1))
    raise SystemExit("failed: " + url[:120])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cand = json.load(open(os.path.join(R, "data", "cache", "places_candidates.json"), encoding="utf-8"))
    path = os.path.join(R, "data", "cache", "places_wiki.json")
    out = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    qids = sorted({c["wikidata"] for c in cand if c["wikidata"]})
    ent = {}
    for i in range(0, len(qids), 40):
        d = get("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=sitelinks|labels&languages=ka|ru|en&sitefilter=kawiki|ruwiki|enwiki&ids=" + "|".join(qids[i:i + 40]))
        ent.update(d.get("entities", {}))
        time.sleep(1)
    n = 0
    for c in cand:
        if c["key"] in out and out[c["key"]].get("done"):
            continue
        e = ent.get(c["wikidata"], {}) if c["wikidata"] else {}
        titles = {lg: e.get("sitelinks", {}).get(lg + "wiki", {}).get("title") for lg in LANGS}
        if ":" in c["wikipedia"]:                                           # the OSM tag "ka:Title" (the tag counts when Wikidata has no link in that language)
            lg, tl = c["wikipedia"].split(":", 1)
            if lg in LANGS and not titles.get(lg):
                titles[lg] = tl
        pages = {}
        for lg, tl in titles.items():
            if not tl:
                continue
            d = get("https://%s.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&explaintext=1&redirects=1&titles=%s" % (lg, urllib.parse.quote(tl)))
            for pg in d.get("query", {}).get("pages", {}).values():
                tx = pg.get("extract")
                if tx:
                    pages[lg] = {"title": pg["title"], "url": "https://%s.wikipedia.org/wiki/%s" % (lg, urllib.parse.quote(pg["title"].replace(" ", "_"))), "text": tx[:MAXCH]}
            time.sleep(0.5)
        out[c["key"]] = {"qid": c["wikidata"], "labels": {lg: e.get("labels", {}).get(lg, {}).get("value", "") for lg in LANGS}, "pages": pages, "done": True}
        n += 1
        if n % 10 == 0:
            json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            print("done", n, flush=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    got = sum(1 for v in out.values() if v["pages"])
    print("candidates:", len(cand), "| with an article:", got, "| bytes:", os.path.getsize(path))


if __name__ == "__main__":
    main()
