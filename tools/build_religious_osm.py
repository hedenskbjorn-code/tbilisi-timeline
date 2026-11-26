"""The places of worship of OpenStreetMap that the layer "Religious buildings" does not hold yet -> site/data/religious_osm.json (loaded after the first screen and joined to the layer).
Input: data/raw/osm_extra/worship_full.json (tools/fetch_worship_osm.py), site/data/religious.json (the objects that exist: an OSM object within 60 m of one of them is the same building and is not added),
site/data/street_geom.json + street_names.json (the nearest street within 150 m names an unnamed building), site/translit.js + names_i18n.json (the Russian and English forms of a Georgian name, the same module as for the register).
Rules: only objects that exist (no ruins); two objects of OSM within 35 m of each other are one building (the one with more tags is taken); the denomination only from the tags (georgian_orthodox / orthodox -> Georgian Orthodox,
armenian_apostolic, catholic, russian_orthodox, lutheran, jewish / muslim / yazidi by the religion; a church without a denomination is "christian", a church whose denomination is not given in OpenStreetMap);
the year only from start_date (otherwise the object is "undated", shown pale); a name goes to the language of its script, the missing Russian and English forms are made from the Georgian one by the module of the site.
Output: {"items": [{"id", "rel", "from", "date", "undated", "lon", "lat", "name": {ka, ru, en} (empty for an unnamed building), "osm": "node/123", "st": street key, "src": [wikipedia link]}], "streets": {key: {ka, ru, en}}}.
Usage: python -P tools/build_religious_osm.py
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import inside, polygons  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_fp = os.path.join(R, "tools", "churches_names.json")
FILL = json.load(open(_fp, encoding="utf-8")) if os.path.exists(_fp) else {}
D = os.path.join(R, "site", "data")
KM = (83000.0, 111000.0)
GEO, CYR = re.compile("[ა-ჿ]"), re.compile("[А-Яа-яЁё]")


def rel_of(t):
    r, d = t.get("religion", ""), t.get("denomination", "")
    if r in ("muslim", "jewish", "yazidi"):
        return r
    if d in ("georgian_orthodox", "orthodox"):
        return "orthodox"
    if d in ("armenian_apostolic", "armenian"):
        return "armenian"
    if d in ("catholic", "roman_catholic"):
        return "catholic"
    if d == "russian_orthodox":
        return "russian"
    if d == "lutheran":
        return "lutheran"
    if d in ("sephardi", "ashkenazi"):
        return "jewish"
    return "orthodox"


def dist(a, b):
    return math.hypot((a[0] - b[0]) * KM[0], (a[1] - b[1]) * KM[1])


def seg_dist(p, a, b):
    ax, ay, bx, by = (a[0] - p[0]) * KM[0], (a[1] - p[1]) * KM[1], (b[0] - p[0]) * KM[0], (b[1] - p[1]) * KM[1]
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
    return math.hypot(ax + t * dx, ay + t * dy)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    els = json.load(open(os.path.join(R, "data", "raw", "osm_extra", "worship_full.json"), encoding="utf-8"))["elements"]
    ours = json.load(open(os.path.join(D, "religious.json"), encoding="utf-8"))
    sg = json.load(open(os.path.join(D, "street_geom.json"), encoding="utf-8"))
    sn = json.load(open(os.path.join(D, "street_names.json"), encoding="utf-8"))["streets"]
    street = {(s.get("geom") or s["now"]["en"]): s["now"] for s in sn}
    lines = []
    for k, g in sg.items():
        if g.get("type") in ("LineString", "MultiLineString"):
            lines.append((k, [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]))

    def nearest(la, lo):
        best = (150.0, None)
        for k, parts in lines:
            for pl in parts:
                for a, b in zip(pl, pl[1:]):
                    if abs(a[1] - la) > 0.004 and abs(b[1] - la) > 0.004:
                        continue
                    d = seg_dist((lo, la), a, b)
                    if d < best[0]:
                        best = (d, k)
        return best[1]

    RINGS = polygons()
    stats = {"osm": len(els), "outside the city": 0, "ruins": 0, "same building as ours": 0, "double in OSM": 0}
    cand = []
    for e in els:
        t = e["tags"]
        if t.get("ruins") == "yes" or t.get("historic") == "ruins" or t.get("building") == "ruins" or t.get("disused") == "yes" or t.get("abandoned") == "yes":
            stats["ruins"] += 1
            continue
        c = e.get("center") or e
        pt = (c["lon"], c["lat"])
        if not any(inside(pt, ring) for rings in RINGS.values() for ring in rings):          # the boundary of the city (the districts), not the box around it: Mtskheta lies in the box
            stats["outside the city"] += 1
            continue
        if any(dist(pt, (o["lon"], o["lat"])) < 60 for o in ours):
            stats["same building as ours"] += 1
            continue
        cand.append((e, pt))
    cand.sort(key=lambda x: -len(x[0]["tags"]))                                       # the object with more tags first: it stays when two objects are one building
    kept = []
    for e, pt in cand:
        if any(dist(pt, q) < 35 for _, q in kept):
            stats["double in OSM"] += 1
            continue
        kept.append((e, pt))
    items, need = [], []
    for e, pt in kept:
        t = e["tags"]
        n = {"ka": "", "ru": "", "en": ""}
        for v in (t.get("name:ka"), t.get("name"), t.get("name:ru"), t.get("name:en")):      # a name goes to the language of ITS SCRIPT whatever tag it stands in (name:en with a Georgian text is a mistake of the tag)
            if v:
                lg = "ka" if GEO.search(v) else "ru" if CYR.search(v) else "en"
                n[lg] = n[lg] or v
        m = re.match(r"(\d{4})", t.get("start_date", ""))
        oid = "%s/%d" % (e["type"], e["id"])
        src = []
        w = t.get("wikipedia", "")
        if ":" in w and w.split(":", 1)[0] in ("ka", "ru", "en"):
            src.append("https://%s.wikipedia.org/wiki/%s" % (w.split(":", 1)[0], urllib.parse.quote(w.split(":", 1)[1].replace(" ", "_"))))
        for lg, v in (FILL.get("osm" + e["type"][0] + str(e["id"])) or {}).items():           # the names in the missing languages that Gemini gave (tools/apply_churches_a.py): they fill the EMPTY forms only
            n[lg] = n.get(lg) or v
        it = {"id": "osm" + e["type"][0] + str(e["id"]), "rel": rel_of(t), "from": int(m.group(1)) if m else 364, "date": m.group(1) if m else "", "undated": not m, "lon": round(pt[0], 6), "lat": round(pt[1], 6),
              "name": n, "osm": oid, "st": nearest(pt[1], pt[0]) or "", "src": src}
        items.append(it)
        if n["ka"] and not (n["ru"] and n["en"]):
            need.append({"id": it["id"], "name": n["ka"]})
    if need:                                                                           # the Russian and English forms of a Georgian name: the module of the site (as for the register)
        with tempfile.TemporaryDirectory() as td:
            inp, outp = os.path.join(td, "in.json"), os.path.join(td, "out.json")
            json.dump(need, open(inp, "w", encoding="utf-8"), ensure_ascii=False)
            subprocess.run(["node", os.path.join(R, "tools", "translit_names.mjs"), inp, outp], check=True, capture_output=True)
            tr = json.load(open(outp, encoding="utf-8"))
        for it in items:
            if it["id"] in tr:
                for lg in ("ru", "en"):
                    v = tr[it["id"]][lg]["name"]
                    if v and not GEO.search(v):                                          # the module returns a Georgian name unchanged when it does not know its words: that is not a Russian or English form
                        it["name"][lg] = it["name"][lg] or v
    used = {it["st"] for it in items if it["st"]}
    for it in items:
        if any(it["name"].values()) and not all(it["name"].values()):
            it["pend"] = 1                                                             # a name that exists in some languages only: the page shows the name that exists
    up = os.path.join(R, "tools", "religious_osm_ui.json")
    ui = json.load(open(up, encoding="utf-8"))["ui"] if os.path.exists(up) else {}
    out = {"items": items, "streets": {k: street[k] for k in sorted(used) if k in street}, "ui": ui}
    p = os.path.join(D, "religious_osm.json")
    open(p, "wb").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    import collections
    print(stats, "| added:", len(items), dict(collections.Counter(i["rel"] for i in items)))
    print("named:", sum(1 for i in items if any(i["name"].values())), "| unnamed:", sum(1 for i in items if not any(i["name"].values())), "| with a street:", sum(1 for i in items if i["st"]), "| dated:", sum(1 for i in items if not i["undated"]), "| bytes:", os.path.getsize(p))


if __name__ == "__main__":
    main()
