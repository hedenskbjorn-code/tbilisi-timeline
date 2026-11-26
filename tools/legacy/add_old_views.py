"""Add a small checked set of old public-domain photographs of Tbilisi (Wikimedia Commons) to site/data/views.json ("Historical views").
Criterion: the Commons file title or description itself names the subject and gives the date; nothing comes from the unverified draft of the Gemini placement.
The photos are NOT tied to a point on the map. The image is the Commons 900 px thumbnail URL (hotlinked, like the register photos).
Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT. Usage: python -P tools/add_old_views.py
"""
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
c = os.environ.get("WIKIMEDIA_CONTACT", "")
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % (("; contact: " + c) if c else "")
NOTE = {"ru": "Фотография из Wikimedia Commons (общественное достояние); подпись и год по описанию на Commons. К карте не привязана.",
        "en": "Photograph from Wikimedia Commons (public domain); the caption and the year are as given on Commons. Not tied to the map.",
        "ka": "ფოტო Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და წელი Commons-ის აღწერის მიხედვით. რუკას არ უკავშირდება."}
ER = {"ru": "Дмитрий Ермаков", "en": "Dmitri Yermakov", "ka": "დიმიტრი ერმაკოვი"}
EN = {"ru": "Александр Энгель", "en": "Alexander Engel", "ka": "ალექსანდრე ენგელი"}
UN = {"ru": "автор неизвестен", "en": "unknown author", "ka": "ავტორი უცნობია"}
# (Commons file, id, year, window, ru title, en title, author)
ITEMS = [
    ("Alexander Engel. Michail Bridge.jpg", "engel_michael_bridge", 1890, 28, "Михайловский мост (А. Энгель, 1890–1918)", "Michael Bridge (A. Engel, 1890-1918)", EN),
    ("Ermakov. Stores on Michael Bridge. 1885.jpg", "ermakov_michael_bridge_1885", 1885, 30, "Лавки на Михайловском мосту, 1885 (Д. Ермаков)", "Shops on the Michael Bridge, 1885 (D. Yermakov)", ER),
    ("Ermakov. Abano (Bath) Street and a rise leading to the Botanical Garden. 1890.jpg", "ermakov_abano_1890", 1890, 30, "Улица Абано и подъём к Ботаническому саду, 1890 (Д. Ермаков)", "Abano (Bath) Street and the rise to the Botanical Garden, 1890 (D. Yermakov)", ER),
    ("Ermakov. An old part of the town seen from Metekhi Castle. 1900.jpg", "ermakov_metekhi_1900", 1900, 20, "Старая часть города с Метехского замка, 1900 (Д. Ермаков)", "The old part of the town seen from Metekhi Castle, 1900 (D. Yermakov)", ER),
    ("Palace of Caucasian Viceroy, Tiflis 15.jpg", "viceroy_palace_1865", 1865, 30, "Дворец кавказского наместника, 1865", "Palace of the Caucasian Viceroy, 1865", UN),
    ("Grand Hotel and Hotel London, Tiflis (D. Ermakov).jpg", "ermakov_grand_hotel", 1900, 20, "Гранд-отель и гостиница «Лондон», около 1900 (Д. Ермаков)", "Grand Hotel and Hotel London, about 1900 (D. Yermakov)", ER),
    ("Alexander Nevsky Cathedral, Tbilisi (ტფილისის სამხედრო ტაძარი).jpg", "ermakov_nevsky", 1881, 35, "Собор Александра Невского (Д. Ермаков, 1881–1916)", "Alexander Nevsky Cathedral (D. Yermakov, 1881-1916)", ER),
    ("Standseilbahn Tiflis 1905.jpg", "funicular_1905", 1905, 20, "Фуникулёр, 1905", "The funicular, 1905", UN),
    ("Alexander Engel. Rique district.jpg", "engel_rike", 1890, 28, "Район Рике (А. Энгель, 1890–1918)", "Rike district (A. Engel, 1890-1918)", EN),
    ("Alexander Engel. Shiite Mosque in Maidan.jpg", "engel_maidan_mosque", 1890, 28, "Шиитская мечеть на Майдане (А. Энгель, 1890–1918)", "Shiite mosque in the Maidan (A. Engel, 1890-1918)", EN),
]


def api(**p):
    p["format"] = "json"
    return json.loads(urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php", data=urllib.parse.urlencode(p).encode(), headers={"User-Agent": UA}), timeout=60).read())


def main():
    vp = os.path.join(ROOT, "site", "data", "views.json")
    views = json.load(open(vp, encoding="utf-8"))
    have = {v["id"] for v in views}
    titles = "|".join("File:" + it[0] for it in ITEMS)
    r = api(action="query", titles=titles, prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=900)
    pages = {p["title"]: p for p in r["query"]["pages"].values()}
    for fn, vid, y, win, ru, en, au in ITEMS:
        if vid in have:
            continue
        pg = pages.get("File:" + fn) or pages.get("File:" + fn.replace("_", " "))
        ii = (pg or {}).get("imageinfo", [{}])[0]
        if not ii.get("thumburl"):
            print("no thumb:", fn)
            continue
        lic = (ii.get("extmetadata", {}).get("LicenseShortName", {}) or {}).get("value", "")
        if "ublic" not in lic and lic not in ("CC0", "PD"):
            print("licence not PD, skipped:", fn, lic)
            continue
        img = ii["thumburl"]          # 900 px thumbnail on upload.wikimedia.org, loaded by the visitor browser like the register photos (CSP allows it); downloading was rate limited (HTTP 429)
        views.append({"id": vid, "year": y, "window": win, "image": img, "title": {"ru": ru, "en": en}, "author": au, "note": NOTE, "license": lic or "Public domain",
                      "page": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(fn.replace(" ", "_"))})
        print("added", vid, lic)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(views), "views")


if __name__ == "__main__":
    main()
