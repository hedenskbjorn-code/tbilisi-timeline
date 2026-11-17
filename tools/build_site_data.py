"""Build the self-contained data folder for the public page (site/data).

Reads : data/tbilisi_monuments.geojson, data/warped/*.webp|json, data/boundaries/*.geojson
Writes: site/data/monuments.json  (slim GeoJSON: no long descriptions, coordinates rounded)
        site/data/plans.json      (plan list: year, image, corners, boundary file)
        site/data/<plan>.webp, site/data/<plan>_boundary.geojson  (copies)
"""
import json
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "site", "data")
os.makedirs(OUT, exist_ok=True)

CLASSES = {  # first token of the Georgian classification -> key used by the page
    "არქიტექტურის": "architecture",
    "არქეოლოგიური": "archaeology",
    "ეთნოგრაფიული": "ethnography",
    "მემორიალური": "memorial",
    "ქალაქთმშენებლობის (ურბანული)": "urban",
    "მონუმენტური სახვითი ხელოვნების": "monumental_art",
    "საბაღე-საპარკო ხელოვნებისა და ლანდშაფტური არქიტექტურის": "garden",
    "მეცნიერების": "science",
    "საინჟინრო": "engineering",
}

# building function (first record of the register field "initial_function", top level) -> type group used by the page filter
FUNCTIONS = {
    "საცხოვრისი": "residential",
    "რელიგიური, რიტუალური": "religious",
    "სათავდაცვო": "defense",
    "საგანმანათლებლო, სამეცნიერო": "culture", "კულტურა": "culture",
    "ადმინისტრაციული": "public", "სავაჭრო": "public", "ჯანდაცვა და სოცუზრუნველყოფა": "public",
    "ფიზიკური კულტურისა და სპორტის": "public", "კომუნალური მეურნეობისა და  საყოფაცხოვრებო მომსახურეობის": "public",
    "საგზაო, სატრანსპორტო": "transport", "ჰიდროტექნიკური": "transport", "სამრეწველო": "transport",
    "მემორიალური": "memorial", "საბაღე_საპარკო ხელოვნების და ლანდშაფტური არქიტექტურის": "memorial",
    "მცირე არქიტექტურული ფორმები (უძრავი)": "memorial",
    "სამოსახლო/ურბანული": "rural", "სასოფლო-სამეურნეო": "rural",
}


import re

# fallback only for objects whose register record gives no usable function: keywords in the (Georgian) name
NAME_GROUPS = [
    ("religious", r"ეკლესია|ტაძარი|მონასტერი|სამლოცველო|საყდარი|სინაგოგა|მეჩეთი|ბაზილიკა|სამრეკლო|ქვაჯვარი|სასაფლაო|პანთეონი|ნაეკლესიარი"),
    ("defense", r"გალავან|ციხე|ზღუდე|ციხესიმაგრე|ბასტიონ|კოშკი"),
    ("transport", r"ხიდი|სადგური|მეტრო|ფუნიკულიორ|გვირაბ|ქარხანა|ფაბრიკა|ჰიდროელექტრო|ჰესი"),
    ("culture", r"თეატრ|მუზეუმ|უნივერსიტეტ|სკოლა|სასწავლებელ|ინსტიტუტ|ბიბლიოთეკ|გიმნაზია|აკადემია|კინო|ფილარმონია|გალერეა|ოპერ|საბავშვო ბაღ|მუსიკალური|ცირკ"),
    ("public", r"სასტუმრო|ბანკ|საავადმყოფო|კლინიკა|პოლიკლინიკა|აბანო|ბაზარი|მაღაზია|სამინისტრო|სასამართლო|ფოსტა|რესტორან|სავაჭრო|სააგენტო|პოლიცია|კაფე"),
]


