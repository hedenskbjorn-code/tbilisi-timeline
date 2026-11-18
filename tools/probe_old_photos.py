"""Probe: how many old (pre-1960) photographs of Tbilisi on Wikimedia Commons carry a location and a viewing direction (heading)?
Crawls Category:Historical images of Tbilisi (depth 3), reads the file wikitext ({{Location|lat|lon|heading:..}}, {{Object location}}) and extmetadata.
Output: data/cache/old_photos_probe.json (not committed). Only public read-only Commons API calls; contact only from WIKIMEDIA_CONTACT.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
c = os.environ.get("WIKIMEDIA_CONTACT", "")
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % (("; contact: " + c) if c else "")


def api(**p):
    p["format"] = "json"
    for k in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php", data=urllib.parse.urlencode(p).encode(), headers={"User-Agent": UA}), timeout=60).read())
        except Exception as e:
            time.sleep(5 * (k + 1))
    raise SystemExit("api failed")


def members(cat, typ):
    out, cont = [], {}
    while True:
        j = api(action="query", list="categorymembers", cmtitle=cat, cmtype=typ, cmlimit=500, **cont)
        out += [m["title"] for m in j["query"]["categorymembers"]]
        if "continue" not in j:
            return out
        cont = j["continue"]


def main():
    root = "Category:Historical images of Tbilisi"
    seen, files, frontier = {root}, set(), [root]
    for depth in range(3):
        nxt = []
        for cat in frontier:
            files.update(members(cat, "file"))
            for sub in members(cat, "subcat"):
                if sub not in seen:
                    seen.add(sub)
                    nxt.append(sub)
        frontier = nxt
        print("depth", depth, "categories", len(seen), "files", len(files), flush=True)
    files = sorted(files)
    res = {}
    for i in range(0, len(files), 40):
        chunk = files[i:i + 40]
        j = api(action="query", titles="|".join(chunk), prop="revisions|imageinfo", rvprop="content", rvslots="main", iiprop="extmetadata", iiextmetadatafilter="DateTimeOriginal|LicenseShortName|ObjectName|Artist")
        for pg in j["query"]["pages"].values():
            txt = (pg.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("*", "") or ""
            em = (pg.get("imageinfo") or [{}])[0].get("extmetadata", {})
            loc = re.search(r"\{\{\s*(?:Location|Object location)[^}]*\}\}", txt, re.I)
            res[pg["title"]] = {"location_tpl": loc.group(0)[:160] if loc else None, "heading": bool(loc and re.search(r"heading\s*[:=]\s*[-\d.]+", loc.group(0), re.I)),
                                "date": (em.get("DateTimeOriginal") or {}).get("value", "")[:120], "license": (em.get("LicenseShortName") or {}).get("value"),
                                "name": (em.get("ObjectName") or {}).get("value", "")[:120]}
        time.sleep(0.5)
        print(i, len(res), flush=True)
    os.makedirs(os.path.join(ROOT, "data", "cache"), exist_ok=True)
    json.dump(res, open(os.path.join(ROOT, "data", "cache", "old_photos_probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n_loc = sum(1 for v in res.values() if v["location_tpl"])
    n_head = sum(1 for v in res.values() if v["heading"])
    print("files", len(res), "with location", n_loc, "with heading", n_head)


if __name__ == "__main__":
    main()
