"""Put map points on the battles, sieges, storms and captures of the timeline that had none (site/data/history_events.json).
Each point is a place named by the sources of the event; where the sources name no particular place, the point is the city as a whole
(the coordinates of the page 'Tbilisi' on English Wikipedia). The Isani palace (1184, 1210) is put at the church of Metekhi, built on its territory (the chronicle). Events whose place is not established by any source (Rakhsi 1118, Botora 1120,
Khunan 1222) and treaties or states of rule (1243, 1477) are left without a point on purpose.
Coordinates were read from English Wikipedia and Wikidata through the API on 2026-11-21.
The script is idempotent: an event that already has a point is not touched.
Usage: python -X utf8 -P tools/add_battle_places.py
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PATH = os.path.join(ROOT, "site", "data", "history_events.json")


def wp(page, lat, lng, ru, en, ka, zoom):
    return {"lng": lng, "lat": lat, "zoom": zoom, "ru": ru, "en": en, "ka": ka,
            "src": "coordinates of the page '%s' on English Wikipedia" % page}


CITY = wp("Tbilisi", 41.7225, 44.7925, "Тбилиси (город целиком)", "Tbilisi (the whole city)", "თბილისი (მთელი ქალაქი)", 13.2)
CITY["src"] = "coordinates of the page 'Tbilisi' on English Wikipedia (the city as a whole: the sources of the event name no particular place)"
NARIKALA = {"lng": 44.80861111, "lat": 41.68777778, "zoom": 16, "ru": "Крепость Нарикала", "en": "Narikala fortress",
            "src": "coordinates of the page 'Narikala' on English Wikipedia", "ka": "ნარიყალას ციხე"}
KRTSANISI = {"lng": 44.90277778, "lat": 41.60972222, "zoom": 14, "ru": "Крцаниси", "en": "Krtsanisi",
             "src": "coordinates of the page 'Battle of Krtsanisi' on English Wikipedia", "ka": "კრწანისი"}
ISANI = {"lng": 44.81118, "lat": 41.69013, "zoom": 16,
         "ru": "Метехи (Исанский дворец; место приблизительно)",
         "en": "Metekhi (the Isani palace; the place is approximate)",
         "ka": "მეტეხი (ისნის სასახლე; ადგილი მიახლოებითია)",
         "src": "coordinates of the page 'Metekhi Church' on English Wikipedia; by Kartlis Tskhovreba (Russian translation, 2008) King Dimitri 'built in the palace of Isani a monastery for the Metekhi "
                "Mother of God', so Metekhi stands on the territory of the Isani palace (commentary 22: Metekhi is a church on the rocky bank of the Kura; commentary 198: Isani is a district on the left bank); "
                "the limits of the palace are not known"}
SAINGILO = {"lng": 46.716666666667, "lat": 41.55, "zoom": 9.5,
            "ru": "Саингило (область; место боя приблизительно)",
            "en": "Saingilo (a region; the place of the battle is approximate)",
            "ka": "საინგილო (მხარე; ბრძოლის ადგილი მიახლოებითია)",
            "src": "coordinates of the Wikidata item 'Zaqatala District' (Q147553): a point in the middle of the region Saingilo, which the commentary of "
                   "Kartlis Tskhovreba (Russian translation, 2008, comm. 62) names as the place of Ertsukhi; the exact place is not known"}

# (year, beginning of the Russian text) -> point
PLACES = [
    (627, "Тбилиси разграблен союзными", CITY),
    (764, "Тбилиси разграблен хазарами", CITY),
    (853, "Арабский полководец Буга", CITY),
    (1064, "Алп-Арслан (1064)", CITY),
    (1068, "Тбилиси разграблен сельджуками", CITY),
    (1104, "Битва при Эрцухи", SAINGILO),
    (1184, "Умирает царь Георгий III", ISANI),               # the palace of Isani (Tamar), see ISANI
    (1210, "Закарий и Иване Мхаргрдзели", ISANI),
    (1227, "Тбилиси освобождён от хорезмийцев", CITY),
    (1238, "Тбилиси захвачен монголами", CITY),
    (1297, "Монгольский полководец Хутлушах", CITY),
    (1440, "Джахан-шах вторгается", CITY),
    (1522, "Шах Исмаил I вторгается", CITY),
    (1541, "Шах Тахмасп I посылает", NARIKALA),            # the sources: the fortress was handed over to the shah
    (1556, "При восшествии на царство Симона I", CITY),
    (1578, "Тбилиси захвачен османами", CITY),
    (1723, "Тбилиси переходит к османам", CITY),
    (1795, "Накануне нашествия Ага-Мохаммед-хана", KRTSANISI),  # the field of Krtsanisi and the entrance to Sololaki from the Kojori road
    (1921, "11-я Красная армия", CITY),
    (1992, "Гражданская война: сторонники", wp("Zugdidi", 42.50833333, 41.86666667, "Зугдиди", "Zugdidi", "ზუგდიდი", 13)),
    (1992, "Война в Абхазии", wp("Sukhumi", 43.0036, 41.0192, "Сухуми (Сухум)", "Sukhumi", "სოხუმი", 13)),
    (2008, "Война в Грузии", wp("Tskhinvali", 42.225, 43.97, "Цхинвали", "Tskhinvali", "ცხინვალი", 13)),
]

NOTES = [  # (year, beginning of the Russian text, language, old phrase, new phrase)
    (1104, "Битва при Эрцухи", "ru", "У статьи нет координат, булавки нет.", "У статьи нет координат."),
    (1104, "Битва при Эрцухи", "ru", "поэтому булавки нет.",
     "булавка стоит в середине области Саингило (точка Закатальского района по Викиданным) и показывает место приблизительно: где именно был Эрцух, неизвестно."),
    (1104, "Битва при Эрцухи", "en", "The article has no coordinates, so there is no pin.", "The article has no coordinates."),
    (1104, "Битва при Эрцухи", "en", "so there is no pin.",
     "the pin is in the middle of the region Saingilo (a point of Zaqatala District by Wikidata) and shows the place only approximately: where exactly Ertsukhi was is not known."),
    (1104, "Битва при Эрцухи", "ka", "სტატიას კოორდინატები არ აქვს, ამიტომ ნიშანი არ არის.", "სტატიას კოორდინატები არ აქვს."),
    (1104, "Битва при Эрцухи", "ka", "ათავსებს, ამიტომ ნიშანი არ არის.",
     "ათავსებს; ნიშანი საინგილოს მხარის შუაშია (ზაქათალის რაიონის წერტილი Wikidata-ს მიხედვით) და ადგილს მიახლოებით აჩვენებს: ერწუხი ზუსტად სად იყო, უცნობია."),
    (1210, "Закарий и Иване Мхаргрдзели", "ru", "Булавки нет: место в Исани не установлено.",
     "Булавка стоит на городе в целом: место дворца в Исани не установлено."),
    (1210, "Закарий и Иване Мхаргрдзели", "en", "There is no pin: the place in Isani is not established.",
     "The pin is on the city as a whole: the place of the palace in Isani is not established."),
    (1210, "Закарий и Иване Мхаргрдзели", "ka", "ნიშანი არ არის: ისანში ადგილი დადგენილი არ არის.",
     "ნიშანი მთელ ქალაქზეა: ისანში სასახლის ადგილი დადგენილი არ არის."),
    (1210, "Закарий и Иване Мхаргрдзели", "ru", "Булавка стоит на городе в целом: место дворца в Исани не установлено.", 'Булавка стоит у церкви Метехи: по «Картлис Цховреба» (рус. пер., 2008) царь Димитрий «выстроил во дворце Исани монастырь для пребывания в нём Метехской Богоматери», то есть Метехи построен на территории дворца; по примечанию издания, это храм на скалистом берегу Куры. Границы дворца неизвестны, поэтому место приблизительное.'),
    (1210, "Закарий и Иване Мхаргрдзели", "en", "The pin is on the city as a whole: the place of the palace in Isani is not established.", "The pin is at the Metekhi church: by the Kartlis Tskhovreba (Russian translation, 2008) King Dimitri 'built in the palace of Isani a monastery for the Metekhi Mother of God', that is, Metekhi was built on the territory of the palace; by the commentary of the edition it is a church on the rocky bank of the Kura. The limits of the palace are not known, so the place is approximate."),
    (1210, "Закарий и Иване Мхаргрдзели", "ka", "ნიშანი მთელ ქალაქზეა: ისანში სასახლის ადგილი დადგენილი არ არის.", 'ნიშანი მეტეხის ტაძართანაა: „ქართლის ცხოვრების“ (რუსული თარგმანი, 2008) მიხედვით, მეფე დიმიტრიმ „ისნის სასახლეში ააშენა მონასტერი მეტეხის ღვთისმშობლის დასამკვიდრებლად“, ანუ მეტეხი სასახლის ტერიტორიაზე აშენდა; გამოცემის კომენტარის მიხედვით, ეს მტკვრის კლდოვან ნაპირზე მდებარე ტაძარია. სასახლის საზღვრები უცნობია, ამიტომ ადგილი მიახლოებითია.'),
    (1184, "Умирает царь Георгий III", "ru", "Булавки нет: точное место дворца Исани не установлено в доступных источниках.", 'Булавка стоит у церкви Метехи: по «Картлис Цховреба» (рус. пер., 2008) царь Димитрий «выстроил во дворце Исани монастырь для пребывания в нём Метехской Богоматери», то есть Метехи построен на территории дворца; по примечанию издания, это храм на скалистом берегу Куры. Границы дворца неизвестны, поэтому место приблизительное.'),
    (1184, "Умирает царь Георгий III", "en", "There is no pin: the exact place of the Isani palace is not established in the available sources.", "The pin is at the Metekhi church: by the Kartlis Tskhovreba (Russian translation, 2008) King Dimitri 'built in the palace of Isani a monastery for the Metekhi Mother of God', that is, Metekhi was built on the territory of the palace; by the commentary of the edition it is a church on the rocky bank of the Kura. The limits of the palace are not known, so the place is approximate."),
    (1184, "Умирает царь Георгий III", "ka", "ნიშანი არ არის: ისნის სასახლის ზუსტი ადგილი ხელმისაწვდომ წყაროებში დადგენილი არ არის.", 'ნიშანი მეტეხის ტაძართანაა: „ქართლის ცხოვრების“ (რუსული თარგმანი, 2008) მიხედვით, მეფე დიმიტრიმ „ისნის სასახლეში ააშენა მონასტერი მეტეხის ღვთისმშობლის დასამკვიდრებლად“, ანუ მეტეხი სასახლის ტერიტორიაზე აშენდა; გამოცემის კომენტარის მიხედვით, ეს მტკვრის კლდოვან ნაპირზე მდებარე ტაძარია. სასახლის საზღვრები უცნობია, ამიტომ ადგილი მიახლოებითია.'),
]


def main():
    d = json.load(open(PATH, encoding="utf-8"))
    ev = d["events"]
    added = 0
    for year, start, place in PLACES:
        hit = [e for e in ev if e["year"] == year and e["ru"].startswith(start)]
        assert len(hit) == 1, (year, start, len(hit))
        cur = hit[0].get("place")
        if cur is None or (cur.get("ru") == CITY["ru"] and place is not CITY):         # a better place replaces the point of the whole city
            hit[0]["place"] = json.loads(json.dumps(place))
            added += 1
    fixed = 0
    for year, start, lang, old, new in NOTES:
        e = [x for x in ev if x["year"] == year and x["ru"].startswith(start)][0]
        t = e["note"][lang]
        if old in t:
            e["note"][lang] = t.replace(old, new)
            fixed += 1
    open(PATH, "w", encoding="utf-8", newline="").write(json.dumps(d, ensure_ascii=False, indent=1))
    print("points added:", added, "; note phrases changed:", fixed)


if __name__ == "__main__":
    main()
