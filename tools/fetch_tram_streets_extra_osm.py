"""Streets of tram routes that the first query (fetch_tram_streets_osm.py) did not have: Revaz Uridia (route 6 and 2, between Tsotne Dadiani and Nikoloz Kakhiani), Richard Holbrooke
(route 7, between Navtlughi and Beri Gabriel Salosi), Bogdan Khmelnitski (route 7, to the aviation plant); the routes are from ru.wikiroutes.info (a wiki edited by users, 2021, no sources named).
Overpass (ODbL). Output: data/raw/osm_transport/tram_streets_extra.json (not committed).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "raw", "osm_transport", "tram_streets_extra.json")
B = "(41.60,44.66,41.86,45.02)"
Q = '[out:json][timeout:180];(way["highway"]["name:en"~"Uridia|Holbrook|Chodrishvili|Makhaldiani|Rkinigza",i]%s;way["highway"]["name"~"ურიდია|ჰოლბრუკ|ჩოდრიშვილ|მახალდიან|რკინიგზის ქ"]%s;);out geom tags;' % (B, B)


def main():
    if os.path.exists(OUT):
        print("exists")
        return
    for k in range(5):
        try:
            d = urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": Q}).encode(),
                                                               headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=240).read()
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            open(OUT, "wb").write(d)
            print(len(json.loads(d)["elements"]), "ways")
            return
        except Exception as e:
            print("retry", str(e)[:60], flush=True)
            time.sleep(25 * (k + 1))
    sys.exit("giving up")


if __name__ == "__main__":
    main()
