"""Build unified object catalog site/data/catalog.json from monuments and curated layers."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, require_file


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(ROOT)
    links_path = Path(require_file(str(root / "data" / "curated" / "catalog_links.json"), "catalog links"))
    links_data = load_json(links_path).get("links", [])

    data_dir = root / "site" / "data"
    mon_feats = load_json(data_dir / "monuments.json").get("features", [])
    rel_arr = load_json(data_dir / "religious.json")
    sci_arr = load_json(data_dir / "science.json")
    edu_arr = load_json(data_dir / "education.json")
    mus_arr = load_json(data_dir / "museums.json")

    records = {}
    for f in mon_feats:
        p = f.get("properties", {})
        ref = f"o:{p['id']}"
        y0, y1, ye = p.get("y0"), p.get("y1"), p.get("ye")
        rng = "" if y0 is None else (str(y0) if y0 == y1 or y1 is None else f"{y0}–{y1}")
        records[ref] = {"ref": ref, "layer": "monuments", "ye": ye, "date": rng, "rid": p["id"]}

    for pfx, layer, arr in (("rl", "religious", rel_arr), ("sc", "science", sci_arr), ("ed", "education", edu_arr), ("mu", "museums", mus_arr)):
        for x in arr:
            ref = f"{pfx}:{x['id']}"
            ye = None if x.get("undated") else x.get("from")
            dt = str(x.get("date") or x.get("built") or x.get("founded") or "")
            records[ref] = {"ref": ref, "layer": layer, "ye": ye, "date": dt, "rid": x.get("rid")}

    groups = {}
    ref_to_cat = {}

    def ensure_group(cat_id: str, primary: str):
        if cat_id not in groups:
            groups[cat_id] = {"id": cat_id, "primary": primary, "refs": []}
        return groups[cat_id]

    def attach(cat_id: str, ref: str, primary: str):
        if ref not in records:
            raise ValueError(f"catalog_links.json references unknown object {ref}")
        if ref in ref_to_cat and ref_to_cat[ref] != cat_id:
            raise ValueError(f"ref {ref} assigned to multiple catalog IDs: {ref_to_cat[ref]} vs {cat_id}")
        g = ensure_group(cat_id, primary)
        if ref not in g["refs"]:
            g["refs"].append(ref)
        ref_to_cat[ref] = cat_id

    for entry in links_data:
        cat_id = entry["cat"]
        refs = entry["refs"]
        primary = refs[0]
        for ref in refs:
            attach(cat_id, ref, primary)
        if entry.get("housed_in"):
            groups[cat_id]["housed_in"] = entry["housed_in"]
        if entry.get("phases"):
            groups[cat_id]["phases"] = entry["phases"]

    for ref, rec in records.items():
        if ref in ref_to_cat:
            continue
        rid = rec.get("rid")
        if rid is not None and f"o:{rid}" in records:
            cat_id = f"cat:reg:{rid}"
            attach(cat_id, f"o:{rid}", f"o:{rid}")
            attach(cat_id, ref, f"o:{rid}")
        elif ref.startswith("o:"):
            cat_id = f"cat:reg:{ref[2:]}"
            attach(cat_id, ref, ref)
        else:
            cat_id = f"cat:cur:{ref}"
            attach(cat_id, ref, ref)

    items = []
    conflicts = 0
    linked = 0
    for cat_id in sorted(groups):
        g = groups[cat_id]
        dates = {}
        yrs = set()
        norm_ranges = set()
        for ref in g["refs"]:
            rec = records[ref]
            dates[ref] = {"ye": rec["ye"], "date": rec["date"]}
            if rec["ye"] is not None:
                yrs.add(rec["ye"])
            if rec["date"]:
                norm_ranges.add(rec["date"].replace("\u2013", "-").replace(" ", ""))
        conflict = len(yrs) > 1 and len(norm_ranges) != 1
        if conflict:
            conflicts += 1
        if len(g["refs"]) > 1:
            linked += 1
        obj = {
            "id": cat_id,
            "primary": g["primary"],
            "refs": g["refs"],
            "dates": dates,
            "date_conflict": conflict,
        }
        if g.get("housed_in"):
            obj["housed_in"] = g["housed_in"]
        if g.get("phases"):
            obj["phases"] = g["phases"]
        items.append(obj)

    out = {
        "stats": {"total": len(items), "linked": linked, "date_conflicts": conflicts},
        "by_ref": dict(sorted(ref_to_cat.items())),
        "items": items,
    }
    out_path = data_dir / "catalog.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {out_path.relative_to(root)}: {len(items)} catalog objects ({linked} multi-layer, {conflicts} date conflicts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
