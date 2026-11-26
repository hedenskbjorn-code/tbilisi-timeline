"""Add more old public-domain photographs of Tbilisi (Wikimedia Commons) to site/data/views.json ("Historical views"), stored locally as webp.
Criterion: public domain according to the Commons metadata; the Commons title or description names the subject; the year or decade is the one given on Commons.
The photos are NOT tied to a point on the map. Author, licence and the Commons page are kept in views.json and shown in the viewer.
Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT. Usage: python -P tools/add_more_views.py
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


def A(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


ROI = A("Александр Роинашвили", "Alexander Roinashvili", "ალექსანდრე როინაშვილი")
KEN = A("Джордж Кеннан (по записи Нью-Йоркской публичной библиотеки)", "George Kennan (as recorded by the New York Public Library)", "ჯორჯ კენანი (ნიუ-იორკის საჯარო ბიბლიოთეკის ჩანაწერით)")
KRE = A("Василий Крейтан", "Vasily Kreitan", "ვასილი კრეიტანი")
ERM = A("Дмитрий Ермаков", "Dmitri Yermakov", "დიმიტრი ერმაკოვი")
CUR = A("Уильям Элерой Кёртис", "William Eleroy Curtis", "უილიამ ელეროი კერტისი")
BAY = A("Жозеф де Бай", "Joseph de Baye", "ჟოზეფ დე ბეი")
DAR = A("Л. Дартиг", "L. Dartigues", "ლ. დარტიგი")
TIM = A("Василий Тимм", "Vasily Timm", "ვასილი ტიმი")
NOTE = A("Фотография из Wikimedia Commons (общественное достояние); подпись и год (десятилетие) по описанию на Commons. К карте не привязана.",
         "Photograph from Wikimedia Commons (public domain); the caption and the year (decade) are as given on Commons. Not tied to the map.",
         "ფოტო Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და წელი (ათწლეული) Commons-ის აღწერის მიხედვით. რუკას არ უკავშირდება.")
NOTE_DRAW = A("Рисунок из Wikimedia Commons (общественное достояние); подпись и годы публикации по описанию на Commons. К карте не привязан.",
              "Drawing from Wikimedia Commons (public domain); the caption and the years of publication are as given on Commons. Not tied to the map.",
              "ნახატი Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და გამოცემის წლები Commons-ის აღწერის მიხედვით. რუკას არ უკავშირდება.")
# (start of the Commons file name, id, year, window, ru, en, ka, author, note)
ITEMS = [
    ("General view of Tbilisi. A. Roinov", "roinashvili_general_1870s", 1875, 20, "Общий вид Тифлиса, А. Роинашвили (1870-е)", "General view of Tiflis, A. Roinashvili (1870s)", "თბილისის საერთო ხედი, ა. როინაშვილი (1870-იანი წწ.)", ROI, NOTE),
    ("Tbilisi, Railroad station, 1870s", "roinashvili_station_1870s", 1875, 20, "Железнодорожный вокзал, А. Роинашвили (1870-е)", "The railway station, A. Roinashvili (1870s)", "რკინიგზის სადგური, ა. როინაშვილი (1870-იანი წწ.)", ROI, NOTE),
    ("A. Roinashvili. 0056 - Tiflis. Vera gardens", "roinashvili_vera_gardens", 1890, 25, "Верийские сады, А. Роинашвили (до 1898)", "The Vera gardens, A. Roinashvili (before 1898)", "ვერის ბაღები, ა. როინაშვილი (1898 წლამდე)", ROI, NOTE),
    ("Tiflis, Michael Bridge and Madatofski Island.jpg", "kennan_michael_bridge_1870s", 1875, 20, "Михайловский мост и Мадатовский остров, Дж. Кеннан (1870-е)", "Michael Bridge and Madatov Island, G. Kennan (1870s)", "მიხეილის ხიდი და მადათოვის კუნძული, ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Golovinskii Prospect in Tbilisi", "kennan_golovinsky_1870s", 1875, 20, "Головинский проспект, Дж. Кеннан (1870-е)", "Golovinsky Prospekt, G. Kennan (1870s)", "გოლოვინის გამზირი, ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Tiflis, Tatar bazaar.jpg", "kennan_tatar_bazaar_1870s", 1875, 20, "Татарский базар, Дж. Кеннан (1870-е)", "The Tatar bazaar, G. Kennan (1870s)", "თათრის ბაზარი, ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Tiflis, The Imperial Theater, 1870s", "kennan_theater_1870s", 1875, 20, "Императорский театр, Дж. Кеннан (1870-е)", "The Imperial Theatre, G. Kennan (1870s)", "საიმპერატორო თეატრი, ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Tbilisi, Orthodox Theological Seminary on Yerevan Square", "kennan_seminary_1870s", 1875, 20, "Духовная семинария на Эриванской площади, Дж. Кеннан (1870-е)", "The Orthodox seminary on Erivan Square, G. Kennan (1870s)", "მართლმადიდებლური სემინარია ერევნის მოედანზე, ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Tbilisi Sioni Cathedral-old", "kennan_sioni_1870s", 1875, 20, "Собор Сиони, Дж. Кеннан (1870-е)", "Sioni Cathedral, G. Kennan (1870s)", "სიონის ტაძარი, ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Square on the sand, Tbilisi 1870s", "kennan_peski_1870s", 1875, 20, "Площадь в Песках, Дж. Кеннан (1870-е)", "A square in Peski, G. Kennan (1870s)", "მოედანი რიყეზე („პესკი“), ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Tbilisi, Mosque at Square and part of suburb of Sololaki", "kennan_mosque_sololaki_1870s", 1875, 20, "Мечеть на площади и часть Сололаки, Дж. Кеннан (1870-е)", "A mosque on the square and part of Sololaki, G. Kennan (1870s)", "მეჩეთი მოედანზე და სოლოლაკის ნაწილი, ჯ. კენანი (1870-იანი წწ.)", KEN, NOTE),
    ("Tsars Entrance at the Assembly of Gentry in Tbilisi", "kennan_tsar_1888", 1888, 15, "Вход царя в Дворянское собрание, 29 сентября 1888 (Дж. Кеннан)", "The Tsar's entrance at the Assembly of the Gentry, 29 September 1888 (G. Kennan)", "მეფის შესვლა თავადაზნაურთა კრების შენობაში, 1888 წლის 29 სექტემბერი (ჯ. კენანი)", KEN, NOTE),
    ("Monument to Prince Vorontsov at Mikhailovsky Bridge, Tiflis", "kreitan_vorontsov_1870s", 1875, 20, "Памятник князю Воронцову у Михайловского моста (В. Крейтан, 1870-е)", "The monument to Prince Vorontsov at the Michael Bridge (V. Kreitan, 1870s)", "თავად ვორონცოვის ძეგლი მიხეილის ხიდთან (ვ. კრეიტანი, 1870-იანი წწ.)", KRE, NOTE),
    ("Ermakov 6275.", "ermakov_griboedov_grave", 1890, 25, "Могила Грибоедова, Д. Ермаков (до 1896)", "Griboyedov's grave, D. Yermakov (before 1896)", "გრიბოედოვის საფლავი, დ. ერმაკოვი (1896 წლამდე)", ERM, NOTE),
    ("Ermakov. 2959.", "ermakov_maidan_bridge", 1890, 25, "Мост на Майдане, татарская мечеть и развалины крепости, Д. Ермаков (до 1896)", "The bridge at the Maidan, a Tatar mosque and the ruins of the fortress, D. Yermakov (before 1896)", "ხიდი მაიდანზე, თათრული მეჩეთი და ციხის ნანგრევები, დ. ერმაკოვი (1896 წლამდე)", ERM, NOTE),
    ("Ermakov. 53.", "ermakov_old_town_53", 1890, 25, "Общий вид старого города, крепость и Кура, Д. Ермаков (до 1896)", "General view of the old town, the fortress and the Kura, D. Yermakov (before 1896)", "ძველი ქალაქის საერთო ხედი, ციხე და მტკვარი, დ. ერმაკოვი (1896 წლამდე)", ERM, NOTE),
    ("Tbilisi Abanotubani and Surb Sargisi church", "ermakov_abanotubani", 1895, 20, "Абанотубани и церковь Сурб Саркис, Д. Ермаков (до 1899)", "Abanotubani and the church of Surb Sargis, D. Yermakov (before 1899)", "აბანოთუბანი და სურბ სარქისის ეკლესია, დ. ერმაკოვი (1899 წლამდე)", ERM, NOTE),
    ("Image-Tbilisi XIXc 05", "ermakov_hotel_palace", 1900, 20, "Гостиница «Палас» на нынешней площади Свободы, Д. Ермаков (около 1900)", "Hotel Palace on today's Freedom Square, D. Yermakov (about 1900)", "სასტუმრო „პალასი“ დღევანდელ თავისუფლების მოედანზე, დ. ერმაკოვი (დაახლ. 1900)", ERM, NOTE),
    ("Floating flour mill, Tiflis (Curtis, 1911)", "curtis_floating_mill_1911", 1911, 15, "Плавучая мельница, Тифлис, У. Кёртис (1911)", "A floating flour mill, Tiflis, W. Curtis (1911)", "მცურავი წისქვილი, ტიფლისი, უ. კერტისი (1911)", CUR, NOTE),
    ("Principal club at Tiflis (Curtis, 1911)", "curtis_club_1911", 1911, 15, "Главный клуб Тифлиса, У. Кёртис (1911)", "The principal club of Tiflis, W. Curtis (1911)", "ტიფლისის მთავარი კლუბი, უ. კერტისი (1911)", CUR, NOTE),
    ("Ruins of fortress, Tbilisi (de Baye)", "debaye_fortress_1900", 1900, 15, "Руины крепости, Ж. де Бай (1900)", "Ruins of the fortress, J. de Baye (1900)", "ციხის ნანგრევები, ჟ. დე ბეი (1900)", BAY, NOTE),
    ("St.-David monastery, Tbilisi (de Baye)-1", "debaye_david_1900", 1900, 15, "Монастырь св. Давида, Ж. де Бай (1900)", "The monastery of St David, J. de Baye (1900)", "წმ. დავითის მონასტერი, ჟ. დე ბეი (1900)", BAY, NOTE),
    ("Quartier de Tiflis ou se trouvait", "dartigues_french_hospital_1918", 1918, 10, "Квартал Тифлиса с Французским госпиталем у Верийского моста, Л. Дартиг (1917-1919)", "The quarter of Tiflis with the French hospital near the Vera bridge, L. Dartigues (1917-1919)", "თბილისის უბანი ფრანგული ჰოსპიტლით ვერის ხიდთან, ლ. დარტიგი (1917-1919)", DAR, NOTE),
    ("Tiflis by Timm, Vasilii Fedorovich", "timm_tiflis_1850s", 1856, 25, "Вид Тифлиса, В. Тимм (опубликован в 1851-1862)", "A view of Tiflis, V. Timm (published 1851-1862)", "თბილისის ხედი, ვ. ტიმი (გამოქვეყნდა 1851-1862)", TIM, NOTE_DRAW),
]


def api(**p):
    p["format"] = "json"
    p["formatversion"] = "2"
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php", data=urllib.parse.urlencode(p).encode(), headers={"User-Agent": UA})
    for k in range(5):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except Exception:
            time.sleep(5 * (k + 1))
    raise SystemExit("API failed")


def main():
    meta = json.load(open(os.environ["PH_META"], encoding="utf-8"))          # list of {title, ...} made by a category listing
    vp = os.path.join(ROOT, "site", "data", "views.json")
    raw = open(vp, encoding="utf-8").read()
    views = json.loads(raw)
    have = {v["id"] for v in views}
    outdir = os.path.join(ROOT, "site", "data", "views")
    for start, vid, y, win, ru, en, ka, au, note in ITEMS:
        if vid in have:
            continue
        cand = [m for m in meta if m["title"][5:].startswith(start)]
        if not cand:
            print("not in listing:", start)
            continue
        m = cand[0]
        if m["lic"] not in ("Public domain", "No restrictions", "CC0"):
            print("licence not PD, skipped:", m["title"], m["lic"])
            continue
        thumb = m["thumb"]
        if "/thumb/" in thumb:                                   # Commons serves only standard thumbnail widths quickly; 1200 px is not one of them
            import re
            thumb = re.sub(r"/\d+px-", "/960px-", thumb)
        data = None
        for k in range(5):
            try:
                data = urllib.request.urlopen(urllib.request.Request(thumb, headers={"User-Agent": UA}), timeout=90).read()
                break
            except urllib.error.HTTPError as e:
                print("http", e.code, vid)
                time.sleep(10 * (k + 1))
            except Exception as e:
                time.sleep(5)
        if not data:
            print("download failed:", vid)
            continue
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if max(im.size) > 1400:
            im.thumbnail((1400, 1400))
        im.save(os.path.join(outdir, vid + ".webp"), "WEBP", quality=80, method=6)
        views.append({"id": vid, "year": y, "window": win, "image": "data/views/%s.webp" % vid, "title": A(ru, en, ka), "author": au, "note": note,
                      "license": m["lic"], "page": m["page"]})
        print("added", vid, im.size)
        time.sleep(2)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("[\n") else None, separators=None if raw.startswith("[\n") else (",", ":"))
    print("views:", len(views))


if __name__ == "__main__":
    main()
