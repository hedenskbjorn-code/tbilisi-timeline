"""The objects on the streets (buildings, monuments, churches, lost places, memorial addresses, planners) from the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008)
(idempotent; --dry-run only checks). Input: data/cache/enc2008_verified5.json (made by tools/verify_enc5.py: every quote is a verbatim part of the text of the entry, the years and the names stand in it).
Output: site/data/street_objects.json ({"objects": {<key of the street>: [object, ...]}}; loaded when the card of a street is opened), the streets that have objects but were not on the map get an entry
(no interval: the card and the search only, "nogeom") in site/data/street_names.json, and data/street_objects_verified.json (the objects with the quotes and the PDF pages: the provenance, not loaded by the site).
An object on the site: k (kind), n (name ru/en/ka), p (person ru/en/ka or null), r (role), y ([from, to] or null), yk (what the year is), a (house number).
Usage: python -P tools/apply_enc_objects.py [--dry-run]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import name_forms, norm_name  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VER = os.path.join(ROOT, "data", "cache", "enc2008_verified5.json")
NAMES = os.path.join(ROOT, "site", "data", "street_names.json")
OBJ = os.path.join(ROOT, "site", "data", "street_objects.json")
PROV = os.path.join(ROOT, "data", "street_objects_verified.json")
DRY = "--dry-run" in sys.argv
CR, LF = chr(13), chr(10)
CYR = re.compile("[Ѐ-ӿ]")


def read(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write(p, obj, compact=True):
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(obj, ensure_ascii=False, indent=1)
    if os.path.exists(p):
        with open(p, "rb") as f:
            crlf = (CR + LF).encode() in f.read()
        if crlf:
            data = data.replace(LF, CR + LF)
    b = data.encode("utf-8")  # encode first: a failure must not truncate the file
    if not DRY:
        with open(p, "wb") as f:
            f.write(b)


def key_of(st):
    return st.get("geom") or st["now"]["en"]


def main():
    rows = read(VER)["ok"]
    d = read(NAMES)
    by_ka, by_en = {}, {}
    for st in d["streets"]:
        for f in name_forms(st["now"]["ka"]):
            by_ka.setdefault(norm_name(f), st)
        by_en.setdefault(st["now"]["en"], st)
    used = {key_of(s) for s in d["streets"]}
    objects, prov, new = {}, [], 0
    for r in rows:
        st = next((by_ka[norm_name(f)] for f in name_forms(r["ka_now"]) if norm_name(f) in by_ka), None) or by_en.get(r["en_now"])
        if st is None:                                         # the street has objects but no name history: the card only
            key = r["en_now"] if r["en_now"] not in used else "%s [%s]" % (r["en_now"], r["id"])
            st = {"now": {"ru": r["ru_now"], "en": r["en_now"], "ka": r["ka_now"]}, "iv": [], "book": "Tbilisi. Streets, avenues, squares (თბილისი. ქუჩები, გამზირები, მოედნები), 2008, PDF p. %s" % r["page"], "nogeom": True}
            if key != r["en_now"]:
                st["geom"] = key
            assert not CYR.search(st["now"]["ka"] + st["now"]["en"])
            d["streets"].append(st)
            used.add(key)
            for f in name_forms(r["ka_now"]):
                by_ka.setdefault(norm_name(f), st)
            by_en.setdefault(st["now"]["en"], st)
            new += 1
        key = key_of(st)
        lst = objects.setdefault(key, [])
        for o in r["objects"]:
            assert not CYR.search(o["name"]["ka"] + o["name"]["en"] + (o["person"]["ka"] + o["person"]["en"] if o["person"] else ""))
            years = [y for y in (o["year_from"], o["year_to"]) if y]
            lst.append({"k": o["kind"], "n": o["name"], "p": o["person"], "r": o["role"], "y": years or None, "yk": o["year_kind"], "a": o["address"]})
            prov.append({"id": r["id"], "street": key, "pdf_page": r["page"], "kind": o["kind"], "name": o["name"]["ru"], "person": o["person"]["ru"] if o["person"] else None,
                         "year_from": o["year_from"], "year_to": o["year_to"], "quote": o["quote"]})
    write(NAMES, d)
    write(OBJ, {"objects": objects})
    write(PROV, {"note": "The objects on the streets from the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008): each with the verbatim quote and the PDF page (2026-11-22); checked by tools/verify_enc5.py.", "objects": prov}, compact=False)
    print("streets with objects: %d (new card-only streets: %d); objects: %d; %s" % (len(objects), new, sum(len(v) for v in objects.values()), "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
