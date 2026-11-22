"""Check the answers of Gemini for the encyclopedia batches (for_gemini/from_desktop/enc_batches/enc_batch_NN_result.json) against the text of the entries.

The rules are the ones of the task (for_gemini/from_desktop/enc_streets_TASK_for_gemini.md): every id once, the schema, the quote is a verbatim substring of the OCR text of the entry and holds the year
(for the kind "dec" the decade), the intervals form a chain, the Georgian note equals the template, no Cyrillic in ka/en, no the calque of the word "prospect".
Output: data/cache/enc2008_verified.json ({"ok": [...], "rejected": [{"id", "reasons"}]}); the rejected ones are printed so they can be sent back to Gemini.
Usage: python -P tools/verify_enc_batches.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
BAT = os.path.join(ROOT, "for_gemini", "from_desktop", "enc_batches")
OUT = os.path.join(ROOT, "data", "cache", "enc2008_verified.json")
CYR = re.compile("[Ѐ-ӿ]")
LAT = re.compile("[A-Za-z]")
CALQUE = "პროსპექტ"
BOOK = "ენციკლოპედია „თბილისი. ქუჩები, გამზირები, მოედნები“ (2008): "
KEYS = {"id", "status", "skip_reason", "ka_now", "ru_now", "en_now", "intervals", "undated", "note_ka"}
IKEYS = {"from", "to", "kind", "ka", "ru", "en", "quote"}
SKIP = {"not_a_street", "gone", "no_named_years", "unsure"}


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def label(iv):
    y, k = iv["from"], iv["kind"]
    if k == "exact":
        return "%d" % y
    if k == "plan":
        return "%d (გეგმის ან სიის წელი)" % y
    if k == "dec":
        return "%d-იანი წლები (ზუსტი წელი დასახელებული არ არის, რუკაზე პირობითად %d-დან)" % (y, y)
    return "%d წლის შემდეგ (ზუსტი წელი დასახელებული არ არის, რუკაზე პირობითად %d-დან)" % (y, y)


def check(e, r):
    bad = []
    if set(r) != KEYS:
        return ["keys differ: " + ",".join(sorted(set(r) ^ KEYS))]
    if r["status"] == "skip":
        if r["skip_reason"] not in SKIP:
            bad.append("skip_reason")
        return bad
    if r["status"] != "ok":
        return ["status"]
    for f in ("ka_now", "ru_now", "en_now", "note_ka"):
        if not isinstance(r[f], str) or not r[f].strip():
            bad.append("empty " + f)
    for f in ("ka_now", "note_ka"):
        if CYR.search(r[f]) or CALQUE in r[f]:
            bad.append("Cyrillic or the calque in " + f)
    if CYR.search(r["en_now"]):
        bad.append("Cyrillic in en_now")
    if not r["intervals"]:
        return bad + ["no intervals for status ok"]
    text = norm(e["text"])
    raw = norm(e.get("text_raw", e["text"]))                 # a quote may come from the repaired text or from the raw OCR text
    prev_to = None
    for i, iv in enumerate(r["intervals"]):
        if set(iv) != IKEYS:
            bad.append("interval %d keys" % i)
            continue
        if not (isinstance(iv["from"], int) and isinstance(iv["to"], int) and 900 <= iv["from"] < iv["to"] <= 2030):
            bad.append("interval %d years" % i)
            continue
        if iv["kind"] not in ("exact", "plan", "dec", "after"):
            bad.append("interval %d kind" % i)
        if prev_to is not None and prev_to != iv["from"] and iv["kind"] != "dec":
            bad.append("interval %d does not follow the previous one (%s -> %s)" % (i, prev_to, iv["from"]))
        prev_to = iv["to"]
        q = norm(iv["quote"])
        if not q or (q not in text and q not in raw):
            bad.append("interval %d: the quote is not a verbatim part of the entry" % i)
        else:
            if iv["kind"] == "dec":
                if not re.search(r"\b%d-" % (iv["from"] % 100), q):
                    bad.append("interval %d: the decade is not in the quote" % i)
            elif str(iv["from"]) not in q:
                bad.append("interval %d: the year %d is not in the quote" % (i, iv["from"]))
        for f in ("ka", "en"):
            if CYR.search(iv[f]) or not iv[f].strip():
                bad.append("interval %d: %s empty or with Cyrillic" % (i, f))
        if CALQUE in iv["ka"] or not iv["ru"].strip():
            bad.append("interval %d: ru empty or the calque" % i)
    if not bad:
        want = BOOK + "; ".join("%s — %s" % (label(iv), iv["ka"]) for iv in r["intervals"]) + "; %d — %s." % (r["intervals"][-1]["to"], r["ka_now"])
        if norm(r["note_ka"]) != norm(want):
            bad.append("note_ka differs from the template")
    return bad


def main():
    ents = {e["id"]: e for e in json.load(open(ENT, encoding="utf-8"))}
    ok, rej, seen = [], [], set()
    # the second pass (enc2_batch_*) is looked at after the first one; its answer replaces an earlier skip of the same entry
    files = sorted(glob.glob(os.path.join(BAT, "enc_batch_*_result.json"))) + sorted(glob.glob(os.path.join(BAT, "enc2_batch_*_result.json"))) + sorted(glob.glob(os.path.join(BAT, "enc3_batch_*_result.json")))
    skipped_first = set()
    if not files:
        sys.exit("no result files yet")
    for fp in files:
        batch = open(fp.replace("_result.json", ".md"), encoding="utf-8").read()
        want = re.findall(r"^## (E\d{4}) \|", batch, re.M)
        try:
            rows = json.load(open(fp, encoding="utf-8"))
        except Exception as ex:
            print(os.path.basename(fp), "is not valid JSON:", ex)
            continue
        ids = [r.get("id") for r in rows if isinstance(r, dict)]
        miss = [i for i in want if i not in ids]
        extra = [i for i in ids if i not in want]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        print(os.path.basename(fp), "rows", len(rows), "| missing", miss, "| extra", extra, "| duplicates", dup)
        for r in rows:
            if not isinstance(r, dict) or r.get("id") not in ents:
                continue
            if r["id"] in seen and r["id"] not in skipped_first:
                continue
            if r["id"] in skipped_first:                       # the second pass replaces the skip
                skipped_first.discard(r["id"])
                rej[:] = [x for x in rej if x["id"] != r["id"]]
            seen.add(r["id"])
            if r.get("status") == "skip" and "enc3_" not in os.path.basename(fp):
                skipped_first.add(r["id"])
            bad = check(ents[r["id"]], r)
            if bad:
                rej.append({"id": r["id"], "reasons": bad})
            elif r["status"] == "ok":
                ok.append({**r, "page": ents[r["id"]]["page"], "district": ents[r["id"]]["district"]})
        for i in miss:
            rej.append({"id": i, "reasons": ["missing in the result"]})
    skip = sum(1 for i in seen if i not in {o["id"] for o in ok} and i not in {x["id"] for x in rej})
    json.dump({"ok": ok, "rejected": rej}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok: %d | skip: %d | rejected: %d" % (len(ok), skip, len(rej)))
    for x in rej[:40]:
        print("  ", x["id"], "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
