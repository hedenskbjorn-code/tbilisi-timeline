"""Adds the project names of the stations and the list of the stations that were not built to site/data/metro_names.json (the file of the former names; the keys "stations" and "ui" stay, the keys "project" and "planned" are
added or replaced). Input: data/cache/metro_project_verified.json (tools/verify_metro_project.py), tools/metro_project_manual.json (a row that the answer missed; its quote is checked here again), tools/metro_project_ui.json
(the strings of the card in ru/en/ka and the Georgian text of the manual rows; made with Gemini). A station of "held" (tools/metro_project_manual.json) is not published.
"project": {<id of the station>: [{"n": {ka, ru, en}, "k": "project"|"working", "y": int|null, "src": {"u": url|"", "p": page|0, "q": quote}}]}
"planned": [{"n": {ka, ru, en}, "g": "ext1"|"l3", "s": state, "y": int|null, "pl": {ka, ru, en}, "src": {...}}]
Usage: python -P tools/apply_metro_project.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_metro import page_text  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GROUPS = {"Ахметели-Варкетилская": "ext1", "Руставели-Вазисубани": "l3"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    v = json.load(open(os.path.join(R, "data", "cache", "metro_project_verified.json"), encoding="utf-8"))
    man = json.load(open(os.path.join(R, "tools", "metro_project_manual.json"), encoding="utf-8"))
    up = os.path.join(R, "tools", "metro_project_ui.json")
    uij = json.load(open(up, encoding="utf-8")) if os.path.exists(up) else {}
    proj = {}
    for r in v["stations"]["ok"]:
        if r["id"] in man["held"]:
            continue
        proj[r["id"]] = [{"n": {k: f[k] for k in ("ka", "ru", "en")}, "k": f["kind"], "y": f["year"], "src": {"u": f["url"], "p": f["page"], "q": f["quote"]}} for f in r["project"]]
    for sid, rows in man["stations"].items():
        for f in rows:
            ka = (uij.get("manual_ka") or {}).get(f["ka_key"])
            if not ka:
                print("manual row without the Georgian text, skipped:", sid, f["ru"])
                continue
            t = page_text(f["url"])
            if t is None or norm(f["quote"]) not in t:
                print("the quote of the manual row is not on the page, skipped:", sid)
                continue
            proj.setdefault(sid, []).append({"n": {"ka": ka, "ru": f["ru"], "en": f["en"]}, "k": f["kind"], "y": f["year"], "src": {"u": f["url"], "p": f["page"], "q": f["quote"]}})
    planned = []
    for r in v["planned"]["ok"]:
        g = GROUPS.get(r["line"])
        if not g:
            print("unknown group:", r["line"])
            continue
        planned.append({"n": r["name"], "g": g, "s": r["state"], "y": r["year"], "pl": r["place"], "src": {"u": r["url"], "p": r["page"], "q": r["quote"]}})
    path = os.path.join(R, "site", "data", "metro_names.json")
    d = json.load(open(path, encoding="utf-8"))
    d["project"], d["planned"] = proj, planned
    ui0 = json.load(open(os.path.join(R, "tools", "metro_ui.json"), encoding="utf-8")) if os.path.exists(os.path.join(R, "tools", "metro_ui.json")) else {}
    d["ui"] = {**ui0, **(uij.get("ui") or {})}
    open(path, "wb").write(json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print("stations with a project name:", len(proj), "| not built:", len(planned), "| bytes:", os.path.getsize(path))


if __name__ == "__main__":
    main()
