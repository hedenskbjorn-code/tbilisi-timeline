"""The second pass about the main roads: for the roads whose article has no phrase of origin, the earliest year in the article that is tied to the existence of the street: a plan, a map, a list of the
streets, the laying ("1841 წ. შედგენილ ... სიაში", "1876 წ. გეგმაზე", "გაყვანილია 1846"). It is the first document, NOT the origin of the street (the card says so). Makes
work/gemini/batches/mainroads/mainroads_batch_02.md (candidate articles as in the first pass, the page that Gemini gave in the first pass). Checked by tools/verify_mainroads2.py.
Usage: python -P tools/mainroads_task2.py
"""
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mainroads_task import ROADS, head  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
RES1 = os.path.join(ROOT, "work", "gemini", "batches/mainroads/mainroads_batch_01_result.json")
OUT = os.path.join(ROOT, "work", "gemini", "batches/mainroads/mainroads_batch_02.md")
KEYS2 = ["rustaveli", "chavchavadze", "tsereteli", "melikishvili", "guramishvili", "dedoplis", "robakidze", "baratashvili", "kostava", "gorgasali", "rustavi", "tskneti", "kojori", "alley",
         "cholokashvili", "salosi"]
OVERRIDE = {"cholokashvili": ("Kakutsa Choloqashvili Avenue (Highway), Vake-Saburtalo", "ქაქუცა ჩოლოყაშვილის გამზირი", "avenue"),     # the avenue of Vake, not the street of Navtlughi
            "salosi": ("Beri Gabriel Salosi Avenue (the old Bogdan Khmelnitsky Street?)", "ბერი გაბრიელ სალოსის გამზირი", "avenue")}


def main():
    ents = json.load(open(ENT, encoding="utf-8"))
    hs = [(e, head(e["text"])) for e in ents]
    p1 = {r["key"]: r.get("page") or 0 for r in json.load(open(RES1, encoding="utf-8"))}
    lines = ["# Пакет 2: магистрали без фразы о возникновении: самый ранний документ (план, карта, список улиц, прокладка)", "",
             "Кандидаты подобраны по сходству заголовка и МОГУТ БЫТЬ ОШИБОЧНЫМИ. Настоящую статью проверяй по PDF `C:/Projects/tbilisi-timeline/data/cache/nplg_pdfs/tbilisi_streets_2008.pdf`. "
             "В первом проходе статья была на указанной странице (если 0, статьи не нашли).", ""]
    for key, en, ka, role in ROADS:
        if key not in KEYS2:
            continue
        if key in OVERRIDE:
            en, ka, role = OVERRIDE[key]
        near = [h for h in hs if abs(h[0]["page"] - p1.get(key, 0)) <= 1] if p1.get(key) else []
        best = sorted(hs, key=lambda h: -difflib.SequenceMatcher(None, ka.split(" / ")[0], h[1]).ratio())[:3]
        cand = {h[0]["id"]: h for h in best + sorted(near, key=lambda h: -difflib.SequenceMatcher(None, ka.split(" / ")[0], h[1]).ratio())[:2]}
        lines += ["## %s | %s | %s | %s | страница первого прохода: %s" % (key, en, ka, role, p1.get(key, 0)), ""]
        for e, h in cand.values():
            t = (e.get("text_long") or e["text"])[:3500].replace("\n", " ")
            lines += ["### кандидат %s, страница PDF %s, заголовок: %s" % (e["id"], e["page"], h), "", t, ""]
    open(OUT, "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
    print("written", OUT, "roads:", len(KEYS2))


if __name__ == "__main__":
    main()
