"""Check the answers of Gemini about the namesakes (for_gemini/from_desktop/namesake_batch_NN_result.json and namesake_objects_result.json, rules: namesake_TASK_for_gemini.md).
Row of an entry: {"id", "status": "ok"|"skip", "skip_reason", "kind": "person"|"place"|"thing"|"event", "name": {ka, ru, en}, "years": [birth, death]|null, "quote", "quote_page", "desc": {ka, ru, en},
"wiki": {"ka": title|"", "ru": title|"", "en": title|""}}. Rules: every id of the pack once; the schema; the quote (<= 40 words) is a verbatim part of the text of the page "quote_page" (+-1; the entries
or the page OCR, the breaks of words joined); the stem of the longest word of name.ka (first 4 letters) stands in the quote (not for kind "thing"/"event" if the name is a description); the years
stand in the quote as numbers; no Cyrillic in ka/en; no "პროსპექტ".
LINKS to Wikipedia only when CONFIRMED (no confirmation, no link): kind "person"; the titles are looked up in the API of Wikipedia (not a disambiguation page, the page has a Wikidata item);
the item is a human (P31 Q5); all the languages that gave a title lead to ONE item; the book gives the years and the item has the same year of birth (and of death if both are known).
For the objects (no text of a book, the name of the object is the quote): the same, but instead of the years of the book two languages must lead to the same human item and the first letter of
the given name must be the initial of the object's name if it has one.
Output: data/cache/namesakes_verified.json ({"ok": [{..., "wiki_ok": {"ka": title, ...}, "qid": "Q..."}], "rejected": [...], "skip": [...]}); cache of the API answers: data/cache/wiki_cache.json.
Usage: python -P tools/verify_namesakes.py [--no-net]
"""
import difflib
import glob
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_mainroads import norm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FD = os.path.join(ROOT, "for_gemini", "from_desktop")
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
PAGES = os.path.join(ROOT, "data", "cache", "ocr", "streets_enc2008_kat.txt")
OUT = os.path.join(ROOT, "data", "cache", "namesakes_verified.json")
CACHE = os.path.join(ROOT, "data", "cache", "wiki_cache.json")
NONET = "--no-net" in sys.argv
CYR = re.compile("[Ѐ-ӿ]")
KINDS = {"person", "place", "thing", "event"}
SKIPS = {"no_namesake", "not_a_toponym", "unsure"}
KEYS = {"id", "status", "skip_reason", "kind", "name", "years", "quote", "quote_page", "desc", "wiki"}
UA = {"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"}


def stem(ka):
    ws = [w for w in re.findall(r"[ა-ჰ]+", ka or "") if len(w) >= 4]
    return max(ws, key=len)[:4] if ws else ""


def name_in_quote(ka, q):
    """the name stands in the quote: the first 4 letters of the longest word, or a word of the quote that is LIKE it (the OCR spoils the surnames: "შარრამვა" for "შარტავა")"""
    st = stem(ka)
    if not st or st in q:
        return True
    lw = max(re.findall(r"[ა-ჰ]+", ka), key=len)
    return max([difflib.SequenceMatcher(None, lw, w).ratio() for w in re.findall(r"[ა-ჰ]+", q)] or [0]) >= 0.7


def year_in_quote(y, q, second):
    """a year stands in the quote (the OCR writes "I944" for 1944; a death year may be given by two digits after a dash: "1944-93")"""
    qq = re.sub(r"[Il](?=\d{3})", "1", q)
    return str(y) in qq or (second and re.search(r"[-–—]\s?%02d\b" % (y % 100), qq) is not None)


def trio(d, bad, w):
    if not (isinstance(d, dict) and set(d) == {"ka", "ru", "en"} and all(isinstance(d[k], str) and d[k].strip() for k in d)):
        bad.append(w + " shape")
        return False
    if CYR.search(d["ka"] + d["en"]) or "პროსპექტ" in d["ka"]:
        bad.append(w + ": Cyrillic in ka/en or the calque")
    return True


def api(url):
    c = CACHE_D.setdefault("api", {})
    if url in c:
        return c[url]
    if NONET:
        return None
    for k in range(4):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
            c[url] = d
            time.sleep(0.2)
            return d
        except Exception as ex:
            time.sleep(3 * (k + 1))
    return None


