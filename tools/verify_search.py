"""Checks the results of a search for the names of nameless places of worship ("churches") and for the descriptions and photographs of monuments without information ("monuments"). The same schema as the tasks
for Gemini (work/gemini/tasks/churches_B*.md and tasks/monuments_E*.md), whoever made the search.
Usage: python -P tools/verify_search.py churches|monuments <result.json> [--refresh]   Output: data/cache/<kind>_verified.json ({"ok": [rows], "rejected": [{id, why}]}; the rows of several runs are merged by id).
churches: the object is a nameless one of site/data/religious_osm.json; status found: name in ka / ru / en (ka Georgian, no Cyrillic in ka and en, ru Cyrillic); every quotation (<= 30 words) stands verbatim on its
 page (tools/safe_fetch.py); a "name" quotation shares a word of 4+ letters with the name; the PLACE is proved: the address is geocoded by Nominatim within 250 m of the object, or a quotation holds the name of the nearest
 street; a year only when a "year" quotation holds it.
monuments: the object is one of the sculptures; found: description in ru / en / ka (no Cyrillic in ka and en) whose years stand in quotations; quotations verbatim; the year / sculptor only with a quotation of that fact;
 "commons_file" exists on Commons and either its title / description / categories share a word of 4+ letters with a name of the object, or its geotag lies within 100 m (ka must be Georgian and so on as above).
"""
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_fetch import fetch_text  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; read-only API client)"}
GE, CY, LAT = re.compile("[ა-ჰ]"), re.compile("[А-Яа-яЁё]"), re.compile("[A-Za-z]")


def canon(s):
    """the text of a page comes out of the HTML with spaces round links and footnotes ("poet , and" / "Azerbaijani [ 1 ] [ 2 ] poet"): only such spaces and the footnote marks are ignored, the words are compared as they are"""
    s = re.sub(r"\[\s*\d+\s*\]", " ", norm(s))
    s = re.sub(r"\s+([,.;:!?)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return re.sub(r"\s+", " ", s).strip().replace("“", '"').replace("”", '"').replace("«", '"').replace("»", '"').replace("’", "'").casefold()


def words(s):
    return {w.casefold() for w in re.findall(r"[^\W\d_]{4,}", s or "")}


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(a))


def get(url):
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception:                                    # noqa: BLE001 - a network error: wait and retry
            time.sleep(6 * (i + 1))
    return None


def quotes_ok(row, why):
    qs = []
    if not row.get("sources"):
        why.append("no source")
    for s in row.get("sources", []):
        q, u = s.get("quote") or "", s.get("url") or ""
        if not q or len(q.split()) > 30:
            why.append("quotation empty or over 30 words")
            continue
        page = fetch_text(u)
        if page is None:
            why.append("page not readable: " + u[:60])
        elif canon(q) not in canon(page):
            why.append("quotation not on the page: " + u[:60])
        else:
            qs.append(s)
    return qs


def check_church(row, ob, geo_cache):
    why = []
    o = ob.get(row["id"])
    if not o or any(o["name"].values()):
        return ["not a nameless object of the layer"]
    if row["status"] != "found":
        return ["not_found"]
    n = row.get("name") or {}
    if not (n.get("ka") and GE.search(n["ka"]) and not CY.search(n["ka"])):
        why.append("bad ka")
    if not (n.get("ru") and CY.search(n["ru"]) and not GE.search(n["ru"])):
        why.append("bad ru")
    if not (n.get("en") and LAT.search(n["en"]) and not CY.search(n["en"]) and not GE.search(n["en"])):
        why.append("bad en")
    if "პროსპექტი" in json.dumps(row, ensure_ascii=False):
        why.append("პროსპექტი")
    qs = quotes_ok(row, why)
    nw = words(" ".join(n.values()))
    if not any(s["fact"] == "name" and nw & words(s["quote"]) for s in qs):
        why.append("no verified quotation that holds the name")
    st = [o.get("street_ka", ""), o.get("street_en", ""), o.get("street_ru", "")]
    sw = set().union(*[words(x) for x in st if x]) if any(st) else set()
    near = False
    if row.get("address"):
        key = row["address"] + ", Tbilisi"
        if key not in geo_cache:
            d = get("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=3&viewbox=44.65,41.86,45.05,41.60&bounded=1&q=" + urllib.parse.quote(key))
            time.sleep(1.1)
            geo_cache[key] = [(float(x["lat"]), float(x["lon"])) for x in (d or [])]
        near = any(hav(la, lo, o["lat"], o["lon"]) <= 250 for la, lo in geo_cache[key])
    if not near and not (sw and any(sw & words(s["quote"]) for s in qs)):
        why.append("the place is not proved: the address is not within 250 m of the object and no quotation holds the name of the nearest street")
    if row.get("year") is not None and not any(str(row["year"]) in s["quote"] for s in qs if s["fact"] == "year"):
        why.append("the year is not in a verified 'year' quotation")
    return why


