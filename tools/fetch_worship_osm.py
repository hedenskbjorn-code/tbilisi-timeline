"""All the places of worship of OpenStreetMap inside Tbilisi with ALL their tags: amenity=place_of_worship and building=church / chapel / cathedral / monastery / mosque / synagogue / temple.
Output: data/raw/osm_extra/worship_full.json (the answer of Overpass: out center tags). Licence: (c) OpenStreetMap contributors, ODbL 1.0. A generic User-Agent. Usage: python -P tools/fetch_worship_osm.py
"""
import collections
import json
import os
import sys
import time
import urllib.parse
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BBOX = "41.62,44.66,41.86,45.02"
QL = '[out:json][timeout:180];(nwr["amenity"="place_of_worship"](%s);nwr["building"~"^(church|chapel|cathedral|monastery|mosque|synagogue|temple)$"](%s);nwr["historic"~"^(church|monastery)$"](%s););out center tags;' % (BBOX, BBOX, BBOX)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data = urllib.parse.urlencode({"data": QL}).encode()
    for k in range(5):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=240))
            break
        except Exception as e:
            print("retry:", str(e)[:60], flush=True)
            time.sleep(20 * (k + 1))
    else:
        raise SystemExit("overpass failed")
    p = os.path.join(R, "data", "raw", "osm_extra", "worship_full.json")
    json.dump(r, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    els = r["elements"]
    print("elements:", len(els))
    c = collections.Counter(e["tags"].get("denomination") or "-" for e in els)
    print("denominations:", c.most_common(12))
    print("religion:", collections.Counter(e["tags"].get("religion") or "-" for e in els))
    for key in ("name", "name:ka", "name:ru", "name:en", "start_date", "wikidata", "wikipedia", "wikimedia_commons", "image", "ruins", "disused", "abandoned", "historic", "building"):
        print("  %-18s %d" % (key, sum(1 for e in els if e["tags"].get(key))))


if __name__ == "__main__":
    main()
