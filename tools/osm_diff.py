"""Report (nothing on the site is changed): what OpenStreetMap says now compared with the data that the site was built from. Three sets:
  places    the named places of tools/fetch_places_osm.py (snapshot data/raw/osm_extra/places.json),
  plaques   memorial=plaque (snapshot: the OSM ids of work/notes/tbilisi_plaques_osm.csv),
  monuments historic=memorial / monument (not the plaques) and tourism=artwork of any type (the tag patterns of the OSM rows of work/notes/tbilisi_monuments_full.csv; snapshot: those rows).
For every set: added (an id that the snapshot does not have), gone (an id of the snapshot that the new answer does not have; it is looked up by id: deleted, or no longer tagged), changed (the name in ka / ru / en, or the
position by more than 25 m). The time of the last edit of the object (OSM "timestamp") decides whether a difference is STABLE: an edit younger than 14 days is "unstable" and is not to be taken (vandalism is mostly
reverted within days). No name of an OSM user is read or kept. Output: the screen and data/cache/osm_diff_<date>.json. Overpass, a generic User-Agent, one request after another.
Usage: python -P tools/osm_diff.py [places] [plaques] [monuments] [--save]   (--save writes the new answer to data/osm_slices/<set>.json: the snapshot of the next comparison)
"""
import csv
import datetime
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project; OSM comparison)"
BBOX = "41.62,44.66,41.86,45.02"
STABLE_DAYS = 14
MOVE_M = 25
Q = {
    "plaques": '(nwr["memorial"="plaque"](%s););' % BBOX,
    "monuments": '(nwr["historic"~"^(memorial|monument)$"]["memorial"!="plaque"](%s);nwr["tourism"="artwork"](%s););' % (BBOX, BBOX),
}


def overpass(body):
    ql = "[out:json][timeout:180];\n%s\nout meta center;" % body
    data = urllib.parse.urlencode({"data": ql}).encode()
    for k in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": UA}), timeout=240))["elements"]
        except Exception as e:
            print("  retry:", str(e)[:60], flush=True)
            time.sleep(20 * (k + 1))
    raise SystemExit("overpass failed")


def key(e):
    return "%s/%s" % (e["type"], e["id"])


def pos(e):
    c = e.get("center") or ({"lat": e["lat"], "lon": e["lon"]} if "lat" in e else None)
    return (c["lat"], c["lon"]) if c else None


def names(t):
    return {k: (t.get(k) or "").strip() for k in ("name", "name:ka", "name:ru", "name:en")}


def metres(a, b):
    return math.hypot((a[1] - b[1]) * 83000, (a[0] - b[0]) * 111000) if a and b else 0


def age_days(e):
    try:
        return (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))).days
    except Exception:
        return None


SLICES = os.path.join(R, "data", "osm_slices")


def snapshot(name):
    """-> {id: {"pos": (lat, lon), "names": {...}}}; the slice of an earlier run (a snapshot of OSM itself) is preferred, the tables of the site are the first comparison only"""
    out = {}
    sp = os.path.join(SLICES, name + ".json")
    if os.path.exists(sp):
        for r in json.load(open(sp, encoding="utf-8")):
            out[r["id"]] = {"pos": tuple(r["pos"]), "names": r["names"]}
        return out
    if name == "places":
        for e in json.load(open(os.path.join(R, "data", "raw", "osm_extra", "places.json"), encoding="utf-8"))["elements"]:
            out[key(e)] = {"pos": pos(e), "names": names(e.get("tags", {}))}
    elif name == "plaques":
        for r in csv.DictReader(open(os.path.join(R, "data", "curated", "tbilisi_plaques_osm.csv"), encoding="utf-8-sig")):
            out[r["osm_id"]] = {"pos": (float(r["lat"]), float(r["lon"])), "names": {"name": "", "name:ka": r["name_ka"], "name:ru": r["name_ru"], "name:en": r["name_en"]}}
    else:
        kinds = {"n": "node", "w": "way", "r": "relation"}
        for r in csv.DictReader(open(os.path.join(R, "data", "curated", "tbilisi_monuments_full.csv"), encoding="utf-8-sig")):
            m = re.match(r"OSM_([nwr])(\d+)$", r["id"])
            if m and r["lat"]:
                out["%s/%s" % (kinds[m.group(1)], m.group(2))] = {"pos": (float(r["lat"]), float(r["lon"])), "names": {"name": "", "name:ka": r["name_ka"], "name:ru": r["name_ru"], "name:en": r["name_en"]}}
    return out