def func_orig(p):
    """Original function group, from the register field only (all recorded functions; a building can list several,
    e.g. a seminary later used as a hospital). Priority: specific religious > first recognised non-memorial function >
    bare 'religious' > 'memorial' (in the register mostly 'connected with a person/event') > archaeological class > other."""
    fn = (p.get("initial_function") or "").strip()
    toks = [t.strip() for t in fn.split(";") if t.strip()]
    specific_religious, groups, bare_religious, memorial = False, [], False, False
    for t in toks:
        top = t.split(">>")[0].strip()
        g = FUNCTIONS.get(top, "other")
        if g == "religious":
            if ">>" in t:
                specific_religious = True
            else:
                bare_religious = True
        elif g == "memorial" and top == "მემორიალური":
            memorial = True
        elif g != "other":
            groups.append(g)
    if specific_religious:
        return "religious"
    if groups:
        return groups[0]
    if bare_religious:
        return "religious"
    if memorial:
        return "memorial"
    if (p.get("classification") or "").startswith("არქეოლოგიური"):
        return "rural"
    return "other"


def func_current(p, orig):
    """Present-day use, estimated from the object name (the register has no 'current use' field). Only used where the
    register function is residential / unknown / memorial, i.e. where a building was most likely repurposed; otherwise
    the original function is kept."""
    if orig not in ("residential", "other", "memorial"):
        return orig
    name = p.get("name") or ""
    if "საცხოვრებელი სახლი" in name:
        return "residential"
    for g, rx in NAME_GROUPS:
        if re.search(rx, name):
            return g
    return orig


RUIN_RX = re.compile(r"ნანგრევ|ნაეკლესიარ|ნაციხარ|ნაქალაქარ|ნასახლარ|ნასოფლარ|დანგრეული|ნაგებობის ნაშთ|ნაშთი|ნაშთები")   # names meaning ruins / remains / abandoned site
src = json.load(open(os.path.join(ROOT, "data", "tbilisi_monuments.geojson"), encoding="utf-8"))
# optional Wikipedia links from tools/fetch_wikipedia_links.py: {object id: {"en": title, "ru": title, "ka": title}}
WP = {}
_wp = os.path.join(ROOT, "data", "wikipedia_links.json")
if os.path.exists(_wp):
    WP = json.load(open(_wp, encoding="utf-8"))
# optional photos from tools/fetch_photos.py (Wikimedia Commons, matched by coordinates)
CACHE = os.path.join(ROOT, "data", "cache")
photo_hits, photo_info = {}, {}
if os.path.exists(os.path.join(CACHE, "photos_geosearch.json")) and os.path.exists(os.path.join(CACHE, "photos_info.json")):
    photo_hits = json.load(open(os.path.join(CACHE, "photos_geosearch.json"), encoding="utf-8"))
    photo_info = json.load(open(os.path.join(CACHE, "photos_info.json"), encoding="utf-8"))
# optional people filter from tools/filter_photos.py: photos flagged "reject" are left out
people = {}
if os.path.exists(os.path.join(CACHE, "photos_people.json")):
    people = json.load(open(os.path.join(CACHE, "photos_people.json"), encoding="utf-8"))
# manual review decisions (photos looked through by hand): data/photos_manual_reject.json
manual_reject = set()
_mr = os.path.join(ROOT, "data", "photos_manual_reject.json")
if os.path.exists(_mr):
    manual_reject = set(json.load(open(_mr, encoding="utf-8"))["titles"])
used = {}

