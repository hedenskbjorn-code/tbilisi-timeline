"""Checks the answer of Gemini about the places whose name is made of words (for_gemini/from_desktop/places4_result.json, rules: places4_TASK_for_gemini.md; the table places4_batch_01.md): every place once in the order
of the table; the schema; "parts": at least two words, every one with the address of ITS OWN page (ka/ru/en Wiktionary or ena.ge: the decoded address holds the word) and a quote (<= 40 words) that stands verbatim on
that page (the page is downloaded; a page that cannot be read gives "unchecked"); no Cyrillic in ka/en; every year of the text stands in a quote. Output: data/cache/places_parts_verified.json ({"ok", "unchecked", "rejected", "skip"}).
Usage: python -P tools/verify_places_parts.py
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_metro import page_text  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FD = os.path.join(R, "for_gemini", "from_desktop")
CYR = re.compile("[А-Яа-яЁё]")
HOSTS = ("ka.wiktionary.org", "ru.wiktionary.org", "en.wiktionary.org", "ena.ge", "www.ena.ge")
KEYS = {"key", "status", "skip_reason", "etym", "parts"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    keys = re.findall(r"^\| ((?:district|garden|hill|bridge|cemetery|market|bath|area):[^ |]+) \|", open(os.path.join(FD, "places4_batch_01.md"), encoding="utf-8").read(), re.M)
    rows = json.load(open(os.path.join(FD, "places4_result.json"), encoding="utf-8"))
    got = [r.get("key") for r in rows if isinstance(r, dict)]
    print("rows", len(rows), "| table", len(keys), "| missing", [k for k in keys if k not in got], "| extra", [k for k in got if k not in keys], "| duplicates", sorted({k for k in got if got.count(k) > 1}), "| order ok", got == keys)
    res = {"ok": [], "unchecked": [], "rejected": [], "skip": []}
    seen = set()
    for r in rows:
        if not isinstance(r, dict) or r.get("key") not in keys or r["key"] in seen:
            continue
        seen.add(r["key"])
        k = r["key"]
        if set(r) != KEYS:
            res["rejected"].append({"key": k, "reasons": ["keys differ"]})
            continue
        if r["status"] == "skip":
            (res["skip"] if r["skip_reason"] in ("not_found", "unsure") else res["rejected"]).append({"key": k, "reason": r["skip_reason"]})
            continue
        bad, unc = [], []
        e, parts = r["etym"], r["parts"]
        if r["status"] != "ok" or not (isinstance(e, dict) and set(e) == {"ru", "en", "ka"} and all(isinstance(e[x], str) and e[x].strip() for x in e)) or not isinstance(parts, list) or len(parts) < 2:
            res["rejected"].append({"key": k, "reasons": ["status, etym or fewer than two parts"]})
            continue
        if CYR.search(e["ka"] + e["en"]) or "პროსპექტ" in e["ka"]:
            bad.append("Cyrillic in ka/en or prospekt")
        allq = ""
        for j, pt in enumerate(parts):
            w = "part %d" % j
            if not isinstance(pt, dict) or set(pt) != {"word", "url", "lang", "quote"} or pt["lang"] not in ("ka", "ru", "en"):
                bad.append(w + ": keys or lang")
                continue
            u = urllib.parse.urlparse(pt["url"])
            word = pt["word"].strip().strip("-")
            if u.scheme != "https" or u.netloc not in HOSTS:
                bad.append(w + ": the address is not on the allowed sites")
                continue
            if not word or word not in urllib.parse.unquote(pt["url"]):
                bad.append(w + ": the page is not the page of the word " + pt["word"])
                continue
            q = norm(pt["quote"] or "")
            if not q or len(q.split()) > 40:
                bad.append(w + ": quote empty or longer than 40 words")
                continue
            t = page_text(pt["url"])
            if t is None:
                unc.append(w + ": the page cannot be read")
            elif q not in t:
                bad.append(w + ": the quote is not on the page")
            allq += " " + q
        for y in set(re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", " ".join(e.values()))):
            if y not in allq:
                bad.append("the year %s is not in a quote" % y)
        if bad:
            res["rejected"].append({"key": k, "reasons": bad})
        elif unc:
            res["unchecked"].append({"key": k, "reasons": unc})
        else:
            res["ok"].append(r)
    json.dump(res, open(os.path.join(R, "data", "cache", "places_parts_verified.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print({x: len(v) for x, v in res.items()})
    for x in res["rejected"][:20]:
        print("  rejected", x["key"], "; ".join(x["reasons"])[:200])
    c = {x["key"]: x for x in json.load(open(os.path.join(R, "data", "cache", "places_candidates.json"), encoding="utf-8"))}
    for r in res["ok"]:
        print("##", c[r["key"]]["name"]["en"], "|", r["etym"]["ru"][:150])
        for pt in r["parts"]:
            print("     ", pt["word"], "|", pt["quote"][:110])


if __name__ == "__main__":
    main()