def check_monument(row, ob):
    why = []
    o = ob.get(row["id"])
    if not o:
        return ["unknown object"]
    if row["status"] != "found":
        return ["not_found"]
    d = row.get("description") or {}
    for l in ("ru", "en"):
        if not (d.get(l) or "").strip():
            why.append("description." + l + " empty")                         # description.ka may be "": the Georgian text waits for Gemini (the card does not show a description without it until it comes)
    if d.get("ka") and (not GE.search(d["ka"]) or CY.search(d["ka"])) or d.get("en") and CY.search(d["en"]):
        why.append("bad script in the description")
    if "პროსპექტი" in json.dumps(row, ensure_ascii=False):
        why.append("პროსპექტი")
    qs = quotes_ok(row, why)
    allq = " ".join(s["quote"] for s in qs)
    for yy in set(re.findall(r"\b(1[5-9]\d\d|20[0-2]\d)\b", " ".join(d.values()))):
        if yy not in allq:
            why.append("year %s of the description is in no verified quotation" % yy)
    if row.get("year") is not None and not any(str(row["year"]) in s["quote"] for s in qs if s["fact"] == "year"):
        why.append("the year is not in a verified 'year' quotation")
    if row.get("sculptor") and not any(s["fact"] == "sculptor" and words(row["sculptor"]) & words(s["quote"]) for s in qs):
        why.append("the sculptor is not in a verified 'sculptor' quotation")
    f = row.get("commons_file")
    if f:
        r = get("https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo|coordinates|categories&iiprop=extmetadata|size&cllimit=30&format=json&titles=" + urllib.parse.quote(f))
        p = list(((r or {}).get("query") or {}).get("pages", {}).values() or [{}])[0]
        if "missing" in p or not p.get("imageinfo"):
            why.append("the Commons file does not exist")
        else:
            md = p["imageinfo"][0].get("extmetadata", {})
            text = " ".join([f, re.sub("<[^>]+>", " ", (md.get("ImageDescription") or {}).get("value", "")), " ".join(c["title"] for c in p.get("categories", []))])
            nw = words(" ".join((o["n"] or {}).values()))
            c = (p.get("coordinates") or [None])[0]
            geo = c and hav(c["lat"], c["lon"], o["lat"], o["lon"]) <= 100
            if not (nw & words(text)) and not geo:
                why.append("the Commons file neither names the object nor is geotagged within 100 m")
    return why


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    kind, path = sys.argv[1], sys.argv[2]
    rows = json.load(open(path, encoding="utf-8"))
    if kind == "churches":
        d = json.load(open(os.path.join(R, "site", "data", "religious_osm.json"), encoding="utf-8"))
        st = d["streets"]
        ob = {c["id"]: {"name": c["name"] or {}, "lat": c["lat"], "lon": c["lon"], "street_ka": (st.get(c["st"]) or {}).get("ka", ""), "street_en": (st.get(c["st"]) or {}).get("en", ""), "street_ru": (st.get(c["st"]) or {}).get("ru", "")} for c in d["items"]}
    else:
        d = json.load(open(os.path.join(R, "site", "data", "sculptures.json"), encoding="utf-8"))
        ob = {c["id"]: c for c in d["items"]}
    out_p = os.path.join(R, "data", "cache", kind + "_verified.json")
    out = json.load(open(out_p, encoding="utf-8")) if os.path.exists(out_p) else {"ok": [], "rejected": []}
    geo_cache = {}
    ids = {r["id"] for r in rows}
    out["ok"] = [r for r in out["ok"] if r["id"] not in ids]
    out["rejected"] = [r for r in out["rejected"] if r["id"] not in ids]
    for r in rows:
        why = check_church(r, ob, geo_cache) if kind == "churches" else check_monument(r, ob)
        (out["rejected"] if why else out["ok"]).append({"id": r["id"], "why": why} if why else r)
    json.dump(out, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(kind, "rows", len(rows), "| ok:", sum(1 for r in rows if r["id"] in {x["id"] for x in out["ok"]}), "| rejected:", [(x["id"], x["why"]) for x in out["rejected"] if x["id"] in ids])


if __name__ == "__main__":
    main()
