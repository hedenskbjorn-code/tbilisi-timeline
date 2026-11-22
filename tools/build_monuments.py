"""The first step of the layer of monuments and memorial plaques: reads the working tables notes/tbilisi_monuments_full.csv (634 objects: sculptures, busts, statues, memorials, reliefs) and
notes/tbilisi_plaques_osm.csv (814 plaques of OSM) and makes the clean lists that the next steps (names, photos, the layer) work on: data/cache/monuments_clean.json.
Rules (decisions of the owner): an object without a point or outside the city (41.62-41.86 N, 44.66-45.02 E) is not taken; an object that is removed or lost is listed apart (not on the map);
a plaque is dated by the FIRST year of the life named in its inscription ("ამ სახლში 1959-1982 წლებში ცხოვრობდა" -> 1959), never by the year of the plaque; a plaque without such a year and a monument
without a year are "undated" (hidden by default, a sub-box shows them); a name that is missing in a language stays empty (the next steps fill it: Wikidata labels, Gemini for the Georgian names).
Output: {"monuments": [...], "plaques": [...], "lost": [...], "skipped": {...}}. The tables are working files and are not committed. Usage: python -P tools/build_monuments.py
"""
import collections
import csv
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IN_CITY = lambda la, lo: 41.62 < la < 41.86 and 44.66 < lo < 45.02  # noqa: E731
FIRST_YEAR = re.compile(r"ამ\s+(?:სახლში|შენობაში|სახლ[ა-ჰ]*)\s*[(\[]?\s*(1[6-9][0-9]{2}|20[0-2][0-9])")
WIKI = {"ka": "https://ka.wikipedia.org/wiki/", "ru": "https://ru.wikipedia.org/wiki/", "en": "https://en.wikipedia.org/wiki/"}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def wiki(r):
    import urllib.parse
    return {lg: WIKI[lg] + urllib.parse.quote(r["wiki_" + lg].replace(" ", "_")) for lg in WIKI if r.get("wiki_" + lg)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    M = list(csv.DictReader(open(os.path.join(R, "notes", "tbilisi_monuments_full.csv"), encoding="utf-8-sig")))
    P = list(csv.DictReader(open(os.path.join(R, "notes", "tbilisi_plaques_osm.csv"), encoding="utf-8-sig")))
    skipped = collections.Counter()
    mons, lost = [], []
    for r in M:
        la, lo = num(r["lat"]), num(r["lon"])
        if la is None or lo is None:
            skipped["monument without a point"] += 1
            continue
        if not IN_CITY(la, lo):
            skipped["monument outside the city"] += 1
            continue
        it = {"id": r["id"], "kind": r["category"], "n": {"ka": r["name_ka"], "ru": r["name_ru"], "en": r["name_en"]}, "year": int(r["year"]) if re.fullmatch(r"\d{4}", r["year"] or "") else None,
              "lat": round(la, 6), "lon": round(lo, 6), "prec": r["coord_precision"], "loc": r["location"], "sculptor": r["sculptor"], "architect": r["architect"], "material": r["material"],
              "image": r["image"], "qid": r["subject_qid"], "wiki": wiki(r), "event": r["event_title"], "src": r["source"]}
        (lost if r["status"] != "existing" else mons).append(it)
    plaques = []
    for r in P:
        la, lo = num(r["lat"]), num(r["lon"])
        if la is None or lo is None or not IN_CITY(la, lo):
            skipped["plaque without a point or outside the city"] += 1
            continue
        m = FIRST_YEAR.search(r["inscription"] or "")
        plaques.append({"id": r["osm_id"].replace("/", ""), "n": {"ka": r["name_ka"], "ru": r["name_ru"], "en": r["name_en"]}, "lat": round(la, 6), "lon": round(lo, 6), "image": r["image"],
                        "qid": r["subject_qid"] or r["wikidata"], "wiki": wiki(r), "inscription": r["inscription"], "year": int(m.group(1)) if m else None})
    json.dump({"monuments": mons, "plaques": plaques, "lost": lost, "skipped": dict(skipped)}, open(os.path.join(R, "data", "cache", "monuments_clean.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("monuments:", len(mons), dict(collections.Counter(x["kind"] for x in mons)), "| lost:", len(lost), "| plaques:", len(plaques), "| skipped:", dict(skipped))
    nm = lambda x: any(x["n"].values())  # noqa: E731
    print("monuments: dated", sum(1 for x in mons if x["year"]), "undated", sum(1 for x in mons if not x["year"]), "| without any name", sum(1 for x in mons if not nm(x)), "| without ru", sum(1 for x in mons if not x["n"]["ru"]), "| with a photo", sum(1 for x in mons if x["image"]))
    print("plaques: dated by the first year of life", sum(1 for x in plaques if x["year"]), "undated", sum(1 for x in plaques if not x["year"]), "| without any name", sum(1 for x in plaques if not nm(x)), "| without ru", sum(1 for x in plaques if not x["n"]["ru"]), "| with a photo", sum(1 for x in plaques if x["image"]), "| with a qid", sum(1 for x in plaques if x["qid"]))
    print("lost (not on the map):", [(x["id"], x["n"]["ka"] or x["n"]["en"] or x["n"]["ru"], x["year"]) for x in lost])


if __name__ == "__main__":
    main()
