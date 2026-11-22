"""The task for Gemini about the main roads (the layer of the avenues): for each of the 25 roads the article of the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008) with the phrase about the
origin of the street ("წარმოიქმნა XX ს. 20-იან წლებში"), a verbatim quote and the PDF page. Makes for_gemini/from_desktop/mainroads_batch_01.md (the candidate articles by the likeness of the heading;
the encyclopedia is alphabetical, the candidates can be wrong: Gemini reads the PDF). The answer is checked by tools/verify_mainroads.py.
Usage: python -P tools/mainroads_task.py
"""
import difflib
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
OUT = os.path.join(ROOT, "for_gemini", "from_desktop", "mainroads_batch_01.md")

ROADS = [  # key, English name (OSM), Georgian name (OSM), role
    ("rustaveli", "Shota Rustaveli Avenue", "შოთა რუსთაველის გამზირი", "avenue"), ("aghmashenebeli", "David Aghmashenebeli Avenue", "დავით აღმაშენებლის გამზირი", "avenue"),
    ("chavchavadze", "Ilia Chavchavadze Avenue", "ილია ჭავჭავაძის გამზირი", "avenue"), ("tsereteli", "Akaki Tsereteli Avenue", "აკაკი წერეთლის გამზირი", "avenue"),
    ("melikishvili", "Petre Melikishvili Avenue", "პეტრე მელიქიშვილის გამზირი", "avenue"), ("tamar", "Tamar Mepe Avenue", "თამარ მეფის გამზირი", "avenue"),
    ("kazbegi", "Alexander Kazbegi Avenue", "ალექსანდრე ყაზბეგის გამზირი", "avenue"), ("guramishvili", "David Guramishvili Avenue", "დავით გურამიშვილის გამზირი", "avenue"),
    ("dedoplis", "Tsminda Ketevan Dedoflis Avenue", "წმინდა ქეთევან დედოფლის გამზირი", "avenue"), ("moscow", "Moscow Avenue", "მოსკოვის გამზირი", "avenue"),
    ("robakidze", "Grigol Robakidze Avenue", "გრიგოლ რობაქიძის გამზირი", "avenue"), ("vazha", "Vazha-Pshavela Avenue", "ვაჟა-ფშაველას გამზირი", "avenue"),
    ("pekini", "Pekini Avenue / Konstantine Gamsakhurdia Avenue (one road in two parts)", "პეკინის გამზირი / კონსტანტინე გამსახურდიას გამზირი", "avenue"),
    ("salosi", "Beri Gabriel Salosi Avenue", "ბერი გაბრიელ სალოსის გამზირი", "avenue"), ("baratashvili", "Nikoloz Baratashvili Street", "ნიკოლოზ ბარათაშვილის ქუჩა", "street"),
    ("kostava", "Merab Kostava Street", "მერაბ კოსტავას ქუჩა", "street"), ("gorgasali", "Vakhtang Gorgasali Street", "ვახტანგ გორგასლის ქუჩა", "street"),
    ("tsabadze", "Giorgi Tsabadze Street", "გიორგი ცაბაძის ქუჩა", "street"), ("cholokashvili", "Cholokashvili Avenue (Street)", "ჩოლოყაშვილის გამზირი / ქუჩა", "street"),
    ("kakheti", "Kakheti Highway", "კახეთის გზატკეცილი", "highway"), ("rustavi", "Rustavi Highway", "რუსთავის გზატკეცილი", "highway"),
    ("tskneti", "Tsqneti Highway", "წყნეთის გზატკეცილი", "highway"), ("kojori", "Tbilisi-Kojori Highway", "თბილისი-კოჯორის გზატკეცილი", "highway"),
    ("alley", "David Aghmashenebeli Alley", "დავით აღმაშენებლის ხეივანი", "avenue"), ("pilsudski", "Marshal Joseph Pilsudski Avenue", "მარშალ იოზეფ პილსუდსკის გამზირი", "avenue"),
]


def head(t):
    return re.split(r"[,.;:(]", t.strip(), maxsplit=1)[0][:70]


def main():
    ents = json.load(open(ENT, encoding="utf-8"))
    hs = [(e, head(e["text"])) for e in ents]
    lines = ["# Пакет: 25 магистралей и кандидаты-статьи энциклопедии 2008 (№ страниц = страницы PDF)", "",
             "Кандидаты подобраны по сходству заголовка и МОГУТ БЫТЬ ОШИБОЧНЫМИ (распознавание текста с ошибками, энциклопедия идёт по алфавиту). Настоящую статью ищи в PDF "
             "`C:/Projects/tbilisi-timeline/data/cache/nplg_pdfs/tbilisi_streets_2008.pdf`: рядом со страницей кандидата (по алфавиту).", ""]
    for key, en, ka, role in ROADS:
        best = sorted(hs, key=lambda h: -difflib.SequenceMatcher(None, ka.split(" / ")[0], h[1]).ratio())[:3]
        lines += ["## %s | %s | %s | %s" % (key, en, ka, role), ""]
        for e, h in best:
            t = (e.get("text_long") or e["text"])[:2600].replace("\n", " ")
            lines += ["### кандидат %s, страница PDF %s, заголовок: %s" % (e["id"], e["page"], h), "", t, ""]
    open(OUT, "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
    print("written", OUT, "roads:", len(ROADS))


if __name__ == "__main__":
    main()