def fresh(name):
    if name == "places":
        import fetch_places_osm
        body = re.search(r"\[out:json\]\[timeout:180\];\n(.*)\nout center tags;", fetch_places_osm.QL, re.S).group(1)
        els = overpass(body)
    else:
        els = overpass(Q[name])
    return {key(e): e for e in els if pos(e) and e.get("tags")}


def lookup(ids):
    """The objects of the snapshot that the answer lacks: is the object still there (with other tags) or deleted?"""
    found = {}
    for i in range(0, len(ids), 40):
        part = ids[i:i + 40]
        body = "(" + "".join("%s(%s);" % (k.split("/")[0], k.split("/")[1]) for k in part) + ");"
        for e in overpass(body):
            found[key(e)] = e
        time.sleep(2)
    return found


def save_slice(name, new):
    os.makedirs(SLICES, exist_ok=True)
    keep = ("historic", "memorial", "tourism", "artwork_type", "place", "leisure", "natural", "amenity", "wikidata", "wikipedia")
    rows = [{"id": k, "pos": list(pos(e)), "names": names(e["tags"]), "tags": {t: e["tags"][t] for t in keep if t in e["tags"]}, "edited": (e.get("timestamp") or "")[:10]} for k, e in sorted(new.items())]
    open(os.path.join(SLICES, name + ".json"), "wb").write(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))      # no name of an OSM user, no changeset
    print("  slice saved: data/osm_slices/%s.json, %d objects" % (name, len(rows)))


def compare(name):
    snap, new = snapshot(name), fresh(name)
    if "--save" in sys.argv:
        save_slice(name, new)
    added = sorted(set(new) - set(snap))
    gone = sorted(set(snap) - set(new))
    changed = []
    for k in sorted(set(snap) & set(new)):
        e = new[k]
        n0, n1 = snap[k]["names"], names(e["tags"])
        diffs = [f for f in ("name:ka", "name:ru", "name:en") if n0.get(f) and n1.get(f) and n0[f] != n1[f]]
        mv = metres(snap[k]["pos"], pos(e))
        if diffs or mv > MOVE_M:
            changed.append((k, diffs, round(mv), age_days(e)))
    still = lookup(gone[:200]) if gone else {}
    print("\n== %s: snapshot %d | OSM now %d | added %d | gone %d | changed %d" % (name, len(snap), len(new), len(added), len(gone), len(changed)))
    rows = {"added": [], "gone": [], "changed": []}
    for k in added:
        e = new[k]
        a = age_days(e)
        rows["added"].append({"id": k, "name": e["tags"].get("name:en") or e["tags"].get("name:ka") or e["tags"].get("name") or "", "age_days": a, "stable": a is not None and a >= STABLE_DAYS})
    for k in gone:
        e = still.get(k)
        state = "deleted" if e is None and gone[:200].count(k) else ("exists, no longer matches (tags changed)" if e else "not looked up")
        rows["gone"].append({"id": k, "name": snap[k]["names"].get("name:ka") or snap[k]["names"].get("name:en") or "", "state": state, "age_days": age_days(e) if e else None})
    for k, d, mv, a in changed:
        rows["changed"].append({"id": k, "name_fields": d, "moved_m": mv, "age_days": a, "stable": a is not None and a >= STABLE_DAYS})
    st = lambda lst: sum(1 for r in lst if r.get("stable"))  # noqa: E731
    print("  added: stable %d, unstable %d | changed: stable %d, unstable %d | gone: %s" % (st(rows["added"]), len(rows["added"]) - st(rows["added"]), st(rows["changed"]), len(rows["changed"]) - st(rows["changed"]),
          {s: sum(1 for r in rows["gone"] if r["state"] == s) for s in {r["state"] for r in rows["gone"]}}))
    for lab in ("added", "gone", "changed"):
        for r in rows[lab][:12]:
            print("   %s %s" % ({"added": "+", "gone": "-", "changed": "~"}[lab], json.dumps(r, ensure_ascii=False)))
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    which = [a for a in sys.argv[1:] if a in ("places", "plaques", "monuments")] or ["places", "plaques", "monuments"]
    out = {}
    for n in which:
        out[n] = compare(n)
        time.sleep(5)
    p = os.path.join(R, "data", "cache", "osm_diff_%s.json" % datetime.date.today().isoformat())
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nreport:", p)


if __name__ == "__main__":
    main()
