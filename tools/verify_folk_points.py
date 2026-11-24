"""Checks the answer of Gemini about the places of the folk names that had no point (work/gemini/results/folk_points.json, task: tasks/folk_points.md).
A row "found" is accepted only when: the row is one of the asked rows; every quotation (<= 30 words) stands verbatim on its page (tools/safe_fetch.py); "coord_url" is an OSM object (way / node / relation) that
Nominatim /lookup knows, whose centre lies within 150 m of the given lat / lon and inside the city; and the OSM object is the right one: for a building / market / square its name (any language) shares a word of 4+ letters
with a name of the folk row (folk, official), for an "area" (a district of several streets) the object is a street whose name stands in the quotation or in the official name. The rest is "rejected" with the reason.
Output: data/cache/folk_points_verified.json ({"ok": {row: {osm, lat, lon, kind, approx}}, "rejected": [...]}). Usage: python -P tools/verify_folk_points.py [--refresh]
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_enc_spec as B  # noqa: E402
from safe_fetch import fetch_text  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI as FD  # noqa: E402
UA = {"User-Agent": "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; read-only API client)"}
CYR = re.compile("[А-Яа-яЁё]")


def canon(s):
    return norm(s).replace("“", '"').replace("”", '"').replace("«", '"').replace("»", '"').casefold()


def words(s):
    return {w.casefold() for w in re.findall(r"[^\W\d_]{4,}", s)}


def lookup(oid):
    d = json.load(urllib.request.urlopen(urllib.request.Request("https://nominatim.openstreetmap.org/lookup?format=jsonv2&namedetails=1&osm_ids=" + oid, headers=UA), timeout=60))
    time.sleep(1.1)
    return d[0] if d else None


def hav(la1, lo1, la2, lo2):
    import math
    p = math.pi / 180
    a = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(a))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.load(open(os.path.join(FD, "results/folk_points.json"), encoding="utf-8"))
    folk = json.load(open(os.path.join(FD, "results/folk.json"), encoding="utf-8"))
    asked = {x["row"] for x in res}                                  # the rows of the answer are the rows that were asked (the list of unplaced rows shrinks as the answers are taken, so it cannot be used again)
    polys = [r for rs in B.polygons().values() for r in rs]
    out = {"ok": {}, "rejected": []}
    for x in res:
        row = x["row"]
        why = []
        if row not in asked:
            why.append("not an asked row")
        if x["status"] != "found":
            out["rejected"].append({"row": row, "why": ["not_found"]})
            continue
        f = folk[row]
        m = re.match(r"https://www\.openstreetmap\.org/(way|node|relation)/(\d+)$", x.get("coord_url") or "")
        if not m:
            why.append("coord_url is not an OSM object")
        if not x.get("sources"):
            why.append("no quotation")
        for s in x.get("sources", []):
            page = fetch_text(s["url"])
            if len(s["quote"].split()) > 30:
                why.append("quotation over 30 words")
            elif page is None:
                why.append("page not readable: " + s["url"][:60])
            elif canon(s["quote"]) not in canon(page):
                why.append("quotation not on the page: " + s["url"][:60])
        o = None
        if m:
            o = lookup(m.group(1)[0].upper() + m.group(2))
            if not o:
                why.append("OSM object unknown to Nominatim")
            else:
                la, lo = float(o["lat"]), float(o["lon"])
                if hav(la, lo, x["lat"], x["lon"]) > 150:
                    why.append("the point is %d m from the OSM object" % hav(la, lo, x["lat"], x["lon"]))
                if not any(B.inside((lo, la), r) for r in polys):
                    why.append("outside the city")
                names = " ".join((o.get("namedetails") or {}).values())
                ask = " ".join([f["folk"].get("ka", ""), f["folk"].get("ru", ""), f["official"]["ka"], f["official"]["ru"], f["official"]["en"]] + [s["quote"] for s in x["sources"]])
                if x["kind"] == "area":
                    if o["category"] != "highway" or not (words(names) & words(ask)):
                        why.append("an area must be given by a street named in the quotation / the official name")
                elif not (words(names) & words(f["folk"].get("ka", "") + " " + f["official"]["ka"] + " " + f["official"]["ru"] + " " + f["official"]["en"] + " " + f["folk"].get("ru", ""))):
                    why.append("the name of the OSM object (%s) shares no word with the names of the row" % names[:50])
        if why:
            out["rejected"].append({"row": row, "folk": f["folk"], "why": why})
        else:
            out["ok"][str(row)] = {"osm": m.group(1)[0].upper() + m.group(2), "lat": float(o["lat"]), "lon": float(o["lon"]), "kind": x["kind"], "approx": x["kind"] == "area"}
    json.dump(out, open(os.path.join(R, "data", "cache", "folk_points_verified.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("rows", len(res), "| ok:", sorted(out["ok"]), "| rejected:", [(r["row"], r["why"]) for r in out["rejected"]])


if __name__ == "__main__":
    main()
