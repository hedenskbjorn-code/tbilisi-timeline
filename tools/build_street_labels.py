"""Geometry for the historical street-name labels on the map: for every street or square of site/data/street_names.json (names checked on Wikipedia)
take the OpenStreetMap ways (Overpass, ODbL; fetched once into data/raw/osm_transport/street_labels.json, not committed) and write site/data/street_geom.json:
{"<English name today>": GeoJSON geometry (MultiLineString, or Point for squares)}.
Usage: python tools/build_street_labels.py
"""
import json
import math
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
    # 1.8.2: the streets whose names the articles of Wikipedia give with years (the OSM names are the same as today's English ones, except Rustaveli)
    "Lado Asatiani Street": "Lado Asatiani Street", "Shalva Dadiani Street": "Shalva Dadiani Street", "Lado Gudiashvili Street": "Lado Gudiashvili Street",
    "Kote Abkhazi Street": "Kote Abkhazi Street", "Galaktion Tabidze Street": "Galaktion Tabidze Street", "Shota Rustaveli Avenue": "Shota Rustaveli Avenue",
    "Mikheil Burdzgla Street": "Mikheil Burdzgla Street", "Sulkhan Tsintsadze Street": "Sulkhan Tsintsadze Street",
}
# OSM holds namesakes in other districts (a Lado Asatiani Street in seven places): for these streets only the chain of ways near the historical place is kept
NEAR = {
    "Lado Asatiani Street": (41.6897, 44.8008), "Galaktion Tabidze Street": (41.6913, 44.8012), "Lado Gudiashvili Street": (41.6961, 44.8011),
    "Kote Abkhazi Street": (41.6920, 44.8055), "Sulkhan Tsintsadze Street": (41.7216, 44.7634), "Mikheil Burdzgla Street": (41.7232, 44.7611),
}
NEAR_M = 1500
MORE_NAMES = ["Lado Asatiani Street", "Lado Gudiashvili Street", "Kote Abkhazi Street", "Galaktion Tabidze Street", "Mikheil Burdzgla Street", "Sulkhan Tsintsadze Street"]
MORE_KA = ["ლადო ასათიანის ქუჩა", "ლადო გუდიაშვილის ქუჩა", "კოტე აფხაზის ქუჩა", "გალაკტიონ ტაბიძის ქუჩა", "გალაქტიონ ტაბიძის ქუჩა", "მიხეილ ბურძგლას ქუჩა", "სულხან ცინცაძის ქუჩა"]
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


def fetch_more():
    """The streets of 1.8.2 (the first fetch above knows the older ones); cached in data/raw/osm_transport/street_labels_more.json, not committed."""
    p = os.path.join(RAW, "street_labels_more.json")
    if os.path.exists(p):
        return
    q = '[out:json][timeout:180];(way["highway"]["name:en"~"^(%s)$"]%s;way["highway"]["name"~"^(%s)$"]%s;);out geom tags;' % ("|".join(MORE_NAMES), B, "|".join(MORE_KA), B)
    for k in range(5):
        try:
            d = urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(),
                                                              headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=240).read()
            json.loads(d)
            open(p, "wb").write(d)
            return
        except Exception as e:
            print("retry", str(e)[:60], flush=True)
            time.sleep(25 * (k + 1))
    sys.exit("giving up")


def near(chains, lat, lon):
    """The chains whose centre lies within NEAR_M metres of the point (a namesake in another district is dropped)."""
    keep = []
    for c in chains:
        la = sum(p[1] for p in c) / len(c)
        lo = sum(p[0] for p in c) / len(c)
        if math.hypot((lo - lon) * 83000, (la - lat) * 111000) <= NEAR_M:
            keep.append(c)
    return keep


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


