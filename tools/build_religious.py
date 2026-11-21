"""Build site/data/religious.json: the main religious buildings of Tbilisi for the layer "Religious buildings" (appears and disappears with the year).
Every entry was checked on the cited Wikipedia pages (English, Russian, Georgian) on 2026-11-18/19; where the pages disagree the note says so.
Coordinates: those of the Wikipedia page of the building (read through the API on 2026-11-19); Khojivank: the coordinates of the Pantheon, on the site of the church.
Fields: id, rel (religion), from (year the building appears), to (year it was destroyed, absent if it stands), date (text), name/status/note {ru,en,ka}, lat, lon, src.
Usage: python -X utf8 -P tools/build_religious.py
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EN = "https://en.wikipedia.org/wiki/"
RU = "https://ru.wikipedia.org/wiki/"
KA = "https://ka.wikipedia.org/wiki/"


# photographs of the buildings (Wikimedia Commons, looked through by hand): {"objects": {building id: [titles]}, "info": {title: licence data}}
PHOTOS = json.load(open(os.path.join(ROOT, "data", "religious_photos.json"), encoding="utf-8"))


def N(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


ITEMS = [
    dict(id="atashgah", rel="zoroastrian", frm=364, date="224-651", lat=41.68885, lon=44.80559,
         name=N("Атешга (храм огня)", "Atashgah (fire temple)", "ათეშგა"),
         status=N("сохранилась: кирпичное здание под защитной крышей", "survives: a brick building under a protective roof", "შემორჩენილია: აგურის შენობა დამცავი სახურავის ქვეშ"),
         note=N("Зороастрийский храм огня; датируется эпохой Сасанидов (224-651). Описывается как самый северный зороастрийский храм огня в мире. Рядом с церковью Земо Бетлеми.",
                "A Zoroastrian fire temple, generally dated to the Sasanian era (224-651). Described as the northernmost Zoroastrian fire temple in the world. Close to the Zemo Betlemi church.",
                "ზოროასტრული ცეცხლის ტაძარი, ჩვეულებრივ სასანიანთა ეპოქით (224-651) თარიღდება. აღწერენ როგორც მსოფლიოში ყველაზე ჩრდილოეთით მდებარე ზოროასტრულ ცეცხლის ტაძარს. ახლოსაა ზემო ბეთლემის ეკლესიასთან."),
         src=[EN + "Atashgah_of_Tbilisi"]),
    dict(id="anchiskhati", rel="orthodox", frm=550, date="500-599", lat=41.69555556, lon=44.80694444,
         name=N("Базилика Анчисхати", "Anchiskhati Basilica", "ანჩისხატის ბაზილიკა"),
         status=N("сохранилась", "survives", "შემორჩენილია"),
         note=N("VI век; старейшая сохранившаяся церковь Тбилиси. Позднее перестраивалась (XV-XVII вв.), колокольня 1675 года, реставрация 1958-1964.",
                "6th century; the oldest surviving church in Tbilisi. Rebuilt later (15th-17th centuries), the belfry is of 1675, restored in 1958-1964.",
                "VI საუკუნე; თბილისის უძველესი შემორჩენილი ეკლესია. შემდგომში გადაკეთდა (XV-XVII სს.), სამრეკლო 1675 წლისაა, რესტავრაცია 1958-1964 წლებში."),
         src=[EN + "Anchiskhati_Basilica"]),
    dict(id="sioni", rel="orthodox", frm=575, date="575-639", lat=41.6914, lon=44.8075,
         name=N("Собор Сиони", "Sioni Cathedral", "სიონის ტაძარი"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Строительство начато около 575, завершено около 639 (по преданию, замысел Вахтанга Горгасали V века). Полностью перестроен Давидом Строителем в 1112; колокольня 1812. До 2004 года резиденция Католикоса-Патриарха.",
                "Begun about 575 and completed about 639 (tradition ascribes the idea to Vakhtang Gorgasali, 5th century). Completely rebuilt by David the Builder in 1112; the belfry is of 1812. Seat of the Catholicos-Patriarch until 2004.",
                "მშენებლობა დაახლოებით 575 წელს დაიწყო და 639 წელს დასრულდა (გადმოცემით იდეა ვახტანგ გორგასალს ეკუთვნის, V ს.). დავით აღმაშენებელმა 1112 წელს მთლიანად ხელახლა ააგო; სამრეკლო 1812 წლისაა. 2004 წლამდე კათოლიკოს-პატრიარქის რეზიდენცია იყო."),
         src=[EN + "Tbilisi_Sioni_Cathedral"]),
    dict(id="surb_gevorg", rel="armenian", frm=1251, date="1251", lat=41.6892, lon=44.8089,
         name=N("Церковь Сурб Геворг (св. Георгия)", "Surb Gevorg (St George) church", "სურბ გევორქის ეკლესია"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Завершена к 1251 году или раньше. Колокольня XV века; в 1795 выгорела изнутри; реставрация 2012-2015. Кафедральный собор Грузинской епархии Армянской апостольской церкви.",
                "Completed by 1251 or earlier. A 15th-century belfry; burnt out inside in 1795; restored in 2012-2015. The cathedral of the Georgian diocese of the Armenian Apostolic Church.",
                "დასრულდა 1251 წლამდე ან უფრო ადრე. XV საუკუნის სამრეკლო; 1795 წელს შიგნიდან დაიწვა; რესტავრაცია 2012-2015 წლებში. სომხური სამოციქულო ეკლესიის საქართველოს ეპარქიის კათედრალი."),
         src=[RU + "Церковь_Сурб_Геворг_(Тбилиси)", EN + "Saint_George%27s_Church,_Tbilisi"]),
    dict(id="metekhi", rel="orthodox", frm=1278, date="1278-1289", lat=41.69013, lon=44.81118,
         name=N("Церковь Метехи (Рождества Богородицы)", "Metekhi Church (Nativity of the Mother of God)", "მეტეხის ღვთისმშობლის შობის ტაძარი"),
         status=N("действует (с 1988)", "in use (since 1988)", "მოქმედია (1988 წლიდან)"),
         note=N("Построена в 1278-1289 при Деметре II. В советское время склад, лагерь НКВД (1921), молодёжный театр (1974); возвращена верующим в 1988.",
                "Built in 1278-1289 under Demetrius II. In Soviet times a store, an NKVD camp (1921), a youth theatre (1974); returned to worship in 1988.",
                "აშენდა 1278-1289 წლებში დემეტრე II-ის დროს. საბჭოთა პერიოდში საწყობი, შსს-ს ბანაკი (1921), ახალგაზრდული თეატრი (1974); ბრუნდება მორწმუნეებს 1988 წელს."),
         src=[EN + "Metekhi_Church"]),
    dict(id="norashen", rel="armenian", frm=1467, date="1467", lat=41.691, lon=44.80654,
         name=N("Церковь Норашен", "Norashen Church", "ნორაშენის ეკლესია"),
         status=N("здание стоит, не действует; спорная церковь", "the building stands, not in use; a disputed church", "შენობა დგას, არ მოქმედებს; სადავო ეკლესია"),
         note=N("Построена в 1467 (Сатат). Закрыта в советское время (1933 по en, 1934-1937 по ru). В 1995 освящена грузинским духовенством как православная; армяне протестовали, церковь закрыта. Реставрация 2015-2016.",
                "Built in 1467 (Satat). Shut in Soviet times (1933 per en, 1934-1937 per ru). In 1995 Georgian clergy re-consecrated it as an Orthodox church; the Armenians protested and it was closed. Restored in 2015-2016.",
                "აშენდა 1467 წელს (სატატი). საბჭოთა პერიოდში დაკეტეს (1933 en-ის მიხედვით, 1934-1937 ru-ს მიხედვით). 1995 წელს ქართულმა სასულიერო პირებმა მართლმადიდებლურად აკურთხეს; სომხებმა გააპროტესტეს და ეკლესია დაიკეტა. რესტავრაცია 2015-2016 წლებში."),
         src=[RU + "Церковь_Норашен_(Тбилиси)", EN + "Norashen_Church"]),
    dict(id="surb_nshan", rel="armenian", frm=1703, date="1703-1711", lat=41.694309, lon=44.804694,
         name=N("Церковь Святого Знака (Сурб Ншан)", "Church of the Holy Sign (Surb Nshan)", "სურბ ნიშანი (წმინდა ნიშნის ეკლესია)"),
         status=N("руины, не действует", "a dilapidated ruin, not in use", "მდგომარეობა მძიმეა, არ მოქმედებს"),
         note=N("Построена в 1703-1711, перестроена в 1780. Пострадала в 1795; частично сгорела в 2002 и 2012 годах.",
                "Built in 1703-1711, rebuilt in 1780. Damaged in 1795; partly burnt in 2002 and 2012.",
                "აშენდა 1703-1711 წლებში, გადაკეთდა 1780 წელს. დაზიანდა 1795 წელს; ნაწილობრივ დაიწვა 2002 და 2012 წლებში."),
         src=[RU + "Сурб_Ншан_(Тбилиси)", EN + "Surb_Nshan_Church,_Tbilisi"]),
    dict(id="zemo_betlemi", rel="armenian", frm=1727, date="1727", lat=41.688871, lon=44.804599,
         name=N("Церковь Земо Бетлеми (Рождества Богородицы)", "Zemo Betlemi church (Holy Mother of God of Bethlehem)", "ზემო ბეთლემის ეკლესია"),
         status=N("действует (православная с 1994)", "in use (Georgian Orthodox since 1994)", "მოქმედია (მართლმადიდებლური 1994 წლიდან)"),
         note=N("Завершена в 1727, перестроена в 1884; изначально армянская. В советское время использовалась заводами; в 1994 передана Грузинской православной церкви.",
                "Completed in 1727, rebuilt in 1884; originally Armenian. Used by factories in Soviet times; handed to the Georgian Orthodox Church in 1994.",
                "დასრულდა 1727 წელს, გადაკეთდა 1884 წელს; თავდაპირველად სომხური. საბჭოთა პერიოდში ქარხნები იყენებდნენ; 1994 წელს გადაეცა ქართულ მართლმადიდებლურ ეკლესიას."),
         src=[RU + "Земо_Бетлеми", EN + "Holy_Mother_of_God_Church_of_Bethlehem,_Tbilisi"]),
    dict(id="kvemo_betlemi", rel="armenian", frm=1727, date="1727", lat=41.68923, lon=44.8040148,
         name=N("Церковь Квемо Бетлеми (св. Стефаноса)", "Lower Bethlehemi Church (St Stepanos)", "ქვემო ბეთლემის ეკლესია"),
         status=N("действует (православная с 1988)", "in use (Georgian Orthodox since 1988)", "მოქმედია (მართლმადიდებლური 1988 წლიდან)"),
         note=N("Первое здание завершено в 1727; часовня перестраивалась в 1840-1875 (по en в 1868-1870). Изначально армянская.",
                "The first building was completed in 1727; rebuilt in the 19th century (1868-1870 per en, the chapel 1840-1875 per ru). Originally Armenian.",
                "პირველი შენობა 1727 წელს დასრულდა; XIX საუკუნეში გადაკეთდა (1868-1870 en-ის მიხედვით). თავდაპირველად სომხური."),
         src=[RU + "Квемо_Бетлеми", EN + "Lower_Bethlehemi_Church"]),
    dict(id="karapet", rel="armenian", frm=1705, date="1705", lat=41.69811111, lon=44.81008333,
         name=N("Церковь Святого Карапета", "Saint Karapet Church", "წმინდა კარაპეტის ეკლესია"),
         status=N("действует (православная с 1995)", "in use (Georgian Orthodox since 1995)", "მოქმედია (მართლმადიდებლური 1995 წლიდან)"),
         note=N("Даты основания расходятся: 1705 (по Нерсесу Аштаракеци), около 1400 (по Казазову, обновлена 1790). Колокольня снесена в 1995. Уцелела при разрушении армянских церквей в 1930-х.",
                "Founding dates differ: 1705 (per Nerses Ashtaraketsi) or about 1400 (per Kazazov, renovated 1790). The belfry was demolished in 1995. It survived the destruction of Armenian churches in the 1930s.",
                "დაარსების თარიღები განსხვავდება: 1705 (ნერსეს აშტარაკეცის მიხედვით) ან დაახლოებით 1400 (კაზაზოვის მიხედვით, განახლდა 1790). სამრეკლო 1995 წელს დაანგრიეს."),
         src=[RU + "Церковь_Святого_Карапета_(Тбилиси)", EN + "Saint_Karapet_Church,_Tbilisi"]),
    dict(id="mughni", rel="armenian", frm=1756, date="1756", lat=41.690259, lon=44.804194,
         name=N("Церковь Мугни Сурб Геворг", "Saint Gevorg of Mughni Church", "მუღნის წმინდა გიორგის ეკლესია"),
         status=N("повреждена, купол обрушился в 2009", "damaged, the dome collapsed in 2009", "დაზიანებულია, გუმბათი 2009 წელს ჩამოინგრა"),
         note=N("Полностью перестроена в 1756 (первая церковь по en XIII века, по ru 1356 или 1537). В советское время склад музея; в 1991 разрушен притвор, в 2009 обрушился купол.",
                "Entirely rebuilt in 1756 (the first church of the 13th century per en; 1356 or 1537 per ru). Museum storage in Soviet times; the vestibule was destroyed in 1991, the dome collapsed in 2009.",
                "მთლიანად გადაკეთდა 1756 წელს (პირველი ეკლესია en-ის მიხედვით XIII ს., ru-ს მიხედვით 1356 ან 1537). 1991 წელს დაინგრა ეკლესიის კარიბჭე, 2009 წელს ჩამოინგრა გუმბათი."),
         src=[RU + "Церковь_Мугни_Сурб_Геворг", EN + "Saint_Gevorg_of_Mughni_Church,_Tbilisi"]),
    dict(id="kldisubani", rel="armenian", frm=1753, date="1753", lat=41.6887, lon=44.806642,
         name=N("Церковь Карапи Святого Георгия (Клдисубани)", "Church of Saint George (Kldisubani)", "კლდისუბნის წმინდა გიორგის ეკლესია"),
         status=N("действует (православная с 1991)", "in use (Georgian Orthodox since 1991)", "მოქმედია (მართლმადიდებლური 1991 წლიდან)"),
         note=N("Построена в 1753 (по ru-календарю 1847 года - 1600). В советское время мастерская и голубятня; освящена 23 ноября 1991.",
                "Built in 1753 (an 1847 calendar gives 1600). A workshop and a pigeon loft in Soviet times; re-consecrated on 23 November 1991.",
                "აშენდა 1753 წელს. საბჭოთა პერიოდში სახელოსნო და მტრედების საბუდარი; აკურთხეს 1991 წლის 23 ნოემბერს."),
         src=[RU + "Церковь_Карапи_Святого_Георгия_(Клдисубани)", EN + "Church_of_Saint_George_(Kldisubani)"]),
    dict(id="vank", rel="armenian", frm=1480, to=1930, date="1480", lat=41.696328, lon=44.806723,
         name=N("Ванкский собор", "Vank Cathedral", "ვანქის ტაძარი"),
         status=N("снесён; сохранилась колокольня (ул. Атонели, 3)", "demolished; the belfry survives (Atoneli Street 3)", "დანგრეულია; შემორჩა სამრეკლო (ატონელის ქ. 3)"),
         note=N("Армянский кафедральный собор; построен или обновлён в 1480 (по ru также около 1720). Снесён по приказу Берии: 1930 (ru текст, en инфобокс) или 1938 (ru инфобокс, en текст).",
                "The Armenian cathedral; built or renovated in 1480 (about 1720 per ru as well). Demolished on Beria's orders: 1930 (ru text, en infobox) or 1938 (ru infobox, en text).",
                "სომხური საკათედრო ტაძარი; აშენდა ან განახლდა 1480 წელს. დაანგრიეს ბერიას ბრძანებით: 1930 ან 1938 წელს (წყაროები განსხვავდება). შემორჩა სამრეკლო."),
         src=[RU + "Ванкский_собор_(Тбилиси)", EN + "Vank_Monastery,_Tbilisi"]),
    dict(id="khojivank", rel="armenian", frm=1655, to=1934, date="1655", lat=41.698333, lon=44.818611,
         name=N("Церковь Сурб Аствацацин (Ходживанк)", "Surb Astvatsatsin church (Khojivank)", "სურბ ასტვაცაცინის ეკლესია (ხოჯივანქი)"),
         status=N("снесена; на месте Самеба, сохранился армянский пантеон (с 1962)", "destroyed; the site lies under Sameba, the Armenian Pantheon remains (opened 1962)", "დანგრეულია; ადგილზე სამებაა, შემორჩა სომხური პანთეონი (1962 წლიდან)"),
         note=N("Построена в 1655 (армянская надпись 1104 года). Разрушение началось в 1934 по приказу Берии; кладбище разрушалось до 1938. Точка на карте: пантеон.",
                "Built in 1655 (an Armenian inscription of 1104 = 1655). The destruction began in 1934 on Beria's order; the cemetery was destroyed until 1938. The point on the map: the Pantheon.",
                "აშენდა 1655 წელს. განადგურება დაიწყო 1934 წელს ბერიას ბრძანებით; სასაფლაო 1938 წლამდე ნადგურდებოდა. წერტილი რუკაზე: პანთეონი."),
         src=[EN + "Khojivank_Pantheon_of_Tbilisi"]),
    dict(id="catholic_cathedral", rel="catholic", frm=1805, date="1805-1808", lat=41.69254, lon=44.80353,
         name=N("Католический собор Вознесения Богородицы", "Catholic Cathedral of the Assumption of the Virgin Mary", "ღვთისმშობლის ამაღლების კათოლიკური ეკლესია"),
         status=N("действует (закрыт в 1937, вновь освящён в 1999)", "in use (closed in 1937, re-consecrated in 1999)", "მოქმედია (1937 წელს დაიკეტა, 1999 წელს ხელახლა აკურთხეს)"),
         note=N("Заложен в 1805, завершён в 1808 монахом Филиппо Форанианом перед церковью Благовещения. Освящён заново во время визита Иоанна Павла II.",
                "Begun in 1805 and completed in 1808 by the monk Philipo Foranian in front of an earlier Church of the Annunciation. Re-consecrated during the visit of John Paul II.",
                "დაიდო 1805 წელს, დასრულდა 1808 წელს ბერ ფილიპო ფორანიანის მიერ. ხელახლა აკურთხეს იოანე პავლე II-ის ვიზიტისას."),
         src=[RU + "Католический_собор_Вознесения_Богородицы_Девы_Марии_(Тбилиси)", EN + "Cathedral_of_the_Assumption_of_the_Virgin,_Tbilisi"]),
    dict(id="great_synagogue", rel="jewish", frm=1911, date="1904-1911", lat=41.69, lon=44.80727,
         name=N("Большая синагога", "Great Synagogue", "დიდი სინაგოგა"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Строительство 1904-1911 по en (по ru 1904-1913; год основания общины 1903). Прежняя домовая синагога 1877 года снесена к 1899.",
                "Built in 1904-1911 per en (1904-1913 per ru; the community was founded in 1903). The earlier house synagogue of 1877 was demolished by 1899.",
                "მშენებლობა 1904-1911 წლებში en-ის მიხედვით (ru-ს მიხედვით 1904-1913). ადრინდელი საოჯახო სინაგოგა 1877 წლისა 1899 წლისთვის დაანგრიეს."),
         src=[RU + "Большая_синагога_(Тбилиси)", EN + "Great_Synagogue_(Tbilisi)"]),
    dict(id="juma", rel="muslim", frm=1851, date="1851", lat=41.68722222, lon=44.81027778,
         name=N("Мечеть Джума", "Juma Mosque", "ჯუმა მეჩეთი"),
         status=N("действует (суннитско-шиитская)", "in use (shared Sunni and Shia)", "მოქმედია (სუნიტურ-შიიტური)"),
         note=N("Первая мечеть XVIII века разрушена персидскими войсками в 1740-х; здание 1846-1851 (Джованни Скудьери); нынешнее кирпичное здание 1895 (на средства Тагиева); реставрация 1998. Единственная сохранившаяся мечеть Старого города.",
                "The first mosque of the 18th century was destroyed by Persian forces in the 1740s; the building of 1846-1851 (Giovanni Scudieri); the present brick building of 1895 (funded by Taghiyev); restored in 1998. The only surviving mosque in Old Town.",
                "XVIII საუკუნის პირველი მეჩეთი სპარსელებმა 1740-იან წლებში დაანგრიეს; შენობა 1846-1851 (ჯოვანი სკუდიერი); დღევანდელი აგურის შენობა 1895 წლისაა (ტაღიევის დაფინანსებით); რესტავრაცია 1998 წელს."),
         src=[EN + "Juma_Mosque,_Tbilisi"]),
    dict(id="shia_mosque", rel="muslim", frm=1522, to=1951, date="1522-1524", lat=41.69033333, lon=44.80946944,
         name=N("Шиитская мечеть шаха Исмаила", "Shia mosque of Shah Ismail", "შაჰ-ისმაილის მეჩეთი"),
         status=N("снесена в 1951 (по инфобоксу 1952)", "demolished in 1951 (1952 per the infobox)", "დანგრეულია 1951 წელს (ინფობოქსში 1952)"),
         note=N("Построена в 1522-1524 при шахе Исмаиле I, расширена в 1606 при шахе Аббасе. Снесена при строительстве нового моста у Метехи.",
                "Built in 1522-1524 under Shah Ismail I, enlarged in 1606 under Shah Abbas. Demolished when the new bridge by Metekhi was built.",
                "აშენდა 1522-1524 წლებში შაჰ ისმაილ I-ის დროს, გაფართოვდა 1606 წელს შაჰ აბასის დროს. დაანგრიეს მეტეხთან ახალი ხიდის მშენებლობისას."),
         src=[RU + "Тбилисская_шиитская_мечеть", KA + "თბილისის_შაჰ-ისმაილის_მეჩეთი"]),
    dict(id="jvari_mama", rel="orthodox", frm=1825, date="1825", lat=41.69068, lon=44.806408,
         name=N("Церковь Джварис Мама", "Jvari Mama church", "ჯვარის მამის ეკლესია"),
         status=N("действует (с 1989)", "in use (since 1989)", "მოქმედია (1989 წლიდან)"),
         note=N("По ru основана в V веке при Вахтанге Горгасали; современная постройка 1825 года. По ka сохранившееся здание относится к XVI веку; в 1825 перестроено.",
                "Per ru founded in the 5th century under Vakhtang Gorgasali; the present building is of 1825. Per ka the surviving building is of the 16th century and was rebuilt in 1825.",
                "ru-ს მიხედვით დაარსებულია V საუკუნეში ვახტანგ გორგასლის დროს; დღევანდელი შენობა 1825 წლისაა. ka-ს მიხედვით შემორჩენილი შენობა XVI საუკუნისაა და 1825 წელს გადაკეთდა."),
         src=[RU + "Джварис_Мама", KA + "თბილისის_ჯვარის_მამის_ეკლესია"]),
    dict(id="peter_paul_catholic", rel="catholic", frm=1877, date="1870-1877", lat=41.7097, lon=44.8017,
         name=N("Католическая церковь Святых Петра и Павла", "St Peter and St Paul's Catholic Church", "წმინდა პეტრესა და პავლეს კათოლიკური ეკლესია"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Построена в 1870-1877 (освящена 16 октября 1877; архитектор Альберт Зальцман); купол добавлен в 1898. В 1999 здесь служил мессу Иоанн Павел II.",
                "Built in 1870-1877 (consecrated on 16 October 1877; architect Albert Zaltsman); the dome was added in 1898. Pope John Paul II celebrated Mass here in 1999.",
                "აშენდა 1870-1877 წლებში (აკურთხეს 1877 წლის 16 ოქტომბერს; არქიტექტორი ალბერტ ზალცმანი); გუმბათი 1898 წელს დაემატა. 1999 წელს აქ წირვა აღავლინა იოანე პავლე II-მ."),
         src=[EN + "St._Peter_and_St._Paul%27s_Church,_Tbilisi", RU + "Католическая_церковь_Святых_Петра_и_Павла_(Тбилиси)"]),
    dict(id="lutheran_pp", rel="lutheran", frm=1897, to=1940, date="1894-1897", lat=41.7094, lon=44.7973,
         name=N("Лютеранская церковь Святых Петра и Павла", "Lutheran Church of St Peter and St Paul", "წმინდა პეტრესა და პავლეს ლუთერანული ეკლესია"),
         status=N("снесена (закрыта в 1930-х, снесена около 1940)", "demolished (closed in the 1930s, pulled down about 1940)", "დანგრეულია (1930-იან წლებში დაიკეტა, დაახლოებით 1940 წელს დაანგრიეს)"),
         note=N("Неоготическая кирха, построена в 1894-1897 (архитектор Леопольд Бильфельдт). По инфобоксу снесена в 1940, по тексту закрыта в 1930-х и снесена в 1940-х. Новая лютеранская церковь «Примирение» освящена 26 октября 1997.",
                "A neo-Gothic church built in 1894-1897 (architect Leopold Bilfeldt). Demolished in 1940 per the infobox; the text says it was closed in the 1930s and pulled down in the 1940s. A new Lutheran church, 'Reconciliation', was consecrated on 26 October 1997.",
                "ნეოგოთიკური ეკლესია, აშენდა 1894-1897 წლებში (არქიტექტორი ლეოპოლდ ბილფელდტი). ინფობოქსის მიხედვით 1940 წელს დაანგრიეს, ტექსტის მიხედვით 1930-იან წლებში დაიკეტა, 1940-იან წლებში კი დაანგრიეს. ახალი ლუთერანული ეკლესია „შერიგება“ აკურთხეს 1997 წლის 26 ოქტომბერს."),
         src=[RU + "Лютеранская_церковь_Святых_Петра_и_Павла_(Тбилиси)"]),
    dict(id="yazidi_temple", rel="yazidi", frm=2015, date="2015", lat=41.70972222, lon=44.87166667,
         name=N("Храм Султана Езида", "Sultan Ezid Temple", "სულთან ეზიდის ტაძარი"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Езидский храм; открыт в июне 2015 (участок передан в 2009, проект начат в 2012, построен на частные средства).",
                "A Yazidi temple, opened in June 2015 (land donated in 2009, project started in 2012, privately financed).",
                "ეზიდური ტაძარი, გაიხსნა 2015 წლის ივნისში (მიწა გადაეცა 2009 წელს, პროექტი დაიწყო 2012 წელს, აშენდა კერძო სახსრებით)."),
         src=[EN + "Sultan_Ezid_Temple"]),
    dict(id="lurji", rel="orthodox", frm=1180, date="1180s", lat=41.70792, lon=44.78899,
         name=N("Лурджи монастырь (Синий монастырь)", "Lurji Monastery (Blue Monastery)", "ლურჯი მონასტერი"),
         status=N("действует (возвращён Церкви в 1990)", "in use (returned to the Church in 1990)", "მოქმედია (ეკლესიას დაუბრუნდა 1990 წელს)"),
         note=N("Построен в 1180-х (при царице Тамар); в XVII веке восстановлен как безкупольная базилика; 1873 перестройка с новым круглым куполом; церковь Иоанна Богослова 1898-1901. От здания XII века сохранились апсида и части стен. В советское время фабрика, склад, музей.",
                "Built in the 1180s (under Queen Tamar); restored as a domeless basilica in the 17th century; rebuilt in 1873 with a new round dome; the church of St John the Theologian dates from 1898-1901. Only the apse and parts of the walls survive from the 12th-century building. A factory, a warehouse and a museum in Soviet times.",
                "აშენდა 1180-იან წლებში (თამარ მეფის დროს); XVII საუკუნეში აღდგა უგუმბათო ბაზილიკად; 1873 წელს გადაკეთდა ახალი მრგვალი გუმბათით; იოანე ღვთისმეტყველის ეკლესია 1898-1901 წლებისაა. XII საუკუნის შენობიდან შემორჩა აფსიდა და კედლების ნაწილები."),
         src=[EN + "Lurji_Monastery", RU + "Лурджи_(Синий)_монастырь"]),
    dict(id="mamadaviti", rel="orthodox", frm=1871, date="1859-1871", lat=41.695833, lon=44.788889,
         name=N("Церковь Святого Давида (Мамадавити)", "St David's Church (Mamadaviti)", "მთაწმინდის მამადავითის ეკლესია"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Нынешняя церковь построена в 1859-1871 и освящена во имя св. Давида Гареджийского; прежняя церковь на этом месте снесена в 1809, новая поставлена на её фундаменте. Рядом Мтацминдский пантеон (открыт в 1929).",
                "The present church was built in 1859-1871 and dedicated to St David of Gareja; an older church on the site was demolished in 1809 and a new one built on its foundations. Next to it, the Mtatsminda Pantheon (opened in 1929).",
                "დღევანდელი ეკლესია აშენდა 1859-1871 წლებში და წმინდა დავით გარეჯელის სახელზეა აკურთხებული; ადგილზე არსებული უფრო ძველი ეკლესია 1809 წელს დაანგრიეს და მის საძირკველზე ახალი ააგეს. გვერდითაა მთაწმინდის პანთეონი (გაიხსნა 1929 წელს)."),
         src=[RU + "Церковь_Святого_Давида_(Тбилиси)", EN + "Mtatsminda_Pantheon"]),
    dict(id="nino", rel="orthodox", frm=1850, date="1850", lat=41.695116, lon=44.794669,
         name=N("Церковь равноапостольной Нины", "Church of St Nino", "წმინდა ნინოს ეკლესია"),
         status=N("действует (службы возобновлены 26 мая 1999)", "in use (services resumed on 26 May 1999)", "მოქმედია (მსახურება განახლდა 1999 წლის 26 მაისს)"),
         note=N("Ул. Шио Читадзе, 9. По тексту построена около 1850 для женского института (архитектор Альберт Зальцман); в инфобоксе указан 1884. Закрыта в советское время.",
                "Shio Chitadze Street 9. The text says it was built about 1850 for a women's institute (architect Albert Zaltsman); the infobox gives 1884. Closed in Soviet times.",
                "შიო ჩიტაძის ქ. 9. ტექსტის მიხედვით აშენდა დაახლოებით 1850 წელს ქალთა ინსტიტუტისთვის (არქიტექტორი ალბერტ ზალცმანი); ინფობოქსში მითითებულია 1884. საბჭოთა პერიოდში დაიკეტა."),
         src=[RU + "Церковь_равноапостольной_Нины_(Тбилиси)"]),
    dict(id="kari", rel="orthodox", frm=1640, date="1640", lat=41.694669, lon=44.806507,
         name=N("Церковь Святого Георгия Кари", "Church of St George Kari", "წმინდა გიორგის კარის ეკლესია"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Первая церковь, по преданию, V века (Вахтанг Горгасали); восстановлена около 1640 при царе Ростоме, ремонт 1710, реставрация 1991-1992. Ул. Шавтели, 4.",
                "The first church dates, by tradition, from the 5th century (Vakhtang Gorgasali); re-established about 1640 under King Rostom, repaired in 1710, restored in 1991-1992. Shavteli Street 4.",
                "პირველი ეკლესია, გადმოცემით, V საუკუნისაა (ვახტანგ გორგასალი); აღდგა დაახლოებით 1640 წელს როსტომ მეფის დროს, შეკეთდა 1710 წელს, რესტავრაცია 1991-1992 წლებში. შავთელის ქ. 4."),
         src=[RU + "Церковь_Святого_Георгия_Кари"]),
    dict(id="michael_tver", rel="russian", frm=1913, date="1911-1913", lat=41.70055556, lon=44.78888889,
         name=N("Церковь Михаила Тверского", "Church of St Michael of Tver", "წმინდა მიხეილ ტვერელის ეკლესია"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Русская православная церковь на ул. Залдастанишвили, 36; построена в 1911-1913 (архитектор Иоганн Дитцман).",
                "A Russian Orthodox church on Zaldastanishvili Street 36; built in 1911-1913 (architect Johann Ditsman).",
                "რუსული მართლმადიდებლური ეკლესია ზალდასტანიშვილის ქ. 36-ზე; აშენდა 1911-1913 წლებში (არქიტექტორი იოჰან დიცმანი)."),
         src=[RU + "Церковь_Михаила_Тверского_(Тбилиси)"]),
    dict(id="old_trinity", rel="orthodox", frm=1863, date="1863", lat=41.69664, lon=44.80184,
         name=N("Старая Троицкая церковь (Калоубани)", "Old Trinity Church (Kaloubani)", "ძველი სამების ეკლესია"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Первое упоминание 1790, освящена в 1863. Ул. Эроши Манджгаладзе, 6.",
                "First mentioned in 1790, consecrated in 1863. Eroshi Manjgaladze Street 6.",
                "პირველად მოხსენიებულია 1790 წელს, აკურთხეს 1863 წელს. ეროში მანჯგალაძის ქ. 6."),
         src=[RU + "Старая_Троицкая_церковь_(Тбилиси)"]),
    dict(id="alexander_nevsky", rel="russian", frm=1897, to=1930, date="1871-1897", lat=41.69666667, lon=44.79805556,
         name=N("Александро-Невский военный собор", "Alexander Nevsky Military Cathedral", "ტფილისის წმინდა ალექსანდრე ნეველის სამხედრო ტაძარი"),
         status=N("снесён в 1930; на месте Дом Правительства (ныне Парламент Грузии)", "demolished in 1930; the Government House (now the Parliament) stands on the site", "დანგრეულია 1930 წელს; ადგილზე სახელმწიფო სახლია (დღეს საქართველოს პარლამენტი)"),
         note=N("Заложен 16 апреля 1871 (по ru 6 апреля) на Гунибской площади; в 1877 стройка остановлена, возобновлена в 1890, новый фундамент 1891; освящён 21 мая 1897 (архитектор Давид Гримм). Снесён по указанию Берии. Рядом в Александровском саду стояла малая часовня Александра Невского (заложена в 1888; к 1925 снята), см. статью на ka.wikipedia.",
                "Begun on 16 April 1871 (6 April per ru) on Gunib Square; suspended in 1877, resumed in 1890, new foundation in 1891; consecrated on 21 May 1897 (architect David Grimm). Demolished on Beria's order. Nearby in Alexander's Garden stood a small Alexander Nevsky chapel (founded in 1888; removed by 1925), see the ka.wikipedia article.",
                "ჩაეყარა 1871 წლის 16 აპრილს ღუნიბის მოედანზე; 1877 წელს მშენებლობა შეჩერდა, 1890 წელს განახლდა, ახალი საძირკველი 1891 წელს; აკურთხეს 1897 წლის 21 მაისს (არქიტექტორი დავით გრიმი). დაანგრიეს ბერიას მითითებით. ახლოს ალექსანდრეს ბაღში იდგა ალექსანდრე ნეველის პატარა სამლოცველო (1888; 1925 წლისთვის მოხსნილია)."),
         src=[EN + "Alexander_Nevsky_Cathedral,_Tiflis", RU + "Собор_Александра_Невского_(Тифлис)", KA + "ტფილისის_სამხედრო_ტაძარი", KA + "თბილისის_წმინდა_ალექსანდრე_ნეველის_სამლოცველო"]),
    dict(id="nevsky_chapel", rel="russian", frm=1888, to=1925, date="1888", lat=41.6985, lon=44.7996, approx=True,
         name=N("Часовня Александра Невского (сад 9 апреля)", "Alexander Nevsky chapel (the garden of 9 April)", "წმინდა ალექსანდრე ნეველის სამლოცველო"),
         status=N("не сохранилась (к 1925 снята)", "does not survive (removed by 1925)", "არ შემორჩა (1925 წლისთვის მოხსნილია)"),
         note=N("Заложена в 1888 в Александровском саду в память о спасении императорской семьи при крушении поезда; для нижних чинов, на месте нынешнего памятника Георгию Леонидзе. По описанию 1925 года военная часовня в конце сада снята. Точка на карте приблизительная: координат нет, взят центр сада.",
                "Founded in 1888 in Alexander's Garden to commemorate the survival of the imperial family in a railway accident; for the lower ranks, on the site of today's monument to Giorgi Leonidze. A description of 1925 says the military chapel at the end of the garden had been removed. The point on the map is approximate: no coordinates exist, the centre of the garden is used.",
                "ჩაეყარა საძირკველი 1888 წელს ალექსანდრეს ბაღში საიმპერატორო ოჯახის მატარებლის კატასტროფისგან გადარჩენის აღსანიშნავად; დაბალი ჩინის სამხედროებისთვის, დღევანდელი გიორგი ლეონიძის ძეგლის ადგილზე. 1925 წლის აღწერით ბაღის ბოლოში მდებარე სამხედრო სამლოცველო მოხსნილია. წერტილი რუკაზე მიახლოებითია."),
         src=[KA + "თბილისის_წმინდა_ალექსანდრე_ნეველის_სამლოცველო", RU + "Парк_9_апреля_(Тбилиси)"]),
    dict(id="nicholas_military", rel="russian", frm=1848, to=1921, date="1848-1890", lat=41.6981, lon=44.7991, approx=True,
         name=N("Военная церковь св. Николая (Александровский сад)", "St Nicholas military church (Alexander's Garden)", "წმინდა ნიკოლოზის სამხედრო ტაძარი (ალექსანდრეს ბაღი)"),
         status=N("не сохранилась; на месте круглый театр", "does not survive; a round theatre stands on the site", "არ შემორჩა; ადგილზე მრგვალი თეატრია"),
         note=N("Заложена в 1848 (сперва у нынешнего пересечения улиц Табукашвили и Собчака); после 1888 перенесена вглубь сада, фундамент освящён в 1889, здание в 1890 (архитектор Бульфруа). В 1921 приписана к Верийской церкви св. Николая (поэтому на карте до 1921); позднее на месте открытый кинотеатр, ныне круглый театр. Точка приблизительная.",
                "Founded in 1848 (first at today's crossing of Tabukashvili and Sobchak streets); after 1888 moved deeper into the garden, the foundation consecrated in 1889 and the building in 1890 (architect Boulfroy). In 1921 it was assigned to the Vera church of St Nicholas (so it is shown until 1921); later an open-air cinema stood on the site, now a round theatre. The point is approximate.",
                "საძირკველი ჩაეყარა 1848 წელს (თავდაპირველად დღევანდელი ტაბუკაშვილისა და სობჭაკის ქუჩების გადაკვეთაზე); 1888 წლის შემდეგ ბაღის სიღრმეში გადაიტანეს, საძირკველი 1889 წელს აკურთხეს, შენობა — 1890 წელს (არქიტექტორი ბულფრუა). 1921 წელს ვერის წმინდა ნიკოლოზის ეკლესიას მიეწერა; შემდგომ ადგილზე ღია კინოთეატრი იყო, დღეს მრგვალი თეატრია. წერტილი მიახლოებითია."),
         src=[KA + "თბილისის_წმინდა_ალექსანდრე_ნეველის_სამლოცველო", RU + "Парк_9_апреля_(Тбილиси)".replace("Тбилиси", "Тбилиси")]),
    dict(id="kashveti", rel="orthodox", frm=1910, date="1904-1910", lat=41.697954, lon=44.799324,
         name=N("Церковь Кашвети (св. Георгия)", "Kashveti Church (St George)", "ქაშვეთის წმინდა გიორგის ტაძარი"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Построена в 1904-1910 (Леопольд Бильфельдт) по образцу Самтависи; до неё на месте стояла кирпичная церковь 1753 года. Росписи Ладо Гудиашвили, 1947.",
                "Built in 1904-1910 (Leopold Bilfeldt) on the model of Samtavisi; an earlier brick church of 1753 stood on the site. Frescoes by Lado Gudiashvili, 1947.",
                "აშენდა 1904-1910 წლებში (ლეოპოლდ ბილფელდტი) სამთავისის მიხედვით; ადგილზე 1753 წლის აგურის ეკლესია იდგა. ლადო გუდიაშვილის მოხატულობა, 1947."),
         src=[EN + "Kashveti_Church"]),
    dict(id="sameba", rel="orthodox", frm=2004, date="1995-2004", lat=41.6975, lon=44.81666667,
         name=N("Собор Святой Троицы (Самеба)", "Holy Trinity Cathedral (Sameba)", "წმინდა სამების საკათედრო ტაძარი"),
         status=N("действует", "in use", "მოქმედია"),
         note=N("Заложен 23 ноября 1995, освящён 23 ноября 2004 (Илия II). Главный собор Грузинской православной церкви; частично построен на месте армянского кладбища Ходживанк.",
                "The foundation was laid on 23 November 1995, consecrated on 23 November 2004 (Ilia II). The main cathedral of the Georgian Orthodox Church; partly built over the Khojivank Armenian cemetery.",
                "საძირკველი ჩაეყარა 1995 წლის 23 ნოემბერს, აკურთხეს 2004 წლის 23 ნოემბერს (ილია II). ქართული მართლმადიდებელი ეკლესიის მთავარი ტაძარი; ნაწილობრივ ხოჯივანქის სომხური სასაფლაოს ადგილზეა აშენებული."),
         src=[EN + "Holy_Trinity_Cathedral_of_Tbilisi"]),
]


def main():
    out = []
    for it in ITEMS:
        o = {"id": it["id"], "rel": it["rel"], "from": it["frm"], "date": it["date"], "lat": it["lat"], "lon": it["lon"],
             "name": it["name"], "status": it["status"], "note": it["note"], "src": it["src"]}
        if "to" in it:
            o["to"] = it["to"]
        if it.get("approx"):
            o["approx"] = True
        if it["id"] in PHOTOS["objects"]:
            o["ph"] = "|".join(PHOTOS["objects"][it["id"]])
        out.append(o)
    # the other worship buildings of the heritage register (tools/add_register_religious.py), after the curated ones
    reg_path = os.path.join(ROOT, "data", "religious_register.json")
    if os.path.exists(reg_path):
        out.extend(json.load(open(reg_path, encoding="utf-8")))
    out.sort(key=lambda x: x["from"])
    p = os.path.join(ROOT, "site", "data", "religious.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "buildings ->", p)
    # the licence data of the photographs go into site/data/photos.json (build_site_data.py does the same when it rebuilds that file)
    pp = os.path.join(ROOT, "site", "data", "photos.json")
    photos = json.load(open(pp, encoding="utf-8"))
    used = {t for ts in PHOTOS["objects"].values() for t in ts}
    for t in used:
        photos[t] = PHOTOS["info"][t]
    json.dump(photos, open(pp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(len(used), "photographs of the buildings in", pp)


if __name__ == "__main__":
    main()
