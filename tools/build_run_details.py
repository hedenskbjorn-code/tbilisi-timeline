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


def jload(*p):
    return json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))


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
    mon = jload("site", "data", "monuments.json")["features"]
    photos = jload("site", "data", "photos.json")
    by = {(round(f["geometry"]["coordinates"][0], 6), round(f["geometry"]["coordinates"][1], 6)): f["properties"] for f in mon}
    wanted = [ph["file"] for d in desc.values() for ph in d.get("photos", [])]
    wanted = [w if w.startswith("File:") else "File:" + w for w in wanted]
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
            f = ph["file"] if ph["file"].startswith("File:") else "File:" + ph["file"]
            e = info.get(f)
            if e and len(pl) < MAX_PHOTOS and all(x["page"] != e["page"] for x in pl):
                pl.append(e)
        item = {"desc": d.get("desc"), "facts": d.get("facts"), "wp": d.get("wp"), "sources": d.get("sources"), "photos": pl}
        res[str(n)] = {k: v for k, v in item.items() if v}
    out = {"note": "Built by tools/build_run_details.py on 2026-11-19 from data/run_descriptions.json (descriptions written from Wikipedia articles) and the photos of Wikimedia Commons (free licences).", "sights": res}
    open(os.path.join(ROOT, "site", "data", "run_details.json"), "wb").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print("sights:", len(res), "| with description:", sum(1 for v in res.values() if v.get("desc")), "| with photos:", sum(1 for v in res.values() if v.get("photos")),
          "| photos:", sum(len(v.get("photos", [])) for v in res.values()))


if __name__ == "__main__":
    main()
