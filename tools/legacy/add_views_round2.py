"""Add eight more photographs and engravings of Tbilisi from Wikimedia Commons (public domain) to site/data/views.json ("Historical views"), stored locally as webp.
They fill the thin periods of the panel: the 1870s, the 1880s, 1898, 1914-1918 and the engravings of 1854 and 1860 (the photographs of the 1850s-60s do not exist on Commons).
Criterion as in add_more_views.py: public domain by the Commons metadata; the caption and the year are the ones given on Commons; the engravings carry a note that they are not photographs.
The photos are NOT tied to a point on the map. Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT. Usage: python -X utf8 -P tools/add_views_round2.py
"""
import importlib.util
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("avm", os.path.join(ROOT, "tools", "add_more_views.py"))
avm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(avm)
A, NOTE, NOTE_DRAW, UA = avm.A, avm.NOTE, avm.NOTE_DRAW, avm.UA

NOAUTH = A("автор не указан на Commons", "the author is not given on Commons", "ავტორი Commons-ზე მითითებული არ არის")
# (Commons file, id, year, window, ru, en, ka, author, note)
ITEMS = [
    ("Avlabar Bridge, 1870s.jpg", "roinashvili_avlabar_bridge_1870s", 1875, 20,
     "Авлабарский мост, А. Роинашвили (1870-е)", "The Avlabar Bridge, A. Roinashvili (1870s)", "ავლაბრის ხიდი, ა. როინაშვილი (1870-იანი წლები)",
     A("Александр Роинашвили", "Alexander Roinashvili", "ალექსანდრე როინაშვილი"), NOTE),
    ("Bridge in Tbilisi, 1870s.jpg", "kennan_bridge_1870s", 1875, 20,
     "Мост в Тифлисе, Дж. Кеннан (1870-е)", "A bridge in Tiflis, G. Kennan (1870s)", "ხიდი ტფილისში, ჯ. კენანი (1870-იანი წლები)",
     A("Джордж Кеннан", "George Kennan", "ჯორჯ კენანი"), NOTE),
    ("Old Tbilisi Konka.jpg", "konka_viceregal_palace_1880s", 1885, 15,
     "Конка и дворец наместника на Головинском проспекте (1880-е)", "A horse tram (konka) and the Viceregal Palace on Golovin Avenue (1880s)", "კონკა და მეფისნაცვლის სასახლე გოლოვინის გამზირზე (1880-იანი წლები)",
     NOAUTH, NOTE),
    ("Ferry boat tiflis (Demidov, 1898).jpg", "demidov_ferry_1898", 1898, 10,
     "Паром в Тифлисе (по названию файла: Демидов, 1898)", "A ferry boat in Tiflis (by the file name: Demidov, 1898)", "ბორანი ტფილისში (ფაილის სახელით: დემიდოვი, 1898)",
     A("автор снимка не указан (в названии файла: Demidov, 1898)", "the author of the photograph is not given (the file name has: Demidov, 1898)", "ფოტოს ავტორი მითითებული არ არის (ფაილის სახელში: Demidov, 1898)"),
     A("Фотография из Wikimedia Commons (общественное достояние); подпись и год по названию и описанию на Commons. К карте не привязана.",
       "Photograph from Wikimedia Commons (public domain); the caption and the year are from the title and the description on Commons. Not tied to the map.",
       "ფოტო Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და წელი Commons-ის სათაურისა და აღწერის მიხედვით. რუკას არ უკავშირდება.")),
    ("Main bridge, tiflis (Demidov, 1898).jpg", "demidov_main_bridge_1898", 1898, 10,
     "Главный мост в Тифлисе (по названию файла: Демидов, 1898)", "The Main Bridge in Tiflis (by the file name: Demidov, 1898)", "მთავარი ხიდი ტფილისში (ფაილის სახელით: დემიდოვი, 1898)",
     A("автор снимка не указан (в названии файла: Demidov, 1898)", "the author of the photograph is not given (the file name has: Demidov, 1898)", "ფოტოს ავტორი მითითებული არ არის (ფაილის სახელში: Demidov, 1898)"),
     A("Фотография из Wikimedia Commons (общественное достояние); подпись и год по названию и описанию на Commons. К карте не привязана.",
       "Photograph from Wikimedia Commons (public domain); the caption and the year are from the title and the description on Commons. Not tied to the map.",
       "ფოტო Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და წელი Commons-ის სათაურისა და აღწერის მიხედვით. რუკას არ უკავშირდება.")),
    ("Tiflis NL-HaNA .24.09 158-2533.jpg", "bufa_tiflis_1914_1918", 1916, 6,
     "Тбилиси, снимок 1914-1918 годов; на первом плане типичная грузинская церковь", "Tbilisi, a photograph of 1914-1918; in the front a typical Georgian church", "თბილისი, 1914-1918 წლების ფოტო; წინა პლანზე ტიპიური ქართული ეკლესია",
     A("BUFA, коллекция фотографий Первой мировой войны (Национальный архив Нидерландов)", "BUFA, the photo collection of the First World War (the National Archives of the Netherlands)", "BUFA, პირველი მსოფლიო ომის ფოტოკოლექცია (ნიდერლანდების ეროვნული არქივი)"),
     A("Фотография из Wikimedia Commons (общественное достояние); подпись и годы (1914-1918) по описанию на Commons. К карте не привязана.",
       "Photograph from Wikimedia Commons (public domain); the caption and the years (1914-1918) are as given on Commons. Not tied to the map.",
       "ფოტო Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და წლები (1914-1918) Commons-ის აღწერის მიხედვით. რუკას არ უკავშირდება.")),
    ("August von Haxthausen. Transcaucasia. View of Tiflis.jpg", "haxthausen_tiflis_1854", 1854, 10,
     "Вид Тифлиса, гравюра из книги Гакстгаузена «Закавказье» (1854)", "A view of Tiflis, an engraving from the book of Haxthausen 'Transcaucasia' (1854)", "ტფილისის ხედი, გრავიურა ჰაქსთჰაუზენის წიგნიდან „ამიერკავკასია“ (1854)",
     A("Грэб; Август фон Гакстгаузен и князь Павел Ливен", "Graeb; August von Haxthausen and Prince Paul Lieven", "გრები; ავგუსტ ფონ ჰაქსთჰაუზენი და თავადი პაველ ლივენი"), NOTE_DRAW),
    ("Le Tour du monde-01-p321.jpg", "tourdumonde_tiflis_1860", 1860, 10,
     "Общий вид Тифлиса, гравюра из журнала «Le Tour du monde» (1860)", "A general view of Tiflis, an engraving from the journal 'Le Tour du monde' (1860)", "ტფილისის საერთო ხედი, გრავიურა ჟურნალ „Le Tour du monde“-დან (1860)",
     A("Эмиль Теодор Терон", "Émile Théodore Thérond", "ემილ თეოდორ ტერონი"), NOTE_DRAW),
]


