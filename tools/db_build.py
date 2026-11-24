"""Builds the project index data/db/project.sqlite (schema: tools/db/schema.sql) from the JSON files of the site (site/data/*.json), the results of the verifiers (data/cache/*_verified.json) and the tasks for Gemini
(work/gemini). The JSON files stay the source of truth: the index is derived, it is rebuilt from nothing every time (written to a temporary file, then put in place), it is not in git.
What it gives: one table of objects of all the layers with a region (country > city > district), names in three languages with their kinds (official / old / folk / alt), facts with the source, the quotation and the state
(imported / verified), photographs, the state of every task for Gemini, an R-tree for "what lies near", a full-text search of the names. Queries: tools/db_query.py.
For the whole of Georgia: a new city is a new region row and new files read by the same importers (each importer takes a file and a region); the ids "<layer>:<id>" do not repeat; the volume of SQLite is not a limit
(millions of rows). Usage: python -P tools/db_build.py [--check] [--georgia] [--raw-all]    (--check: the numbers of the index are compared with the JSON files and the exit code says whether they agree)
"""
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
import urllib.parse

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(R, "site", "data")
DB = os.path.join(R, "data", "db", "project.sqlite")
LANGS = ("ka", "ru", "en")
_rd = os.path.join(R, "tools", "register_names_dict.json")
REGDICT = json.load(open(_rd, encoding="utf-8")) if os.path.exists(_rd) else {}          # typical names of the register: {ka: {ru, en}}
# The cities that the index reads. Every city has its own region id (ISO 3166-2:GE style), a short code that goes into every object id ("TB/mn:KAW_015": no id repeats between cities) and a folder of data files of the
# same layout as site/data. A new city = a new entry here (+ its folder); nothing else in this file mentions Tbilisi.
CITIES = [{"region": "GE-TB", "code": "TB", "dir": os.path.join(R, "site", "data"), "ka": "თბილისი", "ru": "Тбилиси", "en": "Tbilisi"}]
CTX = dict(CITIES[0])                                              # the city that is being read now


def jl(name):
    return json.load(open(os.path.join(CTX["dir"], name), encoding="utf-8"))


