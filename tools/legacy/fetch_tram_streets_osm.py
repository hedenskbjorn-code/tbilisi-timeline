"""Geometry of the streets on which Tbilisi trams ran (street names from the ka.wikipedia route lists of 1962 and 1986, see data/tram_verified.json).
Overpass (ODbL): all highway ways in the Tbilisi box whose English name matches one of the keys. Output: data/raw/osm_transport/tram_streets.json (not committed).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "raw", "osm_transport", "tram_streets.json")
B = "(41.60,44.66,41.86,45.02)"
KEYS = ("Dadiani|Eristavi|Akaki Tsereteli|Tsabadze|Mghvdeli|Abastumani|Tsinamdzg|Askurava|Chodrishvili|Khudadov|Tseronisi|Akhtala|Kakhiani|Lotkini|Managadze|"
        "Guramishvili|Sarajishvili|Libani|Barisakhos|Anapa|Dedoplis|Navtlughi|Baghdadi|Bagdadi|Khmelnitsk|Salosi|Purtseladze|Atoneli|Italy|Gogiberidze|"
        "Javakhishvili|Constitution|Pirosmani|Kostava|Melikishvili|Chavchavadze|Tamar Mepe|Sheshelidze|Khizanishvili|Beliashvili|Aghmashenebeli|Agmashenebeli|Tbilisi Sea|"
        "Moscow|Vekua|Baratashvili|Khetagurov|Mshrali|Dry Bridge|Saarbr|Chugureti|Didube|Kolmeurneobis|Kolmeurneobis")
KA = "ჩოდრიშვილ|ასკურავა|ბარისახო|იტალიის ქ|კონსტიტუციის|ბაღდადის|ანაპის|ქეთევან დედოფლის|თბილისის ზღვის|5 დეკემბრის|კოლმეურნეობის|ბელიაშვილ|გოგიბერიძ|ხეთაგუროვ|მოსკოვის|ვეკუა"
Q = '[out:json][timeout:180];(way["highway"]["name:en"~"%s",i]%s;way["highway"]["name"~"%s"]%s;);out geom tags;' % (KEYS, B, KA, B)


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
