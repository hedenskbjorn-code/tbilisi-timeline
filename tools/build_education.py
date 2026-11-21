"""Build site/data/education.json (the layer 'Education': schools and kindergartens of the heritage register) from data/education_register.json
(made by tools/add_register_layers.py).
Usage: python -X utf8 -P tools/build_education.py
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data = json.load(open(os.path.join(ROOT, "data", "education_register.json"), encoding="utf-8"))
data.sort(key=lambda x: (x["from"], x["rid"]))
for o in data:
    assert all(o["name"][l] and o["note"][l] for l in ("ru", "en", "ka")), o["id"]
p = os.path.join(ROOT, "site", "data", "education.json")
open(p, "wb").write(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
print(len(data), "objects ->", p)
