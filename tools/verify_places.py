"""Checks the answer of Gemini about the local names (work/gemini/results/places2.json, rules: tasks/places2.md) against the articles (data/cache/places_wiki.json):
one row per place of the packs in the order of the packs; the keys by the schema; a quote is a verbatim part of the text of the article in the language named (the spaces squeezed); "etym" only with a quote;
every year of "about" and "etym" stands in the articles of the place; no Cyrillic in ka/en. Output: data/cache/places_verified.json ({"ok": [...rows], "skip": [...], "rejected": [{"key", "reasons"}]}).
Usage: python -P tools/verify_places.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI as FD  # noqa: E402
CYR = re.compile("[А-Яа-яЁё]")
KEYS = {"key", "status", "skip_reason", "name", "about", "about_quote", "etym", "etym_quote"}
KINDS = {"district", "garden", "hill", "market", "bath", "bridge", "cemetery"}


def sq(s):
    return re.sub(r"\s+", " ", (s or "").replace(" ", " ")).strip()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    wiki = json.load(open(os.path.join(R, "data", "cache", "places_wiki.json"), encoding="utf-8"))
    keys = []
    BD = os.path.join(FD, "batches", "places2")
    for fn in sorted(os.listdir(BD)):
        if re.match(r"places2_batch_\d+\.md$", fn):
            keys += re.findall(r"^## (\S+)$", open(os.path.join(BD, fn), encoding="utf-8").read(), re.M)
    rows = json.load(open(os.path.join(FD, "results/places2.json"), encoding="utf-8"))
    got = [r.get("key") for r in rows if isinstance(r, dict)]
    print("rows", len(rows), "| packs", len(keys), "| missing", [k for k in keys if k not in got], "| extra", [k for k in got if k not in keys], "| duplicates", sorted({k for k in got if got.count(k) > 1}), "| order ok", got == keys)
    res = {"ok": [], "skip": [], "rejected": []}
    seen = set()
    for r in rows:
        if not isinstance(r, dict) or r.get("key") not in keys or r["key"] in seen:
            continue
        seen.add(r["key"])
        k = r["key"]
        bad = []
        if set(r) != KEYS:
            res["rejected"].append({"key": k, "reasons": ["keys differ: " + str(set(r) ^ KEYS)]})
            continue
        if r["status"] == "skip":
            (res["skip"] if r["skip_reason"] in ("no_info", "not_local", "unsure") else res["rejected"]).append({"key": k, "reason": r["skip_reason"], "reasons": ["skip_reason"]})
            continue
        if r["status"] != "ok":
            res["rejected"].append({"key": k, "reasons": ["status"]})
            continue
        pages = wiki.get(k, {}).get("pages", {})
        arts = {lg: sq(p["text"]) for lg, p in pages.items()}
        allt = " ".join(arts.values())
        n = r["name"]
        if not (isinstance(n, dict) and set(n) == {"ka", "ru", "en"} and all(isinstance(n[x], str) and n[x].strip() for x in n)) or CYR.search(str(n.get("ka")) + str(n.get("en"))):
            bad.append("name")
        for fld in ("about", "etym"):
            v = r[fld]
            if fld == "etym" and v is None:
                continue
            if not (isinstance(v, dict) and set(v) == {"ru", "en", "ka"} and all(isinstance(v[x], str) and v[x].strip() for x in v)) or CYR.search(str(v.get("ka")) + str(v.get("en"))):
                bad.append(fld + " text")
                continue
            for y in set(re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", " ".join(v.values()))):
                if y not in allt:
                    bad.append("%s: the year %s is not in the articles" % (fld, y))
            if "პროსპექტ" in v["ka"]:
                bad.append(fld + ": prospekt")
        for fld in ("about_quote", "etym_quote"):
            q = r[fld]
            if fld == "etym_quote" and r["etym"] is None:
                if q is not None:
                    bad.append("etym_quote without etym")
                continue
            if not (isinstance(q, dict) and set(q) == {"lang", "quote"} and q["lang"] in arts):
                bad.append(fld + ": lang or keys (the place has articles in " + ",".join(arts) + ")")
                continue
            qq = sq(q["quote"])
            if not qq or len(qq.split()) > 40:
                bad.append(fld + ": empty or longer than 40 words")
            elif qq not in arts[q["lang"]]:
                bad.append(fld + ": the quote is not a verbatim part of the article " + q["lang"])
        if r["etym"] is None and r["etym_quote"] is not None:
            bad.append("etym_quote without etym")
        if bad:
            res["rejected"].append({"key": k, "reasons": bad})
        else:
            res["ok"].append(r)
    json.dump(res, open(os.path.join(R, "data", "cache", "places_verified.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print({x: len(v) for x, v in res.items()}, "| with etymology:", sum(1 for r in res["ok"] if r["etym"]))
    for x in res["rejected"][:60]:
        print("  rejected", x["key"], "; ".join(x["reasons"])[:220])


if __name__ == "__main__":
    main()
