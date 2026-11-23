"""Points for the buildings that tools/geocode_modernism.py could not place (Wikidata has no coordinates, the exact names are not in OSM). Each point was found by hand and kept with its origin:
the OSM object (looked up by its id through Nominatim /lookup: the centre of the object) whose name or address is that of the building in the sources, or the coordinates printed on a page that is named.
Matches (name or street address in the sources -> OSM object): the Chess Palace named for Gaprindashvili (Kostava Street), the State Concert Hall (1 Melikishvili Avenue), the former Laguna Vere pool,
the Central Bus Station (1 Dimitri Gulia Street), ExpoGeorgia, the Scientific-Technical Library (47 Kostava Street), the Nutsubidze housing (an OSM node of the complex "Shatili", Ermile Bedia Street; a file of Commons
named "Houses with bridges on the Nutsubidze Slope" is geotagged 15 m from it). The archaeological museum: the coordinates printed on the Atlas Obscura page named in its sources.
The result is merged into data/cache/modernism_geo.json (made by tools/geocode_modernism.py). Usage: python -P tools/modernism_points.py
"""
import json
import os
import sys
import time
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; read-only API client)"}
BY_OSM = {"2": "N6213121286", "4": "W1278771525", "6": "W58071533", "8": "R18129586", "11": "W34149222", "12": "N10222031845", "13": "R18138143"}
BY_PAGE = {"3": (41.763788, 44.766703, "https://www.atlasobscura.com/places/museum-of-archaeology-landmarks-of-tbilisi")}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = os.path.join(R, "data", "cache", "modernism_geo.json")
    geo = json.load(open(p, encoding="utf-8"))
    ids = ",".join(BY_OSM.values())
    d = json.load(urllib.request.urlopen(urllib.request.Request("https://nominatim.openstreetmap.org/lookup?format=jsonv2&osm_ids=" + ids, headers=UA), timeout=60))
    found = {x["osm_type"][0].upper() + str(x["osm_id"]): x for x in d}
    for k, oid in BY_OSM.items():
        x = found.get(oid)
        if x:
            geo[k] = {"lat": float(x["lat"]), "lon": float(x["lon"]), "how": "osm", "ref": oid.lower()}
            print(k, oid, geo[k]["lat"], geo[k]["lon"], x["display_name"][:70])
        else:
            print(k, oid, "NOT FOUND")
    for k, (la, lo, ref) in BY_PAGE.items():
        geo[k] = {"lat": la, "lon": lo, "how": "page", "ref": ref}
    json.dump(geo, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("without a point:", [k for k, v in geo.items() if not v])
    time.sleep(0)


if __name__ == "__main__":
    main()
