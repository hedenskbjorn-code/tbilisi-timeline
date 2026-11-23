"""For the monuments without a description (data/cache/mon_search_list.json: those with an author or a year in the data): the article of Wikipedia about WHO / WHAT the monument shows, found by the name of the monument
(en.wikipedia.org API: search, then the introduction of the best hit). The introduction is a quotation for the description of the card ("Bust of X. X was ..."); it is only a candidate: the pairs are looked through by hand
(a namesake is not taken). Output: data/cache/mon_leads.json ({id: {title, url, extract}}). Read-only requests to the public API with the generic User-Agent. Usage: python -P tools/mon_subject_leads.py
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; read-only API client)"}


def get(u):
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
        except Exception:                                    # noqa: BLE001
            time.sleep(5 * (i + 1))
    return {}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = json.load(open(os.path.join(R, "data", "cache", "mon_search_list.json"), encoding="utf-8"))
    out = {}
    for oid, kind, name, year, sc, st in rows:
        q = re.sub(r"^(Monument to|Memorial to|Statue of)\s+", "", name.replace('"', "")).strip()
        d = get("https://en.wikipedia.org/w/api.php?action=query&list=search&srlimit=3&format=json&srsearch=" + urllib.parse.quote(q + " Georgia"))
        hits = [h["title"] for h in d.get("query", {}).get("search", [])]
        if not hits:
            out[oid] = None
            continue
        e = get("https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&exsentences=2&format=json&redirects=1&titles=" + urllib.parse.quote(hits[0]))
        p = list(e.get("query", {}).get("pages", {}).values() or [{}])[0]
        out[oid] = {"name": name, "title": p.get("title"), "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote((p.get("title") or "").replace(" ", "_")), "extract": (p.get("extract") or "").strip(), "others": hits[1:]}
        time.sleep(0.4)
    json.dump(out, open(os.path.join(R, "data", "cache", "mon_leads.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("with a candidate:", sum(1 for v in out.values() if v), "of", len(out))


if __name__ == "__main__":
    main()
