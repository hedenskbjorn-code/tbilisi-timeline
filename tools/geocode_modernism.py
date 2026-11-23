"""Coordinates of the verified buildings of Soviet modernism (data/cache/modernism_verified.json, made by tools/verify_modernism.py).
Order of sources (every coordinate keeps its origin in "how"): 1. Wikidata P625 of the item named in the answer; 2. the coordinates of the Wikipedia article named in a source of the building
(action=query&prop=coordinates, the wiki of the url); 3. OpenStreetMap by the name through Overpass (an object of the city whose name/name:en/name:ru/name:ka equals one of the names).
A point outside the city (district polygons of tools/build_enc_spec) is dropped. Output: data/cache/modernism_geo.json ({index: {lat, lon, how, ref}}); the buildings without a point are printed.
Only public read-only API calls with the generic User-Agent. Usage: python -P tools/geocode_modernism.py
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; read-only API client)"}
BOX = (41.60, 44.65, 41.86, 45.05)                    # south, west, north, east: a rough frame only; the exact test is the city polygon below


def get(url, data=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:                           # noqa: BLE001 - a network error: wait and retry
            print("   retry", i + 1, str(e)[:80], flush=True)
            time.sleep(8 * (i + 1))
    return None


def wikidata(q):
    d = get("https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims&ids=%s&format=json" % q)
    try:
        v = d["entities"][q]["claims"]["P625"][0]["mainsnak"]["datavalue"]["value"]
        return v["latitude"], v["longitude"]
    except (TypeError, KeyError, IndexError):
        return None


def wikipedia(url):
    m = re.match(r"https://(\w+)\.wikipedia\.org/wiki/(.+)", url)
    if not m:
        return None
    d = get("https://%s.wikipedia.org/w/api.php?action=query&prop=coordinates&titles=%s&format=json&redirects=1" % (m.group(1), m.group(2)))
    for p in ((d or {}).get("query") or {}).get("pages", {}).values():
        c = (p.get("coordinates") or [None])[0]
        if c:
            return c["lat"], c["lon"]
    return None


def overpass(names):
    nm = "|".join(re.escape(n) for n in names if n)
    q = '[out:json][timeout:60];nwr["name"~"^(%s)$"](%s,%s,%s,%s);out center 5;' % (nm, *BOX)
    d = None
    for host in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):          # a mirror when the main server answers 502
        d = get(host, data=urllib.parse.urlencode({"data": q}).encode(), tries=2)
        if d:
            break
    for e in (d or {}).get("elements", []):
        c = e.get("center") or e
        if "lat" in c:
            return c["lat"], c["lon"], e["type"][0] + str(e["id"])
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import build_enc_spec as B                            # the polygons of the districts of the city
    polys = [r for rs in B.polygons().values() for r in rs]
    rows = json.load(open(os.path.join(R, "data", "cache", "modernism_verified.json"), encoding="utf-8"))["ok"]
    out = {}
    for i, b in enumerate(rows):
        n = b["name"]
        pt = None
        if b.get("wikidata"):
            c = wikidata(b["wikidata"])
            if c:
                pt = {"lat": c[0], "lon": c[1], "how": "wikidata", "ref": b["wikidata"]}
                if round(c[0], 3) == c[0] and round(c[1], 3) == c[1]:
                    pt["rough"] = True                    # given to 2-3 decimals only (about 1 km): OSM is asked as well and wins when it has the object
        if not pt:
            for s in b["sources"]:
                c = wikipedia(s["url"])
                if c:
                    pt = {"lat": c[0], "lon": c[1], "how": "wikipedia", "ref": s["url"]}
                    break
        if not pt or pt.get("rough"):
            c = overpass([n["en"], n["ru"], n["ka"]])
            if c:
                pt = {"lat": c[0], "lon": c[1], "how": "osm", "ref": c[2]}
            elif pt:
                print("   rough point kept")
        if pt and not any(B.inside((pt["lon"], pt["lat"]), r) for r in polys):
            print("  outside the city:", n["en"], pt)
            pt = None
        out[str(i)] = pt
        print(i, n["en"][:60], "->", pt and (round(pt["lat"], 5), round(pt["lon"], 5), pt["how"]), flush=True)
        time.sleep(1)
    json.dump(out, open(os.path.join(R, "data", "cache", "modernism_geo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("without a point:", [rows[int(k)]["name"]["en"] for k, v in out.items() if not v])


if __name__ == "__main__":
    main()
