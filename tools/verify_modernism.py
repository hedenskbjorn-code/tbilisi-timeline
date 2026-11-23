"""Checks the answer of Gemini about the buildings of Soviet modernism (for_gemini/from_desktop/modernism_result.json, rules: modernism_TASK_for_gemini.md).
Per building: the schema; a Wikidata id (Q + digits) or empty; "year" a number or null; status in existing/renovated/abandoned/demolished; names in ru/en/ka (no Cyrillic in ka/en, no "პროსპექტი");
at least two sources on DIFFERENT sites (one Wikipedia / Georgian encyclopedia page is enough); every quote (<= 30 words) stands verbatim on its page (downloaded by tools/safe_fetch.py: https, public addresses, text pages);
at least one "style" quote that itself names modernism / brutalism / a Soviet modernist style; every 4-digit year of the description (any language) stands in some quote; the year field stands in some quote.
A page that cannot be read gives "unchecked", not a rejection. Output: data/cache/modernism_verified.json ({"ok", "unchecked", "rejected"}).
Usage: python -P tools/verify_modernism.py
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_fetch import fetch_text  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(R, "for_gemini", "from_desktop", "modernism_result.json")
OUT = os.path.join(R, "data", "cache", "modernism_verified.json")
CYR = re.compile("[А-Яа-яЁё]")
STATUS = {"existing", "renovated", "abandoned", "demolished"}
FACTS = {"year", "architects", "function", "style", "status", "about"}
STYLE = re.compile(r"modernis|brutalis|модернист|брутал|მოდერნიზ|მოდერნისტ|ბრუტალ", re.I)
SINGLE_OK = re.compile(r"(wikipedia|wiktionary)\.org$|georgianencyclopedia\.ge$")


def site(u):
    h = (urllib.parse.urlparse(u).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def canon(s):
    return norm(s).replace("“", '"').replace("”", '"').replace("„", '"').replace("«", '"').replace("»", '"').replace("’", "'").casefold()


def check(b):
    """(problems, unchecked) of one building"""
    p, un = [], []
    n = b.get("name") or {}
    for k in ("ru", "en", "ka"):
        if not (n.get(k) or "").strip():
            p.append("name." + k + " empty")
    if CYR.search(n.get("ka", "") + n.get("en", "")):
        p.append("Cyrillic in the name ka/en")
    w = b.get("wikidata") or ""
    if w and not re.fullmatch(r"Q\d+", w):
        p.append("bad wikidata id")
    y = b.get("year")
    if y is not None and not (isinstance(y, int) and 1900 <= y <= 1995):
        p.append("year out of range / not a number")
    if b.get("status") not in STATUS:
        p.append("bad status")
    d = b.get("description") or {}
    for k in ("ru", "en", "ka"):
        if not (d.get(k) or "").strip():
            p.append("description." + k + " empty")
    if CYR.search(d.get("ka", "") + d.get("en", "")):
        p.append("Cyrillic in description ka/en")
    if "პროსპექტი" in json.dumps(b, ensure_ascii=False):
        p.append("the word პროსპექტი (must be გამზირი)")
    src = b.get("sources") or []
    if len(src) < 2 and not (len(src) == 1 and SINGLE_OK.search(site(src[0].get("url", "")))):
        p.append("fewer than two sources")
    if len({site(s.get("url", "")) for s in src}) < 2 and not (len(src) >= 1 and SINGLE_OK.search(site(src[0].get("url", "")))):
        p.append("sources are not on different sites")
    quotes, style_ok = [], False
    for s in src:
        q, u = s.get("quote") or "", s.get("url") or ""
        if s.get("fact") not in FACTS:
            p.append("bad fact " + str(s.get("fact")))
        if not q or len(q.split()) > 30:
            p.append("quote empty or over 30 words: " + u)
            continue
        quotes.append(q)
        if s.get("fact") == "style" and STYLE.search(q):
            style_ok = True
        page = fetch_text(u)
        if page is None:
            un.append(u)
        elif canon(q) not in canon(page):
            p.append("quote not found on the page: " + u)
    if not style_ok:
        p.append("no style quote that names modernism / brutalism")
    allq = " ".join(quotes)
    if y is not None and str(y) not in allq:
        p.append("year %s not in any quote" % y)
    for yy in set(re.findall(r"\b(1[89]\d\d)\b", " ".join(d.values()))):
        if yy not in allq:
            p.append("year %s of the description not in any quote" % yy)
    return p, un


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = json.load(open(RES, encoding="utf-8"))
    out = {"ok": [], "unchecked": [], "rejected": []}
    for b in rows:
        p, un = check(b)
        name = (b.get("name") or {}).get("en", "?")
        if p:
            out["rejected"].append({"name": name, "problems": p})
        elif un:
            out["unchecked"].append({"name": name, "pages": un, "row": b})
        else:
            out["ok"].append(b)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("rows", len(rows), {k: len(v) for k, v in out.items()})
    for r in out["rejected"]:
        print("  REJECT", r["name"], "|", "; ".join(r["problems"]))
    for r in out["unchecked"]:
        print("  UNCHECKED", r["name"], r["pages"])


if __name__ == "__main__":
    main()
