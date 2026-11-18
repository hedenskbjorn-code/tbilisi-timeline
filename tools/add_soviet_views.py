"""Add public-domain and openly licensed photographs of Tbilisi from the Soviet and early post-Soviet years (Wikimedia Commons) to site/data/views.json,
3-5 per five-year period where Commons has suitable files. The licence is the one given in the Commons metadata (public domain, CC0, CC BY, CC BY-SA);
author, licence and the Commons page are stored in every record and shown in the viewer; the images are stored locally as webp (reduced).
The photos are NOT tied to a point on the map. Also trims the Chubinidze selection to five frames.
Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT; PH_META = a json list made from the category listing (title, lic, artist, thumb, page, ...).
Usage: python -u -X utf8 -P tools/add_soviet_views.py
"""
import io
import json
import os
import re
import time
import urllib.error
import urllib.request

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
c = os.environ.get("WIKIMEDIA_CONTACT", "")
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % (("; contact: " + c) if c else "")


def A(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


UN = A("автор неизвестен", "unknown author", "ავტორი უცნობია")
NOTE_PD = A("Фотография из Wikimedia Commons (общественное достояние); подпись и год по описанию на Commons. К карте не привязана.",
            "Photograph from Wikimedia Commons (public domain); the caption and the year are as given on Commons. Not tied to the map.",
            "ფოტო Wikimedia Commons-იდან (საჯარო სივრცე); წარწერა და წელი Commons-ის აღწერის მიხედვით. რუკას არ უკავშირდება.")


def note_cc(lic):
    return A("Фотография из Wikimedia Commons, лицензия %s: указание автора и ссылка на страницу файла обязательны; копия уменьшена. Подпись и год по описанию на Commons. К карте не привязана." % lic,
             "Photograph from Wikimedia Commons, licence %s: the credit to the author and the link to the file page are required; the copy is reduced in size. The caption and the year are as given on Commons. Not tied to the map." % lic,
             "ფოტო Wikimedia Commons-იდან, ლიცენზია %s: ავტორის მითითება და ფაილის გვერდის ბმული სავალდებულოა; ასლი შემცირებულია. წარწერა და წელი Commons-ის აღწერის მიხედვით. რუკას არ უკავშირდება." % lic)


# (start of the Commons file name, id, year, window, ru, en, ka, author override or None)
ITEMS = [
    ("Red Army in Tiflis Feb 25 1921", "red_army_1921", 1921, 6, "Вступление 11-й Красной армии в Тбилиси, 25 февраля 1921", "The 11th Red Army enters Tbilisi, 25 February 1921", "მე-11 წითელი არმიის შესვლა თბილისში, 1921 წლის 25 თებერვალი", None),
    ("Бойцы 11-й Красной армии в Тбилиси", "red_army_soldiers_1921", 1921, 6, "Бойцы 11-й Красной армии в Тбилиси, 1921", "Soldiers of the 11th Red Army in Tbilisi, 1921", "მე-11 წითელი არმიის მებრძოლები თბილისში, 1921", None),
    ("Second International delegation in Tbilisi", "klar_second_international_1920", 1920, 6, "Делегация II Интернационала в Тбилиси, сентябрь 1920 (Э. Клар)", "The Second International delegation in Tbilisi, September 1920 (E. Klar)", "II ინტერნაციონალის დელეგაცია თბილისში, 1920 წლის სექტემბერი (ე. კლარი)", A("Эдуард Клар", "Eduard Klar", "ედუარდ კლარი")),
    ("No-nb bldsa 6d026", "nansen_view_1925", 1925, 6, "Вид на город, 1925 (снимок из поездки Ф. Нансена)", "A view of the city, 1925 (a picture from Fridtjof Nansen's journey)", "ქალაქის ხედი, 1925 (ფ. ნანსენის მოგზაურობის ფოტო)", A("Фритьоф Нансен (по записи Национальной библиотеки Норвегии)", "Fridtjof Nansen (as recorded by the National Library of Norway)", "ფრიტიოფ ნანსენი (ნორვეგიის ეროვნული ბიბლიოთეკის ჩანაწერით)")),
    ("No-nb bldsa 6d037", "nansen_fortress_1925", 1925, 6, "Вид на юг со старой «персидской» крепостью, 1925 (снимок из поездки Ф. Нансена)", "A view to the south with the old 'Persian' fortress, 1925 (a picture from Nansen's journey)", "ხედი სამხრეთით ძველი „სპარსული“ ციხით, 1925 (ნანსენის მოგზაურობის ფოტო)", A("Фритьоф Нансен (по записи Национальной библиотеки Норвегии)", "Fridtjof Nansen (as recorded by the National Library of Norway)", "ფრიტიოფ ნანსენი (ნორვეგიის ეროვნული ბიბლიოთეკის ჩანაწერით)")),
    ("No-nb bldsa 6d038", "nansen_gate_1925", 1925, 6, "Проход у базаров, 1925 (снимок из поездки Ф. Нансена)", "A gate near the bazaars, 1925 (a picture from Nansen's journey)", "კარიბჭე ბაზრების მახლობლად, 1925 (ნანსენის მოგზაურობის ფოტო)", A("Фритьоф Нансен (по записи Национальной библиотеки Норвегии)", "Fridtjof Nansen (as recorded by the National Library of Norway)", "ფრიტიოფ ნანსენი (ნორვეგიის ეროვნული ბიბლიოთეკის ჩანაწერით)")),
    ("Old Tbilisi, Oskar Shmerling 8", "schmerling_old_tbilisi_1928", 1928, 6, "Старый Тбилиси, О. Шмерлинг (1928)", "Old Tbilisi, O. Schmerling (1928)", "ძველი თბილისი, ო. შმერლინგი (1928)", A("Оскар Шмерлинг", "Oskar Schmerling", "ოსკარ შმერლინგი")),
    ("Խոջիվանքի գերեզմանատուն, Թիֆլիս - Khojivank Armenian Pantheon, Tiflis (1934) 01", "khojivank_1934", 1934, 4, "Армянское кладбище Ходживанк, 1934", "The Armenian Khojivank cemetery, 1934", "ხოჯივანქის სომხური სასაფლაო, 1934", None),
    ("Tbilisi Tuberculosis Institute", "tb_institute_1930s", 1932, 6, "Здание Тбилисского института туберкулёза (1930-е)", "The building of the Tbilisi Tuberculosis Institute (1930s)", "თბილისის ტუბერკულოზის ინსტიტუტის შენობა (1930-იანი წწ.)", None),
    ("Խոջիվանքի գերեզմանատուն, Թիֆլիս - Khojivank Armenian Pantheon, Tiflis (1935) 02", "khojivank_1935_02", 1935, 4, "Армянское кладбище Ходживанк, 1935", "The Armenian Khojivank cemetery, 1935", "ხოჯივანქის სომხური სასაფლაო, 1935", None),
    ("Խոջիվանքի գերեզմանատուն, Թիֆլիս - Khojivank Armenian Pantheon, Tiflis (1935) 06", "khojivank_1935_06", 1935, 4, "Армянское кладбище Ходживанк (другой вид), 1935", "The Armenian Khojivank cemetery (another view), 1935", "ხოჯივანქის სომხური სასაფლაო (სხვა ხედი), 1935", None),
    ("Խոջիվանքի Սուրբ Աստվածածին եկեղեցի", "khojivank_church", 1936, 4, "Армянская церковь Св. Богородицы в Ходживанке (до 1936-1938)", "The Armenian Church of the Holy Mother of God at Khojivank (before 1936-1938)", "ხოჯივანქის ღვთისმშობლის სომხური ეკლესია (1936-1938 წლებამდე)", None),
    ("Tram type M Tbilisi", "tram_m_1935", 1935, 4, "Трамвай типа М в Тбилиси, 1935", "A type M tram in Tbilisi, 1935", "M ტიპის ტრამვაი თბილისში, 1935", None),
    ("1938-InstituteMarxEngelsLenin Building.jpg", "institute_mel_1938", 1938, 4, "Здание Института Маркса - Энгельса - Ленина, 1938", "The building of the Marx-Engels-Lenin Institute, 1938", "მარქსის-ენგელსის-ლენინის ინსტიტუტის შენობა, 1938", None),
    ("Tbilisi circus", "circus_1940", 1940, 5, "Тбилисский государственный цирк, 1940", "The Tbilisi State Circus, 1940", "თბილისის სახელმწიფო ცირკი, 1940", None),
    ("Tbilisi State Conservatoire-1940", "conservatoire_1940", 1940, 5, "Преподаватели и студенты Тбилисской консерватории, 1940", "Staff and students of the Tbilisi Conservatoire, 1940", "თბილისის კონსერვატორიის პედაგოგები და სტუდენტები, 1940", None),
    ("Georgian Academy of Sciences (1950)-1", "building_1950_1", 1950, 5, "Строительство административного здания (в названии файла: Академия наук Грузии), 1950", "Construction of an administrative building (the file is titled Georgian Academy of Sciences), 1950", "ადმინისტრაციული შენობის მშენებლობა (ფაილის სათაური: საქართველოს მეცნიერებათა აკადემია), 1950", None),
    ("Georgian Academy of Sciences (1950)-2", "building_1950_2", 1950, 5, "Строительство административного здания, другой кадр, 1950", "Construction of an administrative building, another frame, 1950", "ადმინისტრაციული შენობის მშენებლობა, სხვა კადრი, 1950", None),
    ("Mirtskhulava on Lenin Square", "lenin_square_1953", 1953, 5, "Площадь Ленина, 1953 (А. Мирцхулава на площади)", "Lenin Square, 1953 (A. Mirtskhulava on the square)", "ლენინის მოედანი, 1953 (ა. მირცხულავა მოედანზე)", None),
    ("1956 Georgian demonstrations in Tbilisi", "demo_1956", 1956, 5, "Толпа у памятника Сталину, март 1956", "A crowd at the statue of Stalin, March 1956", "ხალხი სტალინის ძეგლთან, 1956 წლის მარტი", None),
    ("Khruschev's train in Tbilisi", "khrushchev_train_1956", 1956, 5, "Встречающие поезд Н. С. Хрущёва в Тбилиси, 1956", "People meeting N. S. Khrushchev's train in Tbilisi, 1956", "ნ. ს. ხრუშჩოვის მატარებლის დახვედრა თბილისში, 1956", None),
    ("Galaktion híd. Fortepan 53527", "fortepan_galaktion_1960", 1960, 5, "Мост Галактиона (Верийский), 1960 (Fortepan 53527)", "The Galaktion Bridge (the Vera bridge), 1960 (Fortepan 53527)", "გალაკტიონის (ვერის) ხიდი, 1960 (Fortepan 53527)", A("Fortepan, ID 53527", "Fortepan, ID 53527", "Fortepan, ID 53527")),
    ("Rusztaveli sugárút a Hotel Mariott (egykor Hotel Majestic) előtt. Fortepan 53528", "fortepan_rustaveli_1960", 1960, 5, "Проспект Руставели у гостиницы «Мажестик» (ныне «Мариотт»), 1960 (Fortepan 53528)", "Rustaveli Avenue by the Hotel Majestic (now the Marriott), 1960 (Fortepan 53528)", "რუსთაველის გამზირი სასტუმრო „მაჟესტიკთან“ (ახლანდელი „მარიოტი“), 1960 (Fortepan 53528)", A("Fortepan, ID 53528", "Fortepan, ID 53528", "Fortepan, ID 53528")),
    ("468 - Panorama of the city of Tbilisi", "dupakier_panorama_1964", 1964, 5, "Панорама Тбилиси, 1964 (Ж. Дюпакье)", "A panorama of Tbilisi, 1964 (J. Dupakier)", "თბილისის პანორამა, 1964 (ჟ. დიუპაკიე)", A("Жак Дюпакье", "Jacques Dupakier", "ჟაკ დიუპაკიე")),
    ("483 - Kura river Tbilisi", "dupakier_kura_1964", 1964, 5, "Кура в Тбилиси, 1964 (Ж. Дюпакье)", "The Kura in Tbilisi, 1964 (J. Dupakier)", "მტკვარი თბილისში, 1964 (ჟ. დიუპაკიე)", A("Жак Дюпакье", "Jacques Dupakier", "ჟაკ დიუპაკიე")),
    ("488 - Monument to VI Lenin Tbilisi", "dupakier_lenin_1964", 1964, 5, "Памятник Ленину на площади Ленина (ныне площадь Свободы), 1964 (Ж. Дюпакье)", "The monument to Lenin on Lenin Square (today Freedom Square), 1964 (J. Dupakier)", "ლენინის ძეგლი ლენინის მოედანზე (დღევანდელი თავისუფლების მოედანი), 1964 (ჟ. დიუპაკიე)", A("Жак Дюпакье", "Jacques Dupakier", "ჟაკ დიუპაკიე")),
    ("View of Tbilisi, Georgian SSR. Viktor Yershov. 1971", "yershov_view_1971", 1971, 5, "Вид Тбилиси, 1971 (В. Ершов)", "A view of Tbilisi, 1971 (V. Yershov)", "თბილისის ხედი, 1971 (ვ. ერშოვი)", A("Виктор Ершов", "Viktor Yershov", "ვიქტორ ერშოვი")),
    ("At a tram stop. Tbilisi", "yershov_tram_stop_1971", 1971, 5, "На трамвайной остановке, 1971 (В. Ершов)", "At a tram stop, 1971 (V. Yershov)", "ტრამვაის გაჩერებაზე, 1971 (ვ. ერშოვი)", A("Виктор Ершов", "Viktor Yershov", "ვიქტორ ერშოვი")),
    ("Tbilisi, Georgian SSR. Viktor Yershov. 1971", "yershov_street_1971", 1971, 5, "Улица Тбилиси, 1971 (В. Ершов)", "A street in Tbilisi, 1971 (V. Yershov)", "ქუჩა თბილისში, 1971 (ვ. ერშოვი)", A("Виктор Ершов", "Viktor Yershov", "ვიქტორ ერშოვი")),
    ("Metekhi church, Georgia. May 1973", "avdoyan_metekhi_1973", 1973, 5, "Церковь Метехи, май 1973 (Л. Авдоян)", "Metekhi church, May 1973 (L. Avdoyan)", "მეტეხის ეკლესია, 1973 წლის მაისი (ლ. ავდოიანი)", A("Левон Авдоян", "Levon Avdoyan", "ლევონ ავდოიანი")),
    ("1975г. Вид с крепости 03", "mskhalaya_view_1975", 1975, 5, "Вид с крепости, 1975 (А. Мсхалая)", "A view from the fortress, 1975 (A. Mskhalaia)", "ხედი ციხიდან, 1975 (ა. მსხალაია)", A("Андрей Мсхалая", "Andrei Mskhalaia", "ანდრია მსხალაია")),
    ("A female traffic-controller", "yershov_traffic_1975", 1975, 5, "Регулировщица на улице Тбилиси, август 1975 (В. Ершов)", "A woman traffic controller in Tbilisi, August 1975 (V. Yershov)", "მოძრაობის მარეგულირებელი ქალი თბილისში, 1975 წლის აგვისტო (ვ. ერშოვი)", A("Виктор Ершов", "Viktor Yershov", "ვიქტორ ერშოვი")),
    ("1979 Tbilisi City hall", "city_hall_1979", 1979, 5, "Здание горсовета и памятник Ленину, 1979 (Б. Мимиц)", "Tbilisi City Hall and the Lenin monument, 1979 (B. Miemietz)", "თბილისის საქალაქო საბჭოს შენობა და ლენინის ძეგლი, 1979 (ბ. მიმიეცი)", A("Бербель Мимиц", "Bärbel Miemietz", "ბერბელ მიმიეცი")),
    ("At the Polytechnic Institute of Georgia", "yershov_polytech_1970s", 1976, 5, "В Политехническом институте Грузии, 1970-е (В. Ершов)", "At the Polytechnic Institute of Georgia, 1970s (V. Yershov)", "საქართველოს პოლიტექნიკურ ინსტიტუტში, 1970-იანი წწ. (ვ. ერშოვი)", A("Виктор Ершов", "Viktor Yershov", "ვიქტორ ერშოვი")),
    ("Kakheti Highway in Tbilisi ca 1982", "kakheti_highway_1982", 1982, 5, "Кахетинское шоссе в Тбилиси, около 1982 (JG)", "The Kakheti highway in Tbilisi, about 1982 (JG)", "კახეთის გზატკეცილი თბილისში, დაახლოებით 1982 (JG)", A("JG", "JG", "JG")),
    ("Misc Shota Kavlashvili Old Tbilisi Model", "kavlashvili_model_1980", 1980, 5, "Ш. Кавлашвили у макета застройки Старого Тбилиси, около 1980", "Shota Kavlashvili with a model of new construction in Old Tbilisi, about 1980", "შ. ქავლაშვილი ძველი თბილისის მშენებლობის მაკეტთან, დაახლოებით 1980", None),
    ("Tiflis1987", "tiflis_1987", 1987, 5, "Тбилиси, весна 1987", "Tbilisi, spring 1987", "თბილისი, 1987 წლის გაზაფხული", None),
    ("Georgien 1987 005", "georgien_1987_005", 1987, 5, "Улица в Тбилиси, 1987", "A street in Tbilisi, 1987", "ქუჩა თბილისში, 1987", None),
    ("Georgien 1987 006", "georgien_1987_006", 1987, 5, "Ботаническая улица, Тбилиси, 1987", "Botanicheskaya Street, Tbilisi, 1987", "ბოტანიკური ქუჩა, თბილისი, 1987", None),
    ("Tbilisi from Hotel Intourist 1988", "intourist_view_1988", 1988, 5, "Вид из гостиницы «Интурист», 1988 (Т. Нирман)", "A view from the Intourist Hotel, 1988 (T. Niermann)", "ხედი სასტუმრო „ინტურისტიდან“, 1988 (ტ. ნირმანი)", A("Тилль Нирман", "Till Niermann", "ტილ ნირმანი")),
    ("Tyflis - Tbilisi - Sept.1988", "wolinski_1988", 1988, 5, "Тбилиси, сентябрь 1988 (А. Волински)", "Tbilisi, September 1988 (A. Wolinski)", "თბილისი, 1988 წლის სექტემბერი (ა. ვოლინსკი)", A("Анджей Волински", "Andrzej Wolinski", "ანჯეი ვოლინსკი")),
    ("The central market in Tbilisi", "widmann_market_1996", 1996, 5, "Центральный рынок Тбилиси, ноябрь 1996 (Т. Видман)", "The central market in Tbilisi, November 1996 (T. Widmann)", "თბილისის ცენტრალური ბაზარი, 1996 წლის ნოემბერი (თ. ვიდმანი)", A("Томас Видман", "Thomas Widmann", "თომას ვიდმანი")),
    ("Trolleybus and Coca-Cola", "widmann_trolleybus_1997", 1997, 5, "Троллейбус у киоска Coca-Cola, март 1997 (Т. Видман)", "A trolleybus and a Coca-Cola stand, March 1997 (T. Widmann)", "ტროლეიბუსი და Coca-Cola-ს ჯიხური, 1997 წლის მარტი (თ. ვიდმანი)", A("Томас Видман", "Thomas Widmann", "თომას ვიდმანი")),
    ("Archil Mishveladze Street, 1997", "mishveladze_1997", 1997, 5, "Улица Арчила Мишвеладзе, 1997 (viralbus)", "Archil Mishveladze Street, 1997 (viralbus)", "არჩილ მიშველაძის ქუჩა, 1997 (viralbus)", A("viralbus", "viralbus", "viralbus")),
    ("A monument in Tbilisi", "galaktion_monument_1997", 1997, 5, "Памятник Галактиону Табидзе в Ваке, июнь 1997 (Т. Видман)", "The monument to Galaktion Tabidze in Vake, June 1997 (T. Widmann)", "გალაკტიონ ტაბიძის ძეგლი ვაკეში, 1997 წლის ივნისი (თ. ვიდმანი)", A("Томас Видман", "Thomas Widmann", "თომას ვიდმანი")),
]
OK_LIC = ("Public domain", "No restrictions", "CC0", "CC BY 2.0", "CC BY 3.0", "CC BY 4.0", "CC BY-SA 2.0", "CC BY-SA 3.0", "CC BY-SA 4.0", "Attribution")
KEEP_CHUB = {3, 13, 25, 59, 62}


def main():
    meta = json.load(open(os.environ["PH_META"], encoding="utf-8"))
    vp = os.path.join(ROOT, "site", "data", "views.json")
    raw = open(vp, encoding="utf-8").read()
    views = json.loads(raw)
    outdir = os.path.join(ROOT, "site", "data", "views")
    # trim the Chubinidze selection
    keep = []
    for v in views:
        m = re.match(r"chubinidze_1991_(\d+)$", v["id"])
        if m and int(m.group(1)) not in KEEP_CHUB:
            f = os.path.join(outdir, v["id"] + ".webp")
            if os.path.exists(f):
                os.remove(f)
            print("removed", v["id"])
            continue
        keep.append(v)
    views = keep
    have = {v["id"] for v in views}
    for start, vid, y, win, ru, en, ka, au in ITEMS:
        if vid in have:
            continue
        cand = [m for m in meta if m["title"][5:].startswith(start)]
        if not cand:
            print("not in listing:", start)
            continue
        m = cand[0]
        if m["lic"] not in OK_LIC:
            print("licence not accepted, skipped:", m["title"], m["lic"])
            continue
        thumb = m["thumb"]
        if "/thumb/" in thumb:
            thumb = re.sub(r"/\d+px-", "/960px-", thumb)
        data = None
        for k in range(6):
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
        if max(im.size) > 1100:
            im.thumbnail((1100, 1100))
        im.save(os.path.join(outdir, vid + ".webp"), "WEBP", quality=78, method=6)
        if au is None:
            a = m["artist"].strip()
            au_ = UN if (not a or re.search(r"unknown|not indicated|anonym", a, re.I)) else A(a, a, a)
        else:
            au_ = au
        pd = m["lic"] in ("Public domain", "No restrictions", "CC0")
        views.append({"id": vid, "year": y, "window": win, "image": "data/views/%s.webp" % vid, "title": A(ru, en, ka), "author": au_,
                      "note": NOTE_PD if pd else note_cc(m["lic"]), "license": m["lic"], "page": m["page"]})
        print("added", vid, im.size, m["lic"])
        time.sleep(2)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("[\n") else None, separators=None if raw.startswith("[\n") else (",", ":"))
    print("views:", len(views))


if __name__ == "__main__":
    main()