def api(**p):
    p.update(format="json", formatversion="2")
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php", data=urllib.parse.urlencode(p).encode(), headers={"User-Agent": UA})
    for k in range(5):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except Exception:
            time.sleep(5 * (k + 1))
    raise SystemExit("API failed")


def main():
    vp = os.path.join(ROOT, "site", "data", "views.json")
    raw = open(vp, encoding="utf-8").read()
    views = json.loads(raw)
    have = {v["id"] for v in views}
    outdir = os.path.join(ROOT, "site", "data", "views")
    for fname, vid, y, win, ru, en, ka, au, note in ITEMS:
        if vid in have:
            continue
        d = api(action="query", titles="File:" + fname, prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=960)
        pg = d["query"]["pages"][0]
        ii = (pg.get("imageinfo") or [None])[0]
        if not ii:
            print("not found:", fname)
            continue
        lic = re.sub(r"<[^>]+>", "", (ii["extmetadata"].get("LicenseShortName") or {}).get("value", "")).strip()
        if lic not in ("Public domain", "No restrictions", "CC0"):
            print("licence is not public domain, skipped:", fname, lic)
            continue
        data = None
        for k in range(5):
            try:
                data = urllib.request.urlopen(urllib.request.Request(ii.get("thumburl") or ii["url"], headers={"User-Agent": UA}), timeout=90).read()
                break
            except Exception:
                time.sleep(8 * (k + 1))
        if not data:
            print("download failed:", vid)
            continue
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if max(im.size) > 1400:
            im.thumbnail((1400, 1400))
        im.save(os.path.join(outdir, vid + ".webp"), "WEBP", quality=80, method=6)
        views.append({"id": vid, "year": y, "window": win, "image": "data/views/%s.webp" % vid, "title": A(ru, en, ka), "author": au, "note": note, "license": lic, "page": ii["descriptionurl"]})
        print("added", vid, im.size, lic)
        time.sleep(2)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("[\n") else None, separators=None if raw.startswith("[\n") else (",", ":"))
    print("views:", len(views))


if __name__ == "__main__":
    main()
