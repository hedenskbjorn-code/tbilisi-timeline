"""Check the answer of Gemini of the second pass about the main roads (for_gemini/from_desktop/mainroads_batch_02_result.json, rules: mainroads_TASK2_for_gemini.md): the earliest year of a document
(a plan, a map, a list of the streets, the laying) in the article of the street.
Row: {"key", "status", "skip_reason", "page", "ka_heading", "doc_quote", "doc_printed", "doc_kind", "year"}.
Rules: every key of tools/mainroads_task2.py KEYS2 once, in the order; the quote (<= 25 words) is a verbatim part of the text of a page (the page given +-1: the entries or the page OCR, the breaks
of words at the end of a line joined); it holds a word of a document (გეგმ, რუკ, სია, გაყვანილია, დაიგო) and a year; the year of "doc_printed" is "year"; no EARLIER year in the same contexts
in the article (the entry that holds the quote) - then the row is rejected with the earlier year. Where the quote stands in the page OCR only (the entry is missing in the index) the check of the
earlier year is not possible and the row is marked "page-only".
Output: data/cache/mainroads_verified2.json. Usage: python -P tools/verify_mainroads2.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mainroads_task2 import KEYS2  # noqa: E402
from verify_mainroads import norm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
PAGES = os.path.join(ROOT, "data", "cache", "ocr", "streets_enc2008_kat.txt")
RES = os.path.join(ROOT, "for_gemini", "from_desktop", "mainroads_batch_02_result.json")
OUT = os.path.join(ROOT, "data", "cache", "mainroads_verified2.json")
KEYS = {"key", "status", "skip_reason", "page", "ka_heading", "doc_quote", "doc_printed", "doc_kind", "year"}
KINDS = {"list", "plan", "map", "laid", "other"}
SKIPS = {"no_article", "no_document", "unsure"}
WORD = re.compile(r"გეგმ|რუკ|სია|გაყვანილია|დაიგო")
CTX = re.compile(r"(\b1[5-9]\d\d)\s*წ\.?\s*(?:[^.]{0,40})?(?:გეგმ|რუკ|სია)|(?:გაყვანილია|დაიგო)\s*(\b1[5-9]\d\d)|(\b1[5-9]\d\d)\s*წ\.?\s*(?:[^.]{0,30})?(?:დაიგო|გაყვანილია)")


def years(t):
    return [int(next(g for g in m.groups() if g)) for m in CTX.finditer(t)]


def main():
    ents = json.load(open(ENT, encoding="utf-8"))
    by_page = {}
    for e in ents:
        by_page.setdefault(e["page"], []).append(norm(e.get("text_long") or e["text"]) + " " + norm(e.get("text_long_raw") or ""))
    pg = {}
    for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", open(PAGES, encoding="utf-8", errors="replace").read(), re.S):
        pg[int(m.group(1))] = norm(m.group(2))
    rows = json.load(open(RES, encoding="utf-8")) if os.path.exists(RES) else sys.exit("no result file yet")
    got = [r.get("key") for r in rows if isinstance(r, dict)]
    print("rows", len(rows), "| missing", [k for k in KEYS2 if k not in got], "| extra", [k for k in got if k not in KEYS2], "| duplicates", sorted({k for k in got if got.count(k) > 1}))
    MAN = os.path.join(ROOT, "tools", "mainroads_manual.json")           # rows added by hand (the quotes are checked like the others)
    manual = json.load(open(MAN, encoding="utf-8"))["rows"] if os.path.exists(MAN) else []
    keys_ok = KEYS2 + [m["key"] for m in manual if m["key"] not in KEYS2]
    for m in manual:
        if m["key"] in got:
            rows = [m if (isinstance(r, dict) and r.get("key") == m["key"]) else r for r in rows]
        else:
            rows.append(m)
    ok, rej, skip, seen = [], [], [], set()
    for r in rows:
        if not isinstance(r, dict) or r.get("key") not in keys_ok or r["key"] in seen:
            continue
        seen.add(r["key"])
        if set(r) != KEYS:
            rej.append({"key": r["key"], "reasons": ["keys differ"]})
            continue
        if r["status"] == "skip":
            (skip if r["skip_reason"] in SKIPS else rej).append({"key": r["key"], "reason": r["skip_reason"]} if r["skip_reason"] in SKIPS else {"key": r["key"], "reasons": ["skip_reason"]})
            continue
        if r["status"] != "ok":
            rej.append({"key": r["key"], "reasons": ["status"]})
            continue
        bad, note = [], ""
        q, pr, pgno = norm(r["doc_quote"] or ""), norm(r["doc_printed"] or ""), r["page"]
        y = r["year"]
        if not isinstance(pgno, int) or not isinstance(y, int):
            bad.append("page or year is not a number")
        else:
            if not q or len(q.split()) > 25:
                bad.append("quote empty or longer than 25 words")
            else:
                where = [(p, t) for p in (pgno - 1, pgno, pgno + 1) for t in by_page.get(p, []) if q in t]
                if where:
                    ts = years(where[0][1])
                    if ts and min(ts) < y:
                        bad.append("an earlier year %d stands in the same article (the row has %d)" % (min(ts), y))
                elif any(q in pg.get(p, "") for p in (pgno - 1, pgno, pgno + 1)):
                    note = "page-only"
                else:
                    bad.append("the quote is not a verbatim part of the text of page %s (+-1)" % pgno)
            if not WORD.search(q):
                bad.append("no word of a document in the quote")
            if not re.search(r"\b%d\b" % y, pr):
                bad.append("the year %d is not in doc_printed" % y)
            if r["doc_kind"] not in KINDS:
                bad.append("doc_kind")
        if bad:
            rej.append({"key": r["key"], "reasons": bad})
        else:
            ok.append({"key": r["key"], "page": pgno, "quote": q, "printed": pr, "kind": r["doc_kind"], "year": y, "note": note})
    json.dump({"ok": ok, "rejected": rej, "skip": skip}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok: %d | skip: %d | rejected: %d" % (len(ok), len(skip), len(rej)))
    for x in ok:
        print("  ok", x["key"], x["kind"], x["year"], "p%s" % x["page"], x["note"])
    for x in skip:
        print("  skip", x["key"], x["reason"])
    for x in rej:
        print("  rejected", x["key"], "; ".join(x["reasons"])[:220])


if __name__ == "__main__":
    main()
