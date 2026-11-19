"""Build site/data/run_details.json for the page of the route (site/run/): for every sight of data/run_trc2026.json the description (ru, en, ka), the facts, the Wikipedia titles,
the sources and up to two photos.
Input: data/run_descriptions.json (the descriptions written from the Wikipedia articles by research agents on 2026-11-19, and the Commons files they suggested); the photos that the
register data of the site already holds (site/data/monuments.json -> photos.json, checked by hand earlier) come first, the suggested files are checked against the Commons API
(free licence only: CC BY, CC BY-SA, CC0, public domain) and fill up to two photos per sight.
Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT (never stored here).
Usage: python -X utf8 -P tools/build_run_details.py
"""
import html
import json
import os
import re
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_contact = os.environ.get("WIKIMEDIA_CONTACT")
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; Wikimedia Commons API client%s)" % ("; contact: " + _contact if _contact else "")
OK_LICENSE = re.compile(r"^(CC[ -]BY([ -]SA)?([ -]\d(\.\d)?)?|CC0.*|CC[ -]BY-SA.*|Public domain.*|PD.*)$", re.I)
MAX_PHOTOS = 2
# (sight, language) pairs where the search found an article about ANOTHER object (checked by hand on 2026-11-19, names of the articles in tools/fetch_run_wikipedia.py output):
# their text and their lead image are not used
EXCLUDE = {
    (10, "en"): "the article of the Sioni Cathedral, not of the monument to Vakhtang Gorgasali",
    (11, "ru"): "the church of the Forty Martyrs (sight 17), not St Abo",
    (12, "en"): "the article of the Metekhi church, not of the bridge",
    (13, "en"): "the article of the fortress Narikala, not of the church of St Nicholas",
    (21, "en"): "the Norashen church (sight 23), not Jvaris Mama",
    (29, "ru"): "the article of Shavteli Street, not of the clock tower",
    (30, "en"): "the article of a hotel, not of the marionette theatre",
    (32, "ru"): "the article of Shavteli Street, not of the city wall",
    (33, "ru"): "the article of Pushkin Street, not of the fragments of the wall",
    (33, "ka"): "the article of Pushkin Street, not of the fragments of the wall",
}


def jload(*p):
    return json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))


def tidy(t):
    """the API cuts an introduction at an abbreviation ("(ок."): a dangling bracket at the end is cut off"""
    t = (t or "").strip()
    if t.count("(") > t.count(")"):
        t = t[:t.rfind("(")].rstrip(" ,;-—")
        if t and t[-1] not in ".!?":
            t += "."
    return t


def commons(titles):
    """imageinfo of Commons files: {title: {thumb, page, author, license, license_url, w, h}} for the files with a free licence"""
    out = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "titles": "|".join(chunk), "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 500})
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read())
        for pg in d["query"]["pages"].values():
            ii = (pg.get("imageinfo") or [None])[0]
            if not ii or not ii.get("mime", "").startswith("image/"):
                continue
            md = ii.get("extmetadata", {})
            lic = (md.get("LicenseShortName") or {}).get("value", "")
            if not OK_LICENSE.match(lic.strip()):
                print("  not a free licence, skipped:", pg["title"], lic)
                continue
            author = html.unescape(re.sub(r"<[^>]+>", "", (md.get("Artist") or {}).get("value", ""))).strip() or "Wikimedia Commons"
            out[pg["title"]] = {"thumb": ii.get("thumburl") or ii["url"], "page": ii["descriptionurl"], "author": author[:80], "license": lic.strip(),
                                "license_url": (md.get("LicenseUrl") or {}).get("value", ""), "w": ii.get("thumbwidth"), "h": ii.get("thumbheight")}
    return out


def main():
    run = jload("site", "data", "run_trc2026.json")
    desc = {d["n"]: d for d in jload("data", "run_descriptions.json")}
    for (n, lg), why in EXCLUDE.items():
        d = desc.get(n)
        if d:
            for k in ("desc", "wp", "src_by_lang"):
                d.get(k, {}).pop(lg, None)
            d["photos"] = [ph for ph in d.get("photos", []) if ("the %s article" % lg) not in ph.get("why", "")]
            d["sources"] = [u for u in d.get("sources", []) if not u.startswith("https://%s.wikipedia.org/" % lg)]
    mon = jload("site", "data", "monuments.json")["features"]
    photos = jload("site", "data", "photos.json")
    by = {(round(f["geometry"]["coordinates"][0], 6), round(f["geometry"]["coordinates"][1], 6)): f["properties"] for f in mon}
    wanted = [ph["file"] for d in desc.values() for ph in d.get("photos", [])]
    for d in desc.values():                                                # clean the texts and add the translations (data/run_translations.json) where an article has no text in a language
        d["desc"] = {lg: tidy(tx) for lg, tx in d.get("desc", {}).items()}
    tr = jload("data", "run_translations.json")["translations"]
    for n, langs in tr.items():
        d = desc.get(int(n))
        if d is None:
            continue
        for lg, e in langs.items():
            if lg not in d["desc"]:
                d["desc"][lg] = e["text"]
                d.setdefault("tr", {})[lg] = e["from"]
    wanted = [(w if w.startswith("File:") else "File:" + w).replace("_", " ") for w in wanted]
    info = commons(sorted(set(wanted))) if wanted else {}
    res = {}
    for s in run["sights"]:
        n = s["n"]
        d = desc.get(n, {})
        pl = []
        p = by.get((s["lon"], s["lat"])) or {}
        for key in [x for x in (p.get("ph") or "").split("|") if x]:
            e = photos.get(key) or photos.get("File:" + key)
            if e and len(pl) < MAX_PHOTOS:
                pl.append({k: e.get(k) for k in ("thumb", "page", "author", "license", "license_url", "w", "h")})
        for ph in d.get("photos", []):
            f = (ph["file"] if ph["file"].startswith("File:") else "File:" + ph["file"]).replace("_", " ")          # the API of Commons returns the titles with spaces
            e = info.get(f)
            if e and len(pl) < MAX_PHOTOS and all(x["page"] != e["page"] for x in pl):
                pl.append(e)
        facts = d.get("facts") or ({"address": p.get("address")} if p.get("address") and not d.get("desc") else None)       # no article: at least the address of the register
        item = {"desc": d.get("desc"), "facts": facts, "wp": d.get("wp"), "sources": d.get("sources"), "src_by_lang": d.get("src_by_lang"), "tr": d.get("tr"), "photos": pl}
        res[str(n)] = {k: v for k, v in item.items() if v}
    out = {"note": "Built by tools/build_run_details.py on 2026-11-19 from data/run_descriptions.json (descriptions written from Wikipedia articles) and the photos of Wikimedia Commons (free licences).", "sights": res}
    open(os.path.join(ROOT, "site", "data", "run_details.json"), "wb").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print("sights:", len(res), "| with description:", sum(1 for v in res.values() if v.get("desc")), "| with photos:", sum(1 for v in res.values() if v.get("photos")),
          "| photos:", sum(len(v.get("photos", [])) for v in res.values()))


if __name__ == "__main__":
    main()
