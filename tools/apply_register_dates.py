"""Dates of register objects that the site does not date yet (2026-11-24), only what was checked:
  1. years that the register itself prints in the Description of the same object (data/cache/register_desc_dates.json, made by Gemini; the quotation must stand verbatim in the Description of the raw record, and the year must be
     the year of the building itself, not of an earlier chapel, a hearsay or a guess: the list DESC below is the reading of every quotation in its context, the others were rejected, see docs/PENDING.md);
  2. two century words that no object had before: "XVIII ს" (the 18th century) and "V-XVIII სს." (the 5th-18th centuries), with the range of the same words in the rules (data/cache/register_dates_rules.json), written like the
     objects of the site with the same kind of words (the end of the range is the year of the timeline, the middle the estimate). The rules for the era before our era are NOT used: the site has no negative years.
Writes data/monument_date_overrides.json (the record, read by tools/build_site_data.py) and the properties y0 / y1 / ye / ym / prec / src of site/data/monuments.json (the same formulas as build_site_data.py).
Idempotent. Usage: python -P tools/apply_register_dates.py [--dry-run]
Use --bagineti-11904 to apply only the timeline-year correction for Bagineti #11904.
"""
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DRY = "--dry-run" in sys.argv

# register id -> (year_from, year_to, why); a single year is "exact", a span of years "years"
DESC = {
    3105: (1935, 1937, "the Description of the register object says the house was built in 1935-1937 (Stalinist period, architect M. Kalashnikov); the register range 'middle of the 19th century' contradicts it"),
    3320: (1881, 1881, "the Description says the house was built in 1881 (design by P. Stern); the register gave the end of the 19th century"),
    3918: (1868, 1868, "the Description says that in 1868 a domed church was built in place of the small chapel (renewed in 1910); the register gave the beginning of the 18th century, the date of the chapel"),
    4100: (1908, 1908, "the Description says the house was built in 1908; the register gave the end of the 19th century"),
    4258: (1914, 1914, "the Description says the house was built in 1914; the register gave the beginning of the 20th century"),
    16008: (1886, 1886, "the Description says the structure dates from 1886 (military engineer Vasil Jorjadze); the register gave no date"),
    16034: (1958, 1960, "the Description says the station was built in 1958-1960; the register gave only the 20th century"),
}
PERIOD_FIXES = {
    3725: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    5061: (801, 1000, "century", "raw_date says 9th-10th c., misparsed as 331-370"),
    5064: (400, 900, "period", "raw_date says early Middle Ages (4th-9th c.), misparsed as 400-1700"),
    6551: (601, 1000, "period", "ExactDate says transitional period (7th-10th c.), left undated"),
    6855: (901, 1500, "period", "Period says developed Middle Ages (10th-15th c.), misparsed as 331-370"),
    16051: (901, 1800, "period", "Period says developed to late Middle Ages (10th-18th c.), misparsed as 331-1570"),
    16247: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    16935: (401, 1800, "mixed", "raw_date says 5th c., 12th-18th c., misparsed as 331-1570"),
    17828: (1501, 2000, "period", "Period says late Middle Ages to modern (16th-20th c.), misparsed as 331-2000"),
    17902: (901, 1500, "period", "Period says developed Middle Ages (10th-15th c.), misparsed as 331-370"),
    18508: (301, 1500, "period", "Period says early to developed Middle Ages (4th-15th c.), misparsed as 331-1570"),
    18515: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    18516: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    20121: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    20140: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    24381: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    26434: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    26449: (301, 900, "period", "Period says early Middle Ages (4th-9th c.), misparsed as 331-370"),
    26684: (1, 900, "period", "Period says late Antiquity (1st-3rd c.) to early Middle Ages (4th-9th c.), misparsed as 331-370"),
    26725: (1701, 1900, "century", "raw_date says 18th-19th c., misparsed as 331-370"),
    26799: (1501, 1700, "century", "DateRange says 16th-17th c., left undated"),
    26800: (1601, 1800, "century", "DateRange says 17th-18th c., left undated"),
    30942: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    38180: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    38181: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
    38197: (1201, 1250, "half", "raw_date says first half of 13th c., misparsed as 331-370"),
    41543: (1501, 1800, "period", "Period says late Middle Ages (16th-18th c.), misparsed as 331-370"),
}
WORDS = {"XVIII ს": "the 18th century (the word of the register 'XVIII ს')", "V-XVIII სს.": "the 5th-18th centuries (the word of the register 'V-XVIII სს.')"}
# Fixes for raw_date strings misparsed by the initial import:
# (old_y0, old_y1, regex_or_substrings) -> (new_y0, new_y1, prec, why_template)
RAW_DATE_FIXES = [
    ("19th_end_20th_start", (1801, 1825), (1876, 1925, "mixed"), "raw_date spans end of 19th to beginning of 20th century (%s), misparsed as 1801-1825"),
    ("20th_words_start", (1801, 2000), (1901, 1925, "quarter"), "raw_date says beginning of 20th century in words (%s), misparsed as 1801-2000"),
    ("19th_end_typo", (1801, 1900), (1876, 1900, "quarter"), "raw_date says end of 19th century with a typo (%s), misparsed as full century 1801-1900"),
]


