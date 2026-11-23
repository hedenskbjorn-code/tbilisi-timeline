"""Adds ALL named parks and gardens of OpenStreetMap inside the city to data/places.json (the layer "Local names"): run it after tools/apply_places.py and tools/apply_folk.py (apply_places writes places.json anew).
Before this the layer had only the 10 gardens that have an article of Wikipedia (the layer needs a quotation of an article); a park that OSM names but Wikipedia does not (Vaso Godziashvili Garden, the
former Red Garden, Orbeliani Garden, Pushkin Park, Alphabet Park ...) had no point. Input: data/raw/osm_extra/places.json and squares.json (tools/fetch_places_osm.py; leisure = park | garden with a name;
the centre of the object must lie inside the district polygons of the site). A card has: the name (in the languages that OSM has: name:ka / name:ru / name:en; a name that lacks a language is marked "pend": 1,
the card shows the name that exists), the former names (old_name*), another name (alt_name*), the Wikipedia article named by the tag (a link only), the source = the OSM object (ODbL). No description of its own
(the "a" field is absent) and no origin of the name: the layer does not invent what OSM and an article do not say. Item: {id: "park-<w|r|n><OSM id>", k: "garden", pk: 1, lon, lat, n, o (old names), al (other names), wp (url), s: {u (OSM url), l: "osm"}}.
Idempotent. Usage: python -P tools/apply_parks.py
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_enc_spec as B  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(R, "site", "data", "places.json")
GE = re.compile("[ა-ჰ]")


def lang_tags(t, base):
    """{ka, ru, en} of a tag family (name, old_name, alt_name): name:xx, and the plain tag for the language of its script"""
    d = {"ka": t.get(base + ":ka", ""), "ru": t.get(base + ":ru", ""), "en": t.get(base + ":en", "")}
    plain = t.get(base, "")
    if plain and not d["ka"] and GE.search(plain):
        d["ka"] = plain
    elif plain and not any(d.values()):
        d["en" if re.search("[A-Za-z]", plain) and not re.search("[А-Яа-яЁё]", plain) else "ru"] = plain
    return d


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    polys = [r for rs in B.polygons().values() for r in rs]
    d = json.load(open(OUT, encoding="utf-8"))
    d["items"] = [c for c in d["items"] if not c["id"].startswith("park-")]
    have = {c["id"].split("-", 1)[1] for c in d["items"] if c["id"].startswith("garden-")}
    npath = os.path.join(R, "tools", "parks_names.json")                 # the missing languages from Gemini (tools/apply_parks_result.py): they fill the empty forms only
    fill = json.load(open(npath, encoding="utf-8")) if os.path.exists(npath) else {}
    seen, new = set(), []
    for f in ("places", "squares"):
        for e in json.load(open(os.path.join(R, "data", "raw", "osm_extra", f + ".json"), encoding="utf-8"))["elements"]:
            t = e.get("tags", {})
            if t.get("leisure") not in ("park", "garden") or not t.get("name"):
                continue
            key = e["type"][0] + str(e["id"])
            ce = e.get("center") or e
            if key in seen or key in have or "lon" not in ce:
                continue
            seen.add(key)
            if not any(B.inside((ce["lon"], ce["lat"]), r) for r in polys):
                continue
            n = lang_tags(t, "name")
            c = {"id": "park-" + key, "k": "garden", "pk": 1, "lon": round(ce["lon"], 6), "lat": round(ce["lat"], 6), "n": n,
                 "s": {"u": "https://www.openstreetmap.org/%s/%d" % (e["type"], e["id"]), "l": "osm"}}
            o = lang_tags(t, "old_name")
            al = lang_tags(t, "alt_name")
            for fld, dd in (("n", n), ("o", o), ("al", al)):
                got = fill.get(c["id"] + "|" + fld)
                if got:
                    for l in dd:
                        dd[l] = dd[l] or got.get(l, "")
            if not all(n.values()):
                c["pend"] = 1                                           # a name waits for its missing languages (the check lets it through; the card shows the name that exists)
            if any(o.values()):
                c["o"] = o
            if any(al.values()):
                c["al"] = al
            if any(x and not all(x.values()) for x in (c.get("o"), c.get("al"))):
                c["pend"] = 1                                           # a former or other name that lacks a language
            wp = t.get("name:wikipedia") or t.get("wikipedia")
            m = re.match(r"(ka|ru|en):(.+)", wp or "")
            if m:
                c["wp"] = "https://%s.wikipedia.org/wiki/%s" % (m.group(1), urllib.parse.quote(m.group(2).replace(" ", "_")))
            new.append(c)
    new.sort(key=lambda c: c["id"])
    d["items"] += new
    json.dump(d, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("parks and gardens added:", len(new), "| with old names:", sum(1 for c in new if "o" in c), "| names waiting for a language:", sum(1 for c in new if c.get("pend")), "| places:", len(d["items"]))


if __name__ == "__main__":
    main()
