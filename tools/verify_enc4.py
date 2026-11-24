"""Check the answers of the full pass (work/gemini/enc_batches/enc4_batch_NN_result.json, rules: tasks/enc4_streets.md) against the text of the entries.
Rules: every id once; the schema; the quotes are verbatim parts of the entry (the repaired text or the raw OCR text) and hold the year (the decade for "dec"); the chain is continuous; an interval of the kind "origin"
starts in the year of "origin" and its quote names the former name; undated names carry quotes; the Georgian note equals the template; no Cyrillic in ka/en; no the calque of the word "prospect".
Output: data/cache/enc2008_verified4.json ({"ok": [...], "rejected": [{"id", "reasons"}], "skip": [{"id", "reason"}]}).
Usage: python -P tools/verify_enc4.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
BAT = os.path.join(ROOT, "work", "gemini", "batches", "enc")
OUT = os.path.join(ROOT, "data", "cache", "enc2008_verified4.json")
CYR = re.compile("[Ѐ-ӿ]")
CALQUE = "პროსპექტ"
BOOK = "ენციკლოპედია „თბილისი. ქუჩები, გამზირები, მოედნები“ (2008): "
KEYS = {"id", "status", "skip_reason", "ka_now", "ru_now", "en_now", "origin", "intervals", "undated", "note_ka"}
IKEYS = {"from", "to", "kind", "ka", "ru", "en", "quote"}
UKEYS = {"ka", "ru", "en", "quote"}
SKIP = {"no_earlier_names", "gone", "not_a_street", "unsure"}


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
    if k == "origin":
        return "წარმოქმნიდან (რუკაზე პირობითად %d-დან)" % y
    return "%d წლის შემდეგ (ზუსტი წელი დასახელებული არ არის, რუკაზე პირობითად %d-დან)" % (y, y)


def check(e, r):
    bad = []
    if not isinstance(r, dict) or set(r) != KEYS:
        return ["keys differ"]
    if r["status"] == "skip":
        return [] if r["skip_reason"] in SKIP else ["skip_reason"]
    if r["status"] != "ok":
        return ["status"]
    text, raw = norm(e["text"]), norm(e.get("text_raw", e["text"]))
    inn = lambda q: bool(q) and (q in text or q in raw)
    for f in ("ka_now", "ru_now", "en_now", "note_ka"):
        if not isinstance(r[f], str) or not r[f].strip():
            bad.append("empty " + f)
    if CYR.search(r["ka_now"] or "") or CYR.search(r["en_now"] or "") or CYR.search(r["note_ka"] or "") or CALQUE in (r["ka_now"] or "") + (r["note_ka"] or ""):
        bad.append("Cyrillic or the calque in the Georgian or English fields")
    org = r["origin"]
    if org is not None:
        if not (isinstance(org, dict) and set(org) == {"from", "quote"} and isinstance(org["from"], int) and 900 <= org["from"] <= 2010):
            bad.append("origin shape")
        elif not inn(norm(org["quote"])):
            bad.append("the origin quote is not a verbatim part of the entry")
    if not r["intervals"] and not r["undated"]:
        return bad + ["status ok with no intervals and no undated names"]
    prev = None
    for i, iv in enumerate(r["intervals"]):
        if set(iv) != IKEYS:
            bad.append("interval %d keys" % i)
            continue
        if not (isinstance(iv["from"], int) and isinstance(iv["to"], int) and 900 <= iv["from"] < iv["to"] <= 2030):
            bad.append("interval %d years" % i)
            continue
        if iv["kind"] not in ("exact", "plan", "dec", "after", "origin"):
            bad.append("interval %d kind" % i)
        if prev is not None and prev != iv["from"] and iv["kind"] != "dec":
            bad.append("interval %d does not follow the previous one" % i)
        prev = iv["to"]
        q = norm(iv["quote"])
        if not inn(q):
            bad.append("interval %d: the quote is not a verbatim part of the entry" % i)
        elif iv["kind"] == "origin":
            if i != 0 or org is None or iv["from"] != org["from"]:
                bad.append("interval %d: origin without a matching origin or not the first" % i)
        elif iv["kind"] == "dec":
            if not re.search(r"\b%d-" % (iv["from"] % 100), q):
                bad.append("interval %d: the decade is not in the quote" % i)
        elif str(iv["from"]) not in q:
            bad.append("interval %d: the year %d is not in the quote" % (i, iv["from"]))
        for f in ("ka", "en"):
            if CYR.search(iv[f]) or not iv[f].strip():
                bad.append("interval %d: %s empty or with Cyrillic" % (i, f))
        if CALQUE in iv["ka"] or not iv["ru"].strip():
            bad.append("interval %d: ru empty or the calque" % i)
    for j, u in enumerate(r["undated"]):
        if not (isinstance(u, dict) and set(u) == UKEYS) or not inn(norm(u["quote"])):
            bad.append("undated %d: shape or quote" % j)
        elif CYR.search(u["ka"] + u["en"]) or CALQUE in u["ka"] or not u["ru"].strip():
            bad.append("undated %d: Cyrillic or empty" % j)
    if not bad:
        parts = ["%s — %s" % (label(iv), iv["ka"]) for iv in r["intervals"]]
        want = BOOK
        if parts:
            want += "; ".join(parts) + "; %d — %s." % (r["intervals"][-1]["to"], r["ka_now"])
        if r["undated"]:
            want += (" " if parts else "") + "ადრე ერქვა (წელი დასახელებული არ არის): " + "; ".join(u["ka"] for u in r["undated"]) + "."
        if norm(r["note_ka"]) != norm(want):
            bad.append("note_ka differs from the template")
    return bad


def main():
    ents = {e["id"]: e for e in json.load(open(ENT, encoding="utf-8"))}
    files = sorted(glob.glob(os.path.join(BAT, "enc4_batch_*_result.json")))
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
            if not isinstance(r, dict) or r.get("id") not in ents:
                continue
            if r["id"] in seen:                     # a later pass (for example the pack of the squares) may turn an earlier "skip" or a rejected row into an accepted answer
                if r.get("status") == "ok" and any(x["id"] == r["id"] for x in skip + rej) and not check(ents[r["id"]], r):
                    skip[:] = [x for x in skip if x["id"] != r["id"]]
                    rej[:] = [x for x in rej if x["id"] != r["id"]]
                    ok.append({**r, "page": ents[r["id"]]["page"], "district": ents[r["id"]]["district"]})
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
    fix = os.path.join(ROOT, "work", "gemini", "results/enc4_fix.json")      # the corrected rows replace the rejected ones
    if os.path.exists(fix):
        rejected_ids = {x["id"] for x in rej}
        for r in json.load(open(fix, encoding="utf-8")):
            if not isinstance(r, dict) or r.get("id") not in rejected_ids:
                continue
            rej[:] = [x for x in rej if x["id"] != r["id"]]
            bad = check(ents[r["id"]], r)
            if bad:
                rej.append({"id": r["id"], "reasons": ["after the correction: " + b for b in bad]})
            elif r["status"] == "ok":
                ok.append({**r, "page": ents[r["id"]]["page"], "district": ents[r["id"]]["district"]})
            else:
                skip.append({"id": r["id"], "reason": r["skip_reason"]})
    man = os.path.join(ROOT, "tools", "enc4_manual.json")                        # rows added by hand after a look at the scan of the PDF (the OCR lost a digit): text_fix repairs the entry before the check
    if os.path.exists(man):
        md = json.load(open(man, encoding="utf-8"))
        for r in md["rows"]:
            e = dict(ents[r["id"]])
            for k in ("text", "text_raw"):
                for x, y in md.get("text_fix", {}).get(r["id"], []):
                    if k in e:
                        e[k] = e[k].replace(x, y)
            bad = check(e, r)
            if bad:
                print("manual row", r["id"], "does not pass:", bad)
                continue
            ok[:] = [x for x in ok if x["id"] != r["id"]]
            skip[:] = [x for x in skip if x["id"] != r["id"]]
            rej[:] = [x for x in rej if x["id"] != r["id"]]
            ok.append({**r, "page": ents[r["id"]]["page"], "district": ents[r["id"]]["district"]})
    json.dump({"ok": ok, "rejected": rej, "skip": skip}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok: %d | skip: %d | rejected: %d" % (len(ok), len(skip), len(rej)))
    for x in rej[:50]:
        print("  ", x["id"], "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
