"""Match register objects (site/data/monuments.json) to Wikipedia articles through Wikidata, so that the card can link to the
article in the interface language.

Candidates: Wikidata items with coordinates inside the Tbilisi box that have an article in ka / en / ru Wikipedia
(query.wikidata.org, one SPARQL request). A register object is linked to the nearest candidate within MAX_M metres only if the
Georgian name of the object and the Georgian label of the item share a DISTINCTIVE word stem (two stems beyond NEAR_M metres) (generic words such as "church" or
"dwelling house" do not count), and the item is not a street, square or quarter. Distance alone is not used: dense old
quarters put several unrelated objects within 40 m of a famous one.

Output: data/wikipedia_links.json  {register_id: {"ka": title, "en": title, "ru": title}}   (read by tools/build_site_data.py)
Objects listed in data/wikipedia_links_reject.json are dropped from the result; data/wikipedia_links_manual.json adds links by hand.
Needs WIKIMEDIA_CONTACT in the environment (never committed).
"""
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAX_M = 80
NEAR_M = 35
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % ("; contact: " + os.environ["WIKIMEDIA_CONTACT"] if os.environ.get("WIKIMEDIA_CONTACT") else "")
QUERY = """SELECT ?item ?c ?ka ?en ?ru ?kaL ?enL WHERE {
 SERVICE wikibase:box { ?item wdt:P625 ?c . bd:serviceParam wikibase:cornerSouthWest "Point(44.66 41.62)"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point(44.98 41.80)"^^geo:wktLiteral }
 OPTIONAL { ?ka schema:about ?item ; schema:isPartOf <https://ka.wikipedia.org/> }
 OPTIONAL { ?en schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
 OPTIONAL { ?ru schema:about ?item ; schema:isPartOf <https://ru.wikipedia.org/> }
 FILTER(BOUND(?ka) || BOUND(?en) || BOUND(?ru))
 OPTIONAL { ?item rdfs:label ?kaL FILTER(LANG(?kaL)="ka") }
 OPTIONAL { ?item rdfs:label ?enL FILTER(LANG(?enL)="en") }
}"""
GENERIC = {"სახლი", "საცხოვრებელი", "ეკლესია", "ტაძარი", "ეკლესიის", "ტაძრის", "მონასტერი", "სამონასტრო", "კომპლექსი", "შენობა", "ნაგებობა",
           "ქუჩა", "ქუჩაზე", "გამზირი", "მოედანი", "უბანი", "თბილისის", "თბილისი", "მდებარე", "ისტორიული", "ძველი", "ახალი", "სასახლე",
           "გიორგი", "გიორგის", "სკოლა", "კაფე", "სინაგოგა", "მეჩეთი", "ბაზილიკა", "წმინდა", "წმ", "წმ.", "ღვთისმშობლის", "ზედა", "ქვედა", "ჯვრის", "მთავარი"}
BAD_LABEL = re.compile(r"(ქუჩა|გამზირი|მოედანი|\(უბანი\)|უბანი|ხეობა|რაიონი|ბულვარი)\s*$")


def tokens(s):
    return [t for t in re.findall(r"[ა-ჿ]{4,}", s or "") if t not in GENERIC]


def same_stem(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n >= 5 and n >= 0.75 * min(len(a), len(b))


def title_of(url):
    return urllib.parse.unquote(url.rsplit("/wiki/", 1)[1]).replace("_", " ") if url else None


def main():
    req = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY, "format": "json"}),
                                 headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    rows = json.load(urllib.request.urlopen(req, timeout=240))["results"]["bindings"]
    items = {}
    for b in rows:
        q = b["item"]["value"].rsplit("/", 1)[1]
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["c"]["value"])
        it = items.setdefault(q, {"q": q, "lng": float(m[1]), "lat": float(m[2]), "links": {}, "kaL": b.get("kaL", {}).get("value", "")})
        for lg in ("ka", "en", "ru"):
            if lg in b:
                it["links"][lg] = title_of(b[lg]["value"])
    cand = [it for it in items.values() if not BAD_LABEL.search(it["kaL"])]
    K = 111320 * math.cos(math.radians(41.7))
    mon = json.load(open(os.path.join(ROOT, "site", "data", "monuments.json"), encoding="utf-8"))["features"]
    out, log = {}, []
    for f in mon:
        p = f["properties"]
        ta = tokens(p["name"])
        if not ta:
            continue
        c = f["geometry"]["coordinates"]
        best = None
        for it in cand:
            d = math.hypot((c[0] - it["lng"]) * K, (c[1] - it["lat"]) * 111190)
            if d > MAX_M or (best and d >= best[0]):
                continue
            tb = tokens(it["kaL"]) + tokens(it["links"].get("ka", ""))
            hits = sum(1 for x in ta if any(same_stem(x, y) for y in tb))
            if hits >= (1 if d <= NEAR_M else 2):          # far matches need two shared distinctive words
                best = (d, it)
        if best:
            out[str(p["id"])] = best[1]["links"]
            log.append((round(best[0]), p["name"], best[1]["kaL"], best[1]["q"]))
    rej = os.path.join(ROOT, "data", "wikipedia_links_reject.json")                # links the owner / review rejected: never put back
    if os.path.exists(rej):
        for i in json.load(open(rej, encoding="utf-8"))["ids"]:
            out.pop(i, None)
    man = os.path.join(ROOT, "data", "wikipedia_links_manual.json")               # links added by hand (the object was not matched, or the match was wrong)
    if os.path.exists(man):
        for i, v in json.load(open(man, encoding="utf-8"))["objects"].items():
            out[i] = {k: t for k, t in v.items() if k in ("ka", "en", "ru")}
    json.dump(out, open(os.path.join(ROOT, "data", "wikipedia_links.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("candidates:", len(cand), "register objects:", len(mon), "linked:", len(out))
    if "--show" in sys.argv:
        for r in log:
            print(r)


if __name__ == "__main__":
    main()
