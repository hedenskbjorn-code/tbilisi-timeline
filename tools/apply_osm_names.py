"""Adds the quarters, squares and bridges of OpenStreetMap that no card had to data/places.json (the layer "Local names") from the answer of Gemini (work/gemini/results/osm_names.json, task: tools/osm_names_task.py):
the name in ka / ru / en, the point of the OSM object, the OSM object as the source (ODbL). Like a park of tools/apply_parks.py the card has NO description and no origin of the name ("pk": 1: the layer does not invent
what OSM does not say). Item: {id: "osm-<n|w|r><OSM id>", k: district | square | bridge, pk: 1, lon, lat, n, s: {u, l: "osm"}}.
Taken only when: the row is in the answer; the OSM object is in the project index (raw_record) and is a quarter / neighbourhood / suburb, a square or a bridge; its centre lies inside the district polygons of the site
(a "New Mtskheta" is not Tbilisi); the name is not that of an administrative district ("raioni": the layer of districts has them) and is not a pin that tools/places_edits.json dropped; no card of the layer has the same
Georgian name already; ka has Georgian letters and no Cyrillic, ru Cyrillic and no Georgian letters, en Latin letters only; no word "prospekt" in Georgian. Idempotent. Run it AFTER tools/apply_places.py, apply_folk.py,
apply_parks.py and BEFORE tools/apply_places_edits.py. Usage: python -P tools/apply_osm_names.py [--dry-run]
"""
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_enc_spec as B  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GE, CY, LAT = re.compile("[ა-ჰ]"), re.compile("[А-Яа-яЁё]"), re.compile("[A-Za-z]")


def kind_of(t):
    if t.get("place") == "square":
        return "square"
    if t.get("bridge") is not None and "ხიდი" in (t.get("name") or ""):
        return "bridge"
    if t.get("place") in ("neighbourhood", "quarter", "suburb"):
        return "district"
    return None


def norm(s):
    return re.sub(r"[\s\-–.,]+", "", (s or "").casefold())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    res = json.load(open(os.path.join(R, "work", "gemini", "results", "osm_names.json"), encoding="utf-8"))
    p = os.path.join(R, "site", "data", "places.json")
    raw = open(p, "rb").read().decode("utf-8")
    doc = json.loads(raw)
    assert json.dumps(doc, ensure_ascii=False, separators=(",", ":")) == raw, "unexpected layout of places.json"
    have_id = {x["id"] for x in doc["items"]}
    have_ka = {norm(x["n"].get("ka")) for x in doc["items"]}
    dropped = set()
    for k in json.load(open(os.path.join(R, "tools", "places_edits.json"), encoding="utf-8")).get("drop", {}):
        dropped.add(k.split("-", 1)[1])
    con = sqlite3.connect("file:%s?mode=ro" % os.path.join(R, "data", "db", "project.sqlite").replace("\\", "/"), uri=True)
    polys = [r for rs in B.polygons().values() for r in rs]
    added = []
    why = {}

    def skip(rid, reason):
        why.setdefault(reason, []).append(rid)

    for rid, n in res.items():
        m = re.match(r"(node|way|relation)/(\d+)$", rid)
        if not m:
            skip(rid, "not an OSM id")
            continue
        short = {"node": "n", "way": "w", "relation": "r"}[m.group(1)] + m.group(2)
        pid = "osm-" + short
        if pid in have_id:
            continue                                                        # already there (a second run)
        if short in dropped:
            skip(rid, "a dropped pin")
            continue
        row = con.execute("SELECT tags, lat, lon FROM raw_record WHERE source = 'osm' AND rid = ? LIMIT 1", (rid,)).fetchone()
        if not row or row[1] is None or row[2] is None:
            skip(rid, "no object or no point in the index")
            continue
        t = json.loads(row[0])
        k = kind_of(t)
        if not k:
            skip(rid, "not a quarter, square or bridge")
            continue
        ka, ru, en = (n.get("ka") or "").strip(), (n.get("ru") or "").strip(), (n.get("en") or "").strip()
        if "რაიონი" in ka or "რაიონი" in (t.get("name") or ""):
            skip(rid, "an administrative district")
            continue
        if norm(ka) in have_ka:
            skip(rid, "a card with this Georgian name exists")
            continue
        if not (GE.search(ka) and not CY.search(ka) and CY.search(ru) and not GE.search(ru) and LAT.search(en) and not CY.search(en) and not GE.search(en)) or "პროსპექტი" in ka:
            skip(rid, "a name in a wrong script")
            continue
        if not any(B.inside((row[2], row[1]), r) for r in polys):
            skip(rid, "outside the city")
            continue
        doc["items"].append({"id": pid, "k": k, "pk": 1, "lon": round(row[2], 6), "lat": round(row[1], 6), "n": {"ka": ka, "ru": ru, "en": en}, "s": {"u": "https://www.openstreetmap.org/" + rid, "l": "osm"}})
        have_id.add(pid)
        have_ka.add(norm(ka))
        added.append((k, pid))
    if added and not dry:
        open(p, "wb").write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    import collections
    print("added:", dict(collections.Counter(k for k, _ in added)), "| items now:", len(doc["items"]), "| dry-run:", dry)
    print("not taken:", {r: len(v) for r, v in why.items()})
    for r, v in why.items():
        if r not in ("a dropped pin",):
            print("  ", r, v[:5])


if __name__ == "__main__":
    main()