class Builder:
    def __init__(self, con):
        self.c = con
        self.src = {}
        self.polys = []

    def source(self, url, lang=None):
        if not url:
            return None
        if url not in self.src:
            host = (urllib.parse.urlparse(url).hostname or "").replace("www.", "")
            cur = self.c.execute("INSERT INTO source(url, host, lang) VALUES (?,?,?)", (url, host, lang))
            self.src[url] = cur.lastrowid
        return self.src[url]

    def region_of(self, lon, lat):
        for rid, ring, box in self.polys:
            if box[0] <= lon <= box[2] and box[1] <= lat <= box[3] and inside(lon, lat, ring):
                return rid
        return CTX["region"]

    def obj(self, layer, local_id, lon=None, lat=None, kind=None, y0=None, y1=None, status=None, props=None, code=None, region=None):
        oid = (code or CTX["code"]) + "/" + layer + ":" + str(local_id)
        region = region or (self.region_of(lon, lat) if lon is not None and lat is not None else CTX["region"])
        cur = self.c.execute("INSERT INTO object(id, layer, local_id, region, kind, lat, lon, year_from, year_to, status, props) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                             (oid, layer, str(local_id), region, kind, lat, lon, y0, y1, status, json.dumps(props, ensure_ascii=False) if props else None))
        if lon is not None and lat is not None:
            self.c.execute("INSERT INTO object_geo VALUES (?,?,?,?,?)", (cur.lastrowid, lon, lon, lat, lat))
        return oid

    def names(self, oid, n, kind="official", y0=None, y1=None, pend=0):
        for lg in LANGS:
            v = (n or {}).get(lg)
            if v:
                self.c.execute("INSERT INTO name(object_id, lang, name, kind, year_from, year_to, pend) VALUES (?,?,?,?,?,?,?)", (oid, lg, v, kind, y0, y1, pend))
                self.c.execute("INSERT INTO name_fts(name, object_id, lang, kind) VALUES (?,?,?,?)", (v, oid, lg, kind))

    def fact(self, oid, key, value, lang=None, url=None, quote=None, status="imported", slang=None):
        if value in (None, "", []):
            return
        self.c.execute("INSERT INTO fact(object_id, key, lang, value, source_id, quote, status) VALUES (?,?,?,?,?,?,?)", (oid, key, lang, str(value), self.source(url, slang), quote, status))

    def fact_langs(self, oid, key, d, **kw):
        for lg in LANGS:
            if isinstance(d, dict) and d.get(lg):
                self.fact(oid, key, d[lg], lang=lg, **kw)

    def media(self, oid, file, photos, near=0):
        p = (photos or {}).get(file) if file else None
        if p and p.get("thumb"):
            self.c.execute("INSERT INTO media(object_id, kind, file, thumb, page, author, license, near) VALUES (?,?,?,?,?,?,?,?)",
                           (oid, "photo", file, p.get("thumb"), p.get("page"), p.get("author"), p.get("license"), 1 if near else 0))


def inside(x, y, ring):
    c, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi, xj, yj = ring[i][0], ring[i][1], ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def seed_country(b):
    c = b.c
    c.executemany("INSERT INTO layer VALUES (?,?,?,?)", [
        ("reg", "Heritage register of Georgia (buildings)", "monuments.json", "public register, see NOTICE.md"),
        ("rel", "Religious buildings (curated)", "religious.json", "own texts CC BY-NC; OSM ODbL"),
        ("relosm", "Places of worship of OpenStreetMap", "religious_osm.json", "ODbL"),
        ("sci", "Science and culture", "science.json", "own texts CC BY-NC"),
        ("edu", "Education", "education.json", "own texts CC BY-NC"),
        ("pl", "Local names (quarters, parks, bridges ...)", "places.json", "Wikipedia CC BY-SA; OSM ODbL"),
        ("mn", "Monuments and sculptures", "sculptures.json", "OSM ODbL; Commons licences per file"),
        ("pq", "Memorial plaques", "plaques.json", "OSM ODbL; Commons licences per file"),
        ("md", "Soviet modernism", "modernism.json", "quotations of the pages named"),
        ("st", "Streets and their names through the years", "street_names.json", "encyclopedia 2008; Wikipedia"),
    ])
    c.execute("INSERT INTO region VALUES ('GE','country',NULL,'საქართველო','Грузия','Georgia')")


def seed_city(b):
    c = b.c
    b.polys = []
    b.city_polys = getattr(b, "city_polys", {})
    c.execute("INSERT INTO region VALUES (?,?,?,?,?,?)", (CTX["region"], "city", "GE", CTX["ka"], CTX["ru"], CTX["en"]))
    for f in jl("districts.json")["features"]:
        p = f["properties"]
        rid = CTX["region"] + "-" + p["name_en"].replace(" ", "")
        if not c.execute("SELECT 1 FROM region WHERE id=?", (rid,)).fetchone():
            c.execute("INSERT INTO region VALUES (?,?,?,?,?,?)", (rid, "district", CTX["region"], p.get("name_ka"), p.get("name_ru"), p["name_en"]))
        g = f["geometry"]
        if g["type"] not in ("Polygon", "MultiPolygon"):                  # the label points of the districts
            continue
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            ring = poly[0]
            xs, ys = [q[0] for q in ring], [q[1] for q in ring]
            b.polys.append((rid, ring, (min(xs), min(ys), max(xs), max(ys))))
    b.city_polys[CTX["region"]] = list(b.polys)


# ---- the register of immovable cultural heritage of the WHOLE of Georgia (data/raw/PS.ImmovableMonumentObjectP_<date>.geojson, a new file every week; tools/register_diff.py compares two of them) ----------------------
GEORGIA = "--georgia" in sys.argv                                  # load the register of the whole country (20,715 objects, an index of about 100 MB) instead of Tbilisi only (2,599)
REGISTRY_URL = "https://memkvidreoba.gov.ge/downloads/PS.ImmovableMonumentObjectP/"
REGIONS = {"კახეთი": ("GE-KA", "Kakheti", "Кахетия"), "მცხეთა-მთიანეთი": ("GE-MM", "Mtskheta-Mtianeti", "Мцхета-Мтианети"), "თბილისი": ("GE-TB", "Tbilisi", "Тбилиси"),
           "სამეგრელო-ზემო სვანეთი": ("GE-SZ", "Samegrelo-Zemo Svaneti", "Самегрело-Земо-Сванети"), "ქვემო ქართლი": ("GE-KK", "Kvemo Kartli", "Квемо-Картли"),
           "შიდა ქართლი": ("GE-SK", "Shida Kartli", "Шида-Картли"), "სამცხე-ჯავახეთი": ("GE-SJ", "Samtskhe-Javakheti", "Самцхе-Джавахети"), "იმერეთი": ("GE-IM", "Imereti", "Имерети"),
           "რაჭა-ლეჩხუმი-ქვემო სვანეთი": ("GE-RL", "Racha-Lechkhumi and Kvemo Svaneti", "Рача-Лечхуми и Квемо-Сванети"), "აჭარა": ("GE-AJ", "Adjara", "Аджария"), "აფხაზეთი": ("GE-AB", "Abkhazia", "Абхазия"),
           "გურია": ("GE-GU", "Guria", "Гурия")}
KINDS = {"არქიტექტურის": "architecture", "არქეოლოგიური": "archaeology", "მემორიალური": "memorial", "საინჟინრო": "engineering", "ეთნოგრაფიული": "ethnography", "ქალაქთმშენებლობის (ურბანული)": "urban"}


def register_file():
    fs = sorted(glob.glob(os.path.join(R, "data", "raw", "PS.ImmovableMonumentObjectP_*.geojson")), key=lambda p: (re.findall(r"(\d+)\.(\d+)\.(\d+)", p) or [("0", "0", "0")])[0][::-1])
    return fs[-1] if fs else None


def load_register_national(b):
    """all the objects of the register: Georgia > region > municipality (> district of Tbilisi); the Tbilisi objects get the derived fields of the site (years, class) when they are found by place and name"""
    path = register_file()
    if not path:
        return
    feats = json.load(open(path, encoding="utf-8"))["features"]
    site_ids = {f["properties"]["id"] for f in jl("monuments.json")["features"]} if CITIES else set()
    if not GEORGIA:                                                  # the project is about Tbilisi (plus any near-ring objects in monuments.json): the rest of the country is loaded only on request (--georgia)
        feats = [f for f in feats if f["properties"].get("Region") == "თბილისი" or f["properties"].get("ID") in site_ids]
    c = b.c
    site, site_id = {}, {}
    for f in jl("monuments.json")["features"] if CITIES else []:
        k = (round(f["geometry"]["coordinates"][0], 4), round(f["geometry"]["coordinates"][1], 4), f["properties"]["name"])
        site.setdefault(k, f["properties"])
        site_id[str(f["properties"]["id"])] = f["properties"]            # the register ID is the id of the site object: the link by it does not depend on a rounded point or a spelling of the name
    for ka, (rid, en, ru) in REGIONS.items():
        if rid != "GE-TB":
            c.execute("INSERT OR IGNORE INTO region VALUES (?,?,?,?,?,?)", (rid, "region", "GE", ka, ru, en))
    date = (re.findall(r"(\d+\.\d+\.\d+)", path) or [""])[0]
    src = b.source(REGISTRY_URL)
    for f in feats:
        p = {k: (None if v in ("None", "", None) else v) for k, v in f["properties"].items()}
        rg = p.get("Region")
        rid, _, _ = REGIONS.get(rg, ("OUT-" + hashlib.md5((rg or "").encode("utf-8")).hexdigest()[:6], None, None))
        if rid.startswith("OUT-"):
            c.execute("INSERT OR IGNORE INTO region VALUES (?,?,?,?,?,?)", (rid, "outside", None, rg, None, None))
        region = rid
        if p.get("Municipality") and rid != "GE-TB":
            region = rid + "/" + p["Municipality"]
            c.execute("INSERT OR IGNORE INTO region VALUES (?,?,?,?,?,?)", (region, "municipality", rid, p["Municipality"], None, None))
        try:
            lon, lat = float(p["X"]), float(p["Y"])
        except (TypeError, ValueError):
            lon = lat = None
        code = rid.split("-")[1] if rid != "GE-TB" else "TB"
        kind = ",".join(KINDS.get(t.strip(), t.strip()) for t in (p.get("Classification") or "").split(",") if t.strip()) or None
        props = {k: p[k] for k in ("RegistryN", "Settlement", "ComplexName") if p.get(k)}
        y0 = y1 = None
        st = (site_id.get(str(p.get("ID"))) or site.get((round(lon, 4), round(lat, 4), p.get("Name")))) if lon is not None and (rid == "GE-TB" or str(p.get("ID")) in site_id) else None
        if st:
            y0, y1 = st.get("ye") or st.get("y0"), st.get("y1")
            props["site_id"] = st["id"]
            props["fn"] = st.get("fn")
        else:
            m = re.search(r"(\d{3,4})\s*წ", p.get("ExactDate") or "")
            y0 = y1 = int(m.group(1)) if m else None
        oid = b.obj("reg", p["ID"], lon, lat, kind, y0, y1, "protected" if p.get("StatusName") == "კულტურული მემკვიდრეობის ძეგლი" else p.get("StatusName") and "object", props, code=code,
                    region=None if rid == "GE-TB" else region)
        nm = p.get("Name") or p.get("FullName")
        if nm:
            b.names(oid, {"ka": nm, **REGDICT.get(nm, {})})                  # a typical name of the register in ru and en (tools/register_names_dict.json: the same words as the site, 59 names, about 79 % of the objects)
        for key, col in (("description", "Description"), ("period", "Period"), ("exact_date", "ExactDate"), ("initial_function", "InitialFunction"), ("current_function", "CurrentFunction"),
                         ("address", "Address"), ("protection_status", "StatusName"), ("category", "CategoryName"), ("coordinates_accuracy", "Accuracy"), ("registry_number", "RegistryN")):
            if p.get(col):
                b.c.execute("INSERT INTO fact(object_id, key, lang, value, source_id, quote, status) VALUES (?,?,?,?,?,?,?)", (oid, key, "ka" if key in ("description", "period", "exact_date", "initial_function", "current_function", "address") else None, p[col], src, None, "imported"))
        if p.get("DateRangeFrom") or p.get("DateRangeTo"):
            b.fact(oid, "date_range", "%s – %s" % (p.get("DateRangeFrom") or "", p.get("DateRangeTo") or ""), url=REGISTRY_URL)
    b.c.execute("INSERT INTO fact(object_id, key, lang, value, source_id, quote, status) SELECT 'GE', 'register_file', NULL, ?, ?, NULL, 'imported' WHERE 0", (date, src))


def load_lists(b):
    for fname, layer, kindk in (("religious.json", "rel", "rel"), ("science.json", "sci", "kind"), ("education.json", "edu", "kind")):
        for x in jl(fname):
            oid = b.obj(layer, x["id"], x["lon"], x["lat"], x.get(kindk), x.get("from"), x.get("to") if isinstance(x.get("to"), int) else None, None,
                        {k: x.get(k) for k in ("date", "rel") if x.get(k)})
            b.names(oid, x.get("name"))
            b.fact_langs(oid, "status" if layer == "rel" else "note", x.get("status") if layer == "rel" else x.get("note"))
    d = jl("religious_osm.json")
    for x in d["items"]:
        oid = b.obj("relosm", x["id"], x["lon"], x["lat"], x["rel"], None if x.get("undated") else x["from"], None, None, {"osm": x.get("osm"), "date": x.get("date"), "street": x.get("st")})
        b.names(oid, x.get("name"), pend=1 if x.get("pend") else 0)
        for u in x.get("src") or []:
            b.fact(oid, "wikipedia", u, url=u)


def load_places(b):
    for x in jl("places.json")["items"]:
        oid = b.obj("pl", x["id"], x["lon"], x["lat"], x["k"], None, None, None, {k: x[k] for k in ("pk", "ap", "ne", "wp") if x.get(k)} | ({"area": True} if x.get("g") else {}))
        b.names(oid, x["n"], pend=1 if x.get("pend") else 0)
        if x.get("o"):
            b.names(oid, x["o"], "old", pend=1 if x.get("pend") else 0)
        if x.get("al"):
            b.names(oid, x["al"], "alt", pend=1 if x.get("pend") else 0)
        s = x.get("s") or {}
        b.fact_langs(oid, "description", x.get("a"), url=s.get("u"), quote=s.get("aq"), status="verified" if s.get("aq") else "imported", slang=s.get("l"))
        eq = s.get("eq") or {}
        b.fact_langs(oid, "origin", x.get("e"), url=eq.get("u"), quote=eq.get("q"), status="verified" if eq.get("q") else "imported", slang=eq.get("l"))
        if x.get("pk") and s.get("u"):
            b.fact(oid, "source_object", s["u"], url=s["u"])
        for fo in x.get("f") or []:
            b.names(oid, fo["n"], "folk")
            q = (fo.get("s") or [{}])[0]
            b.fact_langs(oid, "folk_meaning", fo.get("m"), url=q.get("u"), quote=q.get("q"), status="verified", slang=q.get("l"))
            for extra in (fo.get("s") or [])[1:]:
                b.fact(oid, "folk_source", extra["u"], url=extra["u"], quote=extra["q"], status="verified", slang=extra.get("l"))


def load_monuments(b):
    for fname, layer in (("sculptures.json", "mn"), ("plaques.json", "pq"), ("modernism.json", "md")):
        d = jl(fname)
        for x in d["items"]:
            props = {k: x[k] for k in ("st", "phn", "pend", "wd", "ins") if x.get(k)}
            if x.get("ar"):
                props["architect"] = x["ar"]
            if x.get("mat"):
                props["material"] = x["mat"]
            oid = b.obj(layer, x["id"], x["lon"], x["lat"], x.get("k") or ("plaque" if layer == "pq" else None), x.get("y"), None, x.get("st") if layer == "md" else None, props)
            b.names(oid, x["n"], pend=1 if x.get("pend") else 0)
            sc = x.get("sc")
            if sc:
                b.fact(oid, "sculptor", sc if isinstance(sc, str) else (sc.get("en") or sc.get("ru") or sc.get("ka")))
            dq = x.get("dq") or ([{"u": s["u"], "l": s["l"], "q": s["q"]} for s in x.get("s", [])] if layer == "md" else [])
            q0 = dq[0] if dq else {}
            b.fact_langs(oid, "description", x.get("d"), url=q0.get("u"), quote=q0.get("q"), status="verified" if dq else "imported", slang=q0.get("l"))
            for q in dq[1:]:
                b.fact(oid, "source_quote", q["q"], url=q["u"], quote=q["q"], status="verified", slang=q.get("l"))
            if layer == "md":
                b.fact_langs(oid, "function_then", x.get("ft"))
                b.fact_langs(oid, "function_now", x.get("fn"))
                for fo in x.get("f") or []:
                    b.names(oid, fo["n"], "folk")
                    fq = (fo.get("s") or [{}])[0]
                    b.fact_langs(oid, "folk_meaning", fo.get("m"), url=fq.get("u"), quote=fq.get("q"), status="verified", slang=fq.get("l"))
                g = x.get("g") or {}
                b.fact(oid, "point_origin", g.get("how"), url=g.get("ref") if str(g.get("ref", "")).startswith("http") else None)
            for lg, u in (x.get("w") or {}).items():
                b.fact(oid, "wikipedia", u, lang=lg, url=u, slang=lg)
            b.media(oid, x.get("ph"), d.get("photos"), x.get("phn"))


def load_streets(b):
    for s in jl("street_names.json")["streets"]:
        key = s.get("geom") or s["now"]["en"]
        oid = b.obj("st", key, None, None, "street", None, None, None, {"nogeom": True} if s.get("nogeom") else None)
        b.names(oid, s["now"])
        for y0, y1, n in s.get("iv") or []:
            if n:
                b.names(oid, n, "old", y0, y1)
        if s.get("src"):
            b.fact(oid, "source", s["src"], url=s["src"] if str(s["src"]).startswith("http") else None)
        if s.get("book"):
            b.fact(oid, "book", json.dumps(s["book"], ensure_ascii=False))


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemini_all import TASKS as _PACKAGE  # noqa: E402
from paths import GEMINI  # noqa: E402
CURRENT_TASKS = {os.path.splitext(os.path.basename(t[0]))[0] for t in _PACKAGE}      # the tasks of the package tools/gemini_all.py makes: only these can be "queued"


def load_tasks(b):
    FD = GEMINI
    prefix = {"churches": "relosm:", "monuments": "mn:", "parks": "pl:"}                      # the tasks of work/gemini are about the city of CTX
    for tf in sorted(glob.glob(os.path.join(FD, "tasks", "*.md"))):
        tid = os.path.splitext(os.path.basename(tf))[0]
        rf = os.path.join(FD, "results", tid + ".json")
        status, rows, found, data = "queued", None, None, None
        if os.path.exists(rf):
            try:
                data = json.load(open(rf, encoding="utf-8"))
            except ValueError:
                data = None
            if isinstance(data, list):
                rows = len(data)
                found = sum(1 for x in data if isinstance(x, dict) and x.get("status") == "found")
                status = "empty" if rows and all(isinstance(x, dict) and x.get("status") == "not_found" for x in data) else "done"
            elif isinstance(data, dict):
                rows, found, status = len(data), len(data), "done"
        if status == "queued" and tid not in CURRENT_TASKS:
            status = "archive"                                   # an old task whose answer was taken under another file name: not waiting for anything
        b.c.execute("INSERT INTO task VALUES (?,?,?,?,?,?,?)", (tid, tid.split("_")[0], os.path.relpath(tf, R), os.path.relpath(rf, R), status, rows, found))
        pre = prefix.get(tid.split("_")[0], "")
        for x in (data if isinstance(data, list) else [{"id": k, "status": "found"} for k in (data or {})]):
            if isinstance(x, dict):
                rid = str(x.get("id", x.get("row", "")))
                oid = CTX["code"] + "/" + pre + rid
                b.c.execute("INSERT INTO task_row VALUES (?,?,?,?)", (tid, oid if b.c.execute("SELECT 1 FROM object WHERE id=?", (oid,)).fetchone() else None, rid, x.get("status")))


# ---- raw data: the files of data/raw that are records (Overpass answers, GeoJSON), loaded as they are ---------------------------------------------------------------------------------------------------------------
RAW_ALL = "--raw-all" in sys.argv                                  # also the footprints of the buildings (76 MB of JSON; the index grows by about as much)


def raw_files():
    out = []
    for pat, source, kind in (("data/raw/osm_extra/*.json", "osm", "overpass"), ("data/raw/osm_transport/*.json", "osm", "overpass"), ("data/raw/osm_roads/*.json", "osm", "overpass"),
                              ("data/raw/admin/geoBoundaries_*.geojson", "geoboundaries", "geojson"), ("data/raw/admin/osm_places.json", "osm", "list"), ("data/raw/admin/osm_water.json", "osm", "list")) +                              ((("data/raw/osm_buildings/*.json", "osm", "overpass"),) if RAW_ALL else ()):
        for f in sorted(glob.glob(os.path.join(R, pat))):
            out.append((f, source, kind))
    return out


def centre(geom_pts, b=None):
    if b:
        return (b["minlat"] + b["maxlat"]) / 2, (b["minlon"] + b["maxlon"]) / 2
    return None, None


def load_raw(b):
    c = b.c
    for path, source, kind in raw_files():
        raw = open(path, "rb").read()
        data = json.loads(raw.decode("utf-8"))
        recs = data["elements"] if isinstance(data, dict) and "elements" in data else data["features"] if isinstance(data, dict) and "features" in data else data if isinstance(data, list) else None
        if recs is None:                                           # a file that is not a list of records (a single answer): not loaded as records
            print("  raw file skipped (not a list of records):", os.path.relpath(path, R))
            continue
        cur = c.execute("INSERT INTO raw_file(path, source, kind, bytes, sha256, records) VALUES (?,?,?,?,?,?)", (os.path.relpath(path, R).replace("\\", "/"), source, kind, len(raw), hashlib.sha256(raw).hexdigest(), len(recs)))
        fid = cur.lastrowid
        for e in recs:
            lat = lon = geom = None
            if "tags" in e or "type" in e and e.get("type") in ("node", "way", "relation"):          # an element of Overpass
                rid, typ, tags = "%s/%s" % (e["type"], e["id"]), e["type"], e.get("tags")
                if "center" in e:
                    lat, lon = e["center"]["lat"], e["center"]["lon"]
                elif "lat" in e:
                    lat, lon = e["lat"], e["lon"]
                elif "bounds" in e:
                    lat, lon = centre(None, e["bounds"])
                if e.get("geometry"):
                    geom = json.dumps([[q["lon"], q["lat"]] for q in e["geometry"] if q], separators=(",", ":"))
                elif e.get("members"):
                    geom = json.dumps({"members": [{"type": m["type"], "ref": m["ref"], "role": m.get("role")} for m in e["members"]]}, separators=(",", ":"))
            elif e.get("type") == "Feature":                       # a feature of GeoJSON
                pr = e.get("properties") or {}
                rid, typ, tags = str(pr.get("shapeID") or pr.get("ID") or len(pr)), "feature", pr
                g = e.get("geometry")
                if g:
                    geom = json.dumps(g, separators=(",", ":"))
                    flat = []
                    def walk(x):
                        if x and isinstance(x[0], (int, float)):
                            flat.append(x)
                        else:
                            for y in x:
                                walk(y)
                    walk(g["coordinates"])
                    if flat:
                        lon = sum(q[0] for q in flat) / len(flat)
                        lat = sum(q[1] for q in flat) / len(flat)
            else:                                                  # a plain record of a list
                tags = e
                rid, typ = str(e.get("id") or e.get("osm_id") or len(str(e))), "record"
                lat, lon = e.get("lat"), e.get("lon")
            r = c.execute("INSERT INTO raw_record(file_id, source, rid, type, lat, lon, tags, geom) VALUES (?,?,?,?,?,?,?,?)",
                          (fid, source, rid, typ, lat, lon, json.dumps(tags, ensure_ascii=False, separators=(",", ":")) if tags is not None else None, geom))
            if lat is not None and lon is not None:
                c.execute("INSERT INTO raw_geo VALUES (?,?,?,?,?)", (r.lastrowid, lon, lon, lat, lat))


def load_raw_register(b):
    """the register as the source gave it: every property, Tbilisi only unless --georgia"""
    path = register_file()
    if not path:
        return
    raw = open(path, "rb").read()
    feats = json.loads(raw.decode("utf-8"))["features"]
    c = b.c
    keep = [f for f in feats if GEORGIA or f["properties"].get("Region") == "თბილისი"]
    fid = c.execute("INSERT INTO raw_file(path, source, kind, bytes, sha256, records) VALUES (?,?,?,?,?,?)", (os.path.relpath(path, R).replace("\\", "/"), "register", "geojson", len(raw), hashlib.sha256(raw).hexdigest(), len(keep))).lastrowid
    for f in keep:
        p = f["properties"]
        try:
            lon, lat = float(p["X"]), float(p["Y"])
        except (TypeError, ValueError):
            lon = lat = None
        r = c.execute("INSERT INTO raw_record(file_id, source, rid, type, lat, lon, tags, geom) VALUES (?,?,?,?,?,?,?,?)", (fid, "register", str(p["ID"]), "feature", lat, lon, json.dumps(p, ensure_ascii=False, separators=(",", ":")), None))
        if lat is not None:
            c.execute("INSERT INTO raw_geo VALUES (?,?,?,?,?)", (r.lastrowid, lon, lon, lat, lat))


def check(con):
    """the numbers of the index against the JSON files of the current city; returns the list of differences"""
    bad = []
    exp = {"rel": len(jl("religious.json")), "sci": len(jl("science.json")), "edu": len(jl("education.json")),
           "relosm": len(jl("religious_osm.json")["items"]), "pl": len(jl("places.json")["items"]), "mn": len(jl("sculptures.json")["items"]), "pq": len(jl("plaques.json")["items"]),
           "md": len(jl("modernism.json")["items"]), "st": len(jl("street_names.json")["streets"])}
    for layer, n in exp.items():
        got = con.execute("SELECT COUNT(*) FROM object WHERE layer=? AND id LIKE ?", (layer, CTX["code"] + "/%")).fetchone()[0]
        if got != n:
            bad.append("%s: %d in the index, %d in the file" % (layer, got, n))
    nph = con.execute("SELECT COUNT(DISTINCT m.object_id) FROM media m JOIN object o ON o.id = m.object_id WHERE o.layer = 'mn'").fetchone()[0]
    nj = sum(1 for x in jl("sculptures.json")["items"] if x.get("ph"))
    if nph != nj:
        bad.append("photos of monuments: %d in the index, %d in the file" % (nph, nj))
    if con.execute("SELECT COALESCE(SUM(records), 0) FROM raw_file").fetchone()[0] != con.execute("SELECT COUNT(*) FROM raw_record").fetchone()[0]:
        bad.append("raw records: the files and the table disagree")
    geo = con.execute("SELECT COUNT(*) FROM object_geo").fetchone()[0]
    pts = con.execute("SELECT COUNT(*) FROM object WHERE lat IS NOT NULL").fetchone()[0]
    if geo != pts:
        bad.append("R-tree %d, points %d" % (geo, pts))
    return bad


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    tmp = DB + ".tmp"
    if os.path.exists(tmp):
        os.replace(tmp, tmp + ".old")                                 # a leftover of a failed run is put aside (the next failure replaces it)
    con = sqlite3.connect(tmp)
    con.executescript(open(os.path.join(R, "tools", "db", "schema.sql"), encoding="utf-8").read())
    b = Builder(con)
    seed_country(b)
    bad = []
    for city in CITIES:
        CTX.update(city)
        seed_city(b)
        for fn in (load_lists, load_places, load_monuments, load_streets, load_tasks):
            fn(b)
        bad += check(con)
    load_raw(b)
    load_raw_register(b)
    CTX.update(CITIES[0])
    b.polys = b.city_polys[CITIES[0]["region"]]                       # the districts of Tbilisi place the objects of the register that are in the city
    load_register_national(b)
    path = register_file()
    site_ids = {f["properties"]["id"] for f in jl("monuments.json")["features"]} if CITIES else set()
    n_raw = sum(1 for f in json.load(open(path, encoding="utf-8"))["features"] if GEORGIA or f["properties"].get("Region") == "თბილისი" or f["properties"].get("ID") in site_ids) if path else 0
    n_reg = con.execute("SELECT COUNT(*) FROM object WHERE layer = 'reg'").fetchone()[0]
    if n_reg != n_raw:
        bad.append("register: %d in the index, %d in the file" % (n_reg, n_raw))
    n_tb = con.execute("SELECT COUNT(*) FROM object WHERE layer = 'reg' AND (id LIKE 'TB/%' OR props LIKE '%site_id%')").fetchone()[0]
    if n_tb != len(jl("monuments.json")["features"]):
        bad.append("register of Tbilisi: %d in the index, %d in the file of the site" % (n_tb, len(jl("monuments.json")["features"])))
    if con.execute("SELECT COUNT(*) FROM object WHERE layer = 'reg' AND id LIKE 'TB/%' AND props LIKE '%site_id%'").fetchone()[0] < n_tb * 0.9:
        bad.append("register of Tbilisi: fewer than 90 %% of the objects found in the file of the site")
    con.commit()
    for layer, n in con.execute("SELECT layer, COUNT(*) FROM object GROUP BY layer ORDER BY 2 DESC"):
        print("  %-7s %6d objects" % (layer, n))
    print("names:", con.execute("SELECT COUNT(*) FROM name").fetchone()[0], "| facts:", con.execute("SELECT COUNT(*) FROM fact").fetchone()[0], "(verified: %d)" % con.execute("SELECT COUNT(*) FROM fact WHERE status='verified'").fetchone()[0],
          "| sources:", con.execute("SELECT COUNT(*) FROM source").fetchone()[0], "| photos:", con.execute("SELECT COUNT(*) FROM media").fetchone()[0], "| tasks:", con.execute("SELECT COUNT(*) FROM task").fetchone()[0])
    con.execute("PRAGMA optimize")
    con.close()
    os.replace(tmp, DB)
    print("index:", os.path.relpath(DB, R), "%d KB" % (os.path.getsize(DB) // 1024), "|", "consistent with the JSON files" if not bad else "DIFFERENCES: " + "; ".join(bad))
    if "--check" in sys.argv and bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
