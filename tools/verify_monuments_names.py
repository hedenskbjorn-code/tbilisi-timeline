"""Checks the answer of Gemini about the names of monuments and plaques (work/gemini/results/monuments_names.json, the table batches/monuments_names/monuments_names_batch_01.md): the keys and the order;
the fields that were filled stay as they were; the empty ones are filled; no Cyrillic in ka/en; Cyrillic in ru; "prospekt" only as gamziri. Output: data/cache/monuments_names_verified.json ({id: {ka, ru, en}}).
Usage: python -P tools/verify_monuments_names.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CYR = re.compile("[А-Яа-яЁё]")


def script_ok(lg, v):
    cyr, geo = len(CYR.findall(v)), len(re.findall("[ა-ჿ]", v))
    return (geo > 0 and cyr == 0) if lg == "ka" else (cyr == 0) if lg == "en" else (cyr > 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows_in = []
    for ln in open(os.path.join(R, "work", "gemini", "batches/monuments_names/monuments_names_batch_01.md"), encoding="utf-8"):
        m = re.match(r"\| ([mp]:[^|]+?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|$", ln.rstrip("\n"))
        if m:
            rows_in.append((m.group(1), {"ka": m.group(2).strip(), "ru": m.group(3).strip(), "en": m.group(4).strip()}))
    rows = json.load(open(os.path.join(R, "work", "gemini", "results/monuments_names.json"), encoding="utf-8"))
    ids = [i for i, _ in rows_in]
    got = [r.get("id") for r in rows if isinstance(r, dict)]
    print("rows", len(rows), "| table", len(ids), "| missing", [i for i in ids if i not in got][:10], "| extra", [i for i in got if i not in ids][:10], "| order ok", got == ids)
    out, bad = {}, []
    src = dict(rows_in)
    for r in rows:
        if not isinstance(r, dict) or r.get("id") not in src or r["id"] in out:
            continue
        w, reasons = src[r["id"]], []
        if set(r) != {"id", "ka", "ru", "en"} or not all(isinstance(r[k], str) and r[k].strip() for k in ("ka", "ru", "en")):
            bad.append((r["id"], ["keys or an empty field"]))
            continue
        for k in ("ka", "ru", "en"):
            if w[k] and r[k] != w[k] and script_ok(k, w[k]):                  # a given name stays as it is, unless it stands in a field of the wrong script
                reasons.append("%s changed: %r -> %r" % (k, w[k], r[k]))
            if w[k] and not script_ok(k, w[k]) and r[k] == w[k]:
                reasons.append("%s is in the wrong script and was not corrected: %r" % (k, w[k]))
        if CYR.search(r["ka"] + r["en"]):
            reasons.append("Cyrillic in ka/en")
        if len(CYR.findall(r["ru"])) < 2:
            reasons.append("ru has no Cyrillic")
        if "პროსპექტ" in r["ka"]:
            reasons.append("prospekt")
        if reasons:
            bad.append((r["id"], reasons))
        else:
            out[r["id"]] = {k: r[k] for k in ("ka", "ru", "en")}
    json.dump(out, open(os.path.join(R, "data", "cache", "monuments_names_verified.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("ok:", len(out), "| rejected:", len(bad))
    for i, rs in bad[:40]:
        print("  rejected", i, "; ".join(rs)[:200])


if __name__ == "__main__":
    main()
