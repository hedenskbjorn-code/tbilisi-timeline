"""Check the answers of the pass about the objects on the streets (for_gemini/from_desktop/enc_batches/enc5_batch_NN_result.json, rules: enc5_objects_TASK_for_gemini.md) against the text of the entries.
Rules: every id of the batch once; the schema; kind, role and year_kind from the lists; the quote is a verbatim part of the long text of the entry (repaired or raw OCR text); the years stand in the quote
as numbers (a range 1833-35: 1833 and 35); the stem of the longest word of name.ka and of person.ka (its first 4 letters) is in the quote; no Cyrillic in ka/en; no the calque of the word "prospect".
Output: data/cache/enc2008_verified5.json ({"ok": [...], "rejected": [{"id", "reasons"}], "skip": [{"id", "reason"}]}).
Usage: python -P tools/verify_enc5.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
BAT = os.path.join(ROOT, "for_gemini", "from_desktop", "enc_batches")
OUT = os.path.join(ROOT, "data", "cache", "enc2008_verified5.json")
CYR = re.compile("[Ѐ-ӿ]")
CALQUE = "პროსპექტ"
KEYS = {"id", "status", "skip_reason", "ka_now", "ru_now", "en_now", "objects"}
OKEYS = {"kind", "name", "person", "role", "year_from", "year_to", "year_kind", "address", "quote"}
KINDS = {"building", "monument", "church", "vanished", "memorial", "planner"}
ROLES = {"architect", "sculptor", "resident", "surveyor", "builder", "founder", "namesake", "other", None}
YKINDS = {"built", "opened", "founded", "erected", "abolished", "lived", "planned", "other", None}
SKIP = {"no_objects", "not_a_street", "unsure"}


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def stem(ka):
    """The first 4 letters of the longest word of a Georgian name (initials and short words do not count)."""
    ws = [w for w in re.findall(r"[ა-ჰ]+", ka or "") if len(w) >= 4]
    return max(ws, key=len)[:4] if ws else ""


def trio(d, f, bad, where):
    if not (isinstance(d, dict) and set(d) == {"ka", "ru", "en"} and all(isinstance(d[k], str) and d[k].strip() for k in d)):
        bad.append("%s shape" % where)
        return
    if CYR.search(d["ka"] + d["en"]) or CALQUE in d["ka"]:
        bad.append("%s: Cyrillic in ka/en or the calque" % where)


def check(e, r):
    bad = []
    if not isinstance(r, dict) or set(r) != KEYS:
        return ["keys differ"]
    if r["status"] == "skip":
        return [] if r["skip_reason"] in SKIP else ["skip_reason"]
    if r["status"] != "ok":
        return ["status"]
    for f in ("ka_now", "ru_now", "en_now"):
        if not isinstance(r[f], str) or not r[f].strip():
            bad.append("empty " + f)
    if CYR.search(r["ka_now"] or "") or CYR.search(r["en_now"] or "") or CALQUE in (r["ka_now"] or ""):
        bad.append("Cyrillic or the calque in the street name")
    if not r["objects"]:
        return bad + ["status ok with no objects"]
    text, raw = norm(e["text_long"]), norm(e.get("text_long_raw", e["text_long"]))
    for i, o in enumerate(r["objects"]):
        w = "object %d" % i
        if not isinstance(o, dict) or set(o) != OKEYS:
            bad.append(w + " keys")
            continue
        if o["kind"] not in KINDS or o["role"] not in ROLES or o["year_kind"] not in YKINDS:
            bad.append(w + " kind/role/year_kind")
        trio(o["name"], "name", bad, w + " name")
        if o["person"] is not None:
            trio(o["person"], "person", bad, w + " person")
        for f in ("year_from", "year_to"):
            if o[f] is not None and not (isinstance(o[f], int) and 900 <= o[f] <= 2030):
                bad.append(w + " " + f)
        if not isinstance(o["address"], str):
            bad.append(w + " address")
        q = norm(o["quote"]) if isinstance(o["quote"], str) else ""
        if not q or (q not in text and q not in raw):
            bad.append(w + ": the quote is not a verbatim part of the entry")
            continue
        for f in ("year_from", "year_to"):
            y = o[f]
            if isinstance(y, int) and str(y) not in q and not (f == "year_to" and re.search(r"[-–—]\s?%02d\b" % (y % 100), q)):
                bad.append("%s: the %s %d is not in the quote" % (w, f, y))
        if o["kind"] != "planner" and isinstance(o["name"], dict) and stem(o["name"].get("ka")) and stem(o["name"]["ka"]) not in q:   # the name of a planner object is the street itself
            bad.append(w + ": the name is not in the quote")
        if isinstance(o["person"], dict) and stem(o["person"].get("ka")) and stem(o["person"]["ka"]) not in q:
            bad.append(w + ": the person is not in the quote")
    return bad


def main():
    ents = {e["id"]: e for e in json.load(open(ENT, encoding="utf-8"))}
    files = sorted(glob.glob(os.path.join(BAT, "enc5_batch_*_result.json")))
    if not files:
        sys.exit("no result files yet")
    ok, rej, skip, seen = [], [], [], set()
    for fp in files:
        want = re.findall(r"^## (E\d{4}) \|", open(fp.replace("_result.json", ".md"), encoding="utf-8").read(), re.M)
        try:
            rows = json.load(open(fp, encoding="utf-8"))
        except Exception as ex:
            print(os.path.basename(fp), "is not valid JSON:", ex)
            continue
        ids = [r.get("id") for r in rows if isinstance(r, dict)]
        print(os.path.basename(fp), "rows", len(rows), "| missing", [i for i in want if i not in ids], "| extra", [i for i in ids if i not in want], "| duplicates", sorted({i for i in ids if ids.count(i) > 1}))
        for r in rows:
            if not isinstance(r, dict) or r.get("id") not in ents or r["id"] in seen:
                continue
            seen.add(r["id"])
            bad = check(ents[r["id"]], r)
            if bad:
                rej.append({"id": r["id"], "reasons": bad})
            elif r["status"] == "ok":
                ok.append({**r, "page": ents[r["id"]]["page"], "district": ents[r["id"]]["district"]})
            else:
                skip.append({"id": r["id"], "reason": r["skip_reason"]})
        for i in want:
            if i not in ids:
                rej.append({"id": i, "reasons": ["missing in the result"]})
    json.dump({"ok": ok, "rejected": rej, "skip": skip}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(len(x["objects"]) for x in ok)
    print("ok streets: %d (objects: %d) | skip: %d | rejected: %d" % (len(ok), n, len(skip), len(rej)))
    for x in rej[:50]:
        print("  ", x["id"], "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
