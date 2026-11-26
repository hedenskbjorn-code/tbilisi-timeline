"""Add positive events (buildings, openings, achievements) and the oldest surviving buildings to the timeline:
site/data/history_events.json and data/history_events.json (kept identical).
Every event was checked against the cited English Wikipedia page on 2026-11-18 (see the 'note' of the file); events not confirmed there were not added.
Map points: the coordinates of the English Wikipedia page of the building (read through the API on 2026-11-18).
The script is idempotent: an event already present (same year, date and category) only gets its point on the map if it has none.
Usage: python -X utf8 -P tools/add_positive_events.py
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W = "https://en.wikipedia.org/wiki/"


def N(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


def P(page, lat, lon, ru, en, zoom=16):
    return {"lng": lon, "lat": lat, "zoom": zoom, "ru": ru, "en": en, "src": "coordinates of the page '%s' on English Wikipedia" % page}


PL = {
    "opera": P("Georgian National Opera Theater", 41.70130556, 44.79616667, "Оперный театр", "The opera house"),
    "theatre": P("Rustaveli Theatre", 41.69972222, 44.79777778, "Театр Руставели", "The Rustaveli Theatre"),
    "tsu": P("Tbilisi State University", 41.71, 44.77833333, "Тбилисский государственный университет", "Tbilisi State University"),
    "dinamo": P("Boris Paichadze Dinamo Arena", 41.72305556, 44.78972222, "Стадион «Динамо» (арена Бориса Пайчадзе)", "The Dinamo stadium (Boris Paichadze Dinamo Arena)"),
    "sameba": P("Holy Trinity Cathedral of Tbilisi", 41.6975, 44.81666667, "Собор Самеба", "Sameba Cathedral"),
    "bridge": P("Bridge of Peace", 41.6929, 44.8082, "Мост Мира", "The Bridge of Peace"),
    "narikala": P("Narikala", 41.68777778, 44.80861111, "Крепость Нарикала", "Narikala fortress"),
    "anchi": P("Anchiskhati Basilica", 41.69555556, 44.80694444, "Базилика Анчисхати", "Anchiskhati Basilica"),
    "sioni": P("Tbilisi Sioni Cathedral", 41.6914, 44.8075, "Собор Сиони", "Sioni Cathedral"),
    "gevorg": P("Saint George's Church, Tbilisi", 41.6892, 44.8089, "Церковь Сурб Геворг", "Surb Gevorg church"),
    "metekhi": P("Metekhi Church", 41.69013, 44.81118, "Церковь Метехи", "Metekhi Church"),
    "tvtower": P("Tbilisi TV Broadcasting Tower", 41.69583333, 44.78472222, "Телебашня на Мтацминде", "The TV tower on Mtatsminda"),
    "vake": P("Vake Park", 41.708889, 44.751389, "Парк Ваке", "Vake Park"),
    "garden": P("National Botanical Garden of Georgia", 41.68611111, 44.8075, "Ботанический сад", "The Botanical Garden"),
    "freedom": P("Freedom Square, Tbilisi", 41.69333333, 44.80166667, "Площадь Свободы", "Freedom Square", 16.5),
}

EVENTS = [
    {"year": 1851, "date": "12.04.1851", "cat": "build", "src": [W + "Georgian_National_Opera_Theater"], "pl": "opera",
     "ru": "Открыт оперный театр в Тбилиси (стройка начата в 1847, торжественное открытие 9 ноября 1851)",
     "en": "The opera house opens in Tbilisi (building began in 1847; grand inauguration on 9 November 1851)",
     "ka": "თბილისში გაიხსნა საოპერო თეატრი (მშენებლობა დაიწყო 1847 წელს; საზეიმო გახსნა 1851 წლის 9 ნოემბერს)",
     "note": N("en.wikipedia (Georgian National Opera Theater): театр сгорел 11 октября 1874; окончательно открыт заново в 1896.",
              "en.wikipedia (Georgian National Opera Theater): the theatre burnt down on 11 October 1874 and finally reopened in 1896.",
              "en.wikipedia (Georgian National Opera Theater): თეატრი 1874 წლის 11 ოქტომბერს დაიწვა და საბოლოოდ 1896 წელს ხელახლა გაიხსნა.")},
    {"year": 1887, "date": "1887", "cat": "build", "src": [W + "Rustaveli_Theatre"], "pl": "theatre",
     "ru": "Достроено здание на проспекте Руставели (тогда Общество художников), с 1921 года Театр имени Руставели",
     "en": "The building on Rustaveli Avenue is completed (then the Artists' Society), the Rustaveli Theatre since 1921",
     "ka": "დასრულდა შენობა რუსთაველის გამზირზე (მაშინ მხატვართა საზოგადოება), 1921 წლიდან რუსთაველის თეატრი"},
    {"year": 1905, "date": "1901-1905", "cat": "build", "src": [W + "Tbilisi_State_Conservatoire"],
     "ru": "Построено здание, в котором с 1917 года работает Тбилисская консерватория",
     "en": "The building of today's Tbilisi State Conservatoire is built (the conservatoire itself was founded on 1 May 1917)",
     "ka": "აშენდა შენობა, რომელშიც 1917 წლიდან თბილისის სახელმწიფო კონსერვატორია მოღვაწეობს"},
    {"year": 1918, "date": "1918", "cat": "build", "src": [W + "Tbilisi_State_University"], "pl": "tsu",
     "ru": "Основан Тбилисский государственный университет, первый университет на Кавказе",
     "en": "Tbilisi State University is founded, the first university in the Caucasus",
     "ka": "დაარსდა თბილისის სახელმწიფო უნივერსიტეტი, პირველი უნივერსიტეტი კავკასიაში",
     "note": N("en.wikipedia: в статье встречаются разные даты: 26 января и 8 февраля 1918.",
               "en.wikipedia: the article gives different dates: 26 January and 8 February 1918.",
               "en.wikipedia: სტატიაში სხვადასხვა თარიღია მითითებული: 1918 წლის 26 იანვარი და 8 თებერვალი.")},
    {"year": 1936, "date": "1936", "cat": "build", "src": [W + "Boris_Paichadze_Dinamo_Arena"], "pl": "dinamo",
     "ru": "Открыт стадион «Динамо» на 23 тысячи мест",
     "en": "The Dinamo stadium opens, with 23,000 seats",
     "ka": "გაიხსნა დინამოს სტადიონი 23 ათასი ადგილით"},
    {"year": 1966, "date": "11.01.1966", "cat": "build", "src": [W + "Tbilisi_Metro"],
     "ru": "Открыто Тбилисское метро: первые шесть станций (стройка началась в 1952); четвёртое метро в СССР",
     "en": "The Tbilisi Metro opens with its first six stations (construction began in 1952); the fourth metro system in the USSR",
     "ka": "გაიხსნა თბილისის მეტროპოლიტენი პირველი ექვსი სადგურით (მშენებლობა დაიწყო 1952 წელს); მეოთხე მეტრო სსრკ-ში"},
    {"year": 1976, "date": "26.09.1976", "cat": "build", "src": [W + "Boris_Paichadze_Dinamo_Arena"], "pl": "dinamo",
     "ru": "Открыта реконструированная арена «Динамо»; первый официальный матч 29 сентября (3:0 с «Кардифф Сити»)",
     "en": "The rebuilt Dinamo Arena is inaugurated; the first official match is on 29 September (3-0 against Cardiff City)",
     "ka": "გაიხსნა რეკონსტრუირებული დინამოს არენა; პირველი ოფიციალური მატჩი 29 სექტემბერს (3:0 კარდიფ სიტისთან)"},
    {"year": 1981, "date": "1981", "cat": "build", "src": [W + "FC_Dinamo_Tbilisi", W + "Boris_Paichadze_Dinamo_Arena"], "pl": "dinamo",
     "ru": "«Динамо» Тбилиси выигрывает Кубок обладателей кубков УЕФА (финал в Дюссельдорфе, 2:1 с «Карл Цейсс»); 80 тысяч болельщиков встречают команду на стадионе",
     "en": "Dinamo Tbilisi win the UEFA Cup Winners' Cup (final in Dusseldorf, 2-1 against Carl Zeiss Jena); 80,000 fans greet the team at the stadium",
     "ka": "თბილისის დინამო იგებს უეფას თასი მფლობელთა თასს (ფინალი დიუსელდორფში, 2:1 კარლ ცაისის წინააღმდეგ); 80 ათასი გულშემატკივარი ხვდება გუნდს სტადიონზე"},
    {"year": 2004, "date": "23.11.2004", "cat": "build", "src": [W + "Holy_Trinity_Cathedral_of_Tbilisi"], "pl": "sameba",
     "ru": "Освящён собор Святой Троицы (Самеба); закладка состоялась 23 ноября 1995",
     "en": "The Holy Trinity Cathedral (Sameba) is consecrated; the foundation was laid on 23 November 1995",
     "ka": "აკურთხეს წმინდა სამების ტაძარი (სამება); საძირკველი 1995 წლის 23 ნოემბერს ჩაეყარა"},
    {"year": 2010, "date": "6.05.2010", "cat": "build", "src": [W + "Bridge_of_Peace"], "pl": "bridge",
     "ru": "Официально открыт Мост Мира через Куру",
     "en": "The Bridge of Peace over the Kura is officially opened",
     "ka": "ოფიციალურად გაიხსნა მშვიდობის ხიდი მტკვარზე"},
    {"year": 2016, "date": "1.2016", "cat": "build", "src": [W + "Georgian_National_Opera_Theater"], "pl": "opera",
     "ru": "Завершена реставрация оперного театра (около 40 млн долларов)",
     "en": "The restoration of the opera house is completed (about 40 million dollars)",
     "ka": "დასრულდა საოპერო თეატრის რესტავრაცია (დაახლოებით 40 მილიონი დოლარი)"},

    # ---- more buildings (checked on the cited pages) ----
    {"year": 1845, "date": "1845", "cat": "build", "src": [W + "National_Botanical_Garden_of_Georgia"], "pl": "garden",
     "ru": "Ботанический сад официально учреждён как Тифлисский ботанический сад",
     "en": "The Botanical Garden is officially established as the Tiflis Botanical Garden",
     "ka": "ბოტანიკური ბაღი ოფიციალურად დაარსდა როგორც ტფილისის ბოტანიკური ბაღი",
     "note": N("en.wikipedia: сад описан уже в 1671 году, возможно, основан не позднее 1625.",
               "en.wikipedia: the garden is described as early as 1671 and may have been founded by 1625.",
               "en.wikipedia: ბაღი უკვე 1671 წელს არის აღწერილი და შესაძლოა 1625 წლამდე იყოს დაარსებული.")},
    {"year": 1883, "date": "3.04.1883", "cat": "build", "src": [W + "Trams_in_Tbilisi"],
     "ru": "Открыта конка, трамвай на конной тяге",
     "en": "The horse tram opens, the first tram line in the city",
     "ka": "გაიხსნა ცხენებით გამწევი ტრამვაი (კონკა)"},
    {"year": 1904, "date": "1904", "cat": "build", "src": [W + "Trams_in_Tbilisi", W + "Tbilisi"],
     "ru": "Начало электрификации трамвая в Тбилиси",
     "en": "The Tbilisi tram begins to be electrified",
     "ka": "თბილისში ტრამვაის ელექტრიფიკაცია დაიწყო",
     "note": N("en.wikipedia (Trams in Tbilisi): электрификация шла с июня 1904 по август 1905.",
               "en.wikipedia (Trams in Tbilisi): the electrification took place between June 1904 and August 1905.",
               "en.wikipedia (Trams in Tbilisi): ელექტრიფიკაცია 1904 წლის ივნისიდან 1905 წლის აგვისტომდე მიმდინარეობდა.")},
    {"year": 1905, "date": "1905", "cat": "build", "src": [W + "Tbilisi"],
     "ru": "Впервые построен фуникулёр на Мтацминду (в 2012 году открыт заново после многолетнего перерыва)",
     "en": "The funicular up Mtatsminda is first built (reopened in 2012 after a multi-year closure)",
     "ka": "პირველად აშენდა ფუნიკულიორი მთაწმინდაზე (2012 წელს ხელახლა გაიხსნა მრავალწლიანი შეჩერების შემდეგ)"},
    {"year": 1946, "date": "1946", "cat": "build", "src": [W + "Vake_Park"], "pl": "vake",
     "ru": "Открыт парк Ваке",
     "en": "Vake Park opens",
     "ka": "გაიხსნა ვაკის პარკი"},
    {"year": 1972, "date": "1972", "cat": "build", "src": [W + "Tbilisi_TV_Broadcasting_Tower"], "pl": "tvtower",
     "ru": "Построена Тбилисская телебашня на Мтацминде",
     "en": "The Tbilisi TV tower is built on Mtatsminda",
     "ka": "მთაწმინდაზე აშენდა თბილისის სატელევიზიო კოშკი"},
    {"year": 2006, "date": "23.11.2006", "cat": "build", "src": [W + "Freedom_Square,_Tbilisi"], "pl": "freedom",
     "ru": "На площади Свободы открыт монумент Свободы со Святым Георгием (на месте памятника Ленину, снесённого в 1991)",
     "en": "The Liberty Monument with St George is unveiled on Freedom Square (where the Lenin statue stood until 1991)",
     "ka": "თავისუფლების მოედანზე გაიხსნა თავისუფლების მონუმენტი წმინდა გიორგით (ლენინის ძეგლის ადგილზე, რომელიც 1991 წელს დაანგრიეს)"},
    {"year": 2012, "date": "2012", "cat": "build", "src": [W + "Tbilisi"],
     "ru": "Начала работать канатная дорога Рике - Нарикала; фуникулёр на Мтацминду открыт вновь",
     "en": "The Rike Park - Narikala gondola lift starts to run; the Mtatsminda funicular reopens",
     "ka": "ამოქმედდა რიყის პარკი - ნარიყალას საბაგირო; მთაწმინდის ფუნიკულიორი ხელახლა გაიხსნა"},

    # ---- the oldest buildings that survive to this day ----
    {"year": 364, "date": "364", "cat": "oldest", "src": [W + "Narikala"], "pl": "narikala",
     "ru": "Крепость Нарикала: основана около 364 года (при Вараз-Бакуре); большая часть сохранившихся укреплений относится к XVI-XVII векам",
     "en": "Narikala fortress: founded about 364 (under Varaz-Bakur); most of the surviving fortifications date from the 16th-17th centuries",
     "ka": "ნარიყალას ციხე: დაარსებულია დაახლოებით 364 წელს (ვარაზ-ბაკურის დროს); შემორჩენილი სიმაგრეების უმეტესობა XVI-XVII საუკუნეებისაა",
     "note": N("en.wikipedia: предание связывает основание и с Вахтангом Горгасали; в 1827 году землетрясение и разборка повредили крепость.",
               "en.wikipedia: tradition also credits Vakhtang Gorgasali; in 1827 an earthquake and demolition damaged the fortress.",
               "en.wikipedia: გადმოცემით დამაარსებლად ვახტანგ გორგასალიც ესახელება; 1827 წელს მიწისძვრამ და დანგრევამ ციხე დააზიანა.")},
    {"year": 550, "date": "500-599", "cat": "oldest", "src": [W + "Anchiskhati_Basilica"], "pl": "anchi",
     "ru": "Базилика Анчисхати, VI век: старейшая сохранившаяся церковь Тбилиси",
     "en": "Anchiskhati Basilica, 6th century: the oldest surviving church in Tbilisi",
     "ka": "ანჩისხატის ბაზილიკა, VI საუკუნე: თბილისის უძველესი შემორჩენილი ეკლესია",
     "note": N("en.wikipedia: позднее неоднократно перестраивалась (XV-XVII вв.), колокольня 1675 года; реставрация 1958-1964 вернула облик XVII века.",
               "en.wikipedia: rebuilt several times later (15th-17th centuries), the belfry is of 1675; a restoration in 1958-1964 returned it to its 17th-century look.",
               "en.wikipedia: შემდგომში არაერთხელ გადაკეთდა (XV-XVII სს.), სამრეკლო 1675 წლისაა; 1958-1964 წლების რესტავრაციამ XVII საუკუნის იერი დაუბრუნა.")},
    {"year": 1112, "date": "1112", "cat": "oldest", "src": [W + "Tbilisi_Sioni_Cathedral"], "pl": "sioni",
     "ru": "Давид Строитель полностью перестраивает собор Сиони: основа нынешней постройки относится к этому времени (первая церковь VI-VII веков)",
     "en": "David the Builder completely rebuilds Sioni Cathedral: the basic elements of the present structure date from then (the first church was of the 6th-7th centuries)",
     "ka": "დავით აღმაშენებელმა სიონის ტაძარი მთლიანად ხელახლა ააგო: დღევანდელი შენობის საფუძველი ამ დროიდან მოდის (პირველი ეკლესია VI-VII საუკუნეებისაა)",
     "note": N("en.wikipedia: в той же статье упомянута и версия XIII века; колокольня 1812 года.",
               "en.wikipedia: the same article also mentions a 13th-century version; the belfry is of 1812.",
               "en.wikipedia: იმავე სტატიაში XIII საუკუნის ვერსიაც არის ნახსენები; სამრეკლო 1812 წლისაა.")},
    {"year": 1251, "date": "1251", "cat": "oldest", "src": [W + "Saint_George%27s_Church,_Tbilisi"], "pl": "gevorg",
     "ru": "Армянская церковь Сурб Геворг (св. Георгия) завершена к 1251 году или раньше",
     "en": "The Armenian church of Surb Gevorg (St George) is completed by 1251 or earlier",
     "ka": "სომხური ეკლესია სურბ გევორგი (წმ. გიორგი) დასრულდა 1251 წლამდე ან უფრო ადრე",
     "note": N("en.wikipedia: одна из двух действующих армянских церквей Тбилиси.",
               "en.wikipedia: one of the two functioning Armenian churches in Tbilisi.",
               "en.wikipedia: თბილისის ორი მოქმედი სომხური ეკლესიიდან ერთ-ერთია.")},
    {"year": 1278, "date": "1278-1289", "cat": "oldest", "src": [W + "Metekhi_Church"], "pl": "metekhi",
     "ru": "Построена церковь Метехи (1278-1289, при Деметре II); сохранились оригинальные стены с восточной и северной сторон",
     "en": "Metekhi Church is built (1278-1289, under Demetrius II); the original walls survive on the east and north sides",
     "ka": "აშენდა მეტეხის ეკლესია (1278-1289, დემეტრე II-ის დროს); შემორჩენილია ორიგინალური კედლები აღმოსავლეთისა და ჩრდილოეთის მხარეს",
     "note": N("en.wikipedia: южная стена перестроена из кирпича в XVIII веке; более ранние даты (V-VI вв.) известны лишь по преданию.",
               "en.wikipedia: the south wall was rebuilt in brick in the 18th century; earlier dates (5th-6th century) rest on oral tradition only.",
               "en.wikipedia: სამხრეთის კედელი XVIII საუკუნეში აგურით გადაკეთდა; უფრო ადრინდელი თარიღები (V-VI სს.) მხოლოდ გადმოცემას ეყრდნობა.")},
]

NOTE_ADD = " Added 2026-11-18 (positive events, category 'build'; the oldest surviving buildings, category 'oldest'): each checked against the cited English Wikipedia page; not added because not confirmed: Jvari Mama, the bridges' opening years, Hotel Iveria, the Sports Palace, Junior Eurovision 2017, the zoo, the Tbilisi Sea; festivals and the UEFA Super Cup 2015 were left out at the owner's request. Points on the map: the coordinates of the English Wikipedia pages of the buildings."


def main():
    for rel in ("site/data/history_events.json", "data/history_events.json"):
        p = os.path.join(ROOT, rel)
        raw = open(p, encoding="utf-8").read()
        d = json.loads(raw)
        have = {(e["year"], e["date"], e["cat"]): e for e in d["events"]}
        for src in EVENTS:
            e = {k: v for k, v in src.items() if k != "pl"}
            if "pl" in src:
                e["place"] = PL[src["pl"]]
            old = have.get((e["year"], e["date"], e["cat"]))
            if old is None:
                d["events"].append(e)
            elif "place" in e and not old.get("place"):
                old["place"] = e["place"]
        d["events"].sort(key=lambda e: e["year"])
        if "Added 2026-11-18" in d["note"]:
            d["note"] = d["note"][:d["note"].index(" Added 2026-11-18")]
        d["note"] += NOTE_ADD
        indent = 1 if raw.startswith("{\n") else None
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))
        print(rel, len(d["events"]))


if __name__ == "__main__":
    main()
