"""Takes the Georgian text of the descriptions of the monuments from Gemini (work/gemini/results/monuments_KA.json, task: tools/ka_descriptions_task.py) and writes it into
data/cache/monuments_verified.json (description.ka). A text is taken only when: it has Georgian letters, no Cyrillic, no word პროსპექტი, and the same numbers as the Russian text. Then run tools/apply_monuments.py.
Usage: python -P tools/apply_monuments_ka.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.load(open(os.path.join(R, "work", "gemini", "results/monuments_KA.json"), encoding="utf-8"))
    p = os.path.join(R, "data", "cache", "monuments_verified.json")
    d = json.load(open(p, encoding="utf-8"))
    nums = lambda t: sorted(re.findall(r"\d+", t))      # noqa: E731
    taken, bad = 0, []
    for r in d["ok"]:
        ka = (res.get(r["id"]) or "").strip()
        if not ka or (r["description"].get("ka") or "").strip():
            continue
        ru = r["description"]["ru"]
        if re.search("[ა-ჰ]", ka) and not re.search("[А-Яа-яЁё]", ka) and "პროსპექტი" not in ka and nums(ka) == nums(ru):
            r["description"]["ka"] = ka
            taken += 1
        else:
            bad.append(r["id"])
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("taken:", taken, "| rejected:", bad)


if __name__ == "__main__":
    main()
