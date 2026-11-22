"""A point on the map for every square of the site (the squares have no line in OSM, so they had a card but no label and no point). The position is found in this order and the way is kept in the answer:
1. "osm": an OSM object of the square itself (place=square, or a pedestrian way / area that carries its name);
2. "streets": the streets that bound the square in the entry of the encyclopedia of 2008 ("A, B and C streets between"): the middle of the points where those streets come nearest to one another (at least two streets found,
   the streets are looked up by their Georgian names in the OSM ways of data/raw);
3. "metro": the entry of the encyclopedia says that a station of the metro "comes out on the square" (მეტროს სადგური „X“): the position of the station (site/data/transport.json);
3b. "stops": the bus stops that carry the name of the square (the centre of the stops that lie within 250 m of one another);
4. none: the square is listed for a manual decision.
Output: tools/square_points.json ({key of the street: {"lon", "lat", "how"}}); tools/build_street_labels.py adds the points to site/data/street_geom.json; with --apply the squares that got a point lose "nogeom" in site/data/street_names.json.
Usage: python -P tools/square_points.py [--apply]
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import SOV, inside, name_forms, norm_name, polygons  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(R, "site", "data")
APPLY = "--apply" in sys.argv
KM = (83000.0, 111000.0)


def dist(a, b):
    return math.hypot((a[0] - b[0]) * KM[0], (a[1] - b[1]) * KM[1])


def load(p):
    return json.load(open(os.path.join(R, p), encoding="utf-8"))["elements"]


def center(e):
    if "center" in e:
        return (e["center"]["lon"], e["center"]["lat"])
    if "lon" in e:
        return (e["lon"], e["lat"])
    g = e.get("geometry")
    return (sum(p["lon"] for p in g) / len(g), sum(p["lat"] for p in g) / len(g)) if g else None


def main():
    sn = json.load(open(os.path.join(D, "street_names.json"), encoding="utf-8"))["streets"]
    sg = json.load(open(os.path.join(D, "street_geom.json"), encoding="utf-8"))
    ents = json.load(open(os.path.join(R, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))
    enc_ka = {}
    for fn in ("enc2008_verified.json", "enc2008_verified4.json", "cards_verified.json"):
        for r in json.load(open(os.path.join(R, "data", "cache", fn), encoding="utf-8"))["ok"]:
            enc_ka[r["id"]] = r["ka_now"]
    by_ka = {}
    for i, ka in enc_ka.items():
        for f in name_forms(ka):
            by_ka.setdefault(norm_name(f), []).append(i)
    ent = {e["id"]: e for e in ents}
    squares = load("data/raw/osm_extra/squares.json")
    ways = {}                                           # the OSM ways by the normalised Georgian name (the streets that bound a square)
    for fp in ("data/raw/osm_roads/roads_center.json", "data/raw/osm_roads/main_roads.json", "data/raw/osm_transport/street_labels.json", "data/raw/osm_transport/street_labels_more.json"):
        if not os.path.exists(os.path.join(R, fp)):
            continue
        for e in load(fp):
            nm = e.get("tags", {}).get("name")
            if nm and e.get("geometry"):
                for f in name_forms(nm):
                    ways.setdefault(norm_name(f), []).append([(p["lon"], p["lat"]) for p in e["geometry"]])
    stations = [(f["properties"]["name_ka"], f["geometry"]["coordinates"]) for f in json.load(open(os.path.join(D, "transport.json"), encoding="utf-8"))["features"] if f["properties"]["kind"] == "metro_station"]
    pp = os.path.join(R, "tools", "square_points.json")
    prev = json.load(open(pp, encoding="utf-8")) if os.path.exists(pp) else {}      # the squares that got a point by an earlier run: they have a geometry now, they are computed again (the same result), not skipped
    poly = polygons()
    out, left = {}, []
    for s in sn:
        if "მოედან" not in s["now"]["ka"]:
            continue
        key = s.get("geom") or s["now"]["en"]
        if key in sg and key not in prev:
            continue
        forms = {norm_name(f) for f in name_forms(s["now"]["ka"])}
        cands = [e for e in squares if any(norm_name(f) in forms for k in ("name", "name:ka") for f in name_forms(e.get("tags", {}).get(k, "")) if f)]
        # 1. an object of the square
        own = [e for e in cands if e["tags"].get("place") == "square" or (e["tags"].get("highway") == "pedestrian" and (e["tags"].get("area") == "yes" or e["type"] != "node"))]
        if own:
            c = center(own[0])
            out[key] = {"lon": round(c[0], 5), "lat": round(c[1], 5), "how": "osm"}
            continue
        # 2. the streets that bound the square (the entry of the encyclopedia)
        ids = sorted({i for f in name_forms(s["now"]["ka"]) for i in by_ka.get(norm_name(f), [])})
        if not ids:                                                             # a square that the full passes did not take (no former name): the entry by its heading
            ids = [i for i, e in ent.items() if norm_name(re.split(r"[,.;:(]", e["text"].strip(), maxsplit=1)[0][:80]) in forms]
        pts = []
        if ids:
            t = (ent[ids[0]].get("text_long") or ent[ids[0]]["text"]).replace("\n", " ")
            t = re.sub(r"(?<=[ა-ჰ])-\s+(?=[ა-ჰ])", "", t)                      # the breaks of words at the end of a line
            m = re.search(r"რ-ნი[^:;]*[:;]\s*(.{10,500}?)\s+შორის", t)
            if m:
                lst = re.sub(r"\s+და\s+", ", ", m.group(1)).replace(". ", ", ")
                names = []
                for x in lst.split(","):
                    x = re.sub(r"(ქუჩებსა|ქუჩებს|გამზირებს|გამზირსა|ქუჩას|გამზირს|სანაპიროსა|სანაპიროს|ხიდსა|ხიდს|მოედანს|მოედნებს)$", "", x.strip()).strip()
                    x = re.sub(r"ისა$", "ის", x)
                    if len(x) > 3:
                        names.append(x)
                dist_names = next((v for k, v in SOV.items() if ent[ids[0]]["district"].startswith(k)), None)           # the streets of the same name lie in other districts too: only the district of the entry counts
                rings = [r for d in (dist_names or ()) for r in poly.get(d, [])]
                in_d = (lambda pl: any(inside(pt, rg) for pt in pl[::3] for rg in rings)) if rings else (lambda pl: True)
                found = []
                for nmx in names:
                    for tp in ("ქუჩა", "გამზირი", "სანაპირო", "გზატკეცილი", "ხეივანი"):
                        w = ways.get(norm_name(nmx + " " + tp))
                        if not w and nmx.endswith("ის"):
                            w = ways.get(norm_name(nmx[:-2] + "ის " + tp))
                        w = [pl for pl in (w or []) if in_d(pl)]
                        if w:
                            found.append(w)
                            break
                for i in range(len(found)):
                    for j in range(i + 1, len(found)):
                        best = min(((dist(a, b), a, b) for l1 in found[i] for a in l1[::2] for l2 in found[j] for b in l2[::2]), key=lambda x: x[0], default=None)
                        if best and best[0] < 200:
                            pts.append(((best[1][0] + best[2][0]) / 2, (best[1][1] + best[2][1]) / 2))
        if pts:
            # the points where the bounding streets come together must lie together: the largest group within 250 m is taken, and it must have at least TWO points (a single crossing of two streets of
            # the same name as the bounding ones may lie in another part of the city: Baratashvili Square came out 4 km away); the squares that stay without a point go to the list for a manual decision
            groups = [[q for q in pts if dist(p, q) < 250] for p in pts]
            g = max(groups, key=len)
            if len(g) >= 2:
                out[key] = {"lon": round(sum(p[0] for p in g) / len(g), 5), "lat": round(sum(p[1] for p in g) / len(g), 5), "how": "streets"}
                continue
        # 3. a station of the metro that comes out on the square
        hit = None
        if ids:
            t2 = re.sub(r"(?<=[ა-ჰ])-\s+(?=[ა-ჰ])", "", (ent[ids[0]].get("text_long") or ent[ids[0]]["text"]).replace("\n", " "))
            for mm in re.finditer(r"მეტრო\S*\s*(?:სადგურ\S*)?\s*[„\"“,']{1,3}\s*([ა-ჰ \-–0-9]{4,40}?)\s*[“”\"'„]", t2):
                q = norm_name(mm.group(1))
                for nm, c in stations:
                    if q and (norm_name(nm)[:6] == q[:6] or q[:6] in norm_name(nm) or norm_name(nm)[:6] in q):
                        hit = c
                        break
                if hit:
                    break
        if not hit:                                       # the square carries the name of a station (Delisi) or the old name of one (Vagzlis Moedani = Station Square)
            own = norm_name(s["now"]["ka"].replace("მოედანი", "").strip())
            for nm, c in stations:
                sn_ = norm_name(re.sub(r"[-0-9 ]+$", "", nm.replace("მოედანი", "").strip()))
                if own and sn_ and (own[:5] == sn_[:5] or (own.startswith(norm_name("ვაგზლის")) and sn_.startswith(norm_name("სადგურის")))):
                    hit = c
                    break
        if hit:
            out[key] = {"lon": round(hit[0], 5), "lat": round(hit[1], 5), "how": "metro"}
            continue
        # 3b. the bus stops with the name of the square
        st = [center(e) for e in cands if e["tags"].get("highway") == "bus_stop"]
        if st:
            c0 = st[0]
            near = [p for p in st if dist(p, c0) < 250]
            out[key] = {"lon": round(sum(p[0] for p in near) / len(near), 5), "lat": round(sum(p[1] for p in near) / len(near), 5), "how": "stops"}
            continue
        left.append(key)
    mp = os.path.join(R, "tools", "square_points_manual.json")                       # the positions given by hand (and checked): they fill the squares that the rules did not find
    if os.path.exists(mp):
        for k, v in json.load(open(mp, encoding="utf-8"))["points"].items():
            if k not in out:
                out[k] = {"lon": v["lon"], "lat": v["lat"], "how": "manual"}
                if k in left:
                    left.remove(k)
    json.dump(out, open(os.path.join(R, "tools", "square_points.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import collections
    print("points:", len(out), dict(collections.Counter(v["how"] for v in out.values())), "| no point (manual):", left)
    if APPLY:
        dropped = set(prev) - set(out)                                    # a point of an earlier run that the stricter rules no longer give: the square has no line again
        for s in sn:
            k = s.get("geom") or s["now"]["en"]
            if k in out:
                s.pop("nogeom", None)
            elif k in dropped:
                s["nogeom"] = True
        raw = open(os.path.join(D, "street_names.json"), "rb").read()
        data = json.dumps({**json.load(open(os.path.join(D, "street_names.json"), encoding="utf-8")), "streets": sn}, ensure_ascii=False, separators=(",", ":"))
        if b"\r\n" in raw:
            data = data.replace("\n", "\r\n")
        open(os.path.join(D, "street_names.json"), "wb").write(data.encode("utf-8"))
        print("nogeom removed for", len(out), "squares")


if __name__ == "__main__":
    main()