feats, unknown = [], set()
for f in src["features"]:
    p = f["properties"]
    first = (p.get("classification") or "").split(",")[0].strip()
    cls = CLASSES.get(first, "other")
    if cls == "other":
        unknown.add(first)
    x, y = f["geometry"]["coordinates"][:2]
    # year shown on the timeline: for a dated range (quarter-century, half, century...) the END of the range ("not later than"),
    # not the midpoint, so that objects with rough dates do not appear earlier than their record allows
    ye_mid = p.get("year_est")
    ye_show = p.get("year_to") if (ye_mid is not None and p.get("date_precision") != "exact" and p.get("year_to")) else ye_mid
    orig_fn = func_orig(p)
    cur_fn = func_current(p, orig_fn)
    ph = [t for t, _ in photo_hits.get(str(p["id"]), []) if photo_info.get(t, {}).get("thumb") and photo_info[t].get("license") and not people.get(t, {}).get("reject") and t not in manual_reject]
    for t in ph:
        used[t] = photo_info[t]
    feats.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [round(x, 6), round(y, 6)]},
        "properties": {
            "id": p["id"], "name": p.get("name"), "address": p.get("address"), "cls": cls, "fn": cur_fn,
            "monument": p.get("status") == "monument", "national": bool(p.get("national")),
            "reg": p.get("registry_n"), "raw_date": p.get("raw_date"),
            "y0": p.get("year_from"), "y1": p.get("year_to"), "ye": ye_show, "ym": ye_mid,
            "prec": p.get("date_precision"), "src": p.get("date_source"),
            "unc": bool(p.get("location_uncertain")),
            **({"ruin": True} if RUIN_RX.search(p.get("name") or "") else {}),
            **({"fo": orig_fn} if orig_fn != cur_fn else {}),
            **({"ph": "|".join(ph)} if ph else {}),
            **({"wp": "|".join("%s:%s" % (l, t) for l, t in WP[str(p["id"])].items())} if str(p["id"]) in WP else {}),
        },
    })
