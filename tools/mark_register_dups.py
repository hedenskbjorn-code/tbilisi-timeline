"""Mark the objects of the register (site/data/monuments.json) that the thematic layers already show: the property "dup": 1 (the map does not draw them; the register keeps
its reg number, dates and status). Idempotent: the flag is recomputed each time (it is first removed from all objects).
Rules (the same function of the object): fn "religious" against religious.json; fn "culture" against science.json and education.json; an education object that was made from the register
(its "rid" is the id of the register object) always marks that object. A pair counts when the distance is up to 25 m AND the Georgian names are alike (the ratio of difflib >= 0.6 after the
removal of everything but letters and digits). A pair up to 25 m with different names is NOT marked: it goes to the list for a manual check (notes/register_dup_candidates.md); the decisions of
the owner are in tools/register_dup_decisions.json ({"dup": [register ids], "keep": [register ids]}).
Usage: python -P tools/mark_register_dups.py [--write]
"""
import difflib
import json
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "site", "data")
MON = os.path.join(D, "monuments.json")
LIST = os.path.join(ROOT, "notes", "register_dup_candidates.md")
DEC = os.path.join(ROOT, "tools", "register_dup_decisions.json")
WRITE = "--write" in sys.argv
CR, LF = chr(13), chr(10)


def load(n):
    with open(os.path.join(D, n + ".json"), encoding="utf-8") as f:
        d = json.load(f)
    return d if isinstance(d, list) else d.get("items") or d.get("objects") or d


def norm(s):
    return re.sub(r"[^ა-ჰa-z0-9]", "", (s or "").lower())


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 83000, (a[1] - b[1]) * 111000)


def name_ka(x):
    n = x["name"]
    return (n.get("ka") or n.get("en") or n.get("ru") or "") if isinstance(n, dict) else n


def main():
    with open(MON, "rb") as f:
        raw = f.read()
    crlf = (CR + LF).encode() in raw
    mon = json.loads(raw.decode("utf-8"))
    feats = mon["features"]
    for f in feats:
        f["properties"].pop("dup", None)
    rel, sci, edu = load("religious"), load("science"), load("education")
    dec = json.load(open(DEC, encoding="utf-8")) if os.path.exists(DEC) else {"dup": [], "keep": []}
    by_id = {f["properties"]["id"]: f for f in feats}
    marked, cands = {}, []
    for x in edu:                                           # made from the register: the same object
        rid = x.get("rid")
        if isinstance(rid, int) and rid in by_id:
            marked[rid] = "education layer (rid)"
    plan = {"religious": rel, "culture": sci + edu}
    for f in feats:
        p = f["properties"]
        layer = plan.get(p["fn"])
        if not layer or p["id"] in marked:
            continue
        best = None
        for t in layer:
            d = dist(f["geometry"]["coordinates"], (t["lon"], t["lat"]))
            if d <= 25 and (best is None or d < best[0]):
                best = (d, t)
        if not best:
            continue
        sim = difflib.SequenceMatcher(None, norm(p["name"]), norm(name_ka(best[1]))).ratio()
        if sim >= 0.6:
            marked[p["id"]] = "%s (%.2f, %d m)" % (best[1].get("id"), sim, best[0])
        else:
            cands.append((p, best[1], best[0], sim))
    for i in dec["dup"]:
        marked[i] = "decision of the owner"
    keep = set(dec["keep"])
    todo = [c for c in cands if c[0]["id"] not in marked and c[0]["id"] not in keep]
    print("marked dup: %d | pairs with different names: %d (decided: %d, to check: %d)" % (len(marked), len(cands), len(cands) - len(todo), len(todo)))
    for f in feats:
        if f["properties"]["id"] in marked:
            f["properties"]["dup"] = 1
    lines = ["# Объекты реестра рядом с объектом слоя, названия разные (до 25 м): проверка вручную", "",
             "Для каждой строки: тот же объект (→ `dup`, на карте не рисуется) или соседний другой объект (→ `keep`, остаётся). Ответ: список id реестра в `tools/register_dup_decisions.json`.", "",
             "| id реестра | название в реестре | слой | объект слоя | м |", "|---|---|---|---|---|"]
    for p, t, d, s in sorted(todo, key=lambda c: c[2]):
        lines.append("| %s | %s | %s | %s | %d |" % (p["id"], p["name"].replace("|", "/"), p["fn"], name_ka(t).replace("|", "/"), d))
    if WRITE:
        out = json.dumps(mon, ensure_ascii=False, separators=(",", ":"))
        if crlf:
            out = out.replace(LF, CR + LF)
        b = out.encode("utf-8")
        with open(MON, "wb") as f:
            f.write(b)
        with open(LIST, "wb") as f:
            f.write((LF.join(lines) + LF).encode("utf-8"))
        print("written:", MON, "and", LIST)


if __name__ == "__main__":
    main()
