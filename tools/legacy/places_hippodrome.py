"""The entry of the former hippodrome of Saburtalo (the Delisi / Old Hippodrome, now the territory of the Central Park) for the layer "Local names": tools/places_manual.json.
The contour is the OSM relation 1723955 (landuse=construction, name "Central Park", was:leisure=sports_centre, was:sport=horse_racing; data/raw/osm_extra/hippodrome_central_park.json); the facts and the quotes
are from the page https://georgia.travel/family-attractions/tbilisi-hippodrome (read 2026-11-23; the quotes stand on the page verbatim, tests/check_data.mjs and this script check them again when the page is
reachable). The closing year of the races is not in the sources and is not given. The Georgian text comes from tools/places_manual_ka.json (the answer of Gemini). Usage: python -P tools/places_hippodrome.py
"""
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_districts import assemble, centroid, inside, signed_area  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
URL = "https://georgia.travel/family-attractions/tbilisi-hippodrome"
QUOTES = [
    "The Old Hippodrome, also called “Delisi Hippodrome,” is located in the Saburtalo district, along Tamarashvili Street.",
    "In the 1840s, the Didube Hippodrome opened, serving as the main hub for horse riders for over a century, until the opening of the Delisi Hippodrome in 1959.",
    "In 1995, the area was privatized and became the property of Jockey Club Inc.",
    "In 2007, the so-called “New Hippodrome” opened near Lisi Lake, and heavy construction started around the Old Hippodrome, significantly reducing the forest cover. By 2009, most of the concrete stands had been removed, as their fragility posed a public danger.",
    "In 2020, the “Cartu Fund” purchased a large part of the hippodrome space from private owners and donated it to the city.",
    "Historical sources attest that the hippodrome was initially even larger, spanning 57 hectares and bordered by the Vera Valley.",
]


def page_text(u):
    try:
        h = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}), timeout=60).read().decode("utf-8", "replace")
    except Exception:
        return None
    import html
    h = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t = page_text(URL)
    if t is None:
        print("the page cannot be read: the quotes are not checked now")
    else:
        for q in QUOTES:
            assert q in t, "the quote is not on the page: " + q[:60]
        print("the quotes stand on the page")
    rel = json.load(open(os.path.join(R, "data", "raw", "osm_extra", "hippodrome_central_park.json"), encoding="utf-8"))["elements"][0]
    outer = [[(p["lon"], p["lat"]) for p in m["geometry"]] for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer" and m.get("geometry")]
    rings = assemble(outer)
    assert rings, "no closed ring"
    big = max(rings, key=lambda q: abs(signed_area(q)))
    c = centroid(big)
    if not inside(c, big):
        xs, ys = [p[0] for p in big], [p[1] for p in big]
        c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    area = sum(abs(signed_area(q)) for q in rings) * 83000 * 111000
    print("rings:", len(rings), "| area, ha: %.1f" % (area / 1e4), "| centre:", round(c[1], 5), round(c[0], 5))
    kp = os.path.join(R, "tools", "places_manual_ka.json")
    ka = json.load(open(kp, encoding="utf-8")) if os.path.exists(kp) else {}
    item = {"id": "area-saburtalo-hippodrome", "k": "area", "lon": round(c[0], 5), "lat": round(c[1], 5),
            "n": {"ru": "Бывший Сабурталинский (Делисский) ипподром, территория Центрального парка", "en": "Former Saburtalo (Delisi) Hippodrome, the territory of the Central Park", **({"ka": ka["name"]} if ka else {})},
            "a": {"ru": "Старый ипподром в Сабуртало вдоль улицы Тамарашвили, открыт в 1959 году. В 1995 году территория приватизирована, в 2007 году у озера Лиси открылся «Новый ипподром», к 2009 году большую часть бетонных трибун убрали. В 2020 году фонд «Карту» выкупил значительную часть территории и передал городу; на ней планируется Центральный парк. Год, когда прекратились скачки, в источниках не назван.",
                  "en": "The Old Hippodrome in Saburtalo along Tamarashvili Street, opened in 1959. The area was privatized in 1995, in 2007 the “New Hippodrome” opened near Lisi Lake, and by 2009 most of the concrete stands had been removed. In 2020 the Cartu Foundation bought a large part of the territory and donated it to the city; the Central Park is planned here. The sources do not say in which year the races stopped.",
                  **({"ka": ka["about"]} if ka else {})},
            "e": None, "ne": 1,
            "s": {"l": "en", "u": URL, "aq": QUOTES[1], "eq": None},
            "x": {"q": [{"l": "en", "u": URL, "q": q} for q in QUOTES if q != QUOTES[1]]},
            "g": {"type": "MultiPolygon", "coordinates": [[[[round(x, 5), round(y, 5)] for x, y in q]] for q in rings]}}
    if not ka:
        print("no Georgian text yet (tools/places_manual_ka.json): the item is written without ka and the data check will stop")
    json.dump({"items": [item]}, open(os.path.join(R, "tools", "places_manual.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