json.dump({"type": "FeatureCollection", "features": feats},
          open(os.path.join(OUT, "monuments.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

json.dump(used, open(os.path.join(OUT, "photos.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("objects with photos:", sum(1 for f in feats if "ph" in f["properties"]), "files:", len(used))

plans_src = json.load(open(os.path.join(ROOT, "viewer", "maps.json"), encoding="utf-8"))
plans = []
for pl in sorted(plans_src, key=lambda p: p["year"]):
    if pl.get("site") is False:        # plans used only for tracing boundaries, not shown on the page
        continue
    pid = pl["id"]
    w = json.load(open(os.path.join(ROOT, "data", "warped", pid + ".json"), encoding="utf-8"))
    from PIL import Image as _Image
    _Image.MAX_IMAGE_PIXELS = None
    _im = _Image.open(os.path.join(ROOT, "data", "warped", pid + ".webp"))
    _sc = 3000.0 / max(_im.size)          # the page uses a lighter copy (long side 3000 px); full size stays in data/warped
    if _sc < 1:
        _im = _im.resize((round(_im.size[0] * _sc), round(_im.size[1] * _sc)), _Image.LANCZOS)
    _im.save(os.path.join(OUT, pid + ".webp"), "WEBP", quality=80, method=6)
    entry = {"id": pid, "year": pl["year"], "title": pl["title"], "source": pl["source"],
             "image": "data/%s.webp" % pid, "corners": w["corners"],
             "accuracy_m": round(w["loo_rms_m"]) if w.get("loo_rms_m") else None, "points": w["points"],
             "boundary": None}
    b = os.path.join(ROOT, "data", "boundaries", pid + ".geojson")
    if os.path.exists(b):
        shutil.copyfile(b, os.path.join(OUT, pid + "_boundary.geojson"))
        entry["boundary"] = "data/%s_boundary.geojson" % pid
        bj = json.load(open(b, encoding="utf-8"))
        entry["boundary_partial"] = any(f["properties"].get("partial") for f in bj["features"])
    plans.append(entry)
json.dump(plans, open(os.path.join(OUT, "plans.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copyfile(os.path.join(ROOT, "data", "city_area.json"), os.path.join(OUT, "city_area.json"))
shutil.copyfile(os.path.join(ROOT, "data", "district_history.json"), os.path.join(OUT, "district_history.json"))

# built-up area outlines by year (what the slider shows instead of old plans):
#   1735-1913    hand-traced from the plans (approximate; 1735 is a schematic plan, 1913 is only a partial line)
#   1972-2021    GUSV satellite built-up boundaries (CC BY 4.0), tools/extract_urban.py
# The 1980 outline traced from the Soviet topographic map (tbilisi_1980_topo.geojson) is NOT used here: it follows the
# filled blocks only, a different measure from the smoothed GUSV envelope, and would make the series jump.
def _round(c):
    return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [_round(x) for x in c]


urban = []
ACC = {1735: 150, 1954: 700}      # rough positional accuracy in metres where it is worse than ~100 m (shown on the page)
for pid, snap in (("tiflis_1735", 1735), ("tiflis_1782", 1782), ("tiflis_1785", 1785), ("tiflis_1800", 1800), ("tiflis_1802", 1802), ("tiflis_1844", 1844), ("tiflis_1879", 1879), ("tiflis_1887", 1887), ("tbilisi_1913", 1913), ("tbilisi_1954_ams", 1954)):
    b = os.path.join(ROOT, "data", "boundaries", pid + ".geojson")
    if os.path.exists(b):
        for f in json.load(open(b, encoding="utf-8"))["features"]:
            urban.append({"type": "Feature", "geometry": {"type": f["geometry"]["type"], "coordinates": _round(f["geometry"]["coordinates"])},
                          "properties": {"snap": snap, "src": "ams" if snap == 1954 else "traced", "kind": "city", "partial": bool(f["properties"].get("partial")), "acc": ACC.get(snap, 0)}})
g = os.path.join(ROOT, "data", "boundaries", "tbilisi_urban_gusv.geojson")
if os.path.exists(g):
    for f in json.load(open(g, encoding="utf-8"))["features"]:
        urban.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": _round(f["geometry"]["coordinates"])},
                      "properties": {"snap": f["properties"]["year"], "src": "gusv", "kind": f["properties"]["kind"], "partial": False}})
json.dump({"type": "FeatureCollection", "features": urban}, open(os.path.join(OUT, "urban.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
def _rdp(pts, eps):
    n = len(pts)
    if n < 5:
        return pts
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1
        norm = (dx * dx + dy * dy) ** 0.5
        best, bi = -1.0, -1
        for k in range(i + 1, j):
            x, y = pts[k]
            d = abs(dy * (x - x1) - dx * (y - y1)) / norm if norm else ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
            if d > best:
                best, bi = d, k
        if best > eps:
            keep[bi] = True
            stack += [(i, bi), (bi, j)]
    return [p for p, k in zip(pts, keep) if k]


def _simplify_ring(ring, eps=1.5):
    pts = [(x * 1e4, y * 1e4) for x, y in ring[:-1]]
    i0 = min(range(len(pts)), key=lambda k: pts[k][0])
    i1 = max(range(len(pts)), key=lambda k: pts[k][0])
    if i0 > i1:
        i0, i1 = i1, i0
    out = _rdp(pts[i0:i1 + 1], eps)[:-1] + _rdp(pts[i1:] + pts[:i0 + 1], eps)[:-1]
    out = [[round(x / 1e4, 5), round(y / 1e4, 5)] for x, y in out]
    return out + [out[0]]


# 10 districts (OpenStreetMap, ODbL): outlines + a label point with names in ka / en / ru
dj = os.path.join(ROOT, "data", "boundaries", "tbilisi_districts_osm.geojson")
if os.path.exists(dj):
    dfe = []
    for f in json.load(open(dj, encoding="utf-8"))["features"]:
        p = f["properties"]
        names = {"name_ka": p["name_ka"], "name_en": (p["name_en"] or "").replace(" District", ""),
                 "name_ru": (p["name_ru"] or "").replace("район ", "")}
        polys = [[_simplify_ring(r[0])] for r in f["geometry"]["coordinates"]]
        dfe.append({"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": polys}, "properties": dict(names)})
        dfe.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": p["label"]}, "properties": dict(names)})
    json.dump({"type": "FeatureCollection", "features": dfe}, open(os.path.join(OUT, "districts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("districts:", len(dfe) // 2)

# older city boundary candidate: geoBoundaries ADM2 "Tbilisi" (metadata year 2007, public domain); date NOT confirmed
gb = os.path.join(ROOT, "data", "raw", "admin", "geoBoundaries_GEO_ADM2.geojson")
if os.path.exists(gb):
    for f in json.load(open(gb, encoding="utf-8"))["features"]:
        if f["properties"].get("shapeName", "").strip() == "Tbilisi":
            g = f["geometry"]
            rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [q[0] for q in g["coordinates"]]
            json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {},
                       "geometry": {"type": "MultiPolygon", "coordinates": [[_simplify_ring(r, 2.0)] for r in rings]}}]},
                      open(os.path.join(OUT, "admin_old.json"), "w", encoding="utf-8"), separators=(",", ":"))

adm = os.path.join(ROOT, "data", "boundaries", "tbilisi_admin_2019.geojson")
if os.path.exists(adm):
    shutil.copyfile(adm, os.path.join(OUT, "admin.json"))
# settlements around Tbilisi with the year they were annexed (curated list + OSM place nodes; see data/settlements_curated.json)
_pl = os.path.join(ROOT, "data", "raw", "admin", "osm_places.json")
_cu = os.path.join(ROOT, "data", "settlements_curated.json")
if os.path.exists(_pl) and os.path.exists(_cu):
    def _inside(pt, rings):
        x, y = pt
        for ring in rings:
            c = False
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    c = not c
            if c:
                return True
        return False

    def _rings(f):
        g = f["geometry"]
        return [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]

    _old = [f for f in json.load(open(os.path.join(ROOT, "data", "raw", "admin", "geoBoundaries_GEO_ADM2.geojson"), encoding="utf-8"))["features"]
            if f["properties"].get("shapeName", "").strip() == "Tbilisi"]
    _new = json.load(open(adm, encoding="utf-8"))["features"] if os.path.exists(adm) else []
    old_r = _rings(_old[0]) if _old else []
    new_r = _rings(_new[0]) if _new else []
    places = json.load(open(_pl, encoding="utf-8"))
    out_s = []
    for it in json.load(open(_cu, encoding="utf-8"))["items"]:
        node = next((e for e in places if (e["tags"].get("name:en") or e["tags"].get("name")) == it["en"] and e["tags"].get("place") == it["place"]), None)
        if not node:
            print("settlement not found in OSM:", it["en"], it["place"])
            continue
        t = node["tags"]
        pt = (node["lon"], node["lat"])
        geom = "inside_old" if _inside(pt, old_r) else ("outside_old_inside_2019" if _inside(pt, new_r) else "outside_2019")
        nm = lambda k: (t.get("name:" + k) or "").replace("село ", "").replace("Village ", "").replace("სოფელი ", "")
        out_s.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(pt[0], 5), round(pt[1], 5)]},
                      "properties": {"name_ka": nm("ka") or t.get("name"), "name_en": nm("en") or it["en"].replace("Village ", ""), "name_ru": nm("ru"),
                                     "joined": it.get("year"), "from": it.get("from"), "note": it.get("note"), "geom": geom,
                                     "conflict": bool(it.get("year") and it["year"] < 2006 and geom == "outside_old_inside_2019")}})
    json.dump({"type": "FeatureCollection", "features": out_s}, open(os.path.join(OUT, "settlements.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("settlements:", len(out_s), {g: sum(1 for f in out_s if f["properties"]["geom"] == g) for g in ("inside_old", "outside_old_inside_2019", "outside_2019")})
print("urban outlines:", len(urban), "years:", sorted({f["properties"]["snap"] for f in urban}))
print("monuments:", len(feats), "unknown classes:", unknown, "plans:", [(p["id"], p["accuracy_m"], bool(p["boundary"])) for p in plans])
