"""Add three old pictures of Tbilisi that were published in Facebook groups to the window "Views" (site/data/views.json).
Taken: pre-1918 pictures whose photographer is unknown (more than 100 years old: public domain). NOT taken (2026-11-21): the Soviet-era pictures (sports palace
1961, the test of the Chelyuskintsy bridge, the tram on Kalinin St.) whose authors and rights are not given, and the trolleybus of 1962 that carries the mark
"Givi Kikvadze, National Archives of Georgia (c)": they need the permission of the owners of the rights.
The pictures: the Fedoseevskaya church (the upper, old picture of a collage 'then and now'), a postcard 'Golovinsky Avenue and the posting station',
a panorama of Erivan Square. The posts and their authors are in index.md of the folder of the archive.
Usage: python -X utf8 -P tools/add_fb_views.py <folder with the files of the archive>   (then python tools/make_view_thumbs.py)
The script is idempotent.
"""
import json
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def A(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


LICENSE = A("общественное достояние (снимок до 1918 года, автор неизвестен)", "public domain (made before 1918, photographer unknown)",
            "საზოგადოებრივი საკუთრება (გადაღებულია 1918 წლამდე, ავტორი უცნობია)")
LABEL = A("пост на Facebook", "post on Facebook", "პოსტი Facebook-ზე")
DATE_NOTE = A("Дата в источнике не названа; по надписи и виду старого снимка он сделан до 1918 года, на шкале показан приблизительно.",
              "The source gives no date; by the caption and the look of an old picture it was made before 1918, shown approximately on the timeline.",
              "წყარო თარიღს არ ასახელებს; წარწერისა და ძველი ფოტოს იერის მიხედვით ის 1918 წლამდეა გადაღებული, დროის სკალაზე მიახლოებით არის ნაჩვენები.")
ITEMS = [
    dict(id="fb_fedoseevskaya_1900", file="10_fedoseevskaya_church_1900_25741006405587497.jpg", crop=(0, 0, 526, 352), year=1900, frm=1895, window=20,
         page="https://www.facebook.com/photo/?fbid=25741006405587497&set=gm.1963455220874591",
         title=A("Федосеевская церковь в начале улицы Грибоедова, около 1900 года", "The Fedoseevskaya church at the beginning of Griboedov Street, about 1900",
                 "ფედოსეეველთა ეკლესია გრიბოედოვის ქუჩის დასაწყისში, დაახლოებით 1900 წელი"),
         author=A("автор снимка неизвестен; из поста Дмитрия Зверева в Facebook (2025)", "photographer unknown; from a Facebook post by Dmitry Zverev (2025)",
                  "ფოტოგრაფი უცნობია; დმიტრი ზვერევის Facebook-პოსტიდან (2025)"),
         note=A("Верхний, старый снимок коллажа «тогда и сейчас» из поста; нижний, современный кадр не используется. Год («около 1900») назван в посте.",
                "The upper, old picture of the collage 'then and now' of the post; the lower, modern picture is not used. The year ('about 1900') is named in the post.",
                "პოსტის კოლაჟის „მაშინ და ახლა“ ზედა, ძველი ფოტო; ქვედა, თანამედროვე კადრი არ გამოიყენება. წელი („დაახლოებით 1900“) პოსტშია დასახელებული.")),
    dict(id="fb_golovinsky_prospekt", file="13_golovinsky_prospekt_215467338787454.jpg", crop=None, year=1905, frm=1900, window=15,
         page="https://www.facebook.com/photo/?fbid=215467338787454&set=a.215467285454126",
         title=A("Головинский проспект и разгонная почта (открытка «Военно-Грузинская дорога. Тифлисъ»)", "Golovinsky Avenue and the posting station (a postcard 'Georgian Military Road. Tiflis')",
                 "გოლოვინის გამზირი და საფოსტო სადგური (ღია ბარათი „საქართველოს სამხედრო გზა. ტფილისი“)"),
         author=A("автор снимка неизвестен; из альбома «Старый Тифлисъ» Николая Демурчяна в Facebook (2015)", "photographer unknown; from the album 'Old Tiflis' of Nikolay Demourchyan on Facebook (2015)",
                  "ფოტოგრაფი უცნობია; ნიკოლაი დემურჩიანის ალბომიდან „ძველი ტფილისი“ Facebook-ზე (2015)"),
         note=A("Открытка с надписью «Военно-Грузинская дорога. Тифлисъ. Головинскiй проспектъ и разгонная почта». Проспект носил имя Головина до 1918 года. " + DATE_NOTE["ru"],
                "A postcard with the caption 'Georgian Military Road. Tiflis. Golovinsky Avenue and the posting station'. The avenue bore the name of Golovin until 1918. " + DATE_NOTE["en"],
                "ღია ბარათი წარწერით „საქართველოს სამხედრო გზა. ტფილისი. გოლოვინის გამზირი და საფოსტო სადგური“. გამზირი გოლოვინის სახელს 1918 წლამდე ატარებდა. " + DATE_NOTE["ka"])),
    dict(id="fb_erivan_square", file="20_erivan_square_tamamshev_kashveti_243041886029999.jpg", crop=None, year=1905, frm=1900, window=15,
         page="https://www.facebook.com/photo/?fbid=243041886029999&set=a.215467285454126",
         title=A("Эриванская площадь и караван-сарай Габриела Тамамшева; слева Дворцовая площадь, церкви Камоянц и Кашвети", "Erivan Square and the caravanserai of Gabriel Tamamshev; on the left the Palace Square and the churches Kamoyants and Kashveti",
                 "ერევნის მოედანი და გაბრიელ ტამამშევის ქარვასლა; მარცხნივ სასახლის მოედანი, კამოიანცისა და ქაშვეთის ეკლესიები"),
         author=A("автор снимка неизвестен; из альбома «Старый Тифлисъ» Николая Демурчяна в Facebook (2015)", "photographer unknown; from the album 'Old Tiflis' of Nikolay Demourchyan on Facebook (2015)",
                  "ფოტოგრაფი უცნობია; ნიკოლაი დემურჩიანის ალბომიდან „ძველი ტფილისი“ Facebook-ზე (2015)"),
         note=A("Подпись в источнике: «Тифлисъ. Эриванская площадь. В центре Караван-сарай Габриела Тамамшева. Слева Дворцовая площадь, церкви Камоянц (Святого Георгия) и Квашвети». " + DATE_NOTE["ru"],
                "Caption in the source: 'Tiflis. Erivan Square. In the centre the caravanserai of Gabriel Tamamshev. On the left the Palace Square, the churches Kamoyants (St. George) and Kvashveti'. " + DATE_NOTE["en"],
                "წარწერა წყაროში: „ტფილისი. ერევნის მოედანი. ცენტრში გაბრიელ ტამამშევის ქარვასლა. მარცხნივ სასახლის მოედანი, კამოიანცის (წმ. გიორგის) და კვაშვეთის ეკლესიები“. " + DATE_NOTE["ka"])),
]


def main():
    src = sys.argv[1]
    vp = os.path.join(ROOT, "site", "data", "views.json")
    views = json.load(open(vp, encoding="utf-8"))
    have = {v["id"] for v in views}
    outdir = os.path.join(ROOT, "site", "data", "views")
    added = 0
    for it in ITEMS:
        if it["id"] in have:                                  # the texts are refreshed (corrections of the translation), the picture stays
            for v in views:
                if v["id"] == it["id"]:
                    v.update({"title": it["title"], "author": it["author"], "note": it["note"], "license": LICENSE, "page_label": LABEL})
            continue
        im = Image.open(os.path.join(src, it["file"])).convert("RGB")
        if it["crop"]:
            im = im.crop(it["crop"])
        if max(im.size) > 1400:
            im.thumbnail((1400, 1400))
        im.save(os.path.join(outdir, it["id"] + ".webp"), "WEBP", quality=82)
        views.append({"id": it["id"], "year": it["year"], "from": it["frm"], "window": it["window"], "image": "data/views/%s.webp" % it["id"], "title": it["title"],
                      "author": it["author"], "note": it["note"], "license": LICENSE, "page": it["page"], "page_label": LABEL})
        added += 1
    views.sort(key=lambda v: v["year"])           # stable: the order of the others stays
    open(vp, "w", encoding="utf-8", newline="").write(json.dumps(views, ensure_ascii=False, indent=1))
    print("added:", added, "; views:", len(views))


if __name__ == "__main__":
    main()
