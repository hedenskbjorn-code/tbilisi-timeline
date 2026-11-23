"""Takes the answer of Gemini about the names of the places of worship in several languages (for_gemini/from_desktop/churches_A_result.json, task: churches_A_TASK_for_gemini.md).
A name is taken only when: the object is one of site/data/religious_osm.json; a form that OSM already gives is NOT changed (the row repeats it); ka has Georgian letters and no Cyrillic; ru has Cyrillic and no
Georgian letters; en has Latin letters and no Cyrillic or Georgian; no word პროსპექტი. Output: tools/churches_names.json ({id: {ka, ru, en}}), which tools/build_religious_osm.py uses to fill the EMPTY forms
(the module of the site fills the rest). Usage: python -P tools/apply_churches_a.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GE, CY, LAT = re.compile("[ა-ჰ]"), re.compile("[А-Яа-яЁё]"), re.compile("[A-Za-z]")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.load(open(os.path.join(R, "for_gemini", "from_desktop", "churches_A_result.json"), encoding="utf-8"))
    items = {c["id"]: c for c in json.load(open(os.path.join(R, "site", "data", "religious_osm.json"), encoding="utf-8"))["items"]}
    # the forms that OSM itself gives, without the forms made by the module of the site: they are rebuilt by tools/build_religious_osm.py from the raw data, here the current file is compared
    ok, bad = {}, []
    for oid, v in res.items():
        c = items.get(oid)
        if not c:
            bad.append((oid, "unknown object"))
            continue
        have = c["name"] or {}
        why = ""
        for l in ("ka", "ru", "en"):
            if not v.get(l):
                why = why or "empty " + l
        if not why and (not GE.search(v["ka"]) or CY.search(v["ka"]) or "პროსპექტი" in v["ka"]):
            why = "bad ka"
        if not why and (not CY.search(v["ru"]) or GE.search(v["ru"])):
            why = "bad ru"
        if not why and (not LAT.search(v["en"]) or CY.search(v["en"]) or GE.search(v["en"])):
            why = "bad en"
        if not why and have.get("ka") and have["ka"] != v["ka"]:
            why = "the Georgian name of OSM was changed"
        if not why and LAT.search(v["ru"]):
            why = "Latin letters inside the Russian name"                       # e.g. a Latin c among Cyrillic letters
        if not why and "ხარებ" in v["ka"] and not (re.search("Благовещ", v["ru"]) and re.search("Annunciation", v["en"], re.I)):
            why = "the Annunciation of the Georgian name is lost"
        if not why and v["ka"].endswith("ტაძარი") and "საკათედრო" not in v["ka"] and re.search("Cathedral", v["en"], re.I):
            why = "ტაძარი is a temple / church, not a cathedral"
        if why:
            bad.append((oid, why))
        else:
            ok[oid] = {l: v[l] for l in ("ka", "ru", "en")}
    json.dump(ok, open(os.path.join(R, "tools", "churches_names.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("names taken:", len(ok), "of", len(res), "| rejected:", bad)


if __name__ == "__main__":
    main()
