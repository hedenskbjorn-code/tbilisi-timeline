"""Takes the answer of Gemini about the parks (for_gemini/from_desktop/parks_result.json, task: parks_TASK_for_gemini.md): the missing languages of the names, former names and other names of the parks of OSM,
and the Georgian text of the strings of the interface. A form is taken only when: the language that the item already had is NOT changed (the row repeats it); ka has Georgian letters and no Cyrillic; en has no Cyrillic;
ru has no Georgian letters; no word პროსპექტი. Output: tools/parks_names.json ({"<id>|<field>": {ka, ru, en}}, read by tools/apply_parks.py) and the "ka" of the strings in tools/folk_mod_ui.json
("ui.<key>" = the part "places", "i18n.<key>" = the part "i18n"; tools/apply_ui_mod_folk.py then puts the i18n ones into site/i18n.js). Usage: python -P tools/apply_parks_result.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GE, CY, LAT = re.compile("[ა-ჰ]"), re.compile("[А-Яа-яЁё]"), re.compile("[A-Za-z]")


def good(d, have):
    for l in ("ka", "ru", "en"):
        if have.get(l) and d.get(l) != have[l]:
            return "changed an existing form " + l
    if d.get("ka") and (not GE.search(d["ka"]) or CY.search(d["ka"]) or "პროსპექტი" in d["ka"]):
        return "bad ka"
    if d.get("en") and (CY.search(d["en"]) or GE.search(d["en"])):
        return "bad en"
    if d.get("ru") and GE.search(d["ru"]):
        return "bad ru"
    return ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.load(open(os.path.join(R, "for_gemini", "from_desktop", "parks_result.json"), encoding="utf-8"))
    items = {c["id"]: c for c in json.load(open(os.path.join(R, "site", "data", "places.json"), encoding="utf-8"))["items"] if c.get("pk")}
    names, bad = {}, []
    for k, v in res.items():
        if "|" not in k:
            continue
        oid, f = k.split("|")
        c = items.get(oid)
        if not c or f not in ("n", "o", "al") or not c.get(f):
            bad.append((k, "not an asked field"))
            continue
        why = good(v, c[f])
        if why:
            bad.append((k, why))
        else:
            names[k] = {l: v.get(l, "") for l in ("ka", "ru", "en")}
    json.dump(names, open(os.path.join(R, "tools", "parks_names.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    up = os.path.join(R, "tools", "folk_mod_ui.json")
    ui = json.load(open(up, encoding="utf-8"))
    taken = 0
    for k, v in res.items():
        m = re.match(r"(ui|i18n)\.(\w+)$", k)
        if not m:
            continue
        part = "places" if m.group(1) == "ui" else "i18n"
        if m.group(2) in ui[part] and not ui[part][m.group(2)]["ka"] and GE.search(v) and not CY.search(v) and "პროსპექტი" not in v:
            ui[part][m.group(2)]["ka"] = v.strip()
            taken += 1
        else:
            bad.append((k, "not taken"))
    json.dump(ui, open(up, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("names taken:", len(names), "| strings taken:", taken, "| rejected:", bad)


if __name__ == "__main__":
    main()
