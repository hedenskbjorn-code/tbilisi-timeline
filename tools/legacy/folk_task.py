"""The task for Gemini about the FOLK (slang, colloquial) names of the places of Tbilisi: work/gemini/results/folk_objects.md (our objects with their ids, so that a find can be bound to an object: kind | ref | ka | ru | en)
and the task tasks/folk.md. The answer results/folk.json is checked by tools/verify_folk.py. Usage: python -P tools/folk_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(R, "site", "data")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = []

    def add(kind, ref, n):
        rows.append((kind, ref, n.get("ka", ""), n.get("ru", ""), n.get("en", "")))

    for c in json.load(open(os.path.join(D, "places.json"), encoding="utf-8"))["items"]:
        add(c["k"], "pl:" + c["id"], c["n"])
    for c in json.load(open(os.path.join(D, "sculptures.json"), encoding="utf-8"))["items"]:
        if any(c["n"].values()):
            add("monument", "mn:" + c["id"], c["n"])
    for s in json.load(open(os.path.join(D, "street_names.json"), encoding="utf-8"))["streets"]:
        add("street", "st:" + (s.get("geom") or s["now"]["en"]), s["now"])
    for c in json.load(open(os.path.join(D, "religious.json"), encoding="utf-8")):
        add("religious", "rl:" + c["id"], c["name"])
    for c in json.load(open(os.path.join(D, "religious_osm.json"), encoding="utf-8"))["items"]:
        if any(c["name"].values()):
            add("religious", "rl:" + c["id"], c["name"])
    L = ["# Объекты сайта (для привязки находок): вид | ref | ka | ru | en", "", "| вид | ref | ka | ru | en |", "|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s | %s |" % r for r in rows]
    open(os.path.join(R, "work", "gemini", "results/folk_objects.md"), "wb").write(("\n".join(L) + "\n").encode("utf-8"))
    print("objects:", len(rows))


if __name__ == "__main__":
    main()
