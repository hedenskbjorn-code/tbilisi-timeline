"""Points of the places of the folk names that have no object in data/places.json (tools/apply_folk.py makes them places of their own). Only the places that an OSM object names clearly are placed:
the OSM object is the square / market / quarter whose official name is the one that the answer of Gemini gives (the "official" field of work/gemini/results/folk.json; the centre of the object is looked up by
its id through Nominatim /lookup). The folk names whose object the sources do not name as a point or an area (streets, a district of a few streets, a building without an OSM object under its name) are not placed:
they are listed in data/cache/folk_points.json under "unplaced". Output: data/cache/folk_points.json. Usage: python -P tools/folk_points.py
"""
import json
import os
import sys
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; read-only API client)"}
# index of the row of results/folk.json -> (OSM object, kind of the place); the rows 7 and 8 name the same square
PLACE = {0: ("R16393287", "district"), 1: ("R15399106", "district"), 5: ("W1056991782", "square"), 7: ("W1476800521", "square"), 8: ("W1476800521", "square"), 9: ("W1217904106", "square"),
         12: ("W1269152262", "building"), 13: ("W1157074584", "building"), 18: ("W62646483", "market"), 20: ("R14154210", "district"), 23: ("N4756361456", "district")}
# the rows that tools/verify_folk_points.py accepted (an answer of Gemini about the place, checked): they join PLACE; a district of several streets ("area") is put on one of the streets: APPROX
APPROX = set()
_v = os.path.join(R, "data", "cache", "folk_points_verified.json")
if os.path.exists(_v):
    for _row, _x in json.load(open(_v, encoding="utf-8"))["ok"].items():
        PLACE[int(_row)] = (_x["osm"], {"building": "building", "market": "market", "area": "district", "square": "square"}[_x["kind"]])
        if _x["approx"]:
            APPROX.add(int(_row))
TO_PLACE = {10: "bridge-w1271777826", 14: "district-r2185664", 16: "bridge-w370148693", 19: "garden-w56677922"}   # rows whose object is already in places.json (their "ref")
# the official name of the place where the answer gives that of a larger object: Nakhalovka is the Old Nadzaladevi (the quotation of ru.wikipedia: the first building became known as "old Nadzaladevi"), a quarter of OSM
# around the railway station (the point of the district Nadzaladevi, 41.747 / 44.821, lies 2 km away, towards the Tbilisi Sea)
NAME = {0: {"ka": "ძველი ნაძალადევი", "ru": "Старый Надзаладеви", "en": "Old Nadzaladevi"}}
TO_MODERN = {17: "Palace of Rituals"}
FORMER = {15: "Maidan is a former OFFICIAL name of Vakhtang Gorgasali Square (the street lists of 1903 and 1940 in the encyclopedia), not a folk name: it is not shown in this layer"}      # rows the sources show to be something else than a folk name                                      # the row is a card of the layer of modernism


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = json.load(open(os.path.join(R, "work", "gemini", "results/folk.json"), encoding="utf-8"))
    ids = ",".join(sorted({v[0] for v in PLACE.values()}))
    d = json.load(urllib.request.urlopen(urllib.request.Request("https://nominatim.openstreetmap.org/lookup?format=jsonv2&osm_ids=" + ids, headers=UA), timeout=60))
    found = {x["osm_type"][0].upper() + str(x["osm_id"]): x for x in d}
    out = {"points": {}, "unplaced": []}
    for oid in {v[0] for v in PLACE.values()}:
        x = found.get(oid)
        if not x:
            print("NOT FOUND", oid)
            continue
        out["points"][oid] = {"lat": float(x["lat"]), "lon": float(x["lon"]), "osm_name": x["display_name"].split(",")[0]}
        print(oid, out["points"][oid])
    for i, r in enumerate(rows):
        if r["adult"] != "none":
            print("left out (rude):", i, r["folk"])
        elif i in FORMER:
            print("left out:", i, FORMER[i])
        elif i not in PLACE and i not in TO_PLACE and i not in TO_MODERN:
            out["unplaced"].append({"row": i, "folk": r["folk"], "official": r["official"]})
    json.dump(out, open(os.path.join(R, "data", "cache", "folk_points.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("unplaced:", [(u["row"], u["folk"].get("ka") or u["folk"].get("ru")) for u in out["unplaced"]])


if __name__ == "__main__":
    main()
