"""Checks the answer of Gemini of the second search of the origin of the names (for_gemini/from_desktop/places3_result.json, rules: places3_TASK_for_gemini.md; the table places3_batch_01.md):
every place once in the order of the table; the schema; for "web" the address is on ka/ru/en.wikipedia.org, georgianencyclopedia.ge, or (when kind == "dictionary") ka/ru/en.wiktionary.org or ena.ge,
the page is downloaded and the quote (<= 40 words) must stand on it verbatim (a page that cannot be read gives "unchecked", not a rejection); for "enc" the quote is a verbatim part of the text of the page
of the encyclopedia of 2008 (+-1); every year of "etym" stands in the quote; no Cyrillic in ka/en. Output: data/cache/places_etym_verified.json ({"ok": [rows], "unchecked": [...], "rejected": [...], "skip": [...]}).
Usage: python -P tools/verify_places_etym.py
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_metro import HOSTS, page_text  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FD = os.path.join(R, "for_gemini", "from_desktop")
CYR = re.compile("[А-Яа-яЁё]")
KEYS = {"key", "status", "skip_reason", "etym", "source", "page", "url", "lang", "quote"}
DICT_HOSTS = ("ka.wiktionary.org", "ru.wiktionary.org", "en.wiktionary.org", "ena.ge", "www.ena.ge")
ALL_HOSTS = HOSTS + DICT_HOSTS


def enc_pages():
    by = {}
    for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", open(os.path.join(R, "data", "cache", "ocr", "streets_enc2008_kat.txt"), encoding="utf-8", errors="replace").read(), re.S):
        by.setdefault(int(m.group(1)), []).append(norm(m.group(2)))
    ents = json.load(open(os.path.join(R, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))
    for e in ents:
        by.setdefault(e["page"], []).append(norm(e.get("text_long") or e["text"]) + " " + norm(e.get("text_long_raw") or ""))
    return by


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    keys = re.findall(r"^\| ((?:district|garden|hill|bridge|cemetery|market|bath|area):[^ |]+) \|", open(os.path.join(FD, "places3_batch_01.md"), encoding="utf-8").read(), re.M)
    rows = json.load(open(os.path.join(FD, "places3_result.json"), encoding="utf-8"))
    got = [r.get("key") for r in rows if isinstance(r, dict)]
    print("rows", len(rows), "| table", len(keys), "| missing", [k for k in keys if k not in got], "| extra", [k for k in got if k not in keys], "| duplicates", sorted({k for k in got if got.count(k) > 1}), "| order ok", got == keys)
    by = enc_pages()
    res = {"ok": [], "unchecked": [], "rejected": [], "skip": []}
    seen = set()
    for r in rows:
        if not isinstance(r, dict) or r.get("key") not in keys or r["key"] in seen:
            continue
        seen.add(r["key"])
        k = r["key"]
        if not (KEYS <= set(r) <= (KEYS | {"kind"})):
            res["rejected"].append({"key": k, "reasons": ["keys differ"]})
            continue
        if "kind" in r and r["kind"] not in ("origin", "dictionary"):
            res["rejected"].append({"key": k, "reasons": ["kind"]})
            continue
        if r["status"] == "skip":
            (res["skip"] if r["skip_reason"] in ("not_found", "unsure") else res["rejected"]).append({"key": k, "reason": r["skip_reason"], "reasons": ["skip_reason"]})
            continue
        bad, unc = [], []
        e = r["etym"]
        if r["status"] != "ok" or not (isinstance(e, dict) and set(e) == {"ru", "en", "ka"} and all(isinstance(e[x], str) and e[x].strip() for x in e)):
            res["rejected"].append({"key": k, "reasons": ["status or etym"]})
            continue
        if CYR.search(e["ka"] + e["en"]):
            bad.append("Cyrillic in ka/en")
        if "პროსპექტ" in e["ka"]:
            bad.append("prospekt")
        q = norm(r["quote"] or "")
        if not q or len(q.split()) > 40:
            bad.append("quote empty or longer than 40 words")
        for y in set(re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", " ".join(e.values()))):
            if y not in q:
                bad.append("the year %s is not in the quote" % y)
        if r["lang"] not in ("ka", "ru", "en"):
            bad.append("lang")
        if r["source"] == "web":
            u = urllib.parse.urlparse(r["url"])
            if u.scheme != "https" or u.netloc not in ALL_HOSTS:
                bad.append("the address is not on the allowed sites")
            elif u.netloc in DICT_HOSTS and r.get("kind") != "dictionary":
                bad.append("dictionary host requires kind=dictionary")
            elif q:
                t = page_text(r["url"])
                if t is None:
                    unc.append("the page cannot be read")
                elif q not in t:
                    bad.append("the quote is not on the page")
        elif r["source"] == "enc":
            pg = r["page"]
            if not isinstance(pg, int) or not any(q in t for p in (pg - 1, pg, pg + 1) for t in by.get(p, [])):
                bad.append("the quote is not a verbatim part of the text of page %s (+-1)" % pg)
        else:
            bad.append("source")
        if bad:
            res["rejected"].append({"key": k, "reasons": bad})
        elif unc:
            res["unchecked"].append({"key": k, "reasons": unc, "row": r})
        else:
            res["ok"].append(r)
    json.dump(res, open(os.path.join(R, "data", "cache", "places_etym_verified.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print({x: len(v) for x, v in res.items()})
    for x in res["rejected"][:40]:
        print("  rejected", x["key"], "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
