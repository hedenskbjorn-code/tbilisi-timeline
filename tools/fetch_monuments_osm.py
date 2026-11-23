"""All the monuments, memorials and artworks of OpenStreetMap inside Tbilisi with ALL their tags (the table of the site was built from a selection of them): historic=memorial / monument (not the plaques) and tourism=artwork.
Output: data/raw/osm_extra/monuments_full.json (the answer of Overpass: out center tags). Licence: (c) OpenStreetMap contributors, ODbL 1.0. A generic User-Agent, one request. Usage: python -P tools/fetch_monuments_osm.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BBOX = "41.62,44.66,41.86,45.02"
QL = '[out:json][timeout:180];(nwr["historic"~"^(memorial|monument)$"]["memorial"!="plaque"](%s);nwr["tourism"="artwork"](%s););out center tags;' % (BBOX, BBOX)


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
    p = os.path.join(R, "data", "raw", "osm_extra", "monuments_full.json")
    json.dump(r, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    els = r["elements"]
    print("elements:", len(els), "| bytes:", os.path.getsize(p))
    for key in ("name", "name:ka", "name:ru", "name:en", "start_date", "artist_name", "material", "image", "wikimedia_commons", "wikidata", "wikipedia", "inscription", "description", "subject:wikidata", "artwork_type", "memorial"):
        print("  %-18s %d" % (key, sum(1 for e in els if e.get("tags", {}).get(key))))


if __name__ == "__main__":
    main()
