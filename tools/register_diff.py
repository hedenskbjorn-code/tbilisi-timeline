"""Comparison of two downloads of the register of immovable cultural heritage (https://memkvidreoba.gov.ge/downloads/PS.ImmovableMonumentObjectP/, a new file every week): which objects were added, removed
or changed. Reads two GeoJSON files (all of Georgia), compares by the field ID (the whole country and the objects of Tbilisi: Region or Municipality "თბილისი"), writes the report to the screen and, with --write-slices, ONE slice of the
objects of Tbilisi (the fields that the site uses, the long Description only as a hash, sorted by ID, so a git diff is readable) to data/register_slices/tbilisi.json (+ tbilisi.meta.json with the date of the file).
It changes nothing else. Usage: python -P tools/register_diff.py OLD.geojson NEW.geojson [--write-slices]
"""
import hashlib
import json
import math
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEEP = ["ID", "Name", "FullName", "ComplexName", "StatusName", "StatusDocDate", "StatusDocNumber", "RegistryN", "CategoryName", "WorldCategoryName", "Region", "Municipality", "Settlement", "Address",
        "Period", "ExactDate", "DateRangeFrom", "DateRangeTo", "InitialFunction", "CurrentFunction", "Classification", "Accuracy", "X", "Y", "CreateDate"]
TBILISI = "თბილისი"


def load(path):
    d = json.load(open(path, encoding="utf-8"))
    out = {}
    for f in d["features"]:
        p = f["properties"]
        g = f.get("geometry") or {}
        c = g.get("coordinates")
        while isinstance(c, list) and c and isinstance(c[0], list):
            c = c[0]
        rec = {k: p.get(k) for k in KEEP}
        rec["lon"], rec["lat"] = (round(c[0], 6), round(c[1], 6)) if c and len(c) >= 2 else (None, None)
        rec["desc"] = hashlib.sha1((p.get("Description") or "").encode("utf-8")).hexdigest()[:10]
        out[str(p["ID"])] = rec
    return out


def is_tbilisi(r):
    return TBILISI in ((r.get("Region") or "") + " " + (r.get("Municipality") or ""))


def metres(a, b):
    if None in (a["lon"], a["lat"], b["lon"], b["lat"]):
        return None
    return math.hypot((a["lon"] - b["lon"]) * 83000, (a["lat"] - b["lat"]) * 111000)


def compare(old, new, label):
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = {}
    for i in set(old) & set(new):
        d = {k: (old[i][k], new[i][k]) for k in list(KEEP) + ["lon", "lat", "desc"] if old[i].get(k) != new[i].get(k)}
        if d:
            changed[i] = d
    print("\n== %s: old %d | new %d | added %d | removed %d | changed %d" % (label, len(old), len(new), len(added), len(removed), len(changed)))
    return added, removed, changed


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    old, new = load(args[0]), load(args[1])
    cmp_all = compare(old, new, "all of Georgia")
    fa = {}
    for d in cmp_all[2].values():
        for k in d:
            fa[k] = fa.get(k, 0) + 1
    print("changed fields (Georgia):", dict(sorted(fa.items(), key=lambda x: -x[1])))
    for i in cmp_all[1]:
        r = old[i]
        print("  - removed in Georgia: %s | %s | %s | %s | %s" % (r["ID"], r["Name"], r["Region"], r["Municipality"], r["StatusName"]))
    ot, nt = {k: v for k, v in old.items() if is_tbilisi(v)}, {k: v for k, v in new.items() if is_tbilisi(v)}
    added, removed, changed = compare(ot, nt, "Tbilisi")
    moved_out = [i for i in old if i in new and is_tbilisi(old[i]) and not is_tbilisi(new[i])]
    moved_in = [i for i in old if i in new and not is_tbilisi(old[i]) and is_tbilisi(new[i])]
    print("moved out of Tbilisi:", len(moved_out), "| moved into Tbilisi:", len(moved_in))
    show = lambda r: "%s | %s | %s | %s | %s" % (r["ID"], r["Name"], r["Address"], r["StatusName"], r["CategoryName"])  # noqa: E731
    for i in added[:40]:
        print("  + ", show(nt[i]))
    for i in removed[:40]:
        print("  - ", show(ot[i]))
    fields = {}
    for i, d in changed.items():
        for k in d:
            fields[k] = fields.get(k, 0) + 1
    print("changed fields (Tbilisi):", dict(sorted(fields.items(), key=lambda x: -x[1])))
    for i, d in list(changed.items())[:60]:
        parts = []
        for k, (a, b) in d.items():
            if k in ("lon", "lat"):
                continue
            parts.append("%s: %r -> %r" % (k, str(a)[:50], str(b)[:50]))
        m = metres(ot[i], nt[i])
        if m:
            parts.append("moved %.0f m" % m)
        print("  ~ %s %s | %s" % (i, nt[i]["Name"], "; ".join(parts)))
    if "--write-slices" in sys.argv:                                    # one file, overwritten at every check: the history of the register is the history of its commits (a change of a week is a small diff)
        os.makedirs(os.path.join(R, "data", "register_slices"), exist_ok=True)
        date = re.search(r"(\d{2}\.\d{2}\.\d{4})", os.path.basename(args[1])).group(1)
        rows = [nt[k] for k in sorted(nt, key=lambda x: int(x) if x.isdigit() else x)]
        p = os.path.join(R, "data", "register_slices", "tbilisi.json")
        open(p, "wb").write(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        meta = {"source": "https://memkvidreoba.gov.ge/downloads/PS.ImmovableMonumentObjectP/", "file_date": date, "objects": len(rows), "note": "Tbilisi objects of the register of immovable cultural heritage (Region or Municipality = თბილისი); the long Description only as a hash; tools/register_diff.py"}
        open(os.path.join(R, "data", "register_slices", "tbilisi.meta.json"), "wb").write(json.dumps(meta, ensure_ascii=False, indent=1).encode("utf-8"))
        print("slice:", p, os.path.getsize(p), "bytes,", len(rows), "objects, file of", date)

if __name__ == "__main__":
    main()
