"""The task for Gemini: the LOCAL toponyms of Tbilisi with their etymology from the dictionary part of the encyclopedia of 2008 (PDF pages 244-360: the explanations of the names, alphabetical: districts,
gardens, hills, markets, baths, old names of places; the people are there too, they are not wanted here). Makes work/gemini/places_batch_NN.md (the text of 15 pages each, with the page numbers).
The answer (places_batch_NN_result.json) is checked by tools/verify_places.py. Usage: python -P tools/places_task.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIRST, LAST, STEP = 244, 360, 15


def main():
    s = open(os.path.join(R, "data", "cache", "ocr", "streets_enc2008_kat.txt"), encoding="utf-8", errors="replace").read()
    pg = {int(m.group(1)): norm(m.group(2)) for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", s, re.S)}
    n = 0
    for a in range(FIRST, LAST + 1, STEP):
        n += 1
        pages = range(a, min(a + STEP, LAST + 1))
        lines = ["# Пакет %02d: словарная часть энциклопедии, страницы PDF %d–%d (названия местностей Тбилиси и их этимология)" % (n, a, pages[-1]), ""]
        for p in pages:
            lines += ["## PDF p. %d" % p, "", pg.get(p, ""), ""]
        open(os.path.join(R, "work", "gemini", "batches", "places", "places_batch_%02d.md" % n), "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
    print("packs:", n)


if __name__ == "__main__":
    main()
