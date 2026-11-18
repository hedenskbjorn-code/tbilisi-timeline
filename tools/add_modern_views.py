"""Add recent photographs of Tbilisi (2018-2025) from the project owner's Immich library to site/data/views.json (webp, no EXIF/GPS).
Credit: the owner of the project; the pictures show no identifiable people. The shown period is the five-year period of the picture ('from').
Usage: python -X utf8 -P tools/add_modern_views.py <folder with m<NN>.jpg>
"""
import json
import os
import sys

from PIL import Image, ImageOps

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def A(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


AUTHOR = A("Михаил Диденко", "Mikhail Didenko", "მიხეილ დიდენკო")
LICENSE = A("авторские права за автором; публикуется с его разрешения", "copyright of the author; published with his permission", "საავტორო უფლებები ეკუთვნის ავტორს; ქვეყნდება მისი ნებართვით")
NOTE = A("Фото автора проекта. Подпись и дата по данным съёмки; к карте не привязано.", "A photograph by the author of the project. The caption and the date are from the shooting data; not tied to the map.", "პროექტის ავტორის ფოტო. წარწერა და თარიღი გადაღების მონაცემებით; რუკას არ უკავშირდება.")
# (file n, id, year, ru, en, ka)
ITEMS = [
    (2, "mod_2018_kura", 2018, "Набережная Куры и Самеба вдали, октябрь 2018", "The Kura embankment with Sameba in the distance, October 2018", "მტკვრის სანაპირო და შორს სამების ტაძარი, 2018 წლის ოქტომბერი"),
    (16, "mod_2019_balconies", 2019, "Дом с кружевными деревянными балконами, июль 2019", "A house with lace-like wooden balconies, July 2019", "სახლი ხის ჩუქურთმიანი აივნებით, 2019 წლის ივლისი"),
    (17, "mod_2019_panorama", 2019, "Панорама Тбилиси с горы, июль 2019", "A panorama of Tbilisi from the hill, July 2019", "თბილისის პანორამა მთიდან, 2019 წლის ივლისი"),
    (11, "mod_2019_evening", 2019, "Вечер над крышами города, май 2019", "Evening over the roofs of the city, May 2019", "საღამო ქალაქის სახურავებზე, 2019 წლის მაისი"),
    (25, "mod_2020_narikala_view", 2020, "Старый Тбилиси, Кура и мост Метехи, вид с Нарикала, февраль 2020", "Old Tbilisi, the Kura and the Metekhi bridge seen from Narikala, February 2020", "ძველი თბილისი, მტკვარი და მეტეხის ხიდი ნარიყალადან, 2020 წლის თებერვალი"),
    (29, "mod_2020_peace_bridge", 2020, "Панорама Тбилиси с мостом Мира, февраль 2020", "A panorama of Tbilisi with the Bridge of Peace, February 2020", "თბილისის პანორამა მშვიდობის ხიდით, 2020 წლის თებერვალი"),
    (34, "mod_2022_snow", 2022, "Заснеженные крыши и Самеба, март 2022", "Snow-covered roofs and Sameba, March 2022", "თოვლიანი სახურავები და სამების ტაძარი, 2022 წლის მარტი"),
    (44, "mod_2023_gorgasali", 2023, "Памятник Вахтангу Горгасали в сумерках, апрель 2023", "The monument to Vakhtang Gorgasali at dusk, April 2023", "ვახტანგ გორგასლის ძეგლი ბინდისას, 2023 წლის აპრილი"),
    (52, "mod_2024_kura_narikala", 2024, "Набережная Куры и холм Нарикала, январь 2024", "The Kura embankment and the Narikala hill, January 2024", "მტკვრის სანაპირო და ნარიყალას გორა, 2024 წლის იანვარი"),
    (64, "mod_2025_panorama", 2025, "Панорама Тбилиси с горы, февраль 2025", "A panorama of Tbilisi from the hill, February 2025", "თბილისის პანორამა მთიდან, 2025 წლის თებერვალი"),
    (68, "mod_2025_rocks", 2025, "Скалы над Старым городом, апрель 2025", "Rocks above the Old Town, April 2025", "კლდეები ძველი ქალაქის ზემოთ, 2025 წლის აპრილი"),
    (76, "mod_2025_kura_towers", 2025, "Кура и башни нового города, октябрь 2025", "The Kura and the towers of the new city, October 2025", "მტკვარი და ახალი ქალაქის კოშკები, 2025 წლის ოქტომბერი"),
    (77, "mod_2025_sunset", 2025, "Закат над Тбилиси, октябрь 2025", "Sunset over Tbilisi, October 2025", "მზის ჩასვლა თბილისზე, 2025 წლის ოქტომბერი"),
    (78, "mod_2025_sameba_night", 2025, "Вечерний Тбилиси: подсвеченная Самеба, ноябрь 2025", "Tbilisi in the evening: the illuminated Sameba, November 2025", "საღამოს თბილისი: განათებული სამების ტაძარი, 2025 წლის ნოემბერი"),
]


def bucket(y):
    s = (y // 5) * 5
    return s, s + 5


def main():
    src = sys.argv[1]
    vp = os.path.join(ROOT, "site", "data", "views.json")
    raw = open(vp, encoding="utf-8").read()
    views = json.loads(raw)
    have = {v["id"] for v in views}
    outdir = os.path.join(ROOT, "site", "data", "views")
    for n, vid, y, ru, en, ka in ITEMS:
        if vid in have:
            continue
        im = ImageOps.exif_transpose(Image.open(os.path.join(src, "m%02d.jpg" % n))).convert("RGB")
        if max(im.size) > 1600:
            im.thumbnail((1600, 1600))
        im.save(os.path.join(outdir, vid + ".webp"), "WEBP", quality=80, method=6)     # no EXIF is kept
        f, e = bucket(y)
        views.append({"id": vid, "year": y, "from": f, "window": e - y, "image": "data/views/%s.webp" % vid, "title": A(ru, en, ka), "author": AUTHOR, "note": NOTE, "license": LICENSE})
        print("added", vid, im.size, f, e)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("[\n") else None, separators=None if raw.startswith("[\n") else (",", ":"))
    print("views:", len(views))


if __name__ == "__main__":
    main()
