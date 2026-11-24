"""Takes the Georgian text of two items of the entry 1.9.0 from Gemini (work/gemini/results/changelog_190.json, task: tools/changelog_190_task.py) and puts them into site/data/changelog.json:
the item about the panel of the filters is REPLACED by the rewritten one (ru, en from tools/changelog_190_task.py, ka from the answer), the item about streets and places is ADDED after it.
A text is taken only when it has Georgian letters, no Cyrillic, no word პროსპექტი and the same numbers as the Russian text. Nothing is written otherwise. The file keeps its layout (indent 1, CRLF).
Usage: python -P tools/apply_changelog_190.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from changelog_190_task import PANEL, R, STREETS  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = json.load(open(os.path.join(R, "work", "gemini", "results", "changelog_190.json"), encoding="utf-8"))
    nums = lambda t: sorted(re.findall(r"\d+", t))      # noqa: E731
    texts = {"panel": PANEL, "streets": STREETS}
    for k, ru in texts.items():
        ka = (res.get(k) or {}).get("ka", "").strip()
        if not (re.search("[ა-ჰ]", ka) and not re.search("[А-Яа-яЁё]", ka) and "პროსპექტი" not in ka and nums(ka) == nums(ru["ru"])):
            print("rejected:", k, "| nothing written")
            sys.exit(1)
    p = os.path.join(R, "site", "data", "changelog.json")
    raw = open(p, encoding="utf-8", newline="").read()
    doc = json.loads(raw)
    assert json.dumps(doc, ensure_ascii=False, indent=1).replace("\n", "\r\n") == raw, "unexpected layout of changelog.json"
    items = doc[0]["items"]
    assert doc[0]["version"] == "1.9.0"
    idx = [i for i, it in enumerate(items) if it["en"].startswith("Updated Filters panel")]
    assert len(idx) == 1, "the panel item was not found"
    items[idx[0]] = {"t": "new", "ru": PANEL["ru"], "en": PANEL["en"], "ka": res["panel"]["ka"].strip()}
    if not any(it["en"].startswith("Streets and places") for it in items):
        items.insert(idx[0] + 1, {"t": "new", "ru": STREETS["ru"], "en": STREETS["en"], "ka": res["streets"]["ka"].strip()})
    open(p, "w", encoding="utf-8", newline="").write(json.dumps(doc, ensure_ascii=False, indent=1).replace("\n", "\r\n"))
    print("changelog 1.9.0: the panel item replaced, the item 'Streets and places' present; items now:", len(items))


if __name__ == "__main__":
    main()
