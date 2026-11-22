"""Audit: do the external addresses of the data of the site answer? Reads data/cache/audit_urls.json ({url: [files]}), checks every address of Wikipedia / Wikidata / Commons file pages / archive.org / other sites
with a HEAD request (GET when HEAD is refused) and a sample of the thumbnails (thumb.wikimedia.org, upload.wikimedia.org), one request at a time with a pause (a generic User-Agent; Retry-After is respected).
Output: data/cache/audit_links.json ({url: status}) and a summary on the screen. Read only. Usage: python -P tools/audit_links.py
"""
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "tbilisi-timeline-hobby/1.0 (non-commercial hobby project; link audit)"}
PAUSE = 0.25
SAMPLE_THUMBS = 120


def check(u):
    for method in ("HEAD", "GET"):
        for k in range(3):
            try:
                req = urllib.request.Request(u, headers=UA, method=method)
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.status
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    ra = e.headers.get("Retry-After")
                    time.sleep(int(ra) if ra and ra.isdigit() else 20 * (k + 1))
                    continue
                if method == "HEAD" and e.code in (403, 405, 501):
                    break
                return e.code
            except Exception as e:
                if k == 2:
                    return "ERR " + type(e).__name__
                time.sleep(3)
    return "ERR"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    urls = json.load(open(os.path.join(R, "data", "cache", "audit_urls.json"), encoding="utf-8"))
    own = ("hedenskbjorn-code.github.io", "hedenskbjorn.workers.dev")
    todo = [u for u in urls if not any(h in u for h in own) and not re.search(r"\.(png|jpg|jpeg|webp)$", u, re.I) or "commons.wikimedia.org" in u]
    thumbs = [u for u in urls if re.search(r"(thumb|upload)\.wikimedia\.org", u)]
    random.seed(7)
    todo = [u for u in todo if u not in thumbs] + random.sample(thumbs, min(SAMPLE_THUMBS, len(thumbs)))
    path = os.path.join(R, "data", "cache", "audit_links.json")
    res = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    todo = [u for u in todo if u not in res]
    print("to check:", len(todo), flush=True)
    for i, u in enumerate(todo, 1):
        res[u] = check(u)
        time.sleep(PAUSE)
        if i % 100 == 0:
            json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            print("  checked", i, flush=True)
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    bad = {u: s for u, s in res.items() if not (isinstance(s, int) and 200 <= s < 400)}
    print("checked:", len(res), "| not ok:", len(bad))
    for u, s in list(bad.items())[:60]:
        print("  ", s, u[:140], "|", ",".join(urls.get(u, [])[:2]))


if __name__ == "__main__":
    main()
