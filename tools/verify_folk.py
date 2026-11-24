"""Checks the answer of Gemini about the folk (slang) names of the places (work/gemini/results/folk.json, rules: tasks/folk.md; the objects: results/folk_objects.md): the schema; "ref" is from the table of
objects or empty; the folk name stands in a quote of every source; every quote (<= 25 words) stands verbatim on its page (the page is downloaded by tools/safe_fetch.py: only https, public addresses, text pages);
at least two sources on DIFFERENT sites (a single page of Wikipedia / an encyclopedia is enough only when it says so directly); no Cyrillic in ka/en; "adult" is none / rude / obscene.
A page that cannot be read gives "unchecked", not a rejection. No name of a forum user is kept: only the address and the short quote. Output: data/cache/folk_verified.json ({"ok", "unchecked", "rejected"}).
Usage: python -P tools/verify_folk.py
"""
import collections
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_fetch import fetch_text  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI as FD  # noqa: E402
CYR = re.compile("[А-Яа-яЁё]")
KEYS = {"ref", "official", "folk", "meaning", "adult", "sources"}
SINGLE_OK = re.compile(r"(wikipedia|wiktionary)\.org$|georgianencyclopedia\.ge$")


def site(u):
    return urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    refs = set(re.findall(r"^\| \w+ \| ([a-z]{2}:[^ |]+) \|", open(os.path.join(FD, "results/folk_objects.md"), encoding="utf-8").read(), re.M))
    rows = json.load(open(os.path.join(FD, "results/folk.json"), encoding="utf-8"))
    res = {"ok": [], "unchecked": [], "rejected": []}
    for i, r in enumerate(rows):
        bad, unc = [], []
        if not isinstance(r, dict) or set(r) != KEYS:
            res["rejected"].append({"i": i, "reasons": ["keys differ"]})
            continue
        f, off = r["folk"], r["official"]
        if not (isinstance(f, dict) and set(f) == {"ka", "ru", "en"} and any(f.values()) and isinstance(off, dict) and set(off) == {"ka", "ru", "en"}):
            res["rejected"].append({"i": i, "reasons": ["folk or official"]})
            continue
        if CYR.search(f["ka"] + f["en"] + off["ka"] + off["en"]) or "პროსპექტ" in f["ka"]:
            bad.append("Cyrillic in ka/en")
        if r["adult"] not in ("none", "rude", "obscene"):
            bad.append("adult")
        if r["ref"] and r["ref"] not in refs:
            bad.append("ref is not in the table of objects")
        m = r["meaning"]
        if m is not None and not (isinstance(m, dict) and set(m) == {"ru", "en", "ka"} and all(isinstance(m[x], str) and m[x].strip() for x in m)):
            bad.append("meaning")
        srcs = r["sources"]
        if not isinstance(srcs, list) or not srcs:
            res["rejected"].append({"i": i, "reasons": bad + ["no sources"]})
            continue
        sites, names = set(), [norm(x) for x in f.values() if x]
        for j, s in enumerate(srcs):
            if not isinstance(s, dict) or set(s) != {"url", "lang", "quote"} or s["lang"] not in ("ka", "ru", "en"):
                bad.append("source %d: keys or lang" % j)
                continue
            q = norm(s["quote"] or "")
            if not q or len(q.split()) > 25:
                bad.append("source %d: quote empty or longer than 25 words" % j)
                continue
            if not any(n and n.lower() in q.lower() for n in names):
                bad.append("source %d: the folk name is not in the quote" % j)
                continue
            t = fetch_text(s["url"])
            if t is None:
                unc.append("source %d: the page cannot be read safely" % j)
            elif q not in t:
                bad.append("source %d: the quote is not on the page" % j)
            else:
                sites.add(site(s["url"]))
        if not bad and not unc and len(sites) < 2 and not (len(sites) == 1 and SINGLE_OK.search(next(iter(sites)))):
            bad.append("fewer than two independent sites")
        label = f["ka"] or f["ru"] or f["en"]
        if bad:
            res["rejected"].append({"i": i, "folk": label, "reasons": bad})
        elif unc:
            res["unchecked"].append({"i": i, "folk": label, "reasons": unc})
        else:
            res["ok"].append(r)
    json.dump(res, open(os.path.join(R, "data", "cache", "folk_verified.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("rows", len(rows), {k: len(v) for k, v in res.items()}, "| adult (ok rows):", dict(collections.Counter(r["adult"] for r in res["ok"])))
    for x in res["rejected"][:25]:
        print("  rejected", x.get("folk", x["i"]), "; ".join(x["reasons"])[:160])


if __name__ == "__main__":
    main()
