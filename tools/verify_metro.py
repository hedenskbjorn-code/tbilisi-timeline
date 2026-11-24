"""Check the answer of Gemini about the former names of the stations of the metro (work/gemini/batches/metro/metro_batch_01_result.json, rules: tasks/metro.md).
Row: {"id", "status": "ok"|"skip", "skip_reason", "former": [{"ka", "ru", "en", "from", "to", "kind": "exact"|"undated", "source": "enc"|"web", "page", "url", "quote"}]}.
Rules: every station of tools/metro_task.py (the stations of transport.json) once, in the order; the schema; no Cyrillic in ka/en; for "enc" the quote (<= 40 words) is a verbatim part of the text of the page "page" (+-1,
the entries and the page OCR, the breaks of words joined) and the stem of the longest word of the former Georgian name stands in it; for "web" the address is on ka/ru/en.wikipedia.org or
georgianencyclopedia.ge: the page is downloaded and the quote must stand on it verbatim (if the page cannot be read the row is marked "unchecked" and is NOT rejected: the owner decides); the years
(from, to) stand in the quote as numbers when they are given.
Output: data/cache/metro_verified.json ({"ok": [...], "unchecked": [...], "rejected": [...], "skip": [...]}). Usage: python -P tools/verify_metro.py
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_mainroads import norm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
PAGES = os.path.join(ROOT, "data", "cache", "ocr", "streets_enc2008_kat.txt")
RES = os.path.join(ROOT, "work", "gemini", "batches/metro/metro_batch_01_result.json")
OUT = os.path.join(ROOT, "data", "cache", "metro_verified.json")
CYR = re.compile("[Ѐ-ӿ]")
HOSTS = ("ka.wikipedia.org", "ru.wikipedia.org", "en.wikipedia.org", "georgianencyclopedia.ge", "www.georgianencyclopedia.ge")
FKEYS = {"ka", "ru", "en", "from", "to", "kind", "source", "page", "url", "quote"}
SKIPS = {"no_former_names", "unsure"}
UA = {"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}
_cache = {}


def stem(ka):
    ws = [w for w in re.findall(r"[ა-ჰ]+", ka or "") if len(w) >= 4]
    return max(ws, key=len)[:4] if ws else ""


def page_text(url):
    if url in _cache:
        return _cache[url]
    t = None
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", errors="replace")
        raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
        t = norm(html.unescape(re.sub(r"<[^>]+>", " ", raw)))
    except Exception:
        t = None
    _cache[url] = t
    return t


def main():
    ids = [x[0] for x in re.findall(r"^\| ([^|]+?) \| (\d) \|", open(os.path.join(ROOT, "work", "gemini", "batches/metro/metro_batch_01.md"), encoding="utf-8").read(), re.M)]
    ents = json.load(open(ENT, encoding="utf-8"))
    by_page = {}
    for e in ents:
        by_page.setdefault(e["page"], []).append(norm(e.get("text_long") or e["text"]) + " " + norm(e.get("text_long_raw") or ""))
    for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", open(PAGES, encoding="utf-8", errors="replace").read(), re.S):
        by_page.setdefault(int(m.group(1)), []).append(norm(m.group(2)))
    rows = json.load(open(RES, encoding="utf-8")) if os.path.exists(RES) else sys.exit("no result file yet")
    got = [r.get("id") for r in rows if isinstance(r, dict)]
    print("rows", len(rows), "| missing", [i for i in ids if i not in got], "| extra", [i for i in got if i not in ids], "| duplicates", sorted({i for i in got if got.count(i) > 1}))
    ok, unchecked, rej, skip, seen = [], [], [], [], set()
    for r in rows:
        if not isinstance(r, dict) or r.get("id") not in ids or r["id"] in seen:
            continue
        seen.add(r["id"])
        if set(r) != {"id", "status", "skip_reason", "former"}:
            rej.append({"id": r["id"], "reasons": ["keys differ"]})
            continue
        if r["status"] == "skip":
            (skip if r["skip_reason"] in SKIPS else rej).append({"id": r["id"], "reason": r["skip_reason"]} if r["skip_reason"] in SKIPS else {"id": r["id"], "reasons": ["skip_reason"]})
            continue
        bad, unc, good = [], [], []
        if r["status"] != "ok" or not isinstance(r["former"], list) or not r["former"]:
            rej.append({"id": r["id"], "reasons": ["status ok without a former name"]})
            continue
        for k, f in enumerate(r["former"]):
            w = "former %d" % k
            if not isinstance(f, dict) or set(f) != FKEYS:
                bad.append(w + " keys")
                continue
            b = []
            if not all(isinstance(f[x], str) and f[x].strip() for x in ("ka", "ru", "en")) or CYR.search(f["ka"] + f["en"]):
                b.append("names (empty or Cyrillic in ka/en)")
            q = norm(f["quote"] or "")
            if not q or len(q.split()) > 40:
                b.append("quote empty or longer than 40 words")
            for y in (f["from"], f["to"]):
                if y is not None and (not isinstance(y, int) or str(y) not in q):
                    b.append("the year %s is not in the quote" % y)
            if f["source"] == "enc":
                pg = f["page"]
                if not isinstance(pg, int) or not any(q in t for p in (pg - 1, pg, pg + 1) for t in by_page.get(p, [])):
                    b.append("the quote is not a verbatim part of the text of page %s (+-1)" % pg)
                elif stem(f["ka"]) and stem(f["ka"]) not in q:
                    b.append("the former name is not in the quote")
            elif f["source"] == "web":
                u = urllib.parse.urlparse(f["url"])
                if u.scheme != "https" or u.netloc not in HOSTS:
                    b.append("the address is not on the allowed sites")
                else:
                    t = page_text(f["url"])
                    if t is None:
                        unc.append(w + ": the page cannot be read")
                    elif q not in t:
                        b.append("the quote is not on the page")
            else:
                b.append("source")
            if b:
                bad += [w + ": " + x for x in b]
            else:
                good.append(f)
        if bad:
            rej.append({"id": r["id"], "reasons": bad})
        elif unc:
            unchecked.append({"id": r["id"], "reasons": unc, "former": r["former"]})
        else:
            ok.append({"id": r["id"], "former": good})
    json.dump({"ok": ok, "unchecked": unchecked, "rejected": rej, "skip": skip}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok: %d | unchecked: %d | skip: %d | rejected: %d" % (len(ok), len(unchecked), len(skip), len(rej)))
    for x in rej:
        print("  rejected", x["id"], "; ".join(x["reasons"])[:220])


if __name__ == "__main__":
    main()
