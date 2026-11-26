"""Fetch the OSM ways (Overpass, ODbL) of the streets of the verified encyclopedia entries (data/cache/enc2008_verified.json) by their Georgian names:
data/raw/osm_transport/street_labels_enc.json (not committed). Only the ways in the bounding box of Tbilisi. Resumable: the names already fetched are kept in the file.
Usage: python -P tools/fetch_enc_osm.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VER = os.path.join(ROOT, "data", "cache", "enc2008_verified.json")
OUT = os.path.join(ROOT, "data", "raw", "osm_transport", "street_labels_enc.json")
B = "(41.60,44.60,41.90,45.05)"


def main():
    import re
    clean = lambda n: re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", "", n)).strip()      # OSM writes "კოტე აფხაზის ქუჩა", the book "კოტე (კონსტანტინე) აფხაზის ქუჩა"
    ka = [r["ka_now"] for r in json.load(open(VER, encoding="utf-8"))["ok"]]
    v4 = os.path.join(ROOT, "data", "cache", "enc2008_verified4.json")          # the full pass
    if os.path.exists(v4):
        ka += [r["ka_now"] for r in json.load(open(v4, encoding="utf-8"))["ok"]]
    names = set(ka) | {clean(n) for n in ka}
    fz = os.path.join(ROOT, "data", "cache", "enc2008_fuzzy_names.json")          # the spelling variants found in OSM by tools/build_enc_spec.py
    if os.path.exists(fz):
        names |= set(json.load(open(fz, encoding="utf-8")))
    names = sorted(names)
    have = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {"names": [], "elements": []}
    todo = [n for n in names if n not in have["names"]]
    print("names:", len(names), "| to fetch:", len(todo))
    for i in range(0, len(todo), 40):
        chunk = todo[i:i + 40]
        q = '[out:json][timeout:240];way["highway"]["name"~"^(%s)$"]%s;out geom tags;' % ("|".join(chunk), B)
        for k in range(6):
            try:
                d = urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(),
                                                                  headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=280).read()
                els = json.loads(d)["elements"]
                break
            except Exception as e:
                print("retry", str(e)[:60], flush=True)
                time.sleep(25 * (k + 1))
        else:
            sys.exit("giving up")
        have["elements"] += els
        have["names"] += chunk
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(have, f, ensure_ascii=False)
        print("fetched", i + len(chunk), "/", len(todo), flush=True)
        time.sleep(3)


if __name__ == "__main__":
    main()
