"""Geometry for the historical street-name labels on the map: for every street or square of site/data/street_names.json (names checked on Wikipedia)
take the OpenStreetMap ways (Overpass, ODbL; fetched once into data/raw/osm_transport/street_labels.json, not committed) and write site/data/street_geom.json:
{"<English name today>": GeoJSON geometry (MultiLineString, or Point for squares)}.
Usage: python tools/build_street_labels.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "raw", "osm_transport")
B = "(41.60,44.66,41.86,45.02)"
# today's English name -> OSM name:en used for the geometry
OSM = {
    "David Aghmashenebeli Avenue": "David Aghmashenebeli Avenue", "Vakhtang Gorgasali Street": "Vakhtang Gorgasali Street", "Vasil Barnov Street": "Vasil Barnov Street",
    "Ilia Chavchavadze Avenue": "Ilia Chavchavadze Avenue", "Dimitri Uznadze Street": "Dimitri Uznadze Street", "Tsotne Dadiani Street": "Tsotne Dadiani Street",
    "Ivane Javakhishvili Street": "Ivane Javakhishvili Street", "Merab Kostava Street": "Merab Kostava Street", "Egnate Ninoshvili Street": "Egnate Ninoshvili Street",
    "Mikheil Javakhishvili Street": "Mikheil Javakhishvili Street", "Ketevan Dedoplis Avenue": "Tsminda Ketevan Dedoflis Avenue", "Tevdore Mghvdeli Street": "Tevdore Mghvdeli Street",
    "Giorgi Tsabadze Street": "Giorgi Tsabadze Street", "Atsquri Street": "Atsquri Street", "Giorgi Chitaia Street": "Giorgi Chitaia Street",
    "Revaz Tabukashvili Street": "Revaz Tabukashvili Street", "Navtlughi Street": "Navtlughi Street",
}
SQUARES = {"Freedom Square": "Freedom Square", "First Republic Square": "First Republic Square"}


def fetch():
    p = os.path.join(RAW, "street_labels.json")
    if os.path.exists(p):
        return
    names = "|".join(sorted(set(OSM.values()) | set(SQUARES.values())))
    sn = json.load(open(os.path.join(ROOT, "site", "data", "street_names.json"), encoding="utf-8"))["streets"]
    ka = "|".join(x["now"]["ka"] for x in sn if x["now"]["en"] in OSM)
    q = '[out:json][timeout:180];(way["highway"]["name:en"~"^(%s)$"]%s;way["highway"]["name"~"^(%s)$"]%s;);out geom tags;nwr["name:en"~"^(Freedom Square|First Republic Square|Republic Square)$"]%s;out center tags;' % (names, B, ka, B, B)
    for k in range(5):
        try:
            d = urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(),
                                                              headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=240).read()
            open(p, "wb").write(d)
            return
        except Exception as e:
            print("retry", str(e)[:60], flush=True)
            time.sleep(25 * (k + 1))
    sys.exit("giving up")


def join(lines):
    """Chain OSM ways that share end points into longer lines (a label along a line needs a line longer than the text)."""
    lines = [list(l) for l in lines]
    changed = True
    while changed:
        changed = False
        for i in range(len(lines)):
            for j in range(len(lines)):
                if i == j or not lines[i] or not lines[j]:
                    continue
                a, b = lines[i], lines[j]
                if a[-1] == b[0]:
                    lines[i] = a + b[1:]
                elif a[-1] == b[-1]:
                    lines[i] = a + b[::-1][1:]
                elif a[0] == b[-1]:
                    lines[i] = b + a[1:]
                elif a[0] == b[0]:
                    lines[i] = b[::-1] + a[1:]
                else:
                    continue
                lines[j] = []
                changed = True
    return [l for l in lines if l]


def main():
    fetch()
    ways = {}
    for fn in ("street_labels", "tram_streets", "avenues", "rustaveli"):
        fp = os.path.join(RAW, fn + ".json")
        if not os.path.exists(fp):
            continue
        for e in json.load(open(fp, encoding="utf-8"))["elements"]:
            nm = e.get("tags", {}).get("name:en")
            if nm and e.get("geometry") and e["type"] == "way":
                ways.setdefault(nm, {})[e["id"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    kaw = {}
    for e in json.load(open(os.path.join(RAW, "street_labels.json"), encoding="utf-8"))["elements"]:
        if e["type"] == "way" and e.get("geometry") and e["tags"].get("name"):
            kaw.setdefault(e["tags"]["name"], {})[e["id"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    kamap = {x["now"]["en"]: x["now"]["ka"] for x in json.load(open(os.path.join(ROOT, "site", "data", "street_names.json"), encoding="utf-8"))["streets"]}
    out = {}
    for now, osm in OSM.items():
        w = ways.get(osm) or kaw.get(kamap.get(now))
        if w:
            out[now] = {"type": "MultiLineString", "coordinates": join(w.values())}
        else:
            print("NO WAYS:", now)
    cent = {}
    for e in json.load(open(os.path.join(RAW, "street_labels.json"), encoding="utf-8"))["elements"]:
        nm = e.get("tags", {}).get("name:en")
        if nm in ("Freedom Square", "First Republic Square", "Republic Square"):
            c = e.get("center") or (e.get("lat") and {"lat": e["lat"], "lon": e["lon"]})
            if c:
                cent.setdefault(nm, []).append(c)
    for now in SQUARES:
        cs = cent.get(now) or (cent.get("Republic Square") if now == "First Republic Square" else None)
        if cs:
            c = cs[0]
            out[now] = {"type": "Point", "coordinates": [round(c["lon"], 5), round(c["lat"], 5)]}
        else:
            print("NO POINT:", now)
    json.dump(out, open(os.path.join(ROOT, "site", "data", "street_geom.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(len(out), "geometries")


if __name__ == "__main__":
    main()
