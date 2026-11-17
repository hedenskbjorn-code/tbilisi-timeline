"""Find Wikimedia Commons photos taken within RADIUS metres of each Tbilisi register object.

Stage 1 (geosearch, one request per object, resumable): data/cache/photos_geosearch.json  {object id: [[title, dist_m], ...]}
Stage 1b (wider radius, only objects without a photo): same cache file, distances > 30 m mark these matches.
Stage 2 (imageinfo, 50 titles per request):             data/cache/photos_info.json       {title: {thumb, page, author, license, license_url, w, h}}
Then:  python tools/fetch_photos.py        runs both stages; Ctrl+C is safe, re-run continues.

Only public read-only Commons API calls; the User-Agent is a generic client name (no personal data).
The match is by coordinates only: a photo near a point may show a neighbouring building, so the site labels it "photo near this point".
Licences are copied as given by Commons (extmetadata); the site shows author + licence and links to the file page.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(ROOT, "data", "cache")
os.makedirs(CACHE, exist_ok=True)
API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks automated clients to identify themselves with a contact. The contact is read from the environment
# (WIKIMEDIA_CONTACT) so that no personal data is stored in this repository.
_contact = os.environ.get("WIKIMEDIA_CONTACT")
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; Wikimedia Commons API client%s)" % ("; contact: " + _contact if _contact else "")
RADIUS = 30      # metres
PER_OBJECT = 3   # photos kept per object
DELAY = 1.0      # seconds between requests
BAD = re.compile(r"\b(map|plan|scheme|diagram|coat of arms|logo|flag)\b", re.I)


def call(params, tries=8):
    url = API
    data = urllib.parse.urlencode(params).encode()   # POST: long Georgian titles overflow a GET URL (HTTP 414)
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:  # network hiccup / rate limit: back off
            wait = 15 * (k + 1)
            ra = getattr(getattr(e, "headers", None), "get", lambda *_: None)("Retry-After")
            if ra and str(ra).isdigit():
                wait = max(wait, int(ra) + 1)
            print("  retry in %ds (%s)" % (wait, e), flush=True)
            time.sleep(wait)
    raise SystemExit("giving up on " + url)


def load(name, default):
    p = os.path.join(CACHE, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def save(name, obj):
    p = os.path.join(CACHE, name)
    json.dump(obj, open(p + ".tmp", "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(p + ".tmp", p)


def hav(lat1, lng1, lat2, lng2):
    import math
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def geosearch(lat, lng, radius):
    d = call({"action": "query", "list": "geosearch", "gscoord": "%f|%f" % (lat, lng), "gsradius": radius,
              "gsnamespace": 6, "gslimit": 500, "format": "json"})
    time.sleep(DELAY)
    return [g for g in d.get("query", {}).get("geosearch", [])
            if g["title"].lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")) and not BAD.search(g["title"])]


def stage1():
    """One query per ~100 m grid cell that contains objects; files are then assigned to objects locally (<= RADIUS m)."""
    feats = json.load(open(os.path.join(ROOT, "data", "tbilisi_monuments.geojson"), encoding="utf-8"))["features"]
    res = load("photos_geosearch.json", {})
    cells = {}
    for f in feats:
        if str(f["properties"]["id"]) in res:
            continue
        lng, lat = f["geometry"]["coordinates"][:2]
        key = (round(lat / 0.0009), round(lng / 0.0012))      # ~100 m x ~100 m at 41.7 N
        cells.setdefault(key, []).append((f["properties"]["id"], lat, lng))
    print("stage 1: %d cells for %d objects (%d objects cached)" % (len(cells), sum(len(v) for v in cells.values()), len(res)), flush=True)
    for n, (key, objs) in enumerate(sorted(cells.items())):
        clat, clng = key[0] * 0.0009, key[1] * 0.0012
        hits = geosearch(clat, clng, 110)
        full = len(hits) >= 500          # cell saturated: fall back to one query per object
        for oid, lat, lng in objs:
            cand = hits if not full else geosearch(lat, lng, RADIUS)
            near = sorted(((g["title"], round(hav(lat, lng, g["lat"], g["lon"]), 1)) for g in cand), key=lambda x: x[1])
            res[str(oid)] = [[t, d] for t, d in near if d <= RADIUS][:PER_OBJECT]
        if (n + 1) % 25 == 0:
            save("photos_geosearch.json", res)
            print("  cell %d/%d" % (n + 1, len(cells)), flush=True)
    save("photos_geosearch.json", res)
    return res


WIDE = 60        # metres, second pass only for objects that got nothing within RADIUS


def stage1b(res):
    """Second pass: objects with no photo within RADIUS get photos up to WIDE m away (distance is kept in the cache).
    Progress marker: photos_wide_done.json (list of object ids already tried)."""
    feats = json.load(open(os.path.join(ROOT, "data", "tbilisi_monuments.geojson"), encoding="utf-8"))["features"]
    done = set(load("photos_wide_done.json", []))
    cells = {}
    for f in feats:
        oid = str(f["properties"]["id"])
        if res.get(oid) or oid in done:
            continue
        lng, lat = f["geometry"]["coordinates"][:2]
        cells.setdefault((round(lat / 0.0009), round(lng / 0.0012)), []).append((oid, lat, lng))
    print("stage 1b: %d cells for %d objects without photo" % (len(cells), sum(len(v) for v in cells.values())), flush=True)
    for n, (key, objs) in enumerate(sorted(cells.items())):
        hits = geosearch(key[0] * 0.0009, key[1] * 0.0012, 160)
        full = len(hits) >= 500
        for oid, lat, lng in objs:
            cand = hits if not full else geosearch(lat, lng, WIDE)
            near = sorted(((g["title"], round(hav(lat, lng, g["lat"], g["lon"]), 1)) for g in cand), key=lambda x: x[1])
            res[oid] = [[t, d] for t, d in near if d <= WIDE][:PER_OBJECT]
            done.add(oid)
        if (n + 1) % 25 == 0:
            save("photos_geosearch.json", res)
            save("photos_wide_done.json", sorted(done))
            print("  cell %d/%d" % (n + 1, len(cells)), flush=True)
    save("photos_geosearch.json", res)
    save("photos_wide_done.json", sorted(done))
    return res


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def stage2(res):
    info = load("photos_info.json", {})
    titles = sorted({t for hits in res.values() for t, _ in hits} - set(info))
    print("stage 2: %d files to describe (%d cached)" % (len(titles), len(info)), flush=True)
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        d = call({"action": "query", "titles": "|".join(chunk), "prop": "imageinfo", "iiprop": "url|extmetadata|size",
                  "iiurlwidth": 400, "format": "json"})
        norm = {n["to"]: n["from"] for n in d.get("query", {}).get("normalized", [])}
        for p in d.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii:
                continue
            md = ii.get("extmetadata", {})
            title = norm.get(p["title"], p["title"])
            info[title] = {
                "thumb": (ii.get("thumburl") or "").split("?")[0] or None, "page": ii.get("descriptionurl"),
                "author": strip(md.get("Artist", {}).get("value")) or None,
                "license": strip(md.get("LicenseShortName", {}).get("value")) or None,
                "license_url": strip(md.get("LicenseUrl", {}).get("value")) or None,
                "w": ii.get("thumbwidth"), "h": ii.get("thumbheight"),
            }
        print("  described %d/%d" % (min(i + 50, len(titles)), len(titles)), flush=True)
        save("photos_info.json", info)    # incremental: an interrupted run keeps what it has
        time.sleep(DELAY)
    save("photos_info.json", info)
    return info


if __name__ == "__main__":
    r = stage1()
    r = stage1b(r)
    inf = stage2(r)
    with_photo = sum(1 for v in r.values() if v)
    print("objects with at least one photo: %d of %d; files described: %d" % (with_photo, len(r), len(inf)))
