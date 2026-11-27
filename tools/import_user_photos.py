"""Imports the photographs that visitors sent and the owner approved (queue of worker/admin.js) into the site.
For every approved item: the picture is taken from the KV of Cloudflare, opened again (it must be a real JPEG), made at most 1600 px on the long side, saved WITHOUT any metadata as
site/img/user/<id>.jpg and written to data/user_photos.json (author, licence CC BY-SA 4.0, object); then tools/build_site_data.py adds it to the object like the photos of Wikimedia
Commons (see the key "User:<id>" in site/data/photos.json). In the queue the item gets the status "imported" and its picture is deleted from KV. Only the register objects ("mon:<id>")
are imported now; others are reported and left.
Environment (never stored in the repository): CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID.
Usage: python -X utf8 -P tools/import_user_photos.py [--dry-run]
"""
import io
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API = "https://api.cloudflare.com/client/v4"
TOK = os.environ["CLOUDFLARE_API_TOKEN"]
AID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
DRY = "--dry-run" in sys.argv
OUT_DIR = os.path.join(ROOT, "site", "img", "user")
DB = os.path.join(ROOT, "data", "user_photos.json")


def req(method, path, data=None, ctype=None, raw=False):
    r = urllib.request.Request(API + path, data=data, method=method, headers={"Authorization": "Bearer " + TOK, "User-Agent": "tbilisi-timeline-import", **({"Content-Type": ctype} if ctype else {})})
    try:
        resp = urllib.request.urlopen(r, timeout=60).read()
    except urllib.error.HTTPError as e:
        sys.exit("API error %s on %s: %s" % (e.code, path, e.read()[:200]))
    return resp if raw else json.loads(resp)


def namespace():
    for n in req("GET", "/accounts/%s/storage/kv/namespaces?per_page=100" % AID)["result"]:
        if n["title"] == "tbilisi-photos":
            return n["id"]
    sys.exit("no KV namespace tbilisi-photos")


def put_with_metadata(ns, key, value, metadata, ttl=None):
    b = uuid.uuid4().hex
    body = ("--%s\r\nContent-Disposition: form-data; name=\"value\"\r\n\r\n%s\r\n--%s\r\nContent-Disposition: form-data; name=\"metadata\"\r\n\r\n%s\r\n--%s--\r\n" % (b, value, b, json.dumps(metadata), b)).encode()
    req("PUT", "/accounts/%s/storage/kv/namespaces/%s/values/%s" % (AID, ns, urllib.parse.quote(key, safe="")) + ("?expiration_ttl=%d" % ttl if ttl else ""), body, "multipart/form-data; boundary=" + b)


def list_meta_keys(ns):
    keys = []
    cursor = None
    while True:
        qs = "prefix=meta:&limit=1000" + ("&cursor=" + urllib.parse.quote(cursor, safe="") if cursor else "")
        res = req("GET", "/accounts/%s/storage/kv/namespaces/%s/keys?%s" % (AID, ns, qs))
        keys.extend(res.get("result") or [])
        cursor = (res.get("result_info") or {}).get("cursor")
        if not cursor:
            break
    return keys


def main():
    ns = namespace()
    keys = list_meta_keys(ns)
    approved = [k for k in keys if (k.get("metadata") or {}).get("s") == "approved"]
    print("in the queue:", len(keys), "| approved:", len(approved))
    db = json.load(open(DB, encoding="utf-8")) if os.path.exists(DB) else {"note": "Photographs sent by visitors through the form of the site and approved by the owner (tools/import_user_photos.py). Licence CC BY-SA 4.0.", "objects": {}}
    os.makedirs(OUT_DIR, exist_ok=True)
    done = 0
    for k in approved:
        mid = k["name"][5:]
        meta = json.loads(req("GET", "/accounts/%s/storage/kv/namespaces/%s/values/%s" % (AID, ns, urllib.parse.quote(k["name"], safe="")), raw=True))
        kind, _, oid = meta["obj"].partition(":")
        if kind != "mon" or not oid.isdigit():
            print("  skipped (only register objects are imported now):", mid, meta["obj"])
            continue
        data = req("GET", "/accounts/%s/storage/kv/namespaces/%s/values/%s" % (AID, ns, urllib.parse.quote("img:" + mid, safe="")), raw=True)
        try:
            im = Image.open(io.BytesIO(data))
            im.load()
            assert im.format in ("JPEG", "PNG", "WEBP")
        except Exception as e:
            print("  not a picture, skipped:", mid, e)
            continue
        im = im.convert("RGB")
        k2 = min(1.0, 1600 / max(im.size))
        if k2 < 1:
            im = im.resize((round(im.size[0] * k2), round(im.size[1] * k2)), Image.LANCZOS)
        path = os.path.join(OUT_DIR, mid + ".jpg")
        if not DRY:
            im.save(path, "JPEG", quality=85, optimize=True)                 # saved without EXIF: no metadata is passed on
        entry = {"id": mid, "file": "img/user/%s.jpg" % mid, "author": meta["name"], "note": meta.get("note", ""), "license": "CC BY-SA 4.0",
                 "license_url": "https://creativecommons.org/licenses/by-sa/4.0/", "w": im.size[0], "h": im.size[1], "sent": meta["ts"]}
        lst = db["objects"].setdefault(oid, [])
        if not any(x["id"] == mid for x in lst):
            lst.append(entry)
        print("  imported:", mid, "->", oid, "|", meta["name"], "|", im.size, "|", "dry run" if DRY else os.path.getsize(path) // 1024, "KB")
        if not DRY:
            meta["status"] = "imported"
            for f in ("lat", "lon", "glat", "glon", "ipH"):
                meta.pop(f, None)                                               # the positions and the hash of the address are not kept after the import
            put_with_metadata(ns, k["name"], json.dumps(meta), {"s": "imported", "o": meta["obj"], "t": meta["ts"], "n": meta["name"][:30]}, ttl=90 * 86400)
            req("DELETE", "/accounts/%s/storage/kv/namespaces/%s/values/%s" % (AID, ns, urllib.parse.quote("img:" + mid, safe="")))
        done += 1
    if not DRY:
        open(DB, "wb").write(json.dumps(db, ensure_ascii=False, indent=1).encode("utf-8"))
    print("imported:", done, "(dry run)" if DRY else "| next: python -X utf8 -P tools/build_site_data.py, check the cards, commit and publish")


if __name__ == "__main__":
    main()
