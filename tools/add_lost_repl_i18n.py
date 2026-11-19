"""Adds repl_en and repl_ka (what stands on the site of a lost building today) next to the Russian repl in site/data/lost.json, and
the Georgian names of the places of the history events (place.ka in site/data/history_events.json and data/history_events.json).
The Georgian texts are written by the assistant and not checked by a native speaker. Idempotent: matches by the Russian text."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPL = {
 "Здание Парламента Грузии (бывший Дом правительства Грузинской ССР, пр. Руставели, 8)": ("The Parliament of Georgia building (formerly the House of Government of the Georgian SSR, 8 Rustaveli Avenue)", "საქართველოს პარლამენტის შენობა (ყოფილი საქართველოს სსრ მთავრობის სახლი, რუსთაველის გამზ. 8)"),
 "Средняя школа № 104 (ул. Г. Атонели, 31); от ансамбля уцелела только отдельно стоящая трёхъярусная колокольня": ("Secondary school no. 104 (31 G. Atoneli St.); of the ensemble only the free-standing three-tier bell tower survived", "104-ე საშუალო სკოლა (გ. ათონელის ქ. 31); ანსამბლიდან მხოლოდ ცალკე მდგომი სამსართულიანი სამრეკლო გადარჩა"),
 "Территория парка 9 Апреля (верхняя часть бывшего Александровского сада за Национальной галереей)": ("The area of the 9 April Park (the upper part of the former Alexander Garden behind the National Gallery)", "9 აპრილის პარკის ტერიტორია (ყოფილი ალექსანდრეს ბაღის ზედა ნაწილი ეროვნული გალერეის უკან)"),
 "Сквер и жилая застройка у площади Марджанишвили (ул. Котэ Марджанишвили)": ("A square and housing by Marjanishvili Square (Kote Marjanishvili St.)", "სკვერი და საცხოვრებელი განაშენიანება მარჯანიშვილის მოედანთან (კოტე მარჯანიშვილის ქ.)"),
 "Правобережный съезд нового Метехского моста и набережная на пл. Вахтанга Горгасали (Майдане)": ("The right-bank ramp of the new Metekhi Bridge and the embankment at Vakhtang Gorgasali Square (the Maidan)", "ახალი მეტეხის ხიდის მარჯვენა სანაპიროს ჩასასვლელი და სანაპირო ვახტანგ გორგასლის მოედანზე (მაიდანი)"),
 "Здание кинотеатра «Руставели» (пр. Шота Руставели, 5, построено в 1938–1939 гг., арх. Н. П. Северов)": ("The building of the Rustaveli cinema (5 Shota Rustaveli Avenue, built in 1938–1939, architect N. Severov)", "კინოთეატრ „რუსთაველის“ შენობა (შოთა რუსთაველის გამზ. 5, აშენდა 1938–1939 წლებში, არქიტექტორი ნ. სევეროვი)"),
 "Застройка между пр. Руставели и ул. Г. Табидзе / пл. Свободы": ("Buildings between Rustaveli Avenue and G. Tabidze St. / Freedom Square", "განაშენიანება რუსთაველის გამზირსა და გ. ტაბიძის ქუჩას / თავისუფლების მოედანს შორის"),
 "Проезжая часть и застройка ул. Котэ Абхази (бывш. Армянский базар / ул. Леселидзе)": ("The roadway and buildings of Kote Abkhazi St. (formerly the Armenian Bazaar / Leselidze St.)", "კოტე აფხაზის ქუჩის სავალი ნაწილი და განაშენიანება (ყოფილი სომხის ბაზარი / ლესელიძის ქ.)"),
 "Парк Дружбы, а с 1995–2004 гг. — комплекс кафедрального собора Святой Троицы (Цминда Самеба) и небольшой сохранившийся мемориал Пантеона Ходживанка": ("The Friendship Park, and in 1995–2004 the complex of the Holy Trinity Cathedral (Tsminda Sameba) and the small surviving memorial of the Khojivank Pantheon", "მეგობრობის პარკი, ხოლო 1995–2004 წლებში წმინდა სამების საკათედრო ტაძრის (წმინდა სამება) კომპლექსი და ხოჯივანქის პანთეონის მცირე შემორჩენილი მემორიალი"),
 "Жилая застройка в районе ул. А. Грибоедова / Кобулетской (вблизи Академии художеств)": ("Housing near Griboedov St. / Kobuleti St. (close to the Academy of Arts)", "საცხოვრებელი განაშენიანება გრიბოედოვის / ქობულეთის ქუჩების რაიონში (სამხატვრო აკადემიასთან ახლოს)"),
 "Жилая застройка района Абанотубани / Харпухи (ул. И. Гришашвили / бывш. Сурб-Саркисская)": ("Housing in the Abanotubani / Kharpukhi area (I. Grishashvili St. / formerly Surb-Sarkis St.)", "საცხოვრებელი განაშენიანება აბანოთუბნის / ხარფუხის რაიონში (ი. გრიშაშვილის ქ. / ყოფილი სურბ-სარკისის ქ.)"),
 "Городская застройка в районе пр. Давида Агмашенебели (бывш. Михайловский пр.) и ул. Г. Читаиа": ("City buildings around David Aghmashenebeli Avenue (formerly Mikhailovsky Avenue) and G. Chitaia St.", "ქალაქის განაშენიანება დავით აღმაშენებლის გამზირისა (ყოფილი მიხეილის გამზ.) და გ. ჭიტაიას ქუჩის რაიონში"),
 "Городская застройка в конце ул. Амаглеба (бывш. Вознесенской ул.) в Сололаки; в 2000-х гг. поблизости выстроен новый храм": ("City buildings at the end of Amaghleba St. (formerly Voznesenskaya St.) in Sololaki; a new church was built nearby in the 2000s", "ქალაქის განაშენიანება ამაღლების ქუჩის (ყოფილი ვოზნესენსკაიას ქ.) ბოლოში, სოლოლაკში; 2000-იან წლებში ახლოს ახალი ტაძარი აშენდა"),
 "Парк Вере (бывш. парк им. С. М. Кирова, заложенный на месте старого Верийского кладбища в 1933 г.)": ("Vere Park (formerly the S. M. Kirov Park, laid out in 1933 on the site of the old Vera cemetery)", "ვერის პარკი (ყოფილი ს. მ. კიროვის სახელობის პარკი, გაშენებული 1933 წელს ვერის ძველი სასაფლაოს ადგილზე)"),
 "Центральное открытое пространство площади Свободы (бывш. Эриванской пл. / пл. Берии / пл. Ленина)": ("The central open space of Freedom Square (formerly Erivan Square / Beria Square / Lenin Square)", "თავისუფლების მოედნის ცენტრალური ღია სივრცე (ყოფილი ერევნის მოედანი / ბერიას მოედანი / ლენინის მოედანი)"),
 "Застройка вдоль набережной Куры и площади Ираклия II (между Сионским собором и Анчисхати)": ("Buildings along the Kura embankment and Erekle II Square (between the Sioni Cathedral and Anchiskhati)", "განაშენიანება მტკვრის სანაპიროსა და ერეკლე II-ის მოედნის გასწვრივ (სიონის ტაძარსა და ანჩისხატს შორის)"),
 "Открытое плато вокруг храма Метехи и памятник царю Вахтангу Горгасали (установлен в 1961 г.)": ("The open plateau around the Metekhi church and the monument to King Vakhtang Gorgasali (erected in 1961)", "მეტეხის ტაძრის გარშემო ღია პლატო და მეფე ვახტანგ გორგასლის ძეგლი (დადგმულია 1961 წელს)"),
 "Мост Николоза Бараташвили (железобетонный двухъярусный мост, открыт в 1965–1966 гг.)": ("Nikoloz Baratashvili Bridge (a reinforced-concrete two-level bridge, opened in 1965–1966)", "ნიკოლოზ ბარათაშვილის ხიდი (რკინაბეტონის ორსაფეხურიანი ხიდი, გაიხსნა 1965–1966 წლებში)"),
 "Современный железобетонный Метехский мост (1951 г.)": ("The present reinforced-concrete Metekhi Bridge (1951)", "დღევანდელი რკინაბეტონის მეტეხის ხიდი (1951 წ.)"),
 "Плотина и мостовой переход Ортачальской ГЭС / мост 300 Арагвинцев": ("The dam and the bridge crossing of the Ortachala hydropower plant / the 300 Aragvians Bridge", "ორთაჭალის ჰესის კაშხალი და სახიდე გადასასვლელი / 300 არაგველის ხიდი"),
 "Современное здание вокзала и ТЦ «Тбилиси-Централ» (Вокзальная пл., 2)": ("The present station building and the Tbilisi Central shopping centre (2 Station Square)", "რკინიგზის სადგურის დღევანდელი შენობა და სავაჭრო ცენტრი „თბილისი სენტრალი“ (სადგურის მოედანი 2)"),
 "Выход ул. Котэ Абхази и ул. Ш. Дадиани к площади Свободы": ("The exits of Kote Abkhazi St. and Sh. Dadiani St. to Freedom Square", "კოტე აფხაზის და შ. დადიანის ქუჩების გასასვლელი თავისუფლების მოედანზე"),
 "Улица Пушкина (в районе пересечения с ул. Серебряной / Чахрухадзе; в 2012 г. при раскопках открыты фундаменты стены и башен)": ("Pushkin Street (near the crossing with Serebryanaya / Chakhrukhadze St.; in 2012 excavations revealed the foundations of the wall and towers)", "პუშკინის ქუჩა (ვერცხლის / ჭახრუხაძის ქუჩასთან გადაკვეთის რაიონში; 2012 წელს გათხრებისას გალავნისა და კოშკების საძირკვლები გამოვლინდა)"),
 "Район ул. Николоза Бараташвили / Шавтели у выхода к Куре": ("The area of N. Baratashvili St. / Shavteli St. at the exit to the Kura", "ნ. ბარათაშვილის / შავთელის ქუჩების რაიონი მტკვართან გასვლისას"),
 "Улица Ботаническая / район Серных бань в Абанотубани": ("Botanicheskaya Street / the area of the Sulphur Baths in Abanotubani", "ბოტანიკური ქუჩა / გოგირდის აბანოების რაიონი აბანოთუბანში"),
 "Подъём от Метехского моста к Авлабару (ул. Метехи / Винный подъём)": ("The climb from the Metekhi Bridge to Avlabari (Metekhi St. / the Wine Ascent)", "აღმართი მეტეხის ხიდიდან ავლაბრისკენ (მეტეხის ქ. / ღვინის აღმართი)"),
 "Сквер на ул. Шавтели южнее базилики Анчисхати и резиденции Патриарха Грузии": ("A square on Shavteli St. south of the Anchiskhati Basilica and the residence of the Patriarch of Georgia", "სკვერი შავთელის ქუჩაზე ანჩისხატის ბაზილიკისა და საქართველოს პატრიარქის რეზიდენციის სამხრეთით"),
 "Улица Николоза Бараташвили / сквер у крепостной стены": ("Nikoloz Baratashvili Street / a square by the fortress wall", "ნიკოლოზ ბარათაშვილის ქუჩა / სკვერი ციხესიმაგრის გალავანთან"),
 "Застройка и дорожная развязка в районе площади Вахтанга Горгасали (Майдана) у подножия Нарикалы": ("Buildings and a road junction near Vakhtang Gorgasali Square (the Maidan) at the foot of Narikala", "განაშენიანება და საგზაო კვანძი ვახტანგ გორგასლის მოედანთან (მაიდანი) ნარიყალას ძირას"),
 "Сквер и проезжая часть в районе площади Вахтанга Горгасали (Майдана) и Серных бань": ("A square and a roadway near Vakhtang Gorgasali Square (the Maidan) and the Sulphur Baths", "სკვერი და სავალი ნაწილი ვახტანგ გორგასლის მოედანთან (მაიდანი) და გოგირდის აბანოებთან"),
 "Городская застройка в квартале между ул. Котэ Абхази и ул. Сиони": ("City buildings in the block between Kote Abkhazi St. and Sioni St.", "ქალაქის განაშენიანება კოტე აფხაზის და სიონის ქუჩებს შორის კვარტალში"),
}
PLACE_KA = {
 "Крепость Нарикала": "ნარიყალას ციხე", "Базилика Анчисхати": "ანჩისხატის ბაზილიკა", "Собор Сиони": "სიონის ტაძარი", "Церковь Сурб Геворг": "სურბ გევორგის ეკლესია",
 "Церковь Метехи": "მეტეხის ტაძარი", "Ботанический сад": "ბოტანიკური ბაღი", "Оперный театр": "ოპერისა და ბალეტის თეატრი", "Театр Руставели": "რუსთაველის თეატრი",
 "Эпицентр по оценке авторов (погрешность около 0,2°, то есть около 20 км)": "ეპიცენტრი ავტორების შეფასებით (ცდომილება დაახლოებით 0,2°, ანუ დაახლოებით 20 კმ)",
 "Тбилисский государственный университет": "თბილისის სახელმწიფო უნივერსიტეტი", "Стадион «Динамо» (арена Бориса Пайчадзе)": "სტადიონი „დინამო“ (ბორის პაიჭაძის სახელობის დინამოს არენა)",
 "Парк Ваке": "ვაკის პარკი", "Телебашня на Мтацминде": "სატელევიზიო კოშკი მთაწმინდაზე", "Проспект Руставели, у здания Парламента": "რუსთაველის გამზირი, პარლამენტის შენობასთან",
 "Собор Самеба": "სამების საკათედრო ტაძარი (სამება)", "Площадь Свободы": "თავისუფლების მოედანი", "Мост Мира": "მშვიდობის ხიდი",
 "Долина реки Вере: площадь Героев, зоопарк": "ვერეს ხეობა: გმირთა მოედანი, ზოოპარკი",
}


def jwrite(path, obj, indent=None):
    # indent=1 reproduces the layout of the history and transport event files byte for byte; lost.json is a single line
    txt = json.dumps(obj, ensure_ascii=False, indent=indent) if indent else json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    open(path, "wb").write(txt.encode("utf-8"))


def main():
    p = os.path.join(ROOT, "site", "data", "lost.json")
    d = json.load(open(p, encoding="utf-8"))
    miss = 0
    for f in d["features"]:
        pr = f["properties"]
        ru = pr.get("repl")
        if ru in REPL:
            pr["repl_en"], pr["repl_ka"] = REPL[ru]
        elif ru:
            miss += 1
            print("no translation:", ru)
    jwrite(p, d)
    print("lost features:", len(d["features"]), "missing:", miss)
    for rel in (("site", "data", "history_events.json"), ("data", "history_events.json")):
        hp = os.path.join(ROOT, *rel)
        if not os.path.exists(hp):
            continue
        h = json.load(open(hp, encoding="utf-8"))
        evs = h if isinstance(h, list) else h["events"]
        n = 0
        for e in evs:
            pl = e.get("place")
            if isinstance(pl, dict) and "ka" not in pl:
                if pl["ru"] in PLACE_KA:
                    pl["ka"] = PLACE_KA[pl["ru"]]
                    n += 1
                else:
                    print("no ka for place:", pl["ru"])
        jwrite(hp, h, 1)
        print(rel[-1], "place.ka added:", n)


if __name__ == "__main__":
    main()
