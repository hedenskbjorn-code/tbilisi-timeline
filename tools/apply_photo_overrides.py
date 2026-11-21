"""Apply hand-chosen photos of objects of the register without a full rebuild of site/data (build_site_data.py rewrites many files).
For the given object ids: take the titles from data/photos_object_override.json, the licence data from the list made from the Commons category
(tools/ reads it from the JSON given as the second argument: {"File:...": {"thumb","page","author","license","license_url","w","h"}}),
add them to data/cache/photos_info.json (the cache read by build_site_data.py), and set "ph" of the objects in site/data/monuments.json and the
entries of site/data/photos.json; a photo that no object uses any more is removed from photos.json.
Usage: python -X utf8 -P tools/apply_photo_overrides.py <object id> [<object id> ...] --info <info.json>
The script is idempotent.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ids = []
info_path = None
a = sys.argv[1:]
while a:
    x = a.pop(0)
    if x == "--info":
        info_path = a.pop(0)
    else:
        ids.append(x)
new_info = json.load(open(info_path, encoding="utf-8"))
override = json.load(open(os.path.join(ROOT, "data", "photos_object_override.json"), encoding="utf-8"))["objects"]

cache_p = os.path.join(ROOT, "data", "cache", "photos_info.json")
cache = json.load(open(cache_p, encoding="utf-8"))
for oid in ids:
    for t in override[oid]:
        if t not in cache:
            cache[t] = new_info[t]
json.dump(cache, open(cache_p, "w", encoding="utf-8"), ensure_ascii=False)

mp = os.path.join(ROOT, "site", "data", "monuments.json")
mon = json.load(open(mp, encoding="utf-8"))
for f in mon["features"]:
    p = f["properties"]
    if str(p["id"]) in ids:
        titles = [t for t in override[str(p["id"])] if cache.get(t, {}).get("thumb") and cache[t].get("license")]
        rest = {k: v for k, v in p.items() if k not in ("ph", "wp")}
        newp = dict(rest)
        newp["ph"] = "|".join(titles)
        if "wp" in p:
            newp["wp"] = p["wp"]
        f["properties"] = newp
json.dump(mon, open(mp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

pp = os.path.join(ROOT, "site", "data", "photos.json")
photos = json.load(open(pp, encoding="utf-8"))
used = {t for f in mon["features"] for t in (f["properties"].get("ph") or "").split("|") if t}
for oid in ids:
    for t in override[oid]:
        if cache.get(t, {}).get("thumb") and cache[t].get("license"):
            photos[t] = cache[t]
photos = {k: v for k, v in photos.items() if k in used or k.startswith("User:")}
json.dump(photos, open(pp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("photos in photos.json:", len(photos), "; objects patched:", len(ids))
