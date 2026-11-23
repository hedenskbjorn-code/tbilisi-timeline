"""Takes the Georgian texts from Gemini (for_gemini/from_desktop/ui_mod_folk_result.json, task: ui_mod_folk_TASK_for_gemini.md) and puts them where they wait:
tools/folk_mod_ui.json (the strings of the layers: "places", "modernism", "i18n"), site/i18n.js (the key showMod), site/data/changelog.json (the last three items of the newest version).
A text is taken only when it has Georgian letters, no Cyrillic, no word პროსპექტი, and the same numbers as the Russian text (for the long ones). Then run tools/apply_folk.py, tools/build_modernism.py and tests/check_data.mjs.
Usage: python -P tools/apply_ui_mod_folk.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(R, "for_gemini", "from_desktop", "ui_mod_folk_result.json")


def ok(ka, ru):
    nums = lambda t: sorted(re.findall(r"\d+", t))      # noqa: E731
    return bool(re.search("[ა-ჰ]", ka)) and not re.search("[А-Яа-яЁё]", ka) and "პროსპექტი" not in ka and nums(ka) == nums(ru)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.load(open(RES, encoding="utf-8"))
    up = os.path.join(R, "tools", "folk_mod_ui.json")
    ui = json.load(open(up, encoding="utf-8"))
    taken = bad = 0
    for part, d in ui.items():
        for k, v in d.items():
            ka = res.get(part + "." + k)
            if v.get("ka") or not ka:
                continue
            if ok(ka, v["ru"]):
                v["ka"] = ka.strip()
                taken += 1
            else:
                bad += 1
                print("REJECTED", part + "." + k, ka[:80])
    json.dump(ui, open(up, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ip = os.path.join(R, "site", "i18n.js")
    s = open(ip, encoding="utf-8").read()
    if ui["i18n"]["showMod"]["ka"]:
        s = s.replace('showMod: "", ', 'showMod: "%s", ' % ui["i18n"]["showMod"]["ka"].replace('"', '\\"'))
        open(ip, "w", encoding="utf-8").write(s)
    cp = os.path.join(R, "site", "data", "changelog.json")
    ch = json.load(open(cp, encoding="utf-8"))
    for i, x in enumerate(ch[0]["items"][-3:]):
        ka = res.get("changelog.%d" % i)
        if ka and not x["ka"]:
            if ok(ka, x["ru"]):
                x["ka"] = ka.strip()
                taken += 1
            else:
                bad += 1
                print("REJECTED changelog.%d" % i, ka[:80])
    json.dump(ch, open(cp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("taken:", taken, "| rejected:", bad)


if __name__ == "__main__":
    main()
