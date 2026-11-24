"""Puts the names of the nameless places of worship that a search found and tools/verify_search.py checked (data/cache/churches_verified.json, "ok" rows of the tasks churches_B1-B4) into tools/churches_names.json
({id: {ka, ru, en}}), which tools/build_religious_osm.py uses to fill the EMPTY names. A row is taken only when the object is in site/data/religious_osm.json and has no name there (a name that exists is never replaced)
and the name is not in the file yet. Nothing else is written. Then run tools/build_religious_osm.py. Usage: python -P tools/apply_churches_b.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ver = json.load(open(os.path.join(R, "data", "cache", "churches_verified.json"), encoding="utf-8"))["ok"]
    items = {x["id"]: x for x in json.load(open(os.path.join(R, "site", "data", "religious_osm.json"), encoding="utf-8"))["items"]}
    p = os.path.join(R, "tools", "churches_names.json")
    fill = json.load(open(p, encoding="utf-8"))
    taken, skipped = [], []
    for r in ver:
        o = items.get(r["id"])
        if o is None:
            skipped.append((r["id"], "not in religious_osm.json"))
        elif any((o.get("name") or {}).values()):
            skipped.append((r["id"], "has a name already"))
        elif r["id"] in fill:
            skipped.append((r["id"], "already in churches_names.json"))
        else:
            fill[r["id"]] = {k: r["name"][k] for k in ("ka", "ru", "en")}
            taken.append(r["id"])
    json.dump(fill, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("names taken:", taken, "| skipped:", skipped, "| file now:", len(fill))


if __name__ == "__main__":
    main()
