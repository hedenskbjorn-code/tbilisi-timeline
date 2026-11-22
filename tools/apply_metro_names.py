"""The former names of the stations of the Tbilisi metro for the card of a station: site/data/metro_names.json (loaded when the card of a station is opened; not part of the first screen).
Input: data/cache/metro_verified.json (made by tools/verify_metro.py: the quote of the encyclopedia of 2008 stands on its page, the quote of a web page stands on the page).
{"stations": {<id of the feature>: [{"n": {ka, ru, en}, "from": int|null, "to": [years of the change, one per source]|[], "src": [{"t": "enc"|"web", "p": page, "u": url, "q": quote}]}]},
 "ui": {...}} (the strings of the card are in this file too). The same former name in several rows (the sources disagree on the year) becomes one entry with several years of change.
Usage: python -P tools/apply_metro_names.py
"""
import json
import os

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
v = json.load(open(os.path.join(R, "data", "cache", "metro_verified.json"), encoding="utf-8"))
st = {}
for r in v["ok"]:
    out = []
    for f in r["former"]:
        e = next((x for x in out if x["n"]["ka"] == f["ka"]), None)
        if e is None:
            e = {"n": {"ka": f["ka"], "ru": f["ru"], "en": f["en"]}, "from": f["from"], "to": [], "src": []}
            out.append(e)
        if f["from"] is not None and e["from"] is None:
            e["from"] = f["from"]
        if f["to"] is not None and f["to"] not in e["to"]:
            e["to"].append(f["to"])
        e["src"].append({"t": f["source"], "p": f["page"], "u": f["url"], "q": f["quote"]})
    for e in out:
        e["to"].sort()
    st[r["id"]] = out
ui = json.load(open(os.path.join(R, "tools", "metro_ui.json"), encoding="utf-8")) if os.path.exists(os.path.join(R, "tools", "metro_ui.json")) else {}
p = os.path.join(R, "site", "data", "metro_names.json")
open(p, "wb").write(json.dumps({"stations": st, "ui": ui}, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
print("stations with former names:", len(st), "| names:", sum(len(x) for x in st.values()), "| bytes:", os.path.getsize(p))
