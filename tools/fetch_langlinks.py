"""For every Wikipedia page cited by data/lost_buildings_gemini.json, fetch the ru / ka / en versions of the article
(Wikipedia API, prop=langlinks) so that the page can open the article in the interface language.

Output: data/lost_langlinks.json  {"<lang>:<title as cited>": {"ru": title, "ka": title, "en": title}}
Needs the environment variable WIKIMEDIA_CONTACT (never committed). Sequential, with pauses; Retry-After is respected.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % ("; contact: " + os.environ["WIKIMEDIA_CONTACT"] if os.environ.get("WIKIMEDIA_CONTACT") else "")
LANGS = ("ru", "ka", "en")


def call(lang, titles, extra=None):
    data = {"action": "query", "format": "json", "titles": "|".join(titles), "prop": "langlinks", "lllimit": "max", "redirects": "1"}
    url = "https://%s.wikipedia.org/w/api.php" % lang
    for k in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers={"User-Agent": UA}), timeout=120))
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After")
            w = min(int(ra) + 10 if ra and ra.isdigit() else 60 * (k + 1), 200)
            print("HTTP", e.code, "wait", w, flush=True)
            time.sleep(w)
    sys.exit("gave up")


def main():
    src = json.load(open(os.path.join(ROOT, "data", "lost_buildings_gemini.json"), encoding="utf-8"))
    cited = {}
    for x in src:
        for u in x.get("sources") or []:
            m = re.match(r"https://(ru|ka|en)\.wikipedia\.org/wiki/(.+)$", u)
            if m:
                cited.setdefault(m.group(1), set()).add(urllib.parse.unquote(m.group(2)).replace("_", " "))
    out = {}
    for lang, titles in cited.items():
        titles = sorted(titles)
        for i in range(0, len(titles), 40):
            chunk = titles[i:i + 40]
            r = call(lang, chunk)["query"]
            alias = {}
            for key in ("normalized", "redirects"):
                for n in r.get(key, []):
                    alias[n["from"]] = n["to"]
            by_title = {p["title"]: p for p in r["pages"].values()}
            for t in chunk:
                tt = t
                for _ in range(3):
                    tt = alias.get(tt, tt)
                p = by_title.get(tt)
                if not p or "missing" in p:
                    print("missing:", lang, t)
                    out[lang + ":" + t] = {"missing": True}
                    continue
                v = {lang: p["title"]}
                for ll in p.get("langlinks", []):
                    if ll["lang"] in LANGS:
                        v[ll["lang"]] = ll["*"]
                out[lang + ":" + t] = v
            time.sleep(5)
    json.dump(out, open(os.path.join(ROOT, "data", "lost_langlinks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("pages:", len(out), "with ka:", sum(1 for v in out.values() if "ka" in v), "with en:", sum(1 for v in out.values() if "en" in v), "with ru:", sum(1 for v in out.values() if "ru" in v), "missing:", sum(1 for v in out.values() if v.get("missing")))


if __name__ == "__main__":
    main()
