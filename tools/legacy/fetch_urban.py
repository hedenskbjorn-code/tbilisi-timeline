"""Download selected years of the GUSV global urban boundary dataset (Zenodo record 14523232, CC BY 4.0).

Mapping of 30 m global urban boundaries from 1972 to 2021 based on multi-source geographic information fusion.
Files are global shapefile archives (160-400 MB each); they are verified against the MD5 checksums published by Zenodo.
Resumable: a partial download (.part) is continued, a finished and verified file is skipped.
Usage:  python tools/fetch_urban.py [year ...]      (default: 1972 1978 1985 1990 2000 2010 2021)
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "raw", "urban")
os.makedirs(OUT, exist_ok=True)
RECORD = "14523232"
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project)"
YEARS = [int(a) for a in sys.argv[1:]] or [1972, 1978, 1985, 1990, 2000, 2010, 2021]


def get_json(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60))


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def download(url, dest):
    part = dest + ".part"
    for attempt in range(6):
        try:
            have = os.path.getsize(part) if os.path.exists(part) else 0
            req = urllib.request.Request(url, headers={"User-Agent": UA, **({"Range": "bytes=%d-" % have} if have else {})})
            with urllib.request.urlopen(req, timeout=120) as r, open(part, "ab" if have and r.status == 206 else "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(part, dest)
            return
        except Exception as e:
            wait = 30 * (attempt + 1)
            print("  retry in %ds (%s)" % (wait, e), flush=True)
            time.sleep(wait)
    raise SystemExit("giving up on " + url)


files = {f["key"]: f for f in get_json("https://zenodo.org/api/records/%s" % RECORD)["files"]}
meta = {}
for y in YEARS:
    name = "GUSV%d.zip" % y
    f = files[name]
    dest = os.path.join(OUT, name)
    want = f["checksum"].split(":", 1)[1]
    if os.path.exists(dest) and md5(dest) == want:
        print(name, "already verified", flush=True)
    else:
        print(name, round(f["size"] / 1e6), "MB ...", flush=True)
        download(f["links"]["self"], dest)
        got = md5(dest)
        print(name, "md5 ok" if got == want else "MD5 MISMATCH (%s != %s)" % (got, want), flush=True)
    meta[name] = {"size": f["size"], "md5": want, "url": f["links"]["self"]}
    time.sleep(5)
json.dump({"record": "https://doi.org/10.5281/zenodo.14523232", "license": "CC BY 4.0", "files": meta},
          open(os.path.join(OUT, "_sources.json"), "w", encoding="utf-8"), indent=1)
print("done")
