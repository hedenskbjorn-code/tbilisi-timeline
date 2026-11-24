"""Check the answers of Gemini about the names of the streets without a card (work/gemini/cards_batch_NN_result.json, rules: tasks/cards.md).
Row: {"id", "status": "ok"|"skip", "skip_reason", "ka_now", "ru_now", "en_now"}. Rules: every id of the pack once, in the order; the keys; no Cyrillic in ka/en; no the calque of "prospect"; ka_now ends with a Georgian word of
the kind of the street; the stem of the longest word of ka_now (first 4 letters) stands in the heading of the entry or at the beginning of its text; en_now ends with an English word of the kind; ru_now has Cyrillic.
Output: data/cache/cards_verified.json ({"ok": [{id, ka_now, ru_now, en_now, page, district}], "rejected": [{id, reasons}], "skip": [{id, reason}]}). Usage: python -P tools/verify_cards.py
"""
import difflib
import glob
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(R, "data", "cache", "enc2008_entries.json")
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI as FD  # noqa: E402
OUT = os.path.join(R, "data", "cache", "cards_verified.json")
CYR = re.compile("[Ѐ-ӿ]")
KA = ("ქუჩა", "გამზირი", "მოედანი", "სანაპირო", "ხეივანი", "გზატკეცილი", "შესახვევი", "ჩიხი", "გასასვლელი", "ბულვარი", "დაღმართი", "აღმართი")
EN = ("Street", "Avenue", "Square", "Embankment", "Alley", "Highway", "Lane", "Dead End", "Passage", "Boulevard", "Road", "Descent", "Ascent")
KEYS = {"id", "status", "skip_reason", "ka_now", "ru_now", "en_now"}
SKIP = {"not_a_street", "unsure"}


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"(?<=[ა-ჰ])-\s+(?=[ა-ჰ])", "", s)).strip()


def stem(ka):
    ws = [w for w in re.findall(r"[ა-ჰ]+", ka or "") if len(w) >= 4]
    return max(ws, key=len)[:4] if ws else ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ents = {e["id"]: e for e in json.load(open(ENT, encoding="utf-8"))}
    files = sorted(glob.glob(os.path.join(FD, "batches", "cards", "cards_batch_*_result.json")))
    if not files:
        sys.exit("no result files yet")
    ok, rej, skip, seen, repaired = [], [], [], set(), []
    for fp in files:
        want = re.findall(r"^## (E\d{4}) \|", open(fp.replace("_result.json", ".md"), encoding="utf-8").read(), re.M)
        rows = json.load(open(fp, encoding="utf-8"))
        ids = [r.get("id") for r in rows if isinstance(r, dict)]
        print(os.path.basename(fp), "rows", len(rows), "| missing", [i for i in want if i not in ids], "| extra", [i for i in ids if i not in want], "| duplicates", sorted({i for i in ids if ids.count(i) > 1}))
        for r in rows:
            if not isinstance(r, dict) or r.get("id") not in want or r["id"] in seen:
                continue
            seen.add(r["id"])
            if set(r) != KEYS:
                rej.append({"id": r["id"], "reasons": ["keys differ"]})
                continue
            if r["status"] == "skip":
                (skip if r["skip_reason"] in SKIP else rej).append({"id": r["id"], "reason": r["skip_reason"]} if r["skip_reason"] in SKIP else {"id": r["id"], "reasons": ["skip_reason"]})
                continue
            e = ents[r["id"]]
            bad = []
            if r["status"] != "ok" or not all(isinstance(r[k], str) and r[k].strip() for k in ("ka_now", "ru_now", "en_now")):
                bad.append("status or empty names")
            else:
                if CYR.search(r["ka_now"] + r["en_now"]) or "პროსპექტ" in r["ka_now"]:
                    bad.append("Cyrillic in ka/en or the calque")
                if not r["ka_now"].rstrip().endswith(KA):
                    bad.append("ka_now does not end with a word of the kind of the street")
                if not r["en_now"].rstrip().endswith(EN):
                    bad.append("en_now does not end with a word of the kind of the street")
                if not CYR.search(r["ru_now"]):
                    bad.append("ru_now has no Cyrillic")
                st = stem(r["ka_now"])
                src = norm(e["name"] + " " + e["text"][:200])
                if st and st not in src:
                    # Gemini repairs the typos of the OCR by the scan of the PDF: the longest word of ka_now must be LIKE a word of the heading (ratio >= 0.7), else it is rejected
                    lw = max(re.findall(r"[ა-ჰ]+", r["ka_now"]), key=len)
                    best = max([difflib.SequenceMatcher(None, lw, w).ratio() for w in re.findall(r"[ა-ჰ]+", src)] or [0])
                    if best < 0.7:
                        bad.append("the word %s of ka_now is not like any word of the heading (%.2f)" % (lw, best))
                    else:
                        repaired.append({"id": r["id"], "ocr": e["name"], "ka_now": r["ka_now"].strip(), "ratio": round(best, 2)})
            if bad:
                rej.append({"id": r["id"], "reasons": bad})
            else:
                ok.append({"id": r["id"], "ka_now": r["ka_now"].strip(), "ru_now": r["ru_now"].strip(), "en_now": r["en_now"].strip(), "page": e["page"], "district": e["district"]})
    man = os.path.join(R, "tools", "cards_manual.json")                        # rows added by hand (the reason is in the file)
    if os.path.exists(man):
        for m in json.load(open(man, encoding="utf-8"))["rows"]:
            e = ents[m["id"]]
            if CYR.search(m["ka_now"] + m["en_now"]) or not m["ka_now"].endswith(KA) or not m["en_now"].endswith(EN) or not CYR.search(m["ru_now"]):
                print("manual row", m["id"], "does not pass")
                continue
            ok[:] = [x for x in ok if x["id"] != m["id"]]
            rej[:] = [x for x in rej if x["id"] != m["id"]]
            skip[:] = [x for x in skip if x["id"] != m["id"]]
            ok.append({"id": m["id"], "ka_now": m["ka_now"], "ru_now": m["ru_now"], "en_now": m["en_now"], "page": e["page"], "district": e["district"]})
    json.dump({"ok": ok, "rejected": rej, "skip": skip, "repaired_by_scan": repaired}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("names repaired by the scan (accepted by the likeness): %d" % len(repaired))
    print("ok: %d | skip: %d | rejected: %d" % (len(ok), len(skip), len(rej)))
    for x in rej[:60]:
        print("  rejected", x["id"], "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
