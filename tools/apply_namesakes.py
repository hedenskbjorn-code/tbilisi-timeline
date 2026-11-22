"""The namesakes (in whose honour a street, a square, a school, a museum is named) for the cards: site/data/namesakes.json (loaded when a card is opened; not part of the first screen).
Input: data/cache/namesakes_verified.json (made by tools/verify_namesakes.py: the quote stands on its page of the encyclopedia of 2008, the link to Wikipedia is confirmed through Wikipedia and Wikidata).
Output: {"streets": {<key of the street (geom or now.en)>: item}, "objects": {<"M<id of the register>" | "SCI:<id>" | "EDU:<id>">: item}, "ui": {...}}; item: {"k": kind, "n": {ka, ru, en}, "y": [birth, death]|null,
"d": {ka, ru, en} (the description of the book), "p": the page of the quote in the PDF (0 for an object), "w": {lang: title} only for the confirmed links}.
The street of an entry is found by the Georgian name of the answers of the full passes (data/cache/enc2008_verified*.json), else by the heading of the entry. Usage: python -P tools/apply_namesakes.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import name_forms, norm_name  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(R, "site", "data")
v = json.load(open(os.path.join(R, "data", "cache", "namesakes_verified.json"), encoding="utf-8"))
ents = {e["id"]: e for e in json.load(open(os.path.join(R, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))}
sn = json.load(open(os.path.join(D, "street_names.json"), encoding="utf-8"))["streets"]
by = {}
for s in sn:
    for f in name_forms(s["now"]["ka"]):
        by.setdefault(norm_name(f), s)
enc_ka = {}
for fn in ("enc2008_verified.json", "enc2008_verified4.json"):
    for r in json.load(open(os.path.join(R, "data", "cache", fn), encoding="utf-8"))["ok"]:
        enc_ka[r["id"]] = r["ka_now"]


cv = os.path.join(R, "data", "cache", "cards_verified.json")        # the streets without a name history: the names of tools/verify_cards.py
if os.path.exists(cv):
    for r in json.load(open(cv, encoding="utf-8"))["ok"]:
        enc_ka.setdefault(r["id"], r["ka_now"])


def head(t):
    return re.split(r"[,.;:(]", t.strip(), maxsplit=1)[0][:80]


idx2 = os.path.join(R, "data", "cache", "namesake2_index.json")                      # the second pass: S001 -> the key of the street
index2 = json.load(open(idx2, encoding="utf-8")) if os.path.exists(idx2) else {}
streets, objects, nokey = {}, {}, 0
for r in v["ok"]:
    item = {"k": r["kind"], "n": r["name"], "y": r["years"], "d": r["desc"], "p": r["quote_page"] if isinstance(r["quote_page"], int) else 0}
    if r["wiki_ok"]:
        item["w"] = r["wiki_ok"]
    if r["id"] in index2:
        streets.setdefault(index2[r["id"]]["key"], item)
    elif re.match(r"E\d{4}$", r["id"]):
        ka = enc_ka.get(r["id"]) or head(ents[r["id"]]["text"])
        st = next((by[norm_name(f)] for f in name_forms(ka) if norm_name(f) in by), None)
        if st is None:
            nokey += 1
            continue
        key = st.get("geom") or st["now"]["en"]
        item["p"] = item["p"] or ents[r["id"]]["page"]
        streets.setdefault(key, item)
    else:
        objects[r["id"]] = item
ui = json.load(open(os.path.join(R, "tools", "namesake_ui.json"), encoding="utf-8")) if os.path.exists(os.path.join(R, "tools", "namesake_ui.json")) else {}
p = os.path.join(D, "namesakes.json")
open(p, "wb").write(json.dumps({"streets": streets, "objects": objects, "ui": ui}, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
print("streets with a namesake:", len(streets), "(entries without a card on the site:", nokey, ") | objects:", len(objects), "| with a link:", sum(1 for x in list(streets.values()) + list(objects.values()) if "w" in x), "| bytes:", os.path.getsize(p))
