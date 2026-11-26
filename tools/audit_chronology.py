"""Deterministic chronology audit across site/data/*.json and project.sqlite descriptions.

Separates:
  - TECH_FROM: technical timeline thresholds (364/370) on dated objects
  - PARSING_MISMATCH: obvious register date-range parsing mismatches (e.g. early middle ages -> 400-1700)
  - BUILDING_PHASE_CONFLICT: cross-layer date conflicts between building layers (monuments vs religious, excluding items with phases)
  - INSTITUTION_VS_BUILDING: cross-layer differences between a building and an institution (science/education/museums)
  - REL_NOTE_PHASES: curated religious objects without `phases` whose notes mention rebuilds/earlier temples
  - REG_DESC_PHASES: register objects (including secular buildings & Narikala) whose SQLite `description` mentions rebuilds or later centuries

Usage: python -P tools/audit_chronology.py
"""
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DB, RESULTS, ROOT

REL_REBUILD_RE = re.compile(
    r"перестро|восстанов|обновл|реставр|первоначальн|сохранил|колокольн|rebuilt|rebuild|restor|initial|original|surviving|გადაკეთ|აღდგენ|თავდაპირველ|შემორჩენ|სამრეკლო",
    re.I,
)
REG_DESC_PHASE_RE = re.compile(
    r"გადაკეთ|აღდგენ|თავდაპირველ|შემორჩენ|დაშენ|მიშენ|გაფართო|სამრეკლო|რესტავრ|უძველეს|ნანგრევ",
    re.I,
)
YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root = Path(ROOT)
    data_dir = root / "site" / "data"
    cat = load_json(data_dir / "catalog.json")
    mon = {f"o:{f['properties']['id']}": f["properties"] for f in load_json(data_dir / "monuments.json")["features"]}
    rel = {f"rl:{x['id']}": x for x in load_json(data_dir / "religious.json")}

    reg_facts: dict[int, dict[str, str]] = {}
    con = sqlite3.connect(DB)
    for oid, key, val in con.execute(
        "SELECT object_id, key, value FROM fact WHERE object_id LIKE 'TB/reg:%' AND key IN ('description', 'period', 'exact_date')"
    ):
        rid = int(oid.split(":", 1)[1])
        reg_facts.setdefault(rid, {})[key] = val or ""
    con.close()

    findings = []

    # 1. Technical thresholds 364/370 on dated religious objects
    for ref, r in sorted(rel.items()):
        if r.get("from") in (364, 370) and not r.get("undated"):
            findings.append({
                "kind": "TECH_FROM",
                "ref": ref,
                "name": r["name"]["ru"],
                "summary": f"from={r['from']}, date={r.get('date')!r}",
            })

    # 2. Register raw_date parsing mismatches (e.g. 5064 early middle ages -> 400-1700)
    for ref, p in sorted(mon.items()):
        raw = (p.get("raw_date") or "").strip()
        y0, y1 = p.get("y0"), p.get("y1")
        if ("ადრეული შუა" in raw or "ადრე შუა" in raw) and y1 == 1700:
            findings.append({
                "kind": "PARSING_MISMATCH",
                "ref": ref,
                "name": p.get("name"),
                "summary": f"raw_date={raw!r} parsed as {y0}-{y1} (expected early middle ages 400-900)",
            })

    # 3. Catalog cross-layer conflicts separated into BUILDING_PHASE_CONFLICT vs INSTITUTION_VS_BUILDING
    for it in cat["items"]:
        if not it.get("date_conflict"):
            continue
        if it.get("phases"):
            continue
        refs = it["refs"]
        is_inst = any(r.startswith(("sc:", "ed:", "mu:")) for r in refs)
        has_rel = any(r.startswith("rl:") for r in refs)
        nm = mon[it["primary"]]["name"] if it["primary"] in mon else it["primary"]
        if is_inst and not has_rel:
            findings.append({
                "kind": "INSTITUTION_VS_BUILDING",
                "ref": it["id"],
                "name": nm,
                "summary": f"dates={it['dates']}",
            })
        else:
            findings.append({
                "kind": "BUILDING_PHASE_CONFLICT",
                "ref": it["id"],
                "name": nm,
                "summary": f"dates={it['dates']}",
            })

    # 4. Curated religious objects without `phases` in catalog whose notes mention rebuilds
    for ref, r in sorted(rel.items()):
        if r.get("rid") is not None:
            continue
        cat_id = cat["by_ref"].get(ref)
        cat_item = next((x for x in cat["items"] if x["id"] == cat_id), None)
        if cat_item and cat_item.get("phases"):
            continue
        note_ru = r.get("note", {}).get("ru", "")
        if REL_REBUILD_RE.search(note_ru):
            findings.append({
                "kind": "REL_NOTE_PHASES",
                "ref": ref,
                "name": r["name"]["ru"],
                "summary": f"from={r['from']}, date={r.get('date')!r} | {note_ru[:160]}",
            })

    # 5. Register objects (including secular buildings & Narikala) whose SQLite description mentions rebuild/phases
    for ref, p in sorted(mon.items()):
        oid = p["id"]
        cat_id = cat["by_ref"].get(ref)
        cat_item = next((x for x in cat["items"] if x["id"] == cat_id), None)
        if cat_item and cat_item.get("phases"):
            continue
        facts = reg_facts.get(oid, {})
        desc = facts.get("description", "")
        if not desc or not REG_DESC_PHASE_RE.search(desc):
            continue
        ye = p.get("ye")
        yrs_in_desc = sorted({int(y) for y in YEAR_RE.findall(desc)})
        later_yrs = [y for y in yrs_in_desc if isinstance(ye, int) and y > ye + 20]
        if later_yrs or (isinstance(ye, int) and ye <= 1750):
            snippet = " ".join(desc.split())[:220]
            findings.append({
                "kind": "REG_DESC_PHASES",
                "ref": ref,
                "name": p.get("name"),
                "fn": p.get("fn"),
                "summary": f"ye={ye} ({p.get('y0')}-{p.get('y1')}), fn={p.get('fn')}, later_years_in_desc={later_yrs[:6]} | {snippet}",
            })

    counts = Counter(f["kind"] for f in findings)
    res_dir = Path(RESULTS)
    res_dir.mkdir(parents=True, exist_ok=True)
    md_path = res_dir / "chronology_audit_20261126.md"
    json_path = res_dir / "chronology_audit_20261126.json"

    json_path.write_text(json.dumps({"counts": dict(counts), "findings": findings}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["# Аудит хронологии и строительных фаз (2026-11-26)\n"]
    for k in ("TECH_FROM", "PARSING_MISMATCH", "BUILDING_PHASE_CONFLICT", "INSTITUTION_VS_BUILDING", "REL_NOTE_PHASES", "REG_DESC_PHASES"):
        lines.append(f"- **{k}**: {counts.get(k, 0)}")
    lines.append("")
    for k in ("TECH_FROM", "PARSING_MISMATCH", "BUILDING_PHASE_CONFLICT", "REL_NOTE_PHASES", "REG_DESC_PHASES", "INSTITUTION_VS_BUILDING"):
        sub = [f for f in findings if f["kind"] == k]
        if not sub:
            continue
        lines.append(f"## {k} ({len(sub)})\n")
        for f in sub:
            lines.append(f"- `{f['ref']}` ({f['name']}) — {f['summary']}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("Counts:", dict(counts))
    print("Wrote:", md_path.relative_to(root), "and", json_path.relative_to(root))
    for k in ("TECH_FROM", "PARSING_MISMATCH", "BUILDING_PHASE_CONFLICT", "REG_DESC_PHASES"):
        sub = [f for f in findings if f["kind"] == k]
        print(f"\n=== {k} ({len(sub)}) ===")
        for f in sub[:12]:
            print(f"  {f['ref']} ({f['name']}): {f['summary'][:130]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
