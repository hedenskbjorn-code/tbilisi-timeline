"""Add photographs of Tbilisi of 2000-2009 from Wikimedia Commons (public domain or CC BY / CC BY-SA) to site/data/views.json, stored locally as webp.
Criterion: the licence is read from the Commons metadata; the date is the one given on Commons (EXIF date or the title); no identifiable people or politics.
The photos are NOT tied to a point on the map. Author, licence and the Commons page are kept in views.json and shown in the viewer.
Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT.
Usage: python -X utf8 -P tools/add_2000s_views.py <meta json from the Commons search: list of {title, lic, artist, thumb, page}>
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
c = os.environ.get("WIKIMEDIA_CONTACT", "")
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % (("; contact: " + c) if c else "")


def A(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


def same(s):
    return A(s, s, s)


NOTE_PD = A("Фотография из Wikimedia Commons (общественное достояние); подпись и дата по описанию на Commons; копия уменьшена. К карте не привязана.",
            "Photograph from Wikimedia Commons (public domain); the caption and the date are as given on Commons; the copy is reduced in size. Not tied to the map.",
            "ფოტო Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და თარიღი Commons-ის აღწერის მიხედვით; ასლი შემცირებულია. რუკას არ უკავშირდება.")


def note_cc(lic):
    return A("Фотография из Wikimedia Commons, лицензия %s: указание автора и ссылка на страницу файла обязательны; копия уменьшена. Подпись и дата по описанию на Commons. К карте не привязана." % lic,
             "Photograph from Wikimedia Commons, licence %s: the credit to the author and the link to the file page are required; the copy is reduced in size. The caption and the date are as given on Commons. Not tied to the map." % lic,
             "ფოტო Wikimedia Commons-იდან, ლიცენზია %s: ავტორის მითითება და ფაილის გვერდის ბმული სავალდებულოა; ასლი შემცირებულია. წარწერა და თარიღი Commons-ის აღწერის მიხედვით. რუკას არ უკავშირდება." % lic,
             )


# (start of the Commons file name, id, year, ru, en, ka)
ITEMS = [
    ("Narikala - 2002.jpg", "c2002_narikala", 2002, "Нарикала, лето 2002", "Narikala, summer 2002", "ნარიყალა, 2002 წლის ზაფხული"),
    ("View of Tbilisi from Metekhi Church - 2002", "c2002_metekhi_view", 2002, "Вид на Тбилиси от церкви Метехи, лето 2002", "A view of Tbilisi from Metekhi Church, summer 2002", "თბილისის ხედი მეტეხის ეკლესიიდან, 2002 წლის ზაფხული"),
    ("Trolleybuses on Chavchavadze Avenue - 2002", "c2002_trolleybuses", 2002, "Троллейбусы на проспекте Чавчавадзе, лето 2002", "Trolleybuses on Chavchavadze Avenue, summer 2002", "ტროლეიბუსები ჭავჭავაძის გამზირზე, 2002 წლის ზაფხული"),
    ("Chavchavadze Ave..jpg", "c2003_chavchavadze", 2003, "Проспект Чавчавадзе, 2003", "Chavchavadze Avenue, 2003", "ჭავჭავაძის გამზირი, 2003"),
    ("19th century health baths.jpg", "c2004_orbeliani_baths", 2004, "Бани Орбелиани в Абанотубани, июль 2004", "The Orbeliani Baths in Abanotubani, July 2004", "ორბელიანების აბანო აბანოთუბანში, 2004 წლის ივლისი"),
    ("Tbilisi 008.jpg", "c2005_freedom_square", 2005, "Площадь Свободы в стройке, ноябрь 2005", "Freedom Square under construction, November 2005", "თავისუფლების მოედანი მშენებლობისას, 2005 წლის ნოემბერი"),
    ("Chardin Street, Tbilisi.JPG", "c2006_chardin", 2006, "Улица Шардени в Старом Тбилиси, октябрь 2006", "Chardin Street in Old Tbilisi, October 2006", "შარდენის ქუჩა ძველ თბილისში, 2006 წლის ოქტომბერი"),
    ("Kura River in the central part of Tbilisi, 2007-09-28.jpg", "c2007_kura", 2007, "Кура в центре Тбилиси, вид с Нарикала, сентябрь 2007", "The Kura in central Tbilisi, seen from Narikala, September 2007", "მტკვარი თბილისის ცენტრში, ხედი ნარიყალადან, 2007 წლის სექტემბერი"),
    ("Marjanishvili Square, Tbilisi.jpg", "c2008_marjanishvili", 2008, "Площадь Марджанишвили, июнь 2008", "Marjanishvili Square, June 2008", "მარჯანიშვილის მოედანი, 2008 წლის ივნისი"),
    ("Old Tbilisi (May 2009).jpg", "c2009_old_tbilisi", 2009, "Старый Тбилиси, вид с Нарикала, май 2009", "Old Tbilisi, a view from Narikala, May 2009", "ძველი თბილისი, ხედი ნარიყალადან, 2009 წლის მაისი"),
]


def main():
    meta = json.load(open(sys.argv[1], encoding="utf-8"))
    vp = os.path.join(ROOT, "site", "data", "views.json")
    raw = open(vp, encoding="utf-8").read()
    views = json.loads(raw)
    have = {v["id"] for v in views}
    outdir = os.path.join(ROOT, "site", "data", "views")
    for start, vid, y, ru, en, ka in ITEMS:
        if vid in have:
            continue
        cand = [m for m in meta if m["title"][5:].startswith(start)]
        if not cand:
            print("not in listing:", start)
            continue
        m = cand[0]
        lic = m["lic"]
        if not (lic == "Public domain" or lic == "CC0" or lic.startswith("CC BY")):
            print("licence not accepted, skipped:", m["title"], lic)
            continue
        thumb = m["thumb"]
        if "/thumb/" in thumb:
            thumb = re.sub(r"/\d+px-", "/960px-", thumb)
        data = None
        for k in range(5):
            try:
                data = urllib.request.urlopen(urllib.request.Request(thumb, headers={"User-Agent": UA}), timeout=90).read()
                break
            except urllib.error.HTTPError as e:
                print("http", e.code, vid)
                time.sleep(10 * (k + 1))
            except Exception:
                time.sleep(5)
        if not data:
            print("download failed:", vid)
            continue
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if max(im.size) > 1400:
            im.thumbnail((1400, 1400))
        im.save(os.path.join(outdir, vid + ".webp"), "WEBP", quality=80, method=6)
        artist = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m["artist"])).strip()
        artist = re.sub(r"^Photo by ", "", artist)
        artist = re.sub(r" from [A-Z][A-Za-z ]+$", "", artist)        # "Henri Bergius from Finland" -> name only
        artist = re.sub(r" at English Wikipedia$", "", artist)
        f = (y // 5) * 5
        views.append({"id": vid, "year": y, "from": f, "window": f + 5 - y, "image": "data/views/%s.webp" % vid, "title": A(ru, en, ka),
                      "author": same(artist), "note": NOTE_PD if lic in ("Public domain", "CC0") else note_cc(lic), "license": lic, "page": m["page"]})
        print("added", vid, im.size, lic, artist)
        time.sleep(1.5)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("[\n") else None, separators=None if raw.startswith("[\n") else (",", ":"))
    print("views:", len(views))


if __name__ == "__main__":
    main()
