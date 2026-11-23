"""A Wikimedia Commons photograph for each verified building of Soviet modernism (data/cache/modernism_verified.json).
Order: 1. the image (P18) of the Wikidata item named in the answer; 2. a file of the Commons category of that item (P373) whose title shares a meaningful word with a name of the building;
3. the first result of a Commons file search by the English name whose title shares such a word. A file is never taken without a shared word (the first file of a category may show something else).
Output: data/cache/modernism_photos.json ({index: {"title": "File:...", "how": ...}}) and, through tools/fetch_monument_photos.py's description of files, data/cache/modernism_photo_info.json
({"File:Name.jpg": {thumb, page, author, license, license_url, w, h}}). Read-only public Commons / Wikidata calls with the generic User-Agent. Usage: python -P tools/fetch_modernism_photos.py
"""
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_photos import call, strip, geosearch  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STOP = {"tbilisi", "tbilissi", "georgia", "georgian", "building", "former", "palace", "center", "centre", "complex", "station", "hotel", "soviet", "ministry", "national", "library", "museum", "scientific", "technical", "science", "academy", "concert", "exhibition", "sports", "complex"}
# other search words for the buildings whose English name finds nothing (key: the beginning of the English name), and the files fixed by hand where P18 shows something else
TERMS = {"Palace of Rituals": ["Palace of Rituals Tbilisi", "Wedding Palace Tbilisi"], "Nutsubidze Skybridge": ["Nutsubidze Skybridge", "Tbilisi Skybridge Nutsubidze plateau"], "Tbilisi Chess Palace": ["Chess Palace Tbilisi", "Chess Palace Vere Park"],
         "Laguna Vere": ["Laguna Vere Tbilisi"], "Ortachala Central Bus": ["Ortachala bus station Tbilisi"], "Expo Georgia": ["Expo Georgia Tbilisi", "Expo Georgia Exhibition Center"]}
NO_PHOTO = ("Isani Metro Station",)                 # the only file of Commons found shows the underground platform, not the surface pavilion of the layer
BAD = ("State Museum of History of Georgia (Tbilisi Archaeological Museum) 8.jpg",)   # a file of the Georgian National Museum (jewellery), not the building
PINNED = {"Chronicle of Georgia": "File:Georgiaren Kronikak (Tbilisi) - The Chronicle of Georgia - Tagzania - 1775459623095.jpg"}
IMG = re.compile(r"\.(jpe?g|png|webp)$", re.I)


def words(s):
    return {w.lower() for w in re.findall(r"[^\W\d_]{4,}", s)} - STOP


def wd(q):
    import urllib.request
    u = "https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims&ids=%s&format=json" % q
    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; read-only API client)"}), timeout=60))
    cl = d["entities"][q]["claims"]
    one = lambda p: (cl.get(p) or [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value")      # noqa: E731
    return one("P18"), one("P373")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = json.load(open(os.path.join(R, "data", "cache", "modernism_verified.json"), encoding="utf-8"))["ok"]
    out = {}
    for i, b in enumerate(rows):
        n = b["name"]
        kw = words(n["en"]) | words(" ".join(b.get("aliases", [])))
        pick = None
        cat = None
        if n["en"].startswith(NO_PHOTO):
            out[str(i)] = None
            print(i, n["en"][:50], "-> no photo (rule)", flush=True)
            continue
        for k0, v0 in PINNED.items():
            if n["en"].startswith(k0):
                pick = {"title": v0, "how": "chosen by hand after looking at it: the monument seen from its foot"}
        if b.get("wikidata") and not pick:
            p18, cat = wd(b["wikidata"])
            if p18:
                pick = {"title": "File:" + p18, "how": "wikidata P18"}
        if not pick and cat:
            r = call({"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat, "cmtype": "file", "cmlimit": 50, "format": "json"})
            files = [m["title"] for m in r.get("query", {}).get("categorymembers", []) if IMG.search(m["title"])]
            f = next((f for f in files if kw & words(f[5:]) and "cropped" not in f), None)
            if f:
                pick = {"title": f, "how": "category " + cat}
        terms = next((v0 for k0, v0 in TERMS.items() if n["en"].startswith(k0)), [n["en"]])
        for term in terms:
            if pick:
                break
            tkw = kw | words(term)
            r = call({"action": "query", "list": "search", "srsearch": term, "srnamespace": 6, "srlimit": 15, "format": "json"})
            files = [m["title"] for m in r.get("query", {}).get("search", []) if IMG.search(m["title"])]
            f = next((f for f in files if tkw & words(f[5:]) and "cropped" not in f), None)
            if f:
                pick = {"title": f, "how": "search: " + term}
            time.sleep(1)
        if pick and pick["title"].endswith(BAD):
            pick = None
        gp = os.path.join(R, "data", "cache", "modernism_geo.json")
        pt = json.load(open(gp, encoding="utf-8")).get(str(i)) if os.path.exists(gp) else None
        if not pick and pt and not n["en"].startswith(NO_PHOTO):                       # a file geotagged within 60 m of the point whose title names the building
            tw = kw | words(" ".join(n.values()))
            for h in sorted(geosearch(pt["lat"], pt["lon"], 60), key=lambda h: h["dist"]):
                if IMG.search(h["title"]) and tw & words(h["title"][5:]):
                    pick = {"title": h["title"], "how": "geotag %d m" % h["dist"]}
                    break
        out[str(i)] = pick
        print(i, n["en"][:50], "->", pick, flush=True)
        time.sleep(1)
    json.dump(out, open(os.path.join(R, "data", "cache", "modernism_photos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    titles = sorted({v["title"] for v in out.values() if v})
    info = {}
    for k in range(0, len(titles), 50):
        r = call({"action": "query", "titles": "|".join(titles[k:k + 50]), "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 400, "format": "json"})
        norm = {x["to"]: x["from"] for x in r.get("query", {}).get("normalized", [])}
        for p in r.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            tt = norm.get(p["title"], p["title"])
            if not ii:
                info[tt] = None
                continue
            md = ii.get("extmetadata", {})
            info[tt] = {"thumb": (ii.get("thumburl") or "").split("?")[0] or None, "page": ii.get("descriptionurl"), "author": strip(md.get("Artist", {}).get("value")) or None,
                        "license": strip(md.get("LicenseShortName", {}).get("value")) or None, "license_url": strip(md.get("LicenseUrl", {}).get("value")) or None, "w": ii.get("thumbwidth"), "h": ii.get("thumbheight")}
    json.dump(info, open(os.path.join(R, "data", "cache", "modernism_photo_info.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("photos:", sum(1 for v in out.values() if v), "of", len(out), "| described:", sum(1 for v in info.values() if v))


if __name__ == "__main__":
    main()
