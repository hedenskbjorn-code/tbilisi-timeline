"""Candidates for the layer "Local names" (data/raw/osm_extra/places.json, tools/fetch_places_osm.py). A place gets into the list when OSM links it to a Wikipedia / Wikidata article or says whom / what the
name comes from (name:etymology*): without an article or a text of the encyclopedia there is nothing that could be quoted about the name. The elements that are parts of one object (the bridge in four pieces)
are joined by the name and the kind; the point is the centre of the biggest piece. Kinds: district (a quarter, a suburb, a village inside the city, a district), garden (a park, a garden, a square park), hill (a peak, a hill),
market, bath, bridge, cemetery. The city blocks (place=city_block) and the unnamed objects are not taken.
Output: data/cache/places_candidates.json (list of {key, kind, name{ka,ru,en}, lon, lat, osm [type/id], wikidata, wikipedia, etym}), data/cache/places_candidates.md (the table for a look).
Usage: python -P tools/places_candidates.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def kind(t):
    if t.get("place") in ("suburb", "neighbourhood", "quarter", "locality", "borough"):
        return "district"
    if t.get("leisure") in ("park", "garden"):
        return "garden"
    if t.get("natural") in ("peak", "hill", "ridge", "valley", "cliff"):
        return "hill"
    if t.get("amenity") == "marketplace":
        return "market"
    if t.get("amenity") == "public_bath" or t.get("historic") in ("bath", "bathhouse") or t.get("building") == "bathhouse":
        return "bath"
    if t.get("bridge") or t.get("man_made") == "bridge" or t.get("historic") == "bridge":
        return "bridge"
    if t.get("landuse") == "cemetery" or t.get("amenity") == "grave_yard":
        return "cemetery"
    return None


def size(e):
    b = e.get("bounds")
    return abs((b["maxlat"] - b["minlat"]) * (b["maxlon"] - b["minlon"])) if b else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    els = json.load(open(os.path.join(R, "data", "raw", "osm_extra", "places.json"), encoding="utf-8"))["elements"]
    groups = {}
    for e in els:
        t = e.get("tags", {})
        k = kind(t)
        nm = t.get("name:ka") or t.get("name")
        if not k or not nm or t.get("place") == "city_block":
            continue
        c = e.get("center") or ({"lat": e["lat"], "lon": e["lon"]} if "lat" in e else None)
        if not c:
            continue
        groups.setdefault((k, nm.strip()), []).append((e, c))
    out = []
    for (k, nm), lst in sorted(groups.items()):
        e, c = max(lst, key=lambda x: size(x[0]))
        tags = {}
        for x, _ in lst:                                            # the tags of all pieces: one of them may carry the link
            for a, b in x["tags"].items():
                tags.setdefault(a, b)
        etym = {a: b for a, b in tags.items() if a.startswith("name:etymology")}
        if not (tags.get("wikidata") or tags.get("wikipedia") or etym):
            continue
        out.append({"key": "%s:%s/%s" % (k, e["type"][0], e["id"]), "kind": k, "name": {"ka": nm, "ru": tags.get("name:ru", ""), "en": tags.get("name:en", "")},
                    "lon": round(c["lon"], 5), "lat": round(c["lat"], 5), "osm": ["%s/%s" % (x["type"], x["id"]) for x, _ in lst],
                    "wikidata": tags.get("wikidata", ""), "wikipedia": tags.get("wikipedia", ""), "etym": etym})
    json.dump(out, open(os.path.join(R, "data", "cache", "places_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import collections
    print("candidates:", len(out), dict(collections.Counter(x["kind"] for x in out)))
    L = ["| kind | ka | ru | en | wikidata | wikipedia | etymology tag |", "|---|---|---|---|---|---|---|"]
    for x in out:
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (x["kind"], x["name"]["ka"], x["name"]["ru"], x["name"]["en"], x["wikidata"], x["wikipedia"], "yes" if x["etym"] else ""))
    open(os.path.join(R, "data", "cache", "places_candidates.md"), "wb").write(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
