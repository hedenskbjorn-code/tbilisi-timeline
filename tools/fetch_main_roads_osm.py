"""The geometry of the main roads of Tbilisi (avenues, main streets, highways) for the layer of the main roads: the ways of the named roads in the box of the city, with the geometry.
The list of the names is in the regular expression below (name:en, also the Georgian names for the roads whose English name varies). Overpass (ODbL).
Output: data/raw/osm_roads/main_roads.json (not committed). Usage: python -P tools/fetch_main_roads_osm.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "raw", "osm_roads", "main_roads.json")
B = "(41.60,44.66,41.86,45.02)"
EN = "Vazha|Pshavela|Kostava|Gorgasali|Tsabadze|Cholokashvili|Tsereteli|Melikishvili|Tamar Mepe|Kazbegi|Guramishvili|Dedoplis|Dedoflis|Moscow|Robakidze|Pekini|Gamsakhurdia|Salosi|Baratashvili|Kakheti|Rustavi Highway|Tskneti|Kojori|Pilsudski|Aghmashenebeli|Rustaveli|Chavchavadze|Amirejibi"
KA = "ვაჟა-ფშაველ|კოსტავა|გორგასალ|ცაბაძ|ჩოლოყაშვილ|წერეთლ|მელიქიშვილ|თამარ მეფ|ყაზბეგ|გურამიშვილ|ქეთევან წამებულ|მოსკოვის გამზ|რობაქიძ|პეკინ|გამსახურდია|სალოს|ბარათაშვილ|კახეთის გზატკეცილ|რუსთავის გზატკეცილ|წყნეთის გზატკეცილ|კოჯრის გზატკეცილ|პილსუდსკ|აღმაშენებლის|რუსთაველის გამზ|ჭავჭავაძის გამზ|ამირეჯიბ"
HW = "motorway|trunk|primary|secondary|tertiary|unclassified|residential|pedestrian|motorway_link|trunk_link|primary_link"
Q = '[out:json][timeout:240];(way["highway"~"^(%s)$"]["name:en"~"%s",i]%s;way["highway"~"^(%s)$"]["name"~"%s"]%s;);out geom;' % (HW, EN, B, HW, KA, B)


def main():
    if os.path.exists(OUT):
        print("exists")
        return
    for k in range(5):
        try:
            d = urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": Q}).encode(),
                                                               headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=280).read()
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            open(OUT, "wb").write(d)
            print(len(json.loads(d)["elements"]), "ways")
            return
        except Exception as e:
            print("retry", str(e)[:80], flush=True)
            time.sleep(25 * (k + 1))
    sys.exit("giving up")


if __name__ == "__main__":
    main()
