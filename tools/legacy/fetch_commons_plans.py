"""Download plan scans from Wikimedia Commons into data/raw/plans/ with checksum verification (SHA-1 from Commons).

Usage: python tools/fetch_commons_plans.py 1782_cgvia="Map of Tbilisi 1782 (1).jpg" ...   (output name = Commons file title)
Wikimedia asks automated clients to identify themselves: set WIKIMEDIA_CONTACT in the environment (never commit it).
Downloads are sequential with pauses; a Retry-After from the server is respected. Source data are appended to
data/raw/plans/_sources.json.
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "raw", "plans")
os.makedirs(OUT, exist_ok=True)
contact = os.environ.get("WIKIMEDIA_CONTACT")
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; Wikimedia Commons API client%s)" % ("; contact: " + contact if contact else "")


def get(url, **kw):
    for k in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, **kw), timeout=240)
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After")
            w = max(int(ra) + 10 if ra and ra.isdigit() else 0, 120 * (k + 1))
            print("HTTP", e.code, "wait", w, flush=True)
            time.sleep(w)
    raise SystemExit("giving up on " + url)


def main(pairs):
    data = urllib.parse.urlencode({"action": "query", "titles": "|".join("File:" + t for _, t in pairs),
                                   "prop": "imageinfo", "iiprop": "size|url|sha1", "format": "json"}).encode()
    d = json.load(get("https://commons.wikimedia.org/w/api.php", data=data, headers={"User-Agent": UA}))
    norm = {n["from"]: n["to"] for n in d["query"].get("normalized", [])}
    info = {p["title"]: p["imageinfo"][0] for p in d["query"]["pages"].values() if "imageinfo" in p}
    meta_path = os.path.join(OUT, "_sources.json")
    meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
    for out, title in pairs:
        full = "File:" + title
        ii = info.get(norm.get(full, full)) or info.get(full)
        if not ii:
            print("not found on Commons:", title)
            continue
        ext = os.path.splitext(ii["url"].split("?")[0])[1].lower() or ".jpg"
        dest = os.path.join(OUT, out + ext)
        url = ii["url"].split("?")[0]
        if not (os.path.exists(dest) and os.path.getsize(dest) == ii["size"]):
            with get(url, headers={"User-Agent": UA}) as r, open(dest + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(dest + ".part", dest)
        ok = hashlib.sha1(open(dest, "rb").read()).hexdigest() == ii["sha1"]
        print(os.path.basename(dest), os.path.getsize(dest), "sha1 ok" if ok else "SHA MISMATCH", flush=True)
        meta[os.path.basename(dest)] = {"commons_title": full, "url": url, "size": ii["size"], "sha1": ii["sha1"]}
        json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(20)


if __name__ == "__main__":
    pairs = [a.split("=", 1) for a in sys.argv[1:]]
    main(pairs)
