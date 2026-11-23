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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import inside, polygons  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RINGS = polygons()
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


OSM_FULL = os.path.join(R, "data", "raw", "osm_extra", "monuments_full.json")
ART = {"statue": "statue", "bust": "bust", "sculpture": "sculpture", "relief": "relief", "installation": "sculpture", "monument": "monument", "memorial": "memorial"}
MEM = {"bust": "bust", "statue": "statue", "sculpture": "sculpture", "relief": "relief"}
NOT_MONUMENTS = {"street_art", "mural", "graffiti", "stained_glass", "mosaic", "painting"}


def osm_kind(t):
    """the kind of an OSM object in the words of the table; None = not a monument (street art, a mosaic ...)"""
    if t.get("historic") == "monument":
        return "monument"
    if t.get("historic") == "memorial":
        return MEM.get(t.get("memorial"), "memorial")
    if t.get("tourism") == "artwork":
        a = t.get("artwork_type", "")
        return None if a in NOT_MONUMENTS else ART.get(a, "sculpture")
    return None


def osm_fields(e):
    """what OSM says about the object, in the fields of the monuments of the site"""
    import urllib.parse
    t, c = e["tags"], e.get("center") or e
    n = {"ka": "", "ru": "", "en": ""}                                                         # a name goes to the language of its script (a Latin name of the tag "name" is English, not Georgian)
    for v in (t.get("name:ka"), t.get("name"), t.get("subject")):
        if v:
            lg = "ka" if re.search("[ა-ჿ]", v) else "ru" if re.search("[А-Яа-яЁё]", v) else "en"
            n[lg] = n[lg] or v
    n["ru"] = t.get("name:ru") or n["ru"]
    n["en"] = t.get("name:en") or n["en"]
    f = {"n": n, "lat": round(c["lat"], 6), "lon": round(c["lon"], 6)}
    m = re.match(r"(\d{4})", t.get("start_date", ""))
    f["year"] = int(m.group(1)) if m else None
    f["sculptor"] = t.get("artist_name") or t.get("architect") or ""
    f["material"] = (t.get("material") or "").split(";")[0].strip()
    img = t.get("wikimedia_commons", "")
    f["image"] = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(img.replace(" ", "_"), safe=":/()_,.-") if img.startswith("File:") else ""
    f["qid"] = t.get("subject:wikidata", "")
    f["sc_qid"] = t.get("artist:wikidata", "")
    w = {}
    for tag in ("wikipedia", "subject:wikipedia"):
        v = t.get(tag, "")
        if ":" in v and v.split(":", 1)[0] in WIKI:
            w.setdefault(v.split(":", 1)[0], WIKI[v.split(":", 1)[0]] + urllib.parse.quote(v.split(":", 1)[1].replace(" ", "_")))
    f["wiki"] = w
    f["d"] = {lg: t["description:" + lg] for lg in ("ru", "en", "ka") if t.get("description:" + lg)}
    return f


def merge_osm(mons):
    """the OSM objects that the table does not have are added, the ones it has are completed (only empty fields are filled); decisions of tools/monuments_manual.json"""
    if not os.path.exists(OSM_FULL):
        return 0, 0
    man = json.load(open(os.path.join(R, "tools", "monuments_manual.json"), encoding="utf-8"))
    kinds = {"node": "n", "way": "w", "relation": "r"}
    for oid in man["skip"]:                                                  # a duplicate that the table already holds is dropped too
        mons[:] = [x for x in mons if x["id"] != oid]
    byid = {x["id"]: x for x in mons}
    added = filled = 0
    for e in json.load(open(OSM_FULL, encoding="utf-8"))["elements"]:
        oid = "OSM_%s%d" % (kinds[e["type"]], e["id"])
        kind = osm_kind(e["tags"])
        f = osm_fields(e)
        target = man["merge"].get(oid)
        if oid in man["skip"] or (not kind and not target):
            continue
        if not IN_CITY(f["lat"], f["lon"]):
            continue
        if not (target or oid in byid) and not any(inside((f["lon"], f["lat"]), ring) for rings in RINGS.values() for ring in rings):
            continue                                                         # a new object must lie inside the boundary of the city (the districts of the site), not only in the box around it
        if target or oid in byid:
            x = byid.get(target or oid)
            if not x:
                continue
            if target:
                x["lat"], x["lon"], x["prec"] = f["lat"], f["lon"], "exact"
            for k in ("year", "sculptor", "material", "image", "qid"):
                if not x.get(k) and f[k]:
                    x[k] = f[k]
            for k in ("sc_qid", "d"):
                if f[k] and not x.get(k):
                    x[k] = f[k]
            for lg, v in f["wiki"].items():
                x["wiki"].setdefault(lg, v)
            for lg in ("ka", "ru", "en"):
                if not x["n"][lg] and f["n"][lg]:
                    x["n"][lg] = f["n"][lg]
            filled += 1
        else:
            x = {"id": oid, "kind": kind, "n": f["n"], "year": f["year"], "lat": f["lat"], "lon": f["lon"], "prec": "exact", "loc": "", "sculptor": f["sculptor"], "architect": "", "material": f["material"],
                 "image": f["image"], "qid": f["qid"], "wiki": f["wiki"], "event": "", "src": "osm", "sc_qid": f["sc_qid"], "d": f["d"], "new": 1}
            mons.append(x)
            byid[oid] = x
            added += 1
    return added, filled


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
    added, filled = merge_osm(mons)
    print("OSM: added %d objects that the table did not have, completed %d" % (added, filled))
    json.dump({"monuments": mons, "plaques": plaques, "lost": lost, "skipped": dict(skipped)}, open(os.path.join(R, "data", "cache", "monuments_clean.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("monuments:", len(mons), dict(collections.Counter(x["kind"] for x in mons)), "| lost:", len(lost), "| plaques:", len(plaques), "| skipped:", dict(skipped))
    nm = lambda x: any(x["n"].values())  # noqa: E731
    print("monuments: dated", sum(1 for x in mons if x["year"]), "undated", sum(1 for x in mons if not x["year"]), "| without any name", sum(1 for x in mons if not nm(x)), "| without ru", sum(1 for x in mons if not x["n"]["ru"]), "| with a photo", sum(1 for x in mons if x["image"]))
    print("plaques: dated by the first year of life", sum(1 for x in plaques if x["year"]), "undated", sum(1 for x in plaques if not x["year"]), "| without any name", sum(1 for x in plaques if not nm(x)), "| without ru", sum(1 for x in plaques if not x["n"]["ru"]), "| with a photo", sum(1 for x in plaques if x["image"]), "| with a qid", sum(1 for x in plaques if x["qid"]))
    print("lost (not on the map):", [(x["id"], x["n"]["ka"] or x["n"]["en"] or x["n"]["ru"], x["year"]) for x in lost])


if __name__ == "__main__":
    main()
