"""Add a selection of the 1991-92 Tbilisi negatives published by Gabriel Chubinidze (Facebook post of 5 Dec 2023) to site/data/views.json.
The photographer is unknown; Chubinidze found the negatives at a flea market and had them scanned (Magnolia Film Lab). The owner of the project has
Chubinidze's (oral) permission to use the scans on the site; credit to Chubinidze and a link to the post are mandatory and are kept in every record.
Usage: python -X utf8 -P tools/add_chubinidze_views.py <folder with chub_NN.jpg>   (the folder holds the 80 images in the order of the post's viewer)
Also adds the event of 22.12.1991-6.01.1992 to data/history_events.json and site/data/history_events.json.
"""
import json
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
POST = "https://www.facebook.com/gchubinidze111/posts/pfbid02r4BvDdBs4FatqqpQtt7f6U4jfNe7Zo3cPYza329BupXXjXDAi2d5zeCR385X4wzkl"
PICK = [3, 4, 6, 8, 13, 19, 25, 29, 36, 42, 51, 52, 56, 59, 62, 63, 78, 79]


def A(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


AUTHOR = A("автор снимков неизвестен; негативы нашёл на барахолке и отсканировал Габриэль Чубинидзе (Gabriel Chubinidze), лаборатория Magnolia Film Lab",
           "the photographer is unknown; the negatives were found at a flea market and scanned by Gabriel Chubinidze, Magnolia Film Lab",
           "ფოტოგრაფი უცნობია; ნეგატივები ბაზრობაზე იპოვა და დაასკანერა გაბრიელ ჩუბინიძემ (Gabriel Chubinidze), Magnolia Film Lab")
NOTE = A("Кадр из негативов 1991-1992 годов (гражданская война в Тбилиси), опубликованных Габриэлем Чубинидзе. Публикуется с разрешения Г. Чубинидзе; при появлении автора снимков подпись будет дополнена. Места съёмки в посте не названы. К карте не привязан.",
         "A frame from negatives of 1991-1992 (the civil war in Tbilisi) published by Gabriel Chubinidze. Used with the permission of G. Chubinidze; the credit will be completed if the photographer is identified. The places are not named in the post. Not tied to the map.",
         "კადრი 1991-1992 წლების ნეგატივებიდან (სამოქალაქო ომი თბილისში), რომელიც გამოაქვეყნა გაბრიელ ჩუბინიძემ. გამოიყენება გ. ჩუბინიძის ნებართვით; ფოტოგრაფის დადგენის შემთხვევაში წარწერა შეივსება. გადაღების ადგილები პოსტში არ არის დასახელებული. რუკას არ უკავშირდება.")
LICENSE = A("используется с разрешения Г. Чубинидзе", "used with the permission of G. Chubinidze", "გამოიყენება გ. ჩუბინიძის ნებართვით")
LABEL = A("пост Габриэля Чубинидзе на Facebook", "Gabriel Chubinidze's Facebook post", "გაბრიელ ჩუბინიძის პოსტი Facebook-ზე")


def main():
    src = sys.argv[1]
    vp = os.path.join(ROOT, "site", "data", "views.json")
    raw = open(vp, encoding="utf-8").read()
    views = json.loads(raw)
    have = {v["id"] for v in views}
    outdir = os.path.join(ROOT, "site", "data", "views")
    for n in PICK:
        vid = "chubinidze_1991_%02d" % n
        if vid in have:
            continue
        im = Image.open(os.path.join(src, "chub_%02d.jpg" % n)).convert("RGB")
        if max(im.size) > 1400:
            im.thumbnail((1400, 1400))
        im.save(os.path.join(outdir, vid + ".webp"), "WEBP", quality=80, method=6)
        views.append({"id": vid, "year": 1992, "window": 8, "image": "data/views/%s.webp" % vid,
                      "title": A("Тбилиси, 1991-1992 (негативы из находки Г. Чубинидзе), кадр %d" % n, "Tbilisi, 1991-1992 (negatives found by G. Chubinidze), frame %d" % n, "თბილისი, 1991-1992 (გ. ჩუბინიძის მიერ ნაპოვნი ნეგატივები), კადრი %d" % n),
                      "author": AUTHOR, "note": NOTE, "license": LICENSE, "page": POST, "page_label": LABEL})
        print("added", vid, im.size)
    views.sort(key=lambda v: v["year"])
    json.dump(views, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("[\n") else None, separators=None if raw.startswith("[\n") else (",", ":"))
    print("views:", len(views))

    ev = {"year": 1991, "date": "22.12.1991-6.01.1992", "cat": "power",
          "ru": "Бои на проспекте Руставели (Тбилисская война): сторонники президента Гамсахурдиа против вооружённых групп Китовани, Иоселиани и Сигуа, осада здания парламента; Гамсахурдиа покидает страну, к власти приходит Военный совет",
          "en": "Fighting on Rustaveli Avenue (the Tbilisi War): supporters of President Gamsakhurdia against armed groups of Kitovani, Ioseliani and Sigua, a siege of the Parliament building; Gamsakhurdia leaves the country and a Military Council takes power",
          "ka": "ბრძოლები რუსთაველის გამზირზე (თბილისის ომი): პრეზიდენტ გამსახურდიას მომხრეები კიტოვანის, იოსელიანისა და სიგუას შეიარაღებული ჯგუფების წინააღმდეგ, პარლამენტის შენობის ალყა; გამსახურდია ქვეყანას ტოვებს, ხელისუფლებაში მოდის სამხედრო საბჭო",
          "src": ["https://en.wikipedia.org/wiki/1991%E2%80%931992_Georgian_coup_d%27%C3%A9tat", {"url": POST, "label": "Gabriel Chubinidze, Facebook: 1991-1992 negatives (photographer unknown)"}],
          "note": A("Хронология и участники по английской Википедии. Фотографии тех дней (негативы, найденные Габриэлем Чубинидзе) смотрите в панели «Виды», 1992 год.",
                    "Dates and parties as in English Wikipedia. Photographs of those days (negatives found by Gabriel Chubinidze) are in the 'Views' panel, 1992.",
                    "თარიღები და მხარეები ინგლისური ვიკიპედიის მიხედვით. იმ დღეების ფოტოები (გაბრიელ ჩუბინიძის მიერ ნაპოვნი ნეგატივები) იხილეთ პანელში „ხედები“, 1992 წელი.")}
    for p in ("data/history_events.json", "site/data/history_events.json"):
        fp = os.path.join(ROOT, p)
        raw = open(fp, encoding="utf-8").read()
        d = json.loads(raw)
        if not any(e.get("date") == ev["date"] for e in d["events"]):
            d["events"].append(json.loads(json.dumps(ev)))
        d["events"].sort(key=lambda e: e["year"])
        json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if raw.startswith("{\n") else None, separators=None if raw.startswith("{\n") else (",", ":"))
    print("event ok")


if __name__ == "__main__":
    main()