def kv_geometry(out):
    """The streets renamed in 1988-1991 (tools/streets_kv_spec.json): the OSM ways are found by the Georgian name of today; the namesakes in other districts are dropped
    by the point of the spec (NEAR_M metres), 'all' keeps every chain (a long avenue), a square becomes a point. Cache: data/raw/osm_transport/street_labels_kv.json, not committed."""
    sp, byka = [], {}
    for n in ("", "2", "3", "4"):  # the batches of 1.8.2, 1.8.3 and 1.8.4
        sp += json.load(open(os.path.join(ROOT, "tools", "streets_kv%s_spec.json" % n), encoding="utf-8"))["spec"]
        for e in json.load(open(os.path.join(RAW, "street_labels_kv%s.json" % n), encoding="utf-8"))["elements"]:
            if e["type"] == "way" and e.get("geometry") and e["tags"].get("name"):
                byka.setdefault(e["tags"]["name"], {})[e["id"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    for s in sp:
        w = byka.get(s.get("osm_ka") or s["now"]["ka"])
        if not w:
            print("NO WAYS (kv):", s["key"])
            continue
        chains = join(w.values())
        if s["near"] not in (None, "all"):
            chains = near(chains, *s["near"])
        if s["key"].endswith("Square"):
            pts = [p for c in chains for p in c]
            out[s["key"]] = {"type": "Point", "coordinates": [round(sum(p[0] for p in pts) / len(pts), 5), round(sum(p[1] for p in pts) / len(pts), 5)]}
        else:
            out[s["key"]] = {"type": "MultiLineString", "coordinates": chains}


def enc_geometry(out):
    """The streets of the encyclopedia (tools/streets_enc1_spec.json, made by tools/build_enc_spec.py): the OSM ways by the Georgian name (osm_ka); a namesake in another place is dropped by the point
    of the spec (NEAR_M metres), 'all' keeps every chain. The key of the geometry is spec.geom. Cache: data/raw/osm_transport/street_labels_enc.json, not committed."""
    sp_path = os.path.join(ROOT, "tools", "streets_enc1_spec.json")
    if not os.path.exists(sp_path):
        return
    sp = json.load(open(sp_path, encoding="utf-8"))["spec"]
    byka = {}
    for e in json.load(open(os.path.join(RAW, "street_labels_enc.json"), encoding="utf-8"))["elements"]:
        if e["type"] == "way" and e.get("geometry") and e["tags"].get("name"):
            byka.setdefault(e["tags"]["name"], {})[e["id"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    for s in sp:
        if s.get("nogeom"):                                    # no usable line in OSM: the street has the card and the search only
            continue
        w = byka.get(s["osm_ka"])
        if not w:
            print("NO WAYS (enc):", s["geom"])
            continue
        chains = join(w.values())
        if s["near"] not in (None, "all"):
            chains = near(chains, *s["near"])
        out[s["geom"]] = {"type": "MultiLineString", "coordinates": chains}


def square_geometry(out):
    """the points of the squares that have no line in OSM (tools/square_points.py made tools/square_points.json: the way of every position is in it)"""
    p = os.path.join(ROOT, "tools", "square_points.json")
    if not os.path.exists(p):
        return
    for key, v in json.load(open(p, encoding="utf-8")).items():
        out[key] = {"type": "Point", "coordinates": [v["lon"], v["lat"]]}


def main():
    fetch()
    fetch_more()
    ways = {}
    for fn in ("street_labels", "street_labels_more", "tram_streets", "avenues", "rustaveli"):
        fp = os.path.join(RAW, fn + ".json")
        if not os.path.exists(fp):
            continue
        for e in json.load(open(fp, encoding="utf-8"))["elements"]:
            nm = e.get("tags", {}).get("name:en")
            if nm and e.get("geometry") and e["type"] == "way":
                ways.setdefault(nm, {})[e["id"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    kaw = {}
    for fn in ("street_labels", "street_labels_more"):
        for e in json.load(open(os.path.join(RAW, fn + ".json"), encoding="utf-8"))["elements"]:
            if e["type"] == "way" and e.get("geometry") and e["tags"].get("name"):
                kaw.setdefault(e["tags"]["name"], {})[e["id"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    kamap = {x["now"]["en"]: x["now"]["ka"] for x in json.load(open(os.path.join(ROOT, "site", "data", "street_names.json"), encoding="utf-8"))["streets"]}
    out = {}
    for now, osm in OSM.items():
        w = ways.get(osm) or kaw.get(kamap.get(now))
        if w:
            chains = join(w.values())
            if now in NEAR:
                chains = near(chains, *NEAR[now])
            out[now] = {"type": "MultiLineString", "coordinates": chains}
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
    kv_geometry(out)
    enc_geometry(out)
    square_geometry(out)
    json.dump(out, open(os.path.join(ROOT, "site", "data", "street_geom.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(len(out), "geometries")


if __name__ == "__main__":
    main()
