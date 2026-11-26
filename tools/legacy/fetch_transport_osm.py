"""Geometry of transport objects from OpenStreetMap (Overpass API, ODbL): railways (all kinds), funicular / aerialway, and the main avenues.
Output: data/raw/osm_transport/<name>.json (not committed).  Dates are NOT taken from OSM (it has almost none); see data/transport_facts.json.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "raw", "osm_transport")
B = "(41.60,44.66,41.86,45.02)"
QUERIES = {
    "railways": 'way["railway"~"^(rail|tram|subway|funicular|light_rail|narrow_gauge|abandoned|disused|construction|preserved)$"]%s;out geom tags;' % B,
    "stations": 'nwr["railway"~"^(station|halt|tram_stop|subway_entrance)$"]%s;out center tags;' % B,
    "aerialway": 'way["aerialway"]%s;out geom tags;' % B,
    "bridges_all": 'way["bridge"]["highway"]["name"~"Aragvel|Aragvi|Vakhushti|Vakhusht|Gulia|Saarbr|Dochanashvili|Queen Tamar|Tamar|Shalikashvili|Didube|Okoev|Mindeli|ვახუშტი|გულია|ზაარბრიუკენ|თამარ მეფ|შალიკაშვილ|ოქოანთ|არაგველ|გვარამ|Мост"]%s;out geom tags;way["bridge"]["name:en"~"Aragvintsev|Vakhushti|Gulia|Saarbr|Dochanashvili|Queen Tamar|Shalikashvili|Didube|Okoev|Mindeli|Mshrali|Dry Bridge"]%s;out geom tags;' % (B, B),
    "rustaveli": 'way["highway"]["name:en"~"Rustaveli"]%s;out geom tags;' % B,
    "bridges": 'way["bridge"]["name:en"~"Baratashvili|Peace Bridge|Bridge of Peace|Metekhi|Avlabari|Dry Bridge|Vera Bridge|Galaktion"]%s;out geom tags;' % B,
    "avenues": 'way["highway"]["name:en"~"^(Rustaveli Avenue|David Aghmashenebeli Avenue|Ilia Chavchavadze Avenue|Konstantine Kostava Street|Vazha-Pshavela Avenue|Davit Agmashenebeli Avenue|Akaki Tsereteli Avenue|Ketevan Tsamebuli Avenue|Heroes.? Square)$"]%s;out geom tags;' % B,
}


def ov(q):
    for k in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": "[out:json][timeout:180];" + q}).encode(),
                                                                  headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=240).read()
        except Exception as e:
            print("  retry", str(e)[:60], flush=True)
            time.sleep(25 * (k + 1))
    sys.exit("giving up")


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, q in QUERIES.items():
        p = os.path.join(OUT, name + ".json")
        if os.path.exists(p):
            continue
        d = ov(q)
        open(p, "wb").write(d)
        print(name, len(json.loads(d)["elements"]), "elements,", len(d) // 1024, "KB", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
