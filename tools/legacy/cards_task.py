"""The streets of the encyclopedia (2008) that have a namesake (tools/verify_namesakes.py) but no card on the site (no name history): a task for Gemini to give their names in ka / ru / en, so that the card
(the namesake, the page of the book, the search) can be made. Makes work/gemini/cards_batch_NN.md (packs of 100). The answer is checked by tools/verify_cards.py.
Usage: python -P tools/cards_task.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import name_forms, norm_name  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ents = {e["id"]: e for e in json.load(open(os.path.join(R, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))}
sn = json.load(open(os.path.join(R, "site", "data", "street_names.json"), encoding="utf-8"))["streets"]
by = {}
for s in sn:
    for f in name_forms(s["now"]["ka"]):
        by.setdefault(norm_name(f), s)
enc_ka = {}
for fn in ("enc2008_verified.json", "enc2008_verified4.json"):
    for r in json.load(open(os.path.join(R, "data", "cache", fn), encoding="utf-8"))["ok"]:
        enc_ka[r["id"]] = r["ka_now"]
head = lambda t: re.split(r"[,.;:(]", t.strip(), maxsplit=1)[0][:80]


def ids():
    out = []
    v = json.load(open(os.path.join(R, "data", "cache", "namesakes_verified.json"), encoding="utf-8"))
    for r in v["ok"]:
        if not re.match(r"E\d{4}$", r["id"]):
            continue
        ka = enc_ka.get(r["id"]) or head(ents[r["id"]]["text"])
        if not any(norm_name(f) in by for f in name_forms(ka)):
            out.append(r["id"])
    return out


def main():
    todo = ids()
    n = 0
    for k in range(0, len(todo), 100):
        n += 1
        lines = ["# Пакет %02d: улицы и площади энциклопедии без карточки на сайте (названия на трёх языках)" % n, ""]
        for i in todo[k:k + 100]:
            e = ents[i]
            t = (e.get("text_long") or e["text"]).replace("\\n", " ").replace("\n", " ")[:420]
            lines += ["## %s | PDF p. %s | район: %s | заголовок (OCR): %s" % (i, e["page"], e["district"], e["name"]), "", t, ""]
        open(os.path.join(R, "work", "gemini", "batches", "cards", "cards_batch_%02d.md" % n), "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
    print("entries:", len(todo), "packs:", n)


if __name__ == "__main__":
    main()
