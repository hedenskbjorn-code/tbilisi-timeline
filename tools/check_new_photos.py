"""Audit newly added entries in site/data/photos.json against HEAD.

Checks metadata cleanliness (no newlines, no duplicated Unknown author, no utm_* params,
no Logo/Icon/SVG/Panoramio/PNG surprises) and optionally verifies HTTP 200 + image/*
content type with `--online`.

Usage: python -P tools/check_new_photos.py [--ref HEAD] [--online]
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS = {"User-Agent": "TbilisiTimelineAudit/1.0 (https://github.com/tbilisi-timeline)"}


def head_check(url):
    req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.headers.get("Content-Type", "")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    online = "--online" in args
    ref = "HEAD"
    if "--ref" in args:
        ref = args[args.index("--ref") + 1]

    cur = json.loads((ROOT / "site/data/photos.json").read_text(encoding="utf-8"))
    try:
        old = json.loads(subprocess.check_output(["git", "show", f"{ref}:site/data/photos.json"], cwd=ROOT).decode("utf-8"))
    except subprocess.CalledProcessError:
        old = {}

    added = {k: v for k, v in cur.items() if k not in old}
    print(f"New photos vs {ref}: {len(added)}")
    problems = []
    warnings = []
    for k, v in sorted(added.items()):
        auth = str(v.get("author") or "")
        lic = str(v.get("license") or "")
        lic_url = str(v.get("license_url") or "")
        thumb = str(v.get("thumb") or "")
        page = str(v.get("page") or "")
        if "\n" in auth or "\r" in auth or "Unknown authorUnknown author" in auth:
            problems.append(f"{k}: dirty author ({auth!r})")
        if any(re.search(r"[?&]utm_(?:source|medium|campaign|content)=", u, re.I) for u in (thumb, page)):
            problems.append(f"{k}: utm_ tracking param in URL")
        if any(re.search(r"\.svg(?:$|[/?#])", u, re.I) for u in (thumb, page)):
            problems.append(f"{k}: SVG URL is not allowed")
        if re.search(r"(?:^|[^a-z])(logo|icon|panoramio)(?:[^a-z]|$)|\.png$", k, re.I):
            warnings.append(f"{k}: review manually (logo/icon/panoramio/png)")
        if lic.startswith("CC ") and not lic_url:
            problems.append(f"{k}: CC license '{lic}' without license_url")
        if online and thumb:
            try:
                st, ct = head_check(thumb)
                if st != 200 or not ct.startswith("image/") or ct == "image/svg+xml":
                    problems.append(f"{k}: thumb HTTP {st} ({ct})")
            except Exception as e:
                problems.append(f"{k}: thumb fetch error ({e})")

    for w in warnings:
        print("WARN:", w)
    if problems:
        print(f"FAIL: {len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("check_new_photos: OK")


if __name__ == "__main__":
    main()
