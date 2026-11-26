"""The task for Gemini about the project names of the stations of the Tbilisi metro (the names under which a station was planned or built before it got its name) and about the stations that were planned
and not built (or are planned now): work/gemini/batches/metro_project/metro_project_batch_01.md (the 23 stations of the site as in batches/metro/metro_batch_01.md, the former names that are already found). The answer
(results/metro_project.json for the stations, results/metro_planned.json for the stations that are not built) is checked by tools/verify_metro_project.py.
Usage: python -P tools/metro_project_task.py
"""
import json
import os

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
d = json.load(open(os.path.join(R, "site", "data", "transport.json"), encoding="utf-8"))
st = [f["properties"] for f in d["features"] if f["properties"]["kind"] == "metro_station"]
mn = json.load(open(os.path.join(R, "site", "data", "metro_names.json"), encoding="utf-8"))["stations"]
L = ["# Станции Тбилисского метро: названия на стадии проекта", "", "## Станции сайта (23): id, линия, названия, год открытия, прежние названия, которые уже найдены (их повторять не нужно)", "",
     "| id | линия | ka | ru | en | открыта | уже найденные прежние названия |", "|---|---|---|---|---|---|---|"]
for p in st:
    former = "; ".join("%s (%s)" % (f["n"]["ka"], f["to"][-1] if f["to"] else "год не назван") for f in mn.get(p["id"], []))
    L.append("| %s | %s | %s | %s | %s | %s | %s |" % (p["id"], p["line"], p["name_ka"], p["name_ru"], p["name_en"], p["y0"], former))
open(os.path.join(R, "work", "gemini", "batches/metro_project/metro_project_batch_01.md"), "wb").write(("\n".join(L) + "\n").encode("utf-8"))
print("stations:", len(st))
