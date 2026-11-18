"""Add a selection of the project owner's photographs of Tbilisi (March 2010; copies from VKontakte, enlarged with SeedVR2 7B) to site/data/views.json.
Author: the owner of the project (credit and permission given by him). The place and the date are estimates (7 March - 4 April 2010).
Usage: python -X utf8 -P tools/add_vk2010_views.py <folder with the enlarged x_*.jpg> <table csv with n,file>
"""
import csv
import json
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def A(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


AUTHOR = A("Михаил Диденко", "Mikhail Didenko", "მიხეილ დიდენკო")
LICENSE = A("авторские права за автором; публикуется с его разрешения", "copyright of the author; published with his permission", "საავტორო უფლებები ეკუთვნის ავტორს; ქვეყნდება მისი ნებართვით")
NOTE = A("Фото автора проекта, март 2010 (копия из ВКонтакте), увеличено нейросетью SeedVR2 7B: на сильно увеличенных деталях возможны дорисованные элементы. Дата и место оценочные. К карте не привязано.",
         "A photograph by the author of the project, March 2010 (a copy from VKontakte), enlarged with the neural network SeedVR2 7B: strongly enlarged details may contain invented elements. The date and the place are estimates. Not tied to the map.",
         "პროექტის ავტორის ფოტო, 2010 წლის მარტი (ასლი „ВКонтакте“-დან), გადიდებულია SeedVR2 7B ნეირონული ქსელით: ძლიერად გადიდებულ დეტალებში შეიძლება იყოს მოგონილი ელემენტები. თარიღი და ადგილი სავარაუდოა. რუკას არ უკავშირდება.")
# (n in the table, id, ru, en, ka)
ITEMS = [
    (205, "vk2010_peace_bridge_aerial", "Мост Мира в стройке: стальной каркас у Куры, вид сверху, март 2010", "The Bridge of Peace under construction: the steel frame by the Kura, seen from above, March 2010", "მშვიდობის ხიდი მშენებლობისას: ფოლადის კარკასი მტკვართან, ხედი ზემოდან, 2010 წლის მარტი"),
    (291, "vk2010_peace_bridge_frame", "Мост Мира в стройке: стальная конструкция на берегу, март 2010", "The Bridge of Peace under construction: the steel structure on the bank, March 2010", "მშვიდობის ხიდი მშენებლობისას: ფოლადის კონსტრუქცია ნაპირზე, 2010 წლის მარტი"),
    (70, "vk2010_panorama_sameba", "Панорама Тбилиси: Самеба и старые крыши, март 2010", "A panorama of Tbilisi: Sameba and the old roofs, March 2010", "თბილისის პანორამა: სამების ტაძარი და ძველი სახურავები, 2010 წლის მარტი"),
    (99, "vk2010_narikala_wall", "Нарикала и город, вид со стены крепости, март 2010", "Narikala and the city, seen from the fortress wall, March 2010", "ნარიყალა და ქალაქი, ხედი ციხის კედლიდან, 2010 წლის მარტი"),
    (104, "vk2010_kura_cliffs", "Кура и скалы Старого города, март 2010", "The Kura and the cliffs of the Old Town, March 2010", "მტკვარი და ძველი ქალაქის კლდეები, 2010 წლის მარტი"),
    (82, "vk2010_metekhi", "Метехи и памятник Вахтангу Горгасали, март 2010", "Metekhi and the monument to Vakhtang Gorgasali, March 2010", "მეტეხი და ვახტანგ გორგასლის ძეგლი, 2010 წლის მარტი"),
    (117, "vk2010_rike_park", "Парк Рике до завершения благоустройства, март 2010", "Rike Park before its landscaping was finished, March 2010", "რიყის პარკი კეთილმოწყობის დასრულებამდე, 2010 წლის მარტი"),
    (61, "vk2010_avlabari_ruins", "Руины старых домов в Авлабари, март 2010", "The ruins of old houses in Avlabari, March 2010", "ძველი სახლების ნანგრევები ავლაბარში, 2010 წლის მარტი"),
    (90, "vk2010_kalantarov_house", "Дом Калантарова (1908): парадная лестница, март 2010", "The Kalantarov House (1908): the main staircase, March 2010", "კალანტაროვის სახლი (1908): მთავარი კიბე, 2010 წლის მარტი"),
    (148, "vk2010_sameba_night", "Ночной Тбилиси: подсвеченная Самеба, март 2010", "Tbilisi at night: the illuminated Sameba, March 2010", "ღამის თბილისი: განათებული სამების ტაძარი, 2010 წლის მარტი"),
]


def main():
    src, table = sys.argv[1], sys.argv[2]
    rows = {int(r["n"]): r for r in csv.DictReader(open(table, encoding="utf-8-sig"))}
    vp = os.path.join(ROOT, "site", "data", "views.json")
    raw = open(vp, encoding="utf-8").read()
    views = json.loads(raw)
    have = {v["id"] for v in views}
    outdir = os.path.join(ROOT, "site", "data", "views")
    for n, vid, ru, en, ka in ITEMS:
        if vid in have:
            continue
        f = os.path.join(src, rows[n]["file"])
        im = Image.open(f).convert("RGB")
        if max(im.size) > 1400:
            im.thumbnail((1400, 1400))
        im.save(os.path.join(outdir, vid + ".webp"), "WEBP", quality=80, method=6)
        views.append({"id": vid, "year": 2010, "from": 2010, "window": 5, "image": "data/views/%s.webp" % vid, "title": A(ru, en, ka),
                      "author": AUTHOR, "note": NOTE, "license": LICENSE})
        print("added", vid, im.size)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("[\n") else None, separators=None if raw.startswith("[\n") else (",", ":"))
    print("views:", len(views))


if __name__ == "__main__":
    main()