def apply_bagineti_year(mon_path):
    fix_path = Path(__file__).with_name("bagineti_11904_year_fix.json")
    fix = json.loads(fix_path.read_bytes())
    original = mon_path.read_bytes()
    data = json.loads(original)
    matches = [f["properties"] for f in data["features"] if str(f["properties"]["id"]) == str(fix["id"])]
    if len(matches) != 1:
        raise SystemExit(f'Expected exactly one register object #{fix["id"]}; found {len(matches)}')
    record = matches[0]
    if any(record.get(field) != fix[field] for field in ("raw_date", "y0", "y1")):
        raise SystemExit(f'The source date of register object #{fix["id"]} differs from the correction input')
    old_year = record.get("ye")
    if old_year == fix["y1"]:
        print(f'0 changes: #{fix["id"]} already has ye={old_year}')
        return
    if old_year != fix["previous_ye"]:
        raise SystemExit(f'Unexpected ye for register object #{fix["id"]}: {old_year!r}')
    record["ye"] = fix["y1"]
    if not DRY:
        updated = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if original.endswith(b"\r\n"):
            updated += b"\r\n"
        elif original.endswith(b"\n"):
            updated += b"\n"
        with TemporaryDirectory(dir=mon_path.parent) as tmp:
            staged = Path(tmp) / mon_path.name
            staged.write_bytes(updated)
            staged.replace(mon_path)
    action = "Would update" if DRY else "Updated"
    print(f'{action} 1 object: #{fix["id"]} ye {old_year} -> {record["ye"]}')


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mon_p = os.path.join(R, "site", "data", "monuments.json")
    if "--bagineti-11904" in sys.argv:
        apply_bagineti_year(Path(mon_p))
        return
    md = json.load(open(mon_p, encoding="utf-8"))
    byid = {p["properties"]["id"]: p["properties"] for p in md["features"]}
    db = sqlite3.connect("file:%s?mode=ro" % os.path.join(R, "data", "db", "project.sqlite").replace("\\", "/"), uri=True)
    raw = {str(rid): json.loads(t) for rid, t in db.execute("SELECT rid, tags FROM raw_record WHERE source='register'")}
    quotes = {r["id"]: r for r in json.load(open(os.path.join(R, "data", "cache", "register_desc_dates.json"), encoding="utf-8"))}
    rules = {r["ExactDate"]: r for r in json.load(open(os.path.join(R, "data", "cache", "register_dates_rules.json"), encoding="utf-8"))["exact_date_rules"]}
    new, skipped = {}, []
    for k, (y0, y1, why) in DESC.items():
        q, pr = quotes[k], byid[k]
        if q["quote"] not in (raw[str(k)].get("Description") or ""):
            skipped.append((k, "quotation not in the Description"))
            continue
        if (pr["prec"], pr["y0"], pr["y1"]) != (q["old_prec"], q["old_y0"], q["old_y1"]) and pr["y0"] is not None and (pr["y0"], pr["y1"]) != (y0, y1) and pr.get("src") != "Description":      # a range written by hand from the same file (src Description, with precision words that the interface does not know) is put right
            skipped.append((k, "the site has another range now: %s %s-%s" % (pr["prec"], pr["y0"], pr["y1"])))
            continue
        est = y0 if y0 == y1 else (y0 + y1) // 2
        new[str(k)] = {"year_from": y0, "year_to": y1, "year_est": est, "date_precision": "exact" if y0 == y1 else "years", "date_source": "Description", "why": why}
    for k, (y0, y1, prec, why) in PERIOD_FIXES.items():
        if k in byid:
            new[str(k)] = {"year_from": y0, "year_to": y1, "year_est": (y0 + y1) // 2, "date_precision": prec, "date_source": "Period", "why": why}
    for k, pr in byid.items():
        t = (pr.get("raw_date") or "").strip()
        if pr["y0"] is None and t in WORDS and t in rules:
            r = rules[t]
            new[str(k)] = {"year_from": r["y0"], "year_to": r["y1"], "year_est": (r["y0"] + r["y1"]) // 2, "date_precision": "century", "date_source": "ExactDate",
                           "why": "raw_date says " + WORDS[t] + ", range %d-%d; the end of the range is shown on the timeline, as for the other objects with a word of this kind" % (r["y0"], r["y1"])}
            continue
        cur = (pr.get("y0"), pr.get("y1"))
        fix = None
        if cur == (1801, 1825) and re.search(r"მე-19.*(ბოლო|დასასრულ).*მე-20.*დასაწყის", t, re.S):
            fix = RAW_DATE_FIXES[0]
        elif cur == (1801, 2000) and "მეოცე" in t and "დასაწყის" in t:
            fix = RAW_DATE_FIXES[1]
        elif cur == (1801, 1900) and "მე-19" in t and re.search(r"(დასარულ|დასასრლ|დასდასრულ|დსასრულ)", t):
            fix = RAW_DATE_FIXES[2]
        if fix:
            _, _, (ny0, ny1, nprec), why_tpl = fix
            new[str(k)] = {"year_from": ny0, "year_to": ny1, "year_est": (ny0 + ny1) // 2, "date_precision": nprec, "date_source": pr.get("src") or "ExactDate",
                           "why": why_tpl % t.replace("\r", " ")}
    ov_p = os.path.join(R, "data", "monument_date_overrides.json")
    raw_txt = open(ov_p, encoding="utf-8").read()
    ov = json.loads(raw_txt)
    add = {k: v for k, v in new.items() if k not in ov["objects"]}
    if add and not DRY:
        head, tail = raw_txt.rstrip("\n").rsplit("\n }}", 1)
        assert tail == "", "unexpected layout of the overrides file"
        lines = ['  %s: %s' % (json.dumps(k), json.dumps(v, ensure_ascii=False)) for k, v in add.items()]
        open(ov_p, "w", encoding="utf-8", newline="\n").write(head + ",\n" + ",\n".join(lines) + "\n }}\n")
    changed = 0
    for k, v in new.items():
        pr = byid[int(k)]
        exact = v["date_precision"] == "exact"
        want = {"y0": v["year_from"], "y1": v["year_to"], "ye": v["year_est"] if exact else v["year_to"], "ym": v["year_est"], "prec": v["date_precision"], "src": v["date_source"]}
        if any(pr.get(a) != b for a, b in want.items()):
            pr.update(want)
            changed += 1
    if changed and not DRY:
        open(mon_p, "w", encoding="utf-8", newline="\n").write(json.dumps(md, ensure_ascii=False, separators=(",", ":")))
    print("overrides added:", len(add), "| objects of the site changed:", changed, "| skipped:", skipped, "| dry-run:", DRY)


if __name__ == "__main__":
    main()