def wiki_items(lang, titles):
    """{title: ("Q..", False) | (None, True) for a disambiguation | missing: absent}"""
    out = {}
    for i in range(0, len(titles), 40):
        part = titles[i:i + 40]
        u = "https://%s.wikipedia.org/w/api.php?action=query&format=json&redirects=1&prop=pageprops&ppprop=wikibase_item|disambiguation&titles=%s" % (lang, urllib.parse.quote("|".join(part)))
        d = api(u)
        if not d:
            continue
        q = d.get("query", {})
        back = {}
        for k in ("normalized", "redirects"):
            for x in q.get(k, []):
                back[x["to"]] = x["from"] if k == "normalized" else back.get(x["from"], x["from"])
        for pg in q.get("pages", {}).values():
            if "missing" in pg:
                continue
            pp = pg.get("pageprops", {})
            orig = back.get(pg["title"], pg["title"])
            for t in part:
                if t == orig or t == pg["title"] or back.get(t) == pg["title"]:
                    out[t] = (pp.get("wikibase_item"), "disambiguation" in pp)
    return out


def human_years(qids):
    """{qid: (is_human, birth_year, death_year)}"""
    out = {}
    qids = sorted(set(qids))
    for i in range(0, len(qids), 40):
        part = qids[i:i + 40]
        d = api("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims&ids=" + "|".join(part))
        for q, e in ((d or {}).get("entities") or {}).items():
            cl = e.get("claims", {})
            hum = any(((c.get("mainsnak", {}).get("datavalue") or {}).get("value") or {}).get("id") == "Q5" for c in cl.get("P31", []))
            def yr(p):
                for c in cl.get(p, []):
                    v = (c.get("mainsnak", {}).get("datavalue") or {}).get("value")
                    if v and v.get("time"):
                        m = re.match(r"[+-]?(\d+)-", v["time"])
                        if m:
                            return int(m.group(1))
                return None
            out[q] = (hum, yr("P569"), yr("P570"))
    return out


