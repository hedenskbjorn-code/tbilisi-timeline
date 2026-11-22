"""The task for Gemini about the former names of the stations of the Tbilisi metro: for_gemini/from_desktop/metro_batch_01.md (the 23 stations of the site, the passages of the encyclopedia of 2008 about the stations,
the five rows that Gemini found earlier). The answer is checked by tools/verify_metro.py. Usage: python -P tools/metro_task.py
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
d = json.load(open(os.path.join(ROOT, "site", "data", "transport.json"), encoding="utf-8"))
st = [f["properties"] for f in d["features"] if f["properties"]["kind"] == "metro_station"]
ents = json.load(open(os.path.join(ROOT, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))
L = ["# Станции Тбилисского метро: прежние названия", "", "## Станции сайта (23)", "", "| id | линия | ka | ru | en | открыта |", "|---|---|---|---|---|---|"]
for p in st:
    L.append("| %s | %s | %s | %s | %s | %s |" % (p["id"], p["line"], p["name_ka"], p["name_ru"], p["name_en"], p["y0"]))
L += ["", "## Места энциклопедии 2008 г., где названа станция метро (id статьи, страница PDF, фраза)", ""]
for e in ents:
    t = (e.get("text_long") or e["text"]).replace("\n", " ")
    for m in re.finditer(r"მეტრო[^.]{0,200}\.", t):
        L.append("- %s | PDF p. %s | %s" % (e["id"], e["page"], m.group(0)))
L += ["", "## Что Gemini уже нашёл раньше (tbilisi_kvamli_42_research_result.md, группа 6), нужно проверить и дополнить", "",
      "| старое (ka) | новое (ka) | год и источник |", "|---|---|---|",
      "| ლენინის მოედანი | თავისუფლების მოედანი | октябрь 1990, georgianencyclopedia.ge |", "| 26 კომისარი | ავლაბარი | апрель 1991, georgianencyclopedia.ge |",
      "| ოქტომბერი | ნაძალადევი | апрель 1991 (georgianencyclopedia.ge) или 1992 (ru.wikipedia); энциклопедия 2008 называет «ოქტომბერი» без года |",
      "| კომკავშირული | სამედიცინო ინსტიტუტი (ныне უნივერსიტეტი) | 1992, ru.wikipedia |", "| პოლიტექნიკური ინსტიტუტი | ტექნიკური უნივერსიტეტი | 1979–2005, georgianencyclopedia.ge |",
      "| თემქა | დავით სარაჯიშვილი | энциклопедия 2008 (стр. 155), год не назван |"]
open(os.path.join(ROOT, "for_gemini", "from_desktop", "metro_batch_01.md"), "wb").write(("\n".join(L) + "\n").encode("utf-8"))
print("stations:", len(st))
