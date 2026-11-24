"""Takes the Georgian text of the steps of the tour from Gemini (work/gemini/results/tour_filters.json, task: tools/tour_ka_task.py) and writes it into site/data/tour.json. A text is taken only when it has Georgian
letters, no Cyrillic, no word პროსპექტი, the same numbers as the Russian text, and the step is one of those that still lack it. Usage: python -P tools/apply_tour_ka.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import RESULTS, SITE_DATA  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.load(open(os.path.join(RESULTS, "tour_filters.json"), encoding="utf-8"))
    p = os.path.join(SITE_DATA, "tour.json")
    tour = json.load(open(p, encoding="utf-8"))
    nums = lambda t: sorted(re.findall(r"\d+", t))      # noqa: E731
    taken, bad = 0, []
    for k, v in res.items():
        i = int(k) - 1
        st = tour["steps"][i] if 0 <= i < len(tour["steps"]) else None
        if not st or (st["title"].get("ka") and st["text"].get("ka")):
            bad.append((k, "not a step that waits"))
            continue
        ok = all(re.search("[ა-ჰ]", v.get(f, "")) and not re.search("[А-Яа-яЁё]", v[f]) and "პროსპექტი" not in v[f] and nums(v[f]) == nums(st[f]["ru"]) for f in ("title", "text") if f in v) and "title" in v and "text" in v
        if ok:
            st["title"]["ka"], st["text"]["ka"] = v["title"].strip(), v["text"].strip()
            taken += 1
        else:
            bad.append((k, "failed the checks"))
    json.dump(tour, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("steps taken:", taken, "| rejected:", bad)


if __name__ == "__main__":
    main()
