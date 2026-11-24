"""Check the answers of Gemini about the project names of the metro stations (work/gemini/results/metro_project.json) and about the stations that are not built (results/metro_planned.json),
rules: tasks/metro_project.md. The quotes are checked as in tools/verify_metro.py (the encyclopedia: verbatim on the page of the PDF; a web page: the page is downloaded and the quote must stand on it;
a page that cannot be read gives "unchecked", not a rejection). Output: data/cache/metro_project_verified.json ({"stations": {"ok", "unchecked", "rejected", "skip"}, "planned": {...}}).
Usage: python -P tools/verify_metro_project.py
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_metro import CYR, HOSTS, page_text, stem  # noqa: E402
from verify_mainroads import norm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI as FD  # noqa: E402
OUT = os.path.join(ROOT, "data", "cache", "metro_project_verified.json")
PKEYS = {"ka", "ru", "en", "year", "kind", "source", "page", "url", "quote"}
QKEYS = {"id", "status", "skip_reason", "name", "line", "state", "place", "year", "source", "page", "url", "quote"}


def pages():
    ents = json.load(open(os.path.join(ROOT, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))
    by = {}
    for e in ents:
        by.setdefault(e["page"], []).append(norm(e.get("text_long") or e["text"]) + " " + norm(e.get("text_long_raw") or ""))
    for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", open(os.path.join(ROOT, "data", "cache", "ocr", "streets_enc2008_kat.txt"), encoding="utf-8", errors="replace").read(), re.S):
        by.setdefault(int(m.group(1)), []).append(norm(m.group(2)))
    return by


def check_source(f, by, w, ka_name=None):
    """-> (reasons, unchecked)"""
    bad, unc = [], []
    q = norm(f["quote"] or "")
    if not q or len(q.split()) > 40:
        bad.append(w + ": quote empty or longer than 40 words")
    if f.get("year") is not None and (not isinstance(f["year"], int) or str(f["year"]) not in q):
        bad.append("%s: the year %s is not in the quote" % (w, f["year"]))
    if f["source"] == "enc":
        pg = f["page"]
        if not isinstance(pg, int) or not any(q in t for p in (pg - 1, pg, pg + 1) for t in by.get(p, [])):
            bad.append("%s: the quote is not a verbatim part of the text of page %s (+-1)" % (w, pg))
        elif ka_name and stem(ka_name) and stem(ka_name) not in q:
            bad.append(w + ": the name is not in the quote")
    elif f["source"] == "web":
        u = urllib.parse.urlparse(f["url"])
        if u.scheme != "https" or u.netloc not in HOSTS:
            bad.append(w + ": the address is not on the allowed sites")
        else:
            t = page_text(f["url"])
            if t is None:
                unc.append(w + ": the page cannot be read")
            elif q not in t:
                bad.append(w + ": the quote is not on the page")
    else:
        bad.append(w + ": source")
    return bad, unc


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    by = pages()
    ids = [x[0] for x in re.findall(r"^\| ([^|]+?) \| (\d) \|", open(os.path.join(FD, "batches/metro_project/metro_project_batch_01.md"), encoding="utf-8").read(), re.M)]
    res = {"stations": {"ok": [], "unchecked": [], "rejected": [], "skip": []}, "planned": {"ok": [], "unchecked": [], "rejected": [], "skip": []}}
    p1 = os.path.join(FD, "results/metro_project.json")
    if os.path.exists(p1):
        rows = json.load(open(p1, encoding="utf-8"))
        got = [r.get("id") for r in rows if isinstance(r, dict)]
        print("stations: rows", len(rows), "| missing", [i for i in ids if i not in got], "| extra", [i for i in got if i not in ids], "| duplicates", sorted({i for i in got if got.count(i) > 1}))
        seen = set()
        for r in rows:
            if not isinstance(r, dict) or r.get("id") not in ids or r["id"] in seen:
                continue
            seen.add(r["id"])
            R_ = res["stations"]
            if set(r) != {"id", "status", "skip_reason", "project"}:
                R_["rejected"].append({"id": r["id"], "reasons": ["keys differ"]})
                continue
            if r["status"] == "skip":
                R_["skip" if r["skip_reason"] in ("no_project_name", "unsure") else "rejected"].append({"id": r["id"], "reason": r["skip_reason"], "reasons": ["skip_reason"]})
                continue
            bad, unc, good = [], [], []
            if r["status"] != "ok" or not isinstance(r["project"], list) or not r["project"]:
                R_["rejected"].append({"id": r["id"], "reasons": ["status ok without a project name"]})
                continue
            for k, f in enumerate(r["project"]):
                w = "project %d" % k
                if not isinstance(f, dict) or set(f) != PKEYS:
                    bad.append(w + " keys")
                    continue
                b0 = []
                if not all(isinstance(f[x], str) and f[x].strip() for x in ("ka", "ru", "en")) or CYR.search(f["ka"] + f["en"]) or f["kind"] not in ("project", "working"):
                    b0.append(w + ": names or kind")
                b, u = check_source(f, by, w, f["ka"])
                if b0 + b:
                    bad += b0 + b
                else:
                    good.append(f)
                unc += u
            if bad:
                R_["rejected"].append({"id": r["id"], "reasons": bad})
            elif unc:
                R_["unchecked"].append({"id": r["id"], "reasons": unc, "project": r["project"]})
            else:
                R_["ok"].append({"id": r["id"], "project": good})
    p2 = os.path.join(FD, "results/metro_planned.json")
    if os.path.exists(p2):
        rows = json.load(open(p2, encoding="utf-8"))
        print("planned: rows", len(rows))
        R_ = res["planned"]
        for r in rows:
            if not isinstance(r, dict) or set(r) != QKEYS:
                R_["rejected"].append({"id": (r or {}).get("id"), "reasons": ["keys differ"]})
                continue
            if r["status"] == "skip":
                R_["skip"].append({"id": r["id"], "reason": r["skip_reason"]})
                continue
            bad = []
            n = r["name"]
            if not (isinstance(n, dict) and set(n) == {"ka", "ru", "en"} and all(isinstance(n[k], str) and n[k].strip() for k in n)) or CYR.search(str(n.get("ka")) + str(n.get("en"))):
                bad.append("name")
            if r["state"] not in ("planned", "cancelled", "under_construction"):
                bad.append("state")
            b, u = check_source(r, by, "planned")
            bad += b
            if bad:
                R_["rejected"].append({"id": r["id"], "reasons": bad})
            elif u:
                R_["unchecked"].append({"id": r["id"], "reasons": u, "row": r})
            else:
                R_["ok"].append(r)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k in ("stations", "planned"):
        print(k, {x: len(v) for x, v in res[k].items()})
        for x in res[k]["rejected"][:40]:
            print("  rejected", x.get("id"), "; ".join(x["reasons"])[:200])


if __name__ == "__main__":
    main()
