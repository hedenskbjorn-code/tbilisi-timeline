"""The cards of the streets of the encyclopedia (2008) that have no name history (idempotent; --dry-run only checks). Input: data/cache/cards_verified.json (tools/verify_cards.py: the names in ka / ru / en).
The entry of a street in site/data/street_names.json: now, geom (the key when the English name is taken), iv [] (no former names), book (the reference with the PDF page), nogeom (no line on the map: the card and
the search only). The namesake of the street comes with tools/apply_namesakes.py (run it after this one). Usage: python -P tools/apply_cards.py [--dry-run]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import name_forms, norm_name  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NAMES = os.path.join(R, "site", "data", "street_names.json")
DRY = "--dry-run" in sys.argv
CR, LF = chr(13), chr(10)
CYR = re.compile("[Ѐ-ӿ]")
BOOK = "Tbilisi. Streets, avenues, squares (თბილისი. ქუჩები, გამზირები, მოედნები), 2008, PDF p. %s"

v = json.load(open(os.path.join(R, "data", "cache", "cards_verified.json"), encoding="utf-8"))
d = json.load(open(NAMES, encoding="utf-8"))
by_ka = {}
for s in d["streets"]:
    for f in name_forms(s["now"]["ka"]):
        by_ka.setdefault(norm_name(f), s)
used = {s.get("geom") or s["now"]["en"] for s in d["streets"]}
added = skipped = 0
for r in v["ok"]:
    if any(norm_name(f) in by_ka for f in name_forms(r["ka_now"])):
        skipped += 1
        continue
    assert not CYR.search(r["ka_now"] + r["en_now"]), r["id"]
    st = {"now": {"ru": r["ru_now"], "en": r["en_now"], "ka": r["ka_now"]}, "iv": [], "book": BOOK % r["page"], "nogeom": True}
    key = r["en_now"] if r["en_now"] not in used else "%s [%s]" % (r["en_now"], r["id"])
    if key != r["en_now"]:
        st["geom"] = key
    used.add(key)
    d["streets"].append(st)
    for f in name_forms(r["ka_now"]):
        by_ka.setdefault(norm_name(f), st)
    added += 1
data = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
with open(NAMES, "rb") as f:
    if (CR + LF).encode() in f.read():
        data = data.replace(LF, CR + LF)
if not DRY:
    with open(NAMES, "wb") as f:
        f.write(data.encode("utf-8"))
print("cards added: %d (already on the site: %d); %s" % (added, skipped, "dry run, nothing written" if DRY else "written"))
