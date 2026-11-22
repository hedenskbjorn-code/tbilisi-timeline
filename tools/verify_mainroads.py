"""Check the answer of Gemini about the origin of the 25 main roads (for_gemini/from_desktop/mainroads_batch_01_result.json, rules: mainroads_TASK_for_gemini.md).
Each row: {"key", "status": "ok"|"skip", "skip_reason", "page", "ka_heading", "origin_quote", "origin_printed", "origin_kind"}.
Rules: every key of tools/mainroads_task.py once, in the order; the quote (<= 30 words) is a verbatim part of an article whose page is the given one or next to it (the OCR text, repaired or raw);
it holds a word of origin (წარმოიქმნა, ჩამოყალიბდა, გაყვანილია); "origin_printed" is the same phrase as printed in the PDF (the OCR spoils Roman numerals and digits) and must be alike the quote
(difflib >= 0.7 after the removal of digits and Roman letters); the years are COMPUTED here from origin_printed (a year, a decade of a century, a part of a century, a century) and the kind must be the same.
Output: data/cache/mainroads_verified.json ({"ok": [{key, page, quote, printed, kind, from, to}], "rejected": [...], "skip": [...]}).
Usage: python -P tools/verify_mainroads.py
"""
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mainroads_task import ROADS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
PAGES = os.path.join(ROOT, "data", "cache", "ocr", "streets_enc2008_kat.txt")
RES = os.path.join(ROOT, "for_gemini", "from_desktop", "mainroads_batch_01_result.json")
OUT = os.path.join(ROOT, "data", "cache", "mainroads_verified.json")
KEYS = {"key", "status", "skip_reason", "page", "ka_heading", "origin_quote", "origin_printed", "origin_kind"}
KINDS = {"year", "decade", "century", "century_part"}
SKIPS = {"no_article", "no_origin_phrase", "unsure"}
ORIGIN = ("წარმოიქმნა", "ჩამოყალიბდა", "გაყვანილია", "გაიხსნა")
BASE = {"XVII": 1600, "XVIII": 1700, "XIX": 1800, "XX": 1900}


def norm(s):
    """whitespace made single and the breaks of a word at the end of a line ("წარმოიქ- მნა") joined: the OCR text and the quote are compared in this form"""
    s = re.sub(r"(?<=[ა-ჰ])-\s+(?=[ა-ჰ])", "", s)
    return re.sub(r"\s+", " ", s).strip()


def compute(printed):
    """(kind, from, to) from the printed phrase, or None."""
    p = norm(printed)
    y = re.search(r"\b(1[5-9]\d\d)\b", p)
    if y and not re.search(r"\d0-იან", p):
        return "year", int(y.group(1)), int(y.group(1))
    c = re.search(r"\b(XVII|XVIII|XIX|XX)\s*(?:ს|საუკუნ)", p)
    if not c:
        return None
    b = BASE[c.group(1)]
    d = re.search(r"\b(\d)0-იან", p)
    if d:
        return "decade", b + int(d.group(1)) * 10, b + int(d.group(1)) * 10 + 9
    if re.search(r"დასაწყისში|დასაწყისს", p):
        return "century_part", b + 1, b + 33
    if re.search(r"შუა", p):
        return "century_part", b + 34, b + 66
    if re.search(r"ბოლოს", p):
        return "century_part", b + 67, b + 100
    if re.search(r"პირველ ნახევარ", p):
        return "century_part", b + 1, b + 50
    if re.search(r"მეორე ნახევარ", p):
        return "century_part", b + 51, b + 100
    return "century", b + 1, b + 100


def letters(s):
    return re.sub(r"[\dIVXL.,;:()\"“”„\s-]", "", s)


def main():
    ents = json.load(open(ENT, encoding="utf-8"))
    texts = {}
    for e in ents:
        texts.setdefault(e["page"], []).append(norm(e.get("text_long") or e["text"]) + " " + norm(e.get("text_long_raw") or "") + " " + norm(e["text"]))
    # the page texts of the OCR: some articles are missing in the index of the entries (found out 2026-11-22: Kazbegi p. 181, Tsabadze p. 194), the quote may stand in the page text as well
    pg = {}
    for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", open(PAGES, encoding="utf-8", errors="replace").read(), re.S):
        pg[int(m.group(1))] = norm(m.group(2))
    for k, v in pg.items():
        texts.setdefault(k, []).append(v)
    rows = json.load(open(RES, encoding="utf-8")) if os.path.exists(RES) else sys.exit("no result file yet")
    keys = [r[0] for r in ROADS]
    MAN = os.path.join(ROOT, "tools", "mainroads_manual1.json")        # rows added by hand after a check of the page text (the quotes are checked like the others)
    for m in (json.load(open(MAN, encoding="utf-8"))["rows"] if os.path.exists(MAN) else []):
        rows = [m if (isinstance(r, dict) and r.get("key") == m["key"]) else r for r in rows]
    got = [r.get("key") for r in rows if isinstance(r, dict)]
    print("rows", len(rows), "| missing", [k for k in keys if k not in got], "| extra", [k for k in got if k not in keys], "| duplicates", sorted({k for k in got if got.count(k) > 1}))
    ok, rej, skip, seen = [], [], [], set()
    for r in rows:
        if not isinstance(r, dict) or r.get("key") not in keys or r["key"] in seen:
            continue
        seen.add(r["key"])
        bad = []
        if set(r) != KEYS:
            rej.append({"key": r["key"], "reasons": ["keys differ"]})
            continue
        if r["status"] == "skip":
            (skip if r["skip_reason"] in SKIPS else rej).append({"key": r["key"], "reason": r["skip_reason"]} if r["skip_reason"] in SKIPS else {"key": r["key"], "reasons": ["skip_reason"]})
            continue
        if r["status"] != "ok":
            rej.append({"key": r["key"], "reasons": ["status"]})
            continue
        q, pr, pg = norm(r["origin_quote"] or ""), norm(r["origin_printed"] or ""), r["page"]
        if not isinstance(pg, int):
            bad.append("page")
        if not q or len(q.split()) > 30:
            bad.append("quote empty or longer than 30 words")
        elif not any(q in t for p in (pg - 1, pg, pg + 1) for t in texts.get(p, [])):
            bad.append("the quote is not a verbatim part of an article on page %s (+-1)" % pg)
        if not any(w in q for w in ORIGIN):
            bad.append("no word of origin in the quote")
        if difflib.SequenceMatcher(None, letters(q), letters(pr)).ratio() < 0.7:
            bad.append("the printed phrase is not like the quote")
        comp = compute(pr)
        if not comp:
            bad.append("the years cannot be read from the printed phrase")
        elif r["origin_kind"] != comp[0]:
            bad.append("kind %s, computed %s" % (r["origin_kind"], comp[0]))
        if r["origin_kind"] not in KINDS:
            bad.append("origin_kind")
        if bad:
            rej.append({"key": r["key"], "reasons": bad})
        else:
            ok.append({"key": r["key"], "page": pg, "quote": q, "printed": pr, "kind": comp[0], "from": comp[1], "to": comp[2]})
    json.dump({"ok": ok, "rejected": rej, "skip": skip}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok: %d | skip: %d | rejected: %d" % (len(ok), len(skip), len(rej)))
    for x in ok:
        print("  ok", x["key"], x["kind"], x["from"], x["to"], "p%s" % x["page"])
    for x in rej:
        print("  rejected", x["key"], "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
