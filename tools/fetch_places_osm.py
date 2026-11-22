"""Candidates for the layer of local names: the named places of Tbilisi from OpenStreetMap (Overpass API): the quarters (place=suburb|neighbourhood|quarter|locality), the parks and gardens, the hills and
peaks, the markets, the baths, the bridges. Licence: (c) OpenStreetMap contributors, ODbL 1.0 (the same attribution wherever the data is republished). A generic User-Agent, no personal data.
Output: data/raw/osm_extra/places.json (the answer of Overpass as it is: "out center tags"). Usage: python -P tools/fetch_places_osm.py
"""
import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"
BBOX = "41.62,44.66,41.86,45.02"
QL = """[out:json][timeout:180];
(
  nwr["place"~"^(suburb|neighbourhood|quarter|locality|borough|city_block)$"]["name"](%(b)s);
  nwr["leisure"~"^(park|garden)$"]["name"](%(b)s);
  nwr["natural"~"^(peak|hill|ridge|valley|cliff|spring)$"]["name"](%(b)s);
  nwr["amenity"~"^(marketplace|public_bath)$"]["name"](%(b)s);
  nwr["historic"~"^(bath|bathhouse|fountain|city_gate|tower)$"]["name"](%(b)s);
  nwr["building"="bathhouse"]["name"](%(b)s);
  way["bridge"]["highway"]["name"](%(b)s);
  way["man_made"="bridge"]["name"](%(b)s);
  nwr["landuse"~"^(cemetery|recreation_ground)$"]["name"](%(b)s);
  nwr["amenity"="grave_yard"]["name"](%(b)s);
);
out center tags;""" % {"b": BBOX}


def main():
    data = urllib.parse.urlencode({"data": QL}).encode()
    for k in range(5):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": UA}), timeout=240))
            break
        except Exception as e:
            print("retry:", e, flush=True)
            time.sleep(15 * (k + 1))
    else:
        raise SystemExit("overpass failed")
    p = os.path.join(ROOT, "data", "raw", "osm_extra", "places.json")
    json.dump(r, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    print("elements:", len(r["elements"]), "| bytes:", os.path.getsize(p))


if __name__ == "__main__":
    main()
