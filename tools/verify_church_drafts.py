"""Checks the answer of Gemini about the DRAFT list of churches (work/gemini/results/churches_C.json, task: tools/church_drafts_task.py). A row with status found is taken ("ok") only when:
  ka has Georgian letters and no Cyrillic, ru has Cyrillic and no Georgian, en has Latin letters and no Cyrillic or Georgian; no word პროსპექტი;
  every quotation (<= 30 words) stands verbatim on its page (tools/safe_fetch.py); a "name" quotation shares a word of 4+ letters with a name; the year only when a "year" quotation holds it;
  the POINT is proved: coord_url is an OpenStreetMap object (centre by Nominatim) or a Wikipedia page (its coordinates by the API, else those of its Wikidata item), and lies within 100 m of lat, lon of the row;
  same_as (when given) is an object of the project index (data/db/project.sqlite).
Output: data/cache/church_drafts_verified.json ({"ok": [rows], "rejected": [{n, why}]}). Nothing is written into site/data. Usage: python -P tools/verify_church_drafts.py [result.json] [--refresh]
"""
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_search import CY, GE, LAT, get, hav, quotes_ok, words  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def point_of(url):
    """the centre of the object / page that coord_url names, or None"""
    m = re.match(r"https://www\.openstreetmap\.org/(node|way|relation)/(\d+)", url or "")
    if m:
        d = get("https://nominatim.openstreetmap.org/lookup?format=jsonv2&osm_ids=%s%s" % (m.group(1)[0].upper(), m.group(2)))
        time.sleep(1.1)
        return (float(d[0]["lat"]), float(d[0]["lon"])) if d else None
    m = re.match(r"https://(ka|ru|en)\.wikipedia\.org/wiki/([^#?]+)", url or "")
    if m:
        d = get("https://%s.wikipedia.org/w/api.php?action=query&prop=coordinates|pageprops&ppprop=wikibase_item&format=json&titles=%s" % (m.group(1), m.group(2)))
        p = list(((d or {}).get("query") or {}).get("pages", {}).values() or [{}])[0]
        c = (p.get("coordinates") or [None])[0]
        if c:
            return c["lat"], c["lon"]
        q = (p.get("pageprops") or {}).get("wikibase_item")                  # no coordinates in the article: those of the Wikidata item of the page (P625)
        if q:
            w = get("https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims&format=json&ids=" + q)
            try:
                v = w["entities"][q]["claims"]["P625"][0]["mainsnak"]["datavalue"]["value"]
                return v["latitude"], v["longitude"]
            except (KeyError, IndexError, TypeError):
                return None
        return None
    return None


def check(row, ids):
    if row.get("status") != "found":
        return ["not_found"]
    why = []
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
    if not any(s.get("fact") == "name" and nw & words(s["quote"]) for s in qs):
        why.append("no verified quotation that holds the name")
    if row.get("year") is not None and not any(str(row["year"]) in s["quote"] for s in qs if s.get("fact") == "year"):
        why.append("the year is not in a verified 'year' quotation")
    pt = point_of(row.get("coord_url"))
    if pt is None:
        why.append("the point is not proved: no coordinates at coord_url")
    elif hav(pt[0], pt[1], row["lat"], row["lon"]) > 100:
        why.append("the point is %d m from coord_url" % hav(pt[0], pt[1], row["lat"], row["lon"]))
    if row.get("same_as") and row["same_as"] not in ids:
        why.append("same_as is not an object of the project index")
    return why


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = args[0] if args else os.path.join(R, "work", "gemini", "results", "churches_C.json")
    rows = json.load(open(src, encoding="utf-8"))
    db = sqlite3.connect("file:%s?mode=ro" % os.path.join(R, "data", "db", "project.sqlite").replace("\\", "/"), uri=True)
    ids = {r[0] for r in db.execute("SELECT id FROM object")}
    out_p = os.path.join(R, "data", "cache", "church_drafts_verified.json")
    ok, bad = [], []
    for r in rows:
        w = check(r, ids)
        (bad if w else ok).append({"n": r["n"], "why": w} if w else r)
    json.dump({"ok": ok, "rejected": bad}, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("rows %d | ok: %d | found but rejected: %s | not_found: %d" % (len(rows), len(ok), [(b["n"], b["why"]) for b in bad if b["why"] != ["not_found"]], sum(1 for b in bad if b["why"] == ["not_found"])))


if __name__ == "__main__":
    main()