def main():
    global CACHE_D
    CACHE_D = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    ents = json.load(open(ENT, encoding="utf-8"))
    by_page = {}
    for e in ents:
        by_page.setdefault(e["page"], []).append(norm(e.get("text_long") or e["text"]) + " " + norm(e.get("text_long_raw") or "") + " " + norm(e["text"]))
    for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", open(PAGES, encoding="utf-8", errors="replace").read(), re.S):
        by_page.setdefault(int(m.group(1)), []).append(norm(m.group(2)))
    pages = {e["id"]: e["page"] for e in ents}
    objs = {}
    for line in open(os.path.join(FD, "namesake_objects.md"), encoding="utf-8"):
        if line.startswith("| ") and not line.startswith("| id") and not line.startswith("|---"):
            c = [x.strip() for x in line.strip().strip("|").split(" | ")]
            objs[c[0]] = c[1]
    packs = []
    for fp in sorted(glob.glob(os.path.join(FD, "namesake_batch_*_result.json"))):
        want = re.findall(r"^## (E\d{4}) \|", open(fp.replace("_result.json", ".md"), encoding="utf-8").read(), re.M)
        packs.append((fp, want, False))
    for fp in sorted(glob.glob(os.path.join(FD, "namesake2_batch_*_result.json"))):        # the second pass: the streets with the candidate bios (ids S001...), the quote page is required
        packs.append((fp, re.findall(r"^## (S\d{3}) \|", open(fp.replace("_result.json", ".md"), encoding="utf-8").read(), re.M), False))
    fo = os.path.join(FD, "namesake_objects_result.json")
    if os.path.exists(fo):
        packs.append((fo, list(objs), True))
    if not packs:
        sys.exit("no result files yet")
    cand, rej, skip, seen = [], [], [], set()
    for fp, want, is_obj in packs:
        try:
            rows = json.load(open(fp, encoding="utf-8"))
        except Exception as ex:
            print(os.path.basename(fp), "is not valid JSON:", ex)
            continue
        ids = [r.get("id") for r in rows if isinstance(r, dict)]
        print(os.path.basename(fp), "rows", len(rows), "| missing", [i for i in want if i not in ids][:8], "| extra", [i for i in ids if i not in want][:8], "| duplicates", sorted({i for i in ids if ids.count(i) > 1})[:8])
        for r in rows:
            if not isinstance(r, dict) or r.get("id") not in want or r["id"] in seen:
                continue
            seen.add(r["id"])
            if set(r) != KEYS:
                rej.append({"id": r["id"], "reasons": ["keys differ"]})
                continue
            if r["status"] == "skip":
                (skip if r["skip_reason"] in SKIPS else rej).append({"id": r["id"], "reason": r["skip_reason"]} if r["skip_reason"] in SKIPS else {"id": r["id"], "reasons": ["skip_reason"]})
                continue
            bad = []
            if r["status"] != "ok" or r["kind"] not in KINDS:
                bad.append("status/kind")
            if trio(r["name"], bad, "name") and trio(r["desc"], bad, "desc"):
                q = norm(r["quote"] or "")
                if not q or len(q.split()) > 40:
                    bad.append("quote empty or longer than 40 words")
                elif is_obj:
                    if q != norm(objs[r["id"]]) and q not in norm(objs[r["id"]]):
                        bad.append("the quote is not the name of the object")
                else:
                    qp = r["quote_page"] if isinstance(r["quote_page"], int) and r["quote_page"] else pages.get(r["id"], 0)
                    if not any(q in t for p in (qp - 1, qp, qp + 1) for t in by_page.get(p, [])):
                        bad.append("the quote is not a verbatim part of the text of page %s (+-1)" % qp)
                    if r["kind"] in ("person", "place") and not name_in_quote(r["name"]["ka"], q):
                        bad.append("the name is not in the quote")
                    if isinstance(r["years"], list):
                        for k, y in enumerate(r["years"]):
                            if y is not None and not year_in_quote(y, q, k == 1):
                                bad.append("the year %s is not in the quote" % y)
            if r["years"] is not None and not (isinstance(r["years"], list) and len(r["years"]) == 2 and all(y is None or isinstance(y, int) for y in r["years"])):
                bad.append("years shape")
            if not (isinstance(r["wiki"], dict) and set(r["wiki"]) == {"ka", "ru", "en"} and all(isinstance(v, str) for v in r["wiki"].values())):
                bad.append("wiki shape")
            if bad:
                rej.append({"id": r["id"], "reasons": bad})
            else:
                cand.append((r, is_obj))
    # links
    need = {l: sorted({r["wiki"][l] for r, _ in cand if r["kind"] == "person" and r["wiki"][l]}) for l in ("ka", "ru", "en")}
    items = {l: wiki_items(l, need[l]) for l in need} if not NONET else {l: {} for l in need}
    hy = human_years([q for l in items for (q, dis) in items[l].values() if q and not dis])
    ok = []
    for r, is_obj in cand:
        r = dict(r)
        r["wiki_ok"], r["qid"] = {}, None
        if r["kind"] == "person":
            found = {l: items[l].get(r["wiki"][l]) for l in ("ka", "ru", "en") if r["wiki"][l]}
            good = {l: v[0] for l, v in found.items() if v and v[0] and not v[1] and hy.get(v[0], (False,))[0]}
            qs = set(good.values())
            if len(qs) == 1 and len(good) == len(found):
                q = next(iter(qs))
                _, b, d = hy[q]
                yrs = r["years"]
                if not is_obj and yrs and yrs[0] is not None and b == yrs[0] and (yrs[1] is None or d is None or d == yrs[1]):
                    r["wiki_ok"], r["qid"] = {l: r["wiki"][l] for l in good}, q
                elif is_obj and len(good) >= 2:
                    r["wiki_ok"], r["qid"] = {l: r["wiki"][l] for l in good}, q
        ok.append(r)
    json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"ok": ok, "rejected": rej, "skip": skip}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    linked = sum(1 for r in ok if r["wiki_ok"])
    print("ok: %d (with a confirmed link: %d) | skip: %d | rejected: %d" % (len(ok), linked, len(skip), len(rej)))
    for x in rej[:60]:
        print("  rejected", x["id"], "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
