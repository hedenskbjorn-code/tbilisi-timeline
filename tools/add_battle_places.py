"""Put map points on the battles, sieges, storms and captures of the timeline that had none (site/data/history_events.json).
Each point is a place named by the sources of the event; where the sources name no particular place, the point is the city as a whole
(the coordinates of the page 'Tbilisi' on English Wikipedia). Events whose place is not established by any source (Rakhsi 1118, Botora 1120,
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
    (1210, "Закарий и Иване Мхаргрдзели", CITY),
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
]


def main():
    d = json.load(open(PATH, encoding="utf-8"))
    ev = d["events"]
    added = 0
    for year, start, place in PLACES:
        hit = [e for e in ev if e["year"] == year and e["ru"].startswith(start)]
        assert len(hit) == 1, (year, start, len(hit))
        if "place" not in hit[0]:
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
