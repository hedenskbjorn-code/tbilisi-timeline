"""The gaps of the site found in the project index: what a layer lacks and what of it can be filled from data that we already have (the raw records and the other layers). Read-only; the report goes to the screen
and to data/db/gaps_report.json. Run tools/db_build.py first. Usage: python -P tools/db_gaps.py
Sections: 1 streets of the encyclopedia without a line that OSM has under the same name; 2 nameless places of worship that stand at a register object of a church; 3 nameless monuments at a register memorial;
4 named objects of OSM (quarters, peaks, bridges, springs) that no card has; 5 what the register says that the site does not show; 6 white spots of the map (a settled cell without any card);
7 years, 8 languages, 9 photographs, 10 verified facts.
"""
import collections
import json
import math
import os
import re
import sqlite3
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(R, "data", "db", "project.sqlite")
CHURCH = re.compile("ეკლესია|ტაძარი|მონასტერი|მეჩეთი|სინაგოგა|ბაზილიკა|სამლოცველო|კათედრალი|საყდარი|ლუთერანული|ყოველწმიდა")


def norm(s):
    return re.sub(r"[\s.,\-–—\"'„“”«»()]+", "", (s or "").casefold())


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(a))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    rep = {}

    def Q(sql, *a):
        return con.execute(sql, a).fetchall()

    # ---- 1. streets without a line, OSM has the name ----
    nog = {r[0]: r[1] for r in Q("SELECT o.id, n.name FROM object o JOIN name n ON n.object_id = o.id AND n.lang = 'ka' AND n.kind = 'official' WHERE o.layer = 'st' AND o.props LIKE '%nogeom%'")}
    osm_names = collections.defaultdict(list)
    for tags, rid in Q("SELECT tags, rid FROM raw_record WHERE source = 'osm' AND tags LIKE '%highway%'"):
        t = json.loads(tags)
        for k in ("name", "name:ka"):
            if t.get(k):
                osm_names[norm(t[k])].append(rid)
    exact = [(i, n) for i, n in nog.items() if norm(n) in osm_names]
    rep["streets_no_line"] = {"total": len(nog), "osm_has_same_name": len(exact), "examples": [n for _, n in exact[:6]]}

    # ---- 2. nameless places of worship at a register church ----
    reg_ch = [(lat, lon, n, rid) for lat, lon, n, rid in Q("SELECT o.lat, o.lon, n.name, o.id FROM object o JOIN name n ON n.object_id = o.id WHERE o.layer = 'reg' AND o.lat IS NOT NULL")
              if CHURCH.search(n or "")]
    nameless = Q("SELECT o.id, o.lat, o.lon FROM v_object_state v JOIN object o ON o.id = v.id WHERE v.layer = 'relosm' AND v.has_name = 0")
    hit = []
    for oid, la, lo in nameless:
        best = min(((hav(la, lo, a, b), n, rid) for a, b, n, rid in reg_ch), default=None)
        if best and best[0] <= 60:
            hit.append((oid, round(best[0]), best[1]))
    rep["churches_from_register"] = {"register_churches_in_tbilisi": len(reg_ch), "nameless": len(nameless), "register_church_within_60m": len(hit), "examples": [(h[1], h[2]) for h in hit[:5]]}

    # ---- 3. nameless monuments at a register memorial ----
    MEM = re.compile("ძეგლი|მემორიალი|ბიუსტი|ქანდაკება|სკულპტურა|მონუმენტი|ობელისკი")      # the NAME says it is a monument (the class "memorial" also holds houses)
    mem = [(lat, lon, n) for lat, lon, n in Q("SELECT o.lat, o.lon, n.name FROM object o JOIN name n ON n.object_id = o.id WHERE o.layer = 'reg' AND o.kind LIKE '%memorial%' AND o.lat IS NOT NULL") if MEM.search(n or "")]
    unn = Q("SELECT o.id, o.lat, o.lon FROM v_object_state v JOIN object o ON o.id = v.id WHERE v.layer = 'mn' AND v.has_name = 0")
    hm = []
    for oid, la, lo in unn:
        best = min(((hav(la, lo, a, b), n) for a, b, n in mem), default=None)
        if best and best[0] <= 40:
            hm.append((oid, round(best[0]), best[1]))
    rep["monuments_from_register"] = {"nameless": len(unn), "register_memorial_within_40m": len(hm), "examples": [(h[1], h[2]) for h in hm[:5]]}

    # ---- 4. named OSM objects that no card has ----
    have_names = {norm(n) for (n,) in Q("SELECT name FROM name WHERE object_id LIKE 'TB/pl:%' OR object_id LIKE 'TB/st:%'")}
    have_ids = {m for (m,) in Q("SELECT local_id FROM object WHERE layer = 'pl'")}
    out4 = collections.OrderedDict()
    sel = {"quarters / neighbourhoods / suburbs": "json_extract(tags,'$.place') IN ('neighbourhood','quarter','suburb')", "peaks": "json_extract(tags,'$.natural') = 'peak'",
           "springs, caves, cliffs": "json_extract(tags,'$.natural') IN ('spring','hot_spring','cave_entrance','cliff')", "named bridges": "json_extract(tags,'$.bridge') IS NOT NULL AND (json_extract(tags,'$.name') LIKE '%ხიდი%' OR json_extract(tags,'$.name:ka') LIKE '%ხიდი%')",
           "named water": "json_extract(tags,'$.natural') = 'water'", "squares": "json_extract(tags,'$.place') = 'square'"}
    for label, cond in sel.items():
        rows = Q("SELECT DISTINCT rid, tags FROM raw_record WHERE source = 'osm' AND " + cond)
        named, seen = [], set()
        for rid, tags in rows:
            t = json.loads(tags)
            nm = t.get("name:ka") or t.get("name")
            if not nm or norm(nm) in seen:
                continue
            seen.add(norm(nm))
            named.append((rid, nm, t.get("name:en") or t.get("name:ru") or ""))
        missing = [x for x in named if norm(x[1]) not in have_names and x[0].replace("/", "-").replace("way-", "w").replace("node-", "n").replace("relation-", "r") not in {h.split("-", 1)[-1] for h in have_ids}]
        out4[label] = {"named_in_osm": len(named), "no_card": len(missing), "examples": [(m[1], m[2]) for m in missing[:5]]}
    rep["osm_without_card"] = out4

    # ---- 5. what the register says and the site does not show ----
    n_desc = Q("SELECT COUNT(DISTINCT object_id) FROM fact WHERE key = 'description' AND object_id LIKE 'TB/reg:%'")[0][0]
    long_desc = Q("SELECT COUNT(DISTINCT object_id) FROM fact WHERE key = 'description' AND object_id LIKE 'TB/reg:%' AND LENGTH(value) > 150")[0][0]
    undated = Q("SELECT COUNT(*) FROM object WHERE layer = 'reg' AND id LIKE 'TB/%' AND year_from IS NULL")[0][0]
    period_only = Q("SELECT COUNT(DISTINCT f.object_id) FROM fact f JOIN object o ON o.id = f.object_id WHERE f.key IN ('period','exact_date') AND o.layer = 'reg' AND o.id LIKE 'TB/%' AND o.year_from IS NULL")[0][0]
    unsure = Q("SELECT COUNT(*) FROM fact f WHERE f.key = 'coordinates_accuracy' AND f.value LIKE 'დასაზუსტებელი%' AND f.object_id LIKE 'TB/reg:%'")[0][0]
    rep["register"] = {"tbilisi_objects": Q("SELECT COUNT(*) FROM object WHERE layer='reg' AND id LIKE 'TB/%'")[0][0], "with_georgian_description": n_desc, "description_over_150_chars": long_desc,
                       "undated_in_index": undated, "undated_but_period_or_exact_date_in_words": period_only, "coordinates_to_be_refined": unsure}

    # ---- 6. white spots of the map ----
    cell = 0.006
    settled = collections.Counter()
    for (g,) in Q("SELECT geom FROM raw_record WHERE source = 'osm' AND file_id IN (SELECT id FROM raw_file WHERE path LIKE '%roads_center%') AND geom IS NOT NULL"):
        pts = json.loads(g)
        for x, y in pts[::3]:
            settled[(int(x / cell), int(y / cell))] += 1
    cards = collections.Counter()
    for lat, lon in Q("SELECT lat, lon FROM object WHERE lat IS NOT NULL AND layer NOT IN ('st')"):
        cards[(int(lon / cell), int(lat / cell))] += 1
    reg_cells = collections.Counter()
    for lat, lon in Q("SELECT lat, lon FROM object WHERE layer = 'reg' AND lat IS NOT NULL"):
        reg_cells[(int(lon / cell), int(lat / cell))] += 1
    holes = sorted(((v, k) for k, v in settled.items() if v >= 40 and cards[k] == 0), reverse=True)
    def where(k):
        lon, lat = (k[0] + 0.5) * cell, (k[1] + 0.5) * cell
        r = Q("SELECT region FROM object WHERE lat IS NOT NULL ORDER BY (lat-?)*(lat-?)+(lon-?)*(lon-?) LIMIT 1", lat, lat, lon, lon)
        return round(lat, 4), round(lon, 4), r[0][0] if r else ""
    rep["white_spots"] = {"settled_cells": sum(1 for v in settled.values() if v >= 40), "without_any_card": len(holes), "biggest": [(v,) + where(k) for v, k in holes[:10]]}

    # ---- 7-10. years, languages, photographs, verified facts per layer ----
    lay = {}
    for layer, n, y, lg3, ph, ver in Q("""SELECT o.layer, COUNT(*), SUM(o.year_from IS NOT NULL), SUM(v.name_languages = 3), SUM(v.has_photo), SUM(v.has_verified_fact)
                                         FROM object o JOIN v_object_state v ON v.id = o.id GROUP BY o.layer"""):
        lay[layer] = {"objects": n, "with_year": y, "names_in_3_languages": lg3, "with_photo": ph, "with_verified_fact": ver}
    rep["layers"] = lay
    json.dump(rep, open(os.path.join(R, "data", "db", "gaps_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
