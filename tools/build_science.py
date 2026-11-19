"""Build site/data/science.json: the layer "science and culture" (kind "science" and kind "culture"), points that appear in a year.
Every fact comes from a Wikipedia page read for this project (en, ru and ka) on 2026-11-19; coordinates are those of the page (the infobox or the API of the page),
never guessed. Dates: "from" is the year the institution or the building appears at this place; "sf" (site from), when given, is the year the present building was
completed or taken into use, before that year the point is drawn faint (the institution existed, but elsewhere). Where the pages disagree, the note says so.
Georgian texts are written by the assistant and not checked by a native speaker.
Usage: python -X utf8 -P tools/build_science.py
"""
import json
import os
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EN, RU, KA = "https://en.wikipedia.org/wiki/", "https://ru.wikipedia.org/wiki/", "https://ka.wikipedia.org/wiki/"


def U(base, title):
    return base + urllib.parse.quote(title.replace(" ", "_"), safe="_(),'")


def N(ru, en, ka):
    return {"ru": ru, "en": en, "ka": ka}


def dms(d, m, s):
    return round(d + m / 60 + s / 3600, 5)


ITEMS = [
    # ------------------------------------------------------------------ science
    dict(id="observatory", kind="science", frm=1837, lat=dms(41, 43, 2), lon=dms(44, 47, 22), approx=True,
         name=N("Тифлисская физическая обсерватория (ныне Геофизическая)", "Tiflis Physical Observatory (now Geophysical)", "თბილისის ფიზიკური ობსერვატორია (დღეს გეოფიზიკური)"),
         founded="1837", built="1861",
         note=N("Основана в 1837; регулярные наблюдения с 1 мая 1844. Несколько раз меняла место (холм Сололаки, Авлабар, в 1851); новое здание в Куки введено 1 мая 1861. Непрерывные геомагнитные записи 1880–1991. Точка на карте приблизительная: это координаты страницы, а какое именно здание сегодня занимает обсерватория, страница не говорит. Источник на русском языке, статьи на английском нет.",
                "Founded in 1837; regular observations from 1 May 1844. It changed its place several times (Sololaki hill, Avlabari in 1851); the new building in Kuki came into service on 1 May 1861. Continuous geomagnetic records 1880-1991. The point on the map is approximate: these are the coordinates of the page, which does not say which building the observatory occupies today. The source is in Russian, there is no English article.",
                "დაარსდა 1837 წელს; რეგულარული დაკვირვებები 1844 წლის 1 მაისიდან. რამდენჯერმე შეიცვალა ადგილი (სოლოლაკის გორა, ავლაბარი 1851 წელს); ახალი შენობა კუკიაში ექსპლუატაციაში შევიდა 1861 წლის 1 მაისს. უწყვეტი გეომაგნიტური ჩანაწერები 1880–1991. წერტილი რუკაზე მიახლოებითია: ეს გვერდის კოორდინატებია, რომელიც არ ამბობს, რომელ შენობას იკავებს დღეს ობსერვატორია. წყარო რუსულენოვანია."),
         src=[U(RU, "Тифлисская физическая обсерватория")]),
    dict(id="botanical", kind="science", frm=1845, lat=dms(41, 41, 10), lon=dms(44, 48, 27),
         name=N("Ботанический сад (Национальный ботанический сад Грузии)", "National Botanical Garden of Georgia", "საქართველოს ეროვნული ბოტანიკური ბაღი"),
         founded="1845",
         note=N("Официально основан в 1845 как Тифлисский ботанический сад; царские сады на этом месте известны с 1620-х (описаны в 1671). Центр флористики с 1888; около 4500 таксонов на 161 га; обновлён в 2018.",
                "Officially established in 1845 as the Tiflis Botanical Garden; royal gardens on the site are known from the 1620s (described in 1671). A centre of floristics from 1888; about 4,500 taxa on 161 ha; renovated in 2018.",
                "ოფიციალურად დაარსდა 1845 წელს თბილისის ბოტანიკური ბაღის სახელით; სამეფო ბაღები აქ ცნობილია 1620-იანი წლებიდან (აღწერილია 1671 წელს). ფლორისტიკის ცენტრი 1888 წლიდან; დაახლოებით 4500 ტაქსონი 161 ჰექტარზე; განახლდა 2018 წელს."),
         src=[U(EN, "National Botanical Garden of Georgia")]),
    dict(id="library", kind="science", frm=1846, sf=1916, lat=dms(41, 41, 50), lon=dms(44, 48, 2),
         name=N("Национальная библиотека Грузии (Тифлисская публичная библиотека)", "National Library of Georgia (Tiflis Public Library)", "საქართველოს ეროვნული ბიბლიოთეკა (თბილისის საჯარო ბიბლიოთეკა)"),
         founded="1846", built="1913–1916",
         note=N("Основана в 1846 как Тифлисская публичная библиотека; в 1851 построено новое здание (другое место). Нынешнее здание №1 (ул. Гудиашвили, 3) возведено в 1913–1916 как Дворянский банк, архитектор Анатолий Калгин. 30 мая 1923 основана Государственная публичная библиотека; с 2000 носит имя Ильи Чавчавадзе. До 1916 точка показана бледной.",
                "Founded in 1846 as the Tiflis Public Library; a new building was put up in 1851 (another place). The present building no. 1 (3 Gudiashvili St.) was built in 1913-1916 as the Bank of the Nobility, architect Anatoly Kalgin. The State Public Library was founded on 30 May 1923; named after Ilia Chavchavadze since 2000. Before 1916 the point is faint.",
                "დაარსდა 1846 წელს თბილისის საჯარო ბიბლიოთეკის სახელით; 1851 წელს ახალი შენობა აშენდა (სხვა ადგილას). დღევანდელი შენობა №1 (გუდიაშვილის ქ. 3) აშენდა 1913–1916 წლებში თავადაზნაურთა ბანკად, არქიტექტორი ანატოლი კალგინი. 1923 წლის 30 მაისს დაარსდა სახელმწიფო საჯარო ბიბლიოთეკა; 2000 წლიდან ილია ჭავჭავაძის სახელს ატარებს. 1916 წლამდე წერტილი ფერმკრთალია."),
         src=[U(EN, "National Library of Georgia")]),
    dict(id="janashia", kind="culture", frm=1852, lat=dms(41, 41, 46), lon=dms(44, 48, 1),
         name=N("Музей Грузии имени Симона Джанашиа (Кавказский музей)", "Simon Janashia Museum of Georgia (Caucasian Museum)", "სიმონ ჯანაშიას სახელობის საქართველოს მუზეუმი (კავკასიის მუზეუმი)"),
         founded="1852",
         note=N("Основан 10 мая 1852 как музей Кавказского отдела Императорского Русского географического общества; в 1865 стал Кавказским музеем (по инициативе Густава Радде); с 1919 Музей Грузии; с 1947 имя Джанашиа; с 2004 в составе Национального музея. Здание на проспекте Руставели спроектировал Николай Северов в 1910 на месте старого здания А. Зальцмана (год завершения страница не называет). Находки из Дманиси, Ахалгорийский клад.",
                "Founded on 10 May 1852 as the museum of the Caucasian Department of the Imperial Russian Geographical Society; the Caucasian Museum from 1865 (on the initiative of Gustav Radde); the Museum of Georgia from 1919; named after Janashia in 1947; part of the Georgian National Museum since 2004. The building on Rustaveli Avenue was designed by Nikolay Severov in 1910 on the site of an older building by A. Zaltsman (the page gives no year of completion). The Dmanisi finds, the Akhalgori hoard.",
                "დაარსდა 1852 წლის 10 მაისს, როგორც რუსეთის იმპერიული გეოგრაფიული საზოგადოების კავკასიის განყოფილების მუზეუმი; 1865 წლიდან კავკასიის მუზეუმი (გუსტავ რადეს ინიციატივით); 1919 წლიდან საქართველოს მუზეუმი; 1947 წელს ჯანაშიას სახელი მიენიჭა; 2004 წლიდან ეროვნული მუზეუმის შემადგენლობაშია. რუსთაველის გამზირზე შენობა დააპროექტა ნიკოლაი სევეროვმა 1910 წელს ა. ცალცმანის ძველი შენობის ადგილას (დასრულების წელს გვერდი არ ასახელებს). დმანისის აღმოჩენები, ახალგორის განძი."),
         src=[U(EN, "Simon Janashia Museum of Georgia")]),
    dict(id="tsu", kind="science", frm=1918, lat=dms(41, 42, 36), lon=dms(44, 46, 42),
         name=N("Тбилисский государственный университет имени Ивана Джавахишвили", "Ivane Javakhishvili Tbilisi State University", "ივანე ჯავახიშვილის სახელობის თბილისის სახელმწიფო უნივერსიტეტი"),
         founded="8.02.1918", built="1899–1906",
         note=N("Первый университет Грузии и Кавказа. Основан в феврале 1918 (в начале статьи 8 февраля, в истории университета 26 января 1918 как день открытия). Главный корпус — здание бывшей Грузинской дворянской гимназии (арх. Симон Клдиашвили, 1899–1906). Здесь школы математики (Размадзе), физики (Андроникашвили) и психологии (Узнадзе).",
                "The first university in Georgia and the Caucasus. Established in February 1918 (the lead of the article says 8 February, the history section says it was opened on 26 January 1918). The main building is the former Georgian Nobility Gymnasium (architect Simon Kldiashvili, 1899-1906). Schools of mathematics (Razmadze), physics (Andronikashvili) and psychology (Uznadze).",
                "საქართველოსა და კავკასიის პირველი უნივერსიტეტი. დაარსდა 1918 წლის თებერვალში (სტატიის შესავალში 8 თებერვალი, ისტორიის ნაწილში გახსნა 1918 წლის 26 იანვარს). მთავარი კორპუსი ყოფილი ქართული სათავადაზნაურო გიმნაზიის შენობაა (არქიტექტორი სიმონ კლდიაშვილი, 1899–1906). მათემატიკის (რაზმაძე), ფიზიკის (ანდრონიკაშვილი) და ფსიქოლოგიის (უზნაძე) სკოლები."),
         src=[U(EN, "Tbilisi State University"), U(KA, "თბილისის სათავადაზნაურო გიმნაზია")]),
    dict(id="tsmu", kind="science", frm=1918, lat=dms(41, 43, 39), lon=dms(44, 45, 14),
         name=N("Тбилисский государственный медицинский университет", "Tbilisi State Medical University", "თბილისის სახელმწიფო სამედიცინო უნივერსიტეტი"),
         founded="1918",
         note=N("Вырос из медицинского факультета Тбилисского университета (в списке вузов «основан в 1918»); университетом называется с 1992.",
                "It grew out of the medical faculty of Tbilisi University (the list of universities says \"founded in 1918\"); a university by name since 1992.",
                "გაიზარდა თბილისის უნივერსიტეტის სამედიცინო ფაკულტეტიდან (უნივერსიტეტების ჩამონათვალში „დაარსდა 1918 წელს“); უნივერსიტეტი 1992 წლიდან."),
         src=[U(EN, "Tbilisi State Medical University")]),
    dict(id="gtu", kind="science", frm=1922, lat=dms(41, 43, 1), lon=dms(44, 46, 41),
         name=N("Грузинский технический университет", "Georgian Technical University", "საქართველოს ტექნიკური უნივერსიტეტი"),
         founded="16.01.1922",
         note=N("Основан 16 января 1922 как политехнический факультет Тбилисского университета; первую лекцию читал Андрея Размадзе; самостоятельный Грузинский политехнический институт с 1928; позже имени Ленина; статус университета к 1990. Крупнейший технический вуз Грузии.",
                "Founded on 16 January 1922 as the polytechnic faculty of Tbilisi University; the first lecture was read by Andrea Razmadze; an independent Georgian Polytechnic Institute from 1928 (later named after Lenin); university status by 1990. The largest technical university in Georgia.",
                "დაარსდა 1922 წლის 16 იანვარს თბილისის უნივერსიტეტის პოლიტექნიკურ ფაკულტეტად; პირველი ლექცია წაიკითხა ანდრია რაზმაძემ; დამოუკიდებელი ქართული პოლიტექნიკური ინსტიტუტი 1928 წლიდან (შემდეგ ლენინის სახელობის); უნივერსიტეტის სტატუსი 1990 წლისთვის. საქართველოს უდიდესი ტექნიკური უნივერსიტეტი."),
         src=[U(EN, "Georgian Technical University")]),
    dict(id="eliava", kind="science", frm=1923, lat=dms(41, 44, 3), lon=dms(44, 46, 19),
         name=N("Институт бактериофага имени Георгия Элиава", "George Eliava Institute of Bacteriophage, Microbiology and Virology", "გიორგი ელიავას სახელობის ბაქტერიოფაგის, მიკრობიოლოგიისა და ვირუსოლოგიის ინსტიტუტი"),
         founded="1923",
         note=N("Открыт в 1923 как бактериологическая лаборатория (основатель Георгий Элиава); в инфобоксе статьи указан 1916, расхождение страница не объясняет. С 1930-х развивает фаготерапию. В 1938 слит в институт микробиологии, эпидемиологии и бактериофага; в 1951 переименован; в 1991 повреждён в войне. Работает и сегодня (ул. Готуа, 3).",
                "Opened in 1923 as a bacteriological laboratory (founder George Eliava); the infobox of the article says 1916, a difference the page does not explain. Develops phage therapy since the 1930s. Merged in 1938 into an institute of microbiology, epidemiology and bacteriophage; renamed in 1951; damaged in the war of 1991. Still active (3 Gotua St.).",
                "გაიხსნა 1923 წელს ბაქტერიოლოგიურ ლაბორატორიად (დამფუძნებელი გიორგი ელიავა); სტატიის ინფოყუთში მითითებულია 1916, განსხვავებას გვერდი არ ხსნის. ფაგოთერაპიას 1930-იანი წლებიდან ავითარებს. 1938 წელს გაერთიანდა მიკრობიოლოგიის, ეპიდემიოლოგიისა და ბაქტერიოფაგის ინსტიტუტში; 1951 წელს გადაერქვა სახელი; 1991 წელს დაზიანდა ომში. დღესაც მოქმედებს (გოტუას ქ. 3)."),
         src=[U(EN, "George Eliava Institute")]),
    dict(id="academy", kind="science", frm=1941, sf=1953, lat=dms(41, 42, 11), lon=dms(44, 47, 27),
         name=N("Национальная академия наук Грузии", "Georgian National Academy of Sciences", "საქართველოს მეცნიერებათა ეროვნული აკადემია"),
         founded="02.1941", built="1953",
         note=N("Основана в феврале 1941 (по грузинской статье 25 февраля, по русской 10 февраля). Координирует научные исследования; 14 научных учреждений. Здание Президиума (пр. Руставели, 52) датировано 1953 в реестре памятников, русская статья называет здание «Грузуголь» (1953); архитектора страницы не называют. До 1953 точка бледная.",
                "Founded in February 1941 (the Georgian article says 25 February, the Russian one 10 February). Coordinates research; 14 research institutions. The building of the Presidium (52 Rustaveli Ave.) is dated 1953 in the heritage register, and the Russian article calls the building \"Gruzugol\" (1953); the pages do not name the architect. Before 1953 the point is faint.",
                "დაარსდა 1941 წლის თებერვალში (ქართული სტატიით 25 თებერვალი, რუსულით 10 თებერვალი). კოორდინაციას უწევს სამეცნიერო კვლევებს; 14 სამეცნიერო დაწესებულება. პრეზიდიუმის შენობა (რუსთაველის გამზ. 52) ძეგლთა რეესტრში 1953 წლითაა დათარიღებული, რუსული სტატია შენობას „გრუზუგოლს“ (1953) უწოდებს; არქიტექტორს გვერდები არ ასახელებს. 1953 წლამდე წერტილი ფერმკრთალია."),
         src=[U(EN, "Georgian National Academy of Sciences"), U(RU, "Национальная академия наук Грузии"), U(KA, "საქართველოს მეცნიერებათა ეროვნული აკადემია")]),
    dict(id="scilib", kind="science", frm=1941, lat=dms(41, 42, 57), lon=dms(44, 46, 58),
         name=N("Национальная научная библиотека", "National Science Library", "ეროვნული სამეცნიერო ბიბლიოთეკა"),
         founded="1941",
         note=N("Основана в 1941 для сотрудников Академии наук; здания: 1941 (бывшая центральная библиотека академии), 1961 (библиотека-музей Иосифа Гришашвили), 1965 (библиотека науки и техники). Крупнейшая библиотека Грузии по описанию статьи.",
                "Founded in 1941 for the staff of the Academy of Sciences; buildings: 1941 (the former central library of the academy), 1961 (the Ioseb Grishashvili Library-Museum), 1965 (the Science and Technology Library). The largest library in Georgia, according to the article.",
                "დაარსდა 1941 წელს მეცნიერებათა აკადემიის თანამშრომლებისთვის; შენობები: 1941 (აკადემიის ყოფილი ცენტრალური ბიბლიოთეკა), 1961 (იოსებ გრიშაშვილის ბიბლიოთეკა-მუზეუმი), 1965 (მეცნიერებისა და ტექნიკის ბიბლიოთეკა). სტატიის მიხედვით საქართველოს უდიდესი ბიბლიოთეკა."),
         src=[U(EN, "National Science Library (Georgia)")]),
    dict(id="zoo", kind="science", frm=1927, lat=dms(41, 42, 47), lon=dms(44, 46, 37),
         name=N("Тбилисский зоопарк", "Tbilisi Zoo", "თბილისის ზოოლოგიური პარკი"),
         founded="10.02.1927",
         note=N("Решение горсовета об основании 10 февраля 1927; проект группы грузинских и русских специалистов. Около 300 видов. Паводок 14 июня 2015 унёс много животных; план переезда 2012 года отложен, зоопарк остался в долине реки Вере.",
                "The city council decided to found it on 10 February 1927; designed by a group of Georgian and Russian specialists. About 300 species. The flood of 14 June 2015 killed many animals; the relocation plan of 2012 was delayed and the zoo stayed in the Vere valley.",
                "ქალაქის საბჭომ დაარსების შესახებ გადაწყვიტა 1927 წლის 10 თებერვალს; პროექტი ქართველი და რუსი სპეციალისტების ჯგუფისაა. დაახლოებით 300 სახეობა. 2015 წლის 14 ივნისის წყალდიდობამ ბევრი ცხოველი იმსხვერპლა; 2012 წლის გადატანის გეგმა გადაიდო, ზოოპარკი ვერეს ხეობაში დარჩა."),
         src=[U(EN, "Tbilisi Zoo")]),
    dict(id="razmadze", kind="science", frm=1933, lat=41.720756, lon=44.744851,
         name=N("Математический институт имени Андрея Размадзе", "Andrea Razmadze Mathematical Institute", "ანდრია რაზმაძის სახელობის მათემატიკის ინსტიტუტი"),
         founded="1933",
         note=N("Основан в 1933 как институт математики, физики и механики при Тбилисском университете; в 1935 ушёл в Грузинский филиал Академии наук СССР; имя Размадзе с 1944; с 1 января 2011 снова в составе университета. Адрес по русской статье ул. Тамарашвили, 6 (в советское время ул. Дзержинского, 8), по грузинской — второй тупик Мераба Алексидзе, 2; здесь точка русской статьи. Английской статьи нет.",
                "Founded in 1933 as an institute of mathematics, physics and mechanics at Tbilisi University; in 1935 it passed to the Georgian branch of the USSR Academy of Sciences; named after Razmadze in 1944; part of the university again from 1 January 2011. The address per the Russian article is 6 Tamarashvili St. (in Soviet times 8 Dzerzhinsky St.), per the Georgian one 2 Merab Aleksidze II lane; the point is that of the Russian article. There is no English article.",
                "დაარსდა 1933 წელს თბილისის უნივერსიტეტთან, როგორც მათემატიკის, ფიზიკისა და მექანიკის ინსტიტუტი; 1935 წელს გადავიდა სსრკ მეცნიერებათა აკადემიის საქართველოს ფილიალში; რაზმაძის სახელი 1944 წლიდან; 2011 წლის 1 იანვრიდან ისევ უნივერსიტეტის შემადგენლობაშია. მისამართი რუსული სტატიით თამარაშვილის ქ. 6, ქართულით მერაბ ალექსიძის მე-2 შესახვევი 2; წერტილი რუსული სტატიისაა."),
         src=[U(RU, "Тбилисский математический институт")]),
    dict(id="geography", kind="science", frm=1945, lat=41.72030051, lon=44.74393751,
         name=N("Институт географии имени Вахушти Багратиони", "Vakhushti Bagrationi Institute of Geography", "ვახუშტი ბაგრატიონის გეოგრაფიის ინსტიტუტი"),
         founded="1945",
         note=N("Основан в 1945 на базе кафедр географии университета (по английской статье 1933 как институт при университете, в 1945 вошёл в Академию наук). С 2010 снова в составе университета. Здание и адрес страницы не называют.",
                "Founded in 1945 on the basis of the geography chairs of the university (the English article says 1933 as an institute of the university, joining the Academy in 1945). Part of the university again from 2010. The pages do not name the building or the address.",
                "დაარსდა 1945 წელს უნივერსიტეტის გეოგრაფიის კათედრების ბაზაზე (ინგლისური სტატიით 1933 წელს უნივერსიტეტთან, 1945 წელს აკადემიაში გადავიდა). 2010 წლიდან ისევ უნივერსიტეტის შემადგენლობაშია. შენობას და მისამართს გვერდები არ ასახელებს."),
         src=[U(RU, "Институт географии имени Вахушти Багратиони"), U(EN, "Vakhushti Bagrationi Institute of Geography"), U(KA, "ვახუშტი ბაგრატიონის გეოგრაფიის ინსტიტუტი")]),
    dict(id="agrarian", kind="science", frm=1929, lat=dms(41, 48, 20), lon=dms(44, 46, 6),
         name=N("Аграрный университет Грузии", "Agricultural University of Georgia", "საქართველოს აგრარული უნივერსიტეტი"),
         founded="1929",
         note=N("Основан в 1929 (по тексту статьи); частный некоммерческий университет; адрес: аллея Давида Агмашенебели, 240. Три школы: сельскохозяйственных и естественных наук, инженерно-технологическая, бизнеса.",
                "Founded in 1929 (per the text of the article); a private non-profit university; address: Davit Aghmashenebeli Alley 240. Three schools: agricultural and natural sciences, engineering and technology, business.",
                "დაარსდა 1929 წელს (სტატიის ტექსტით); კერძო არაკომერციული უნივერსიტეტი; მისამართი: დავით აღმაშენებლის ხეივანი 240. სამი სკოლა: სასოფლო-სამეურნეო და საბუნებისმეტყველო მეცნიერებათა, საინჟინრო-ტექნოლოგიური, ბიზნესის."),
         src=[U(EN, "Agricultural University of Georgia")]),
    dict(id="andronikashvili", kind="science", frm=1950, lat=dms(41, 43, 15), lon=dms(44, 44, 41),
         name=N("Институт физики имени Элефтера Андроникашвили", "Elephter Andronikashvili Institute of Physics", "ელეფთერ ანდრონიკაშვილის სახელობის ფიზიკის ინსტიტუტი"),
         founded="12.1950",
         note=N("Основан в декабре 1950; сначала на площади Ладо Гудиашвили, затем в специально построенном здании на ул. Тамарашвили (год и архитектор не названы). Ядерный реактор: строительство с 1957, открыт 21 ноября 1959, работал до 1990. Работы по жидкому гелию и космическим лучам; участвует в эксперименте ATLAS (ЦЕРН). Сегодня исследовательский институт университета.",
                "Founded in December 1950; first on Lado Gudiashvili Square, later in a purpose-built building on Tamarashvili St. (year and architect not stated). Nuclear reactor: construction began in 1957, opened on 21 November 1959, operated until 1990. Work on liquid helium and cosmic rays; takes part in the ATLAS experiment (CERN). Today a research institute of the university.",
                "დაარსდა 1950 წლის დეკემბერში; თავდაპირველად ლადო გუდიაშვილის მოედანზე, შემდეგ თამარაშვილის ქუჩაზე სპეციალურად აშენებულ შენობაში (წელი და არქიტექტორი არ არის მითითებული). ბირთვული რეაქტორი: მშენებლობა 1957 წლიდან, გაიხსნა 1959 წლის 21 ნოემბერს, მუშაობდა 1990 წლამდე. მუშაობა თხევად ჰელიუმსა და კოსმოსურ სხივებზე; მონაწილეობს ATLAS-ის ექსპერიმენტში (CERN). დღეს უნივერსიტეტის კვლევითი ინსტიტუტია."),
         src=[U(EN, "Elephter Andronikashvili Institute of Physics")]),
    dict(id="manuscripts", kind="science", frm=1958, lat=dms(41, 43, 3), lon=dms(44, 47, 0),
         name=N("Национальный центр рукописей (Институт рукописей имени Корнелия Кекелидзе)", "Georgian National Centre of Manuscripts (Korneli Kekelidze Institute of Manuscripts)", "ხელნაწერთა ეროვნული ცენტრი (კორნელი კეკელიძის სახელობის ხელნაწერთა ინსტიტუტი)"),
         founded="30.06.1958",
         note=N("Основан 30 июня 1958 как Институт рукописей Академии наук Грузии; первый директор Илия Абуладзе; имя Кекелидзе с 1962; с 23 мая 2007 Национальный центр рукописей. Грузинские рукописи V–XIX веков, более 30 000 исторических документов X–XIX веков. Адрес: ул. Мераба Алексидзе, 1/3.",
                "Founded on 30 June 1958 as the Institute of Manuscripts of the Georgian Academy of Sciences; first director Ilia Abuladze; named after Kekelidze in 1962; the National Centre of Manuscripts since 23 May 2007. Georgian manuscripts of the 5th-19th centuries, over 30,000 historical documents of the 10th-19th centuries. Address: 1/3 Merab Aleksidze St.",
                "დაარსდა 1958 წლის 30 ივნისს, როგორც საქართველოს მეცნიერებათა აკადემიის ხელნაწერთა ინსტიტუტი; პირველი დირექტორი ილია აბულაძე; კეკელიძის სახელი 1962 წლიდან; 2007 წლის 23 მაისიდან ხელნაწერთა ეროვნული ცენტრი. V–XIX საუკუნეების ქართული ხელნაწერები, X–XIX საუკუნეების 30 000-ზე მეტი ისტორიული დოკუმენტი. მისამართი: მერაბ ალექსიძის ქ. 1/3."),
         src=[U(EN, "Georgian National Centre of Manuscripts")]),
    dict(id="lugar", kind="science", frm=2011, lat=dms(41, 41, 22), lon=dms(44, 56, 41),
         name=N("Научно-исследовательский центр общественного здравоохранения имени Ричарда Лугара", "Richard Lugar Center for Public Health Research", "რიჩარდ ლუგარის სახელობის საზოგადოებრივი ჯანდაცვის კვლევითი ცენტრი"),
         founded="18.03.2011",
         note=N("Лаборатория общественного здравоохранения с уровнем BSL-3; открыта 18 марта 2011, полностью работает с августа 2013; строительство начато в 2004 по соглашению США и Грузии. Адрес: Кахетинское шоссе, 99. Обвинения России 2017 года в биологическом оружии, по статье, отвергнуты.",
                "A public-health laboratory with a BSL-3 facility; opened on 18 March 2011, fully operational from August 2013; construction began in 2004 under a US-Georgia agreement. Address: Kakheti highway 99. The Russian allegations of biological weapons in 2017 were, according to the article, dismissed.",
                "საზოგადოებრივი ჯანდაცვის ლაბორატორია BSL-3 დონის; გაიხსნა 2011 წლის 18 მარტს, სრულად მოქმედებს 2013 წლის აგვისტოდან; მშენებლობა დაიწყო 2004 წელს აშშ-საქართველოს შეთანხმებით. მისამართი: კახეთის გზატკეცილი 99. რუსეთის 2017 წლის ბრალდებები ბიოლოგიურ იარაღზე, სტატიის მიხედვით, უარყოფილია."),
         src=[U(EN, "Lugar Research Center")]),
    dict(id="conservatoire", kind="culture", frm=1917, lat=41.6995, lon=44.7951,
         name=N("Тбилисская консерватория имени Вано Сараджишвили", "Vano Sarajishvili Tbilisi State Conservatoire", "ვანო სარაჯიშვილის სახელობის თბილისის სახელმწიფო კონსერვატორია"),
         founded="1.05.1917", built="1901–1905",
         note=N("Основана 1 мая 1917 (выросла из музыкальной школы 1883 года); статус консерватории с 1924; имя Сараджишвили с 1947. Здание архитектора Александра Шимкевича: 1901–1905 по английской, 1901–1904 по грузинской статье; русская статья говорит о завершении в 1917 (расхождение). Адрес: ул. Грибоедова, 8–10.",
                "Founded on 1 May 1917 (it grew out of a music school of 1883); conservatoire status from 1924; named after Sarajishvili in 1947. The building by architect Aleksander Szymkiewicz: 1901-1905 per the English article, 1901-1904 per the Georgian one; the Russian article speaks of completion in 1917 (a disagreement). Address: 8-10 Griboedov St.",
                "დაარსდა 1917 წლის 1 მაისს (გაიზარდა 1883 წლის მუსიკალური სკოლიდან); კონსერვატორიის სტატუსი 1924 წლიდან; სარაჯიშვილის სახელი 1947 წლიდან. შენობა არქიტექტორ ალექსანდრე შიმკევიჩისა: 1901–1905 ინგლისური სტატიით, 1901–1904 ქართულით; რუსული სტატია დასრულებაზე 1917 წელს საუბრობს (განსხვავება). მისამართი: გრიბოედოვის ქ. 8–10."),
         src=[U(EN, "Tbilisi State Conservatoire"), U(KA, "თბილისის სახელმწიფო კონსერვატორია"), U(RU, "Тбилисская государственная консерватория имени Вано Сараджишвили")]),
    # ------------------------------------------------------------------ culture
    dict(id="artmuseum", kind="culture", frm=1838, lat=dms(41, 41, 49.28), lon=dms(44, 48, 2.6),
         name=N("Музей искусств Грузии (бывшая духовная семинария)", "Art Museum of Georgia (the former theological seminary)", "საქართველოს ხელოვნების მუზეუმი (ყოფილი სასულიერო სემინარია)"),
         founded="1.02.1920", built="1838",
         note=N("Здание 1838 года в неоклассическом стиле; в имперское время в нём Тифлисская духовная семинария (по грузинской статье открыта 1 октября 1817; закрыта в 1917 по грузинской и в 1919 по английской и русской статьям). Музей переехал сюда в 1950. Предшественник, Национальная картинная галерея, открыт 1 февраля 1920; Центральный музей изобразительных искусств август 1923; имя Музея искусств Грузии с 1950; с конца 2004 в Национальном музее. Архитектор здания страница музея не называет.",
                "The building of 1838, neoclassical; in imperial times the Tiflis Theological Seminary (the Georgian article says it opened on 1 October 1817; closed in 1917 per the Georgian and in 1919 per the English and Russian articles). The museum moved here in 1950. Its predecessor, the National Art Gallery, opened on 1 February 1920; the Central Museum of Fine Arts in August 1923; the name Art Museum of Georgia from 1950; part of the National Museum since the end of 2004. The museum page does not name the architect of the building.",
                "1838 წლის შენობა, ნეოკლასიკური სტილის; საიმპერატორო ხანაში აქ იყო თბილისის სასულიერო სემინარია (ქართული სტატიით გაიხსნა 1817 წლის 1 ოქტომბერს; დაიხურა 1917 წელს ქართულით და 1919 წელს ინგლისური და რუსული სტატიებით). მუზეუმი აქ გადმოვიდა 1950 წელს. წინამორბედი, ეროვნული სამხატვრო გალერეა, გაიხსნა 1920 წლის 1 თებერვალს; ხელოვნების ცენტრალური მუზეუმი 1923 წლის აგვისტოში; საქართველოს ხელოვნების მუზეუმის სახელი 1950 წლიდან; 2004 წლის ბოლოდან ეროვნული მუზეუმის შემადგენლობაშია."),
         src=[U(EN, "Art Museum of Georgia"), U(EN, "Tbilisi Theological Seminary"), U(KA, "თბილისის სასულიერო სემინარია")]),
    dict(id="gallery", kind="culture", frm=1888, lat=41.698313, lon=44.798785,
         name=N("Национальная картинная галерея (Тбилисская картинная галерея, «Голубая галерея»)", "Tbilisi Art Gallery (National Gallery, the \"Blue Gallery\")", "თბილისის სამხატვრო გალერეა (ეროვნული გალერეა, „ცისფერი გალერეა“)"),
         built="1888",
         note=N("Здание проспект Руставели, 11, 1888 год, архитектор Альберт Зальцман (по грузинской и русской статьям; английская статья в одном разделе говорит 1888, в другом 1880–1883). Первая выставка в октябре 1920; в Национальном музее с 2007. Объект национального значения (решение от 7 ноября 2006).",
                "The building at 11 Rustaveli Avenue, 1888, architect Albert Zaltsman (per the Georgian and Russian articles; the English article says 1888 in one section and 1880-1883 in another). The first exhibition in October 1920; part of the National Museum since 2007. A monument of national significance (decree of 7 November 2006).",
                "შენობა რუსთაველის გამზირზე 11, 1888 წელი, არქიტექტორი ალბერტ ცალცმანი (ქართული და რუსული სტატიებით; ინგლისური სტატია ერთ ნაწილში 1888-ს ამბობს, მეორეში 1880–1883-ს). პირველი გამოფენა 1920 წლის ოქტომბერში; 2007 წლიდან ეროვნული მუზეუმის შემადგენლობაშია. ეროვნული მნიშვნელობის ძეგლი (2006 წლის 7 ნოემბრის დადგენილება)."),
         src=[U(EN, "Tbilisi Art Gallery"), U(RU, "Национальная картинная галерея Грузии"), U(KA, "საქართველოს ეროვნული გალერეა")]),
    dict(id="opera", kind="culture", frm=1851, lat=41.701306, lon=44.796167,
         name=N("Театр оперы и балета имени Палиашвили", "Paliashvili Opera and Ballet Theatre", "ზაქარია ფალიაშვილის სახელობის ოპერისა და ბალეტის თეატრი"),
         founded="1851", built="1896",
         note=N("Первое здание Джованни Скудьери открыто в 1851 (закладка 15 апреля 1847); сгорело 11 октября 1874. Нынешнее здание в мавританском стиле: проект Виктора Шрётера утверждён в 1880, открыто в 1896. Имя Палиашвили с 1937; реставрация завершена в январе 2016. По английской статье пр. Руставели, 25.",
                "The first building by Giovanni Scudieri opened in 1851 (foundation laid on 15 April 1847); it burned down on 11 October 1874. The present neo-Moorish building: the design of Viktor Schroeter approved in 1880, opened in 1896. Named after Paliashvili since 1937; the restoration was completed in January 2016. 25 Rustaveli Avenue per the English article.",
                "ჯოვანი სკუდიერის პირველი შენობა გაიხსნა 1851 წელს (საძირკველი ჩაეყარა 1847 წლის 15 აპრილს); დაიწვა 1874 წლის 11 ოქტომბერს. დღევანდელი შენობა მავრიტანული სტილისაა: ვიქტორ შრეტერის პროექტი დამტკიცდა 1880 წელს, გაიხსნა 1896 წელს. ფალიაშვილის სახელი 1937 წლიდან; რესტავრაცია დასრულდა 2016 წლის იანვარში. ინგლისური სტატიით რუსთაველის გამზ. 25."),
         src=[U(EN, "Georgian National Opera Theater"), U(RU, "Грузинский театр оперы и балета имени Палиашвили"), U(KA, "თბილისის ოპერისა და ბალეტის თეატრი")]),
    dict(id="rustaveli_theatre", kind="culture", frm=1887, lat=41.69972, lon=44.79778,
         name=N("Театр имени Шота Руставели", "Rustaveli Theatre", "შოთა რუსთაველის სახელობის თეატრი"),
         founded="1887", built="1887",
         note=N("Здание завершено в 1887 на средства Александра Манташева (по английской статье архитекторы Корнелий Татищев и Александр Шимкевич); стиль рококо и барокко; реставрация 2002–2005. Театр носит имя Руставели с 1921 (25 ноября). Пр. Руставели, 17.",
                "The building was completed in 1887 with money of Alexander Mantashev (per the English article the architects were Cornell Tatishchev and Aleksander Szymkiewicz); Rococo and Baroque style; restored in 2002-2005. Named after Rustaveli since 1921 (25 November). 17 Rustaveli Avenue.",
                "შენობა დასრულდა 1887 წელს ალექსანდრე მანთაშევის სახსრებით (ინგლისური სტატიით არქიტექტორები კორნელი ტატიშჩევი და ალექსანდრე შიმკევიჩი); როკოკოსა და ბაროკოს სტილი; აღდგენილია 2002–2005 წლებში. რუსთაველის სახელს ატარებს 1921 წლიდან (25 ნოემბერი). რუსთაველის გამზ. 17."),
         src=[U(EN, "Rustaveli Theatre"), U(RU, "Грузинский театр имени Шота Руставели"), U(KA, "რუსთაველის თეატრი")]),
    dict(id="armenian_theatre", kind="culture", frm=1858, sf=1936, lat=dms(41, 41, 30), lon=dms(44, 48, 59),
         name=N("Тбилисский государственный армянский драматический театр имени Петроса Адамяна", "Petros Adamian Tbilisi State Armenian Drama Theatre", "პეტროს ადამიანის სახელობის თბილისის სახელმწიფო სომხური დრამატული თეატრი"),
         founded="1858", built="1936",
         note=N("Основан в 1858 (Геворг Чмшкян); в 1922–1936 «Художественный театр». Новое здание завершено в 1936 (архитектор не назван); район Авлабар. До 1936 точка бледная.",
                "Founded in 1858 (Gevorg Chmshkyan); the \"Artistic theatre\" in 1922-1936. The new building was finished in 1936 (architect not named); Avlabari district. Before 1936 the point is faint.",
                "დაარსდა 1858 წელს (გევორგ ჩმშკიანი); 1922–1936 წლებში „მხატვრული თეატრი“. ახალი შენობა დასრულდა 1936 წელს (არქიტექტორი არ არის დასახელებული); ავლაბრის რაიონი. 1936 წლამდე წერტილი ფერმკრთალია."),
         src=[U(EN, "Petros Adamian Tbilisi State Armenian Drama Theatre")]),
    dict(id="marjanishvili", kind="culture", frm=1930, lat=41.7088, lon=44.7945,
         name=N("Театр имени Котэ Марджанишвили", "Marjanishvili Theatre", "კოტე მარჯანიშვილის სახელობის თეატრი"),
         founded="1928",
         note=N("Основан в Кутаиси в 1928; в 1930 переехал в Тбилиси, в бывший Народный дом Зубалашвили. Архитектор Стефан Кржижинский, строительством руководил Александр Рогойский (год постройки здания страница не называет); модерн. Отремонтирован, открыт 17 сентября 2006. Ул. Котэ Марджанишвили, 8.",
                "Founded in Kutaisi in 1928; it moved to Tbilisi in 1930, into the former Zubalashvili People's House. Architect Stefan Kryczynski, construction led by Aleksander Rogojski (the page does not give the year of the building); Art Nouveau. Renovated and reopened on 17 September 2006. 8 Kote Marjanishvili St.",
                "დაარსდა ქუთაისში 1928 წელს; 1930 წელს გადავიდა თბილისში, ყოფილ ზუბალაშვილის სახალხო სახლში. არქიტექტორი სტეფან კრიჟინსკი, მშენებლობას ხელმძღვანელობდა ალექსანდრე როგოისკი (შენობის აგების წელს გვერდი არ ასახელებს); მოდერნი. გარემონტდა, გაიხსნა 2006 წლის 17 სექტემბერს. კოტე მარჯანიშვილის ქ. 8."),
         src=[U(EN, "Marjanishvili Theatre"), U(KA, "მარჯანიშვილის თეატრი"), U(RU, "Тбилисский академический театр имени К. Марджанишвили")]),
    dict(id="writers_house", kind="culture", frm=1905, lat=dms(41, 41, 25), lon=dms(44, 47, 59),
         name=N("Дом писателей Грузии (особняк Сараджишвили)", "Writers' House of Georgia (the Sarajishvili mansion)", "საქართველოს მწერალთა სახლი (სარაჯიშვილის სასახლე)"),
         built="1903–1905",
         note=N("Особняк построен в 1903–1905 для предпринимателя Давида Сараджишвили, архитектор Карл Заар, модерн с элементами необарокко. Литературе посвящён с 2008; с 2021 Музей репрессированных писателей. Сололаки, ул. Ивана Мачабели, 13.",
                "A mansion built in 1903-1905 for the entrepreneur David Sarajishvili, architect Karl Zaar, Art Nouveau with neo-Baroque elements. Dedicated to literature since 2008; the Museum of Repressed Writers since 2021. Sololaki, 13 Ivane Machabeli St.",
                "სასახლე აშენდა 1903–1905 წლებში მეწარმე დავით სარაჯიშვილისთვის, არქიტექტორი კარლ ცაარი, მოდერნი ნეობაროკოს ელემენტებით. ლიტერატურას მიეძღვნა 2008 წლიდან; 2021 წლიდან რეპრესირებულ მწერალთა მუზეუმი. სოლოლაკი, ივანე მაჩაბლის ქ. 13."),
         src=[U(EN, "Writers' House of Georgia")]),
    dict(id="circus", kind="culture", frm=1940, lat=dms(41, 42, 51), lon=dms(44, 47, 6),
         name=N("Тбилисский цирк", "Tbilisi Circus", "თბილისის ცირკი"),
         founded="1888", built="1939–1940",
         note=N("История цирка с 1888; первый шапито сгорел в 1911. Нынешняя ротонда в неоклассическом сталинском стиле строилась с 1939, завершена в 1940 (архитекторы Николай Непринцев, Владимир Урушадзе, Степан Сатунц); 2000 мест. В 1990-х упадок; в 2003 куплен Бадри Патаркацишвили, ремонт остановлен после 2007; вновь открыт в 2011.",
                "The circus has a history since 1888; the first big top burned down in 1911. The present rotunda, in neoclassical Stalinist style, was begun in 1939 and completed in 1940 (architects Nikolay Neprintsev, Vladimer Urushadze, Stepan Satunts); 2,000 seats. Decline in the 1990s; bought in 2003 by Badri Patarkatsishvili, the renovation stalled after 2007; reopened in 2011.",
                "ცირკის ისტორია 1888 წლიდან იწყება; პირველი შატრი დაიწვა 1911 წელს. დღევანდელი როტონდა, ნეოკლასიკური სტალინური სტილის, დაიწყო 1939 წელს და დასრულდა 1940 წელს (არქიტექტორები ნიკოლოზ ნეპრინცევი, ვლადიმერ ურუშაძე, სტეპან სატუნცი); 2000 ადგილი. 1990-იან წლებში დაცემა; 2003 წელს ბადრი პატარკაციშვილმა იყიდა, რემონტი 2007 წლის შემდეგ შეჩერდა; ხელახლა გაიხსნა 2011 წელს."),
         src=[U(EN, "Tbilisi Circus")]),
    dict(id="academy_arts", kind="culture", frm=1922, lat=dms(41, 42, 5.1), lon=dms(44, 47, 34.9),
         name=N("Тбилисская государственная академия художеств", "Tbilisi State Academy of Arts", "თბილისის სახელმწიფო სამხატვრო აკადემია"),
         founded="8.03.1922", built="1856/1902",
         note=N("Основана 8 марта 1922. Здание — бывший дом Аршакуни: проект Г. Иванова, 1856; перестроен Симоном Клдиашвили в 1902 (инфобокс: «1850-е»). Десятиэтажный корпус добавлен в 1972. Реставрация 2005–2006. Точка с русской страницы; по грузинской статье адрес ул. Грибоедова, 22.",
                "Founded on 8 March 1922. The building is the former House of Arshakuni: designed by G. Ivanov, 1856; reconstructed by Simon Kldiashvili in 1902 (the infobox says \"1850s\"). A ten-storey block was added in 1972. Restored in 2005-2006. The point is from the Russian page; per the Georgian article the address is 22 Griboedov St.",
                "დაარსდა 1922 წლის 8 მარტს. შენობა არშაკუნის ყოფილი სახლია: გ. ივანოვის პროექტი, 1856 წელი; გადააკეთა სიმონ კლდიაშვილმა 1902 წელს (ინფოყუთში „1850-იანი წლები“). ათსართულიანი კორპუსი დაემატა 1972 წელს. აღდგენილია 2005–2006 წლებში. წერტილი რუსული გვერდისაა; ქართული სტატიით მისამართი გრიბოედოვის ქ. 22."),
         src=[U(EN, "Tbilisi State Academy of Arts"), U(KA, "თბილისის სამხატვრო აკადემია")]),
    dict(id="history_museum", kind="culture", frm=1910, sf=1984, lat=41.691014, lon=44.807772,
         name=N("Музей истории Тбилиси имени Иосифа Гришашвили (Карвасла)", "Ioseb Grishashvili Tbilisi History Museum (Karvasla)", "იოსებ გრიშაშვილის სახელობის თბილისის ისტორიის მუზეუმი (ქარვასლა)"),
         founded="1910", built="1818",
         note=N("Музей основан в 1910 (городской); с 1984 размещён в бывшем караван-сарае Арцруни, построенном в 1818. Ул. Сиони, 8. До 1984 точка бледная.",
                "The museum was founded in 1910 (a municipal one); since 1984 it has been in the former Artsruni caravanserai, built in 1818. 8 Sioni St. Before 1984 the point is faint.",
                "მუზეუმი დაარსდა 1910 წელს (საქალაქო); 1984 წლიდან განთავსებულია არწრუნების ყოფილ ქარვასლაში, აშენებულია 1818 წელს. სიონის ქ. 8. 1984 წლამდე წერტილი ფერმკრთალია."),
         src=[U(RU, "Музей истории Тбилиси"), U(KA, "თბილისის ისტორიის მუზეუმი")]),
    dict(id="open_air", kind="culture", frm=1966, lat=dms(41, 42, 7), lon=dms(44, 44, 35),
         name=N("Этнографический музей под открытым небом имени Георгия Читаиа", "Giorgi Chitaia Open-Air Museum of Ethnography", "გიორგი ჩიტაიას სახელობის ეთნოგრაფიული მუზეუმი ღია ცის ქვეშ"),
         founded="27.04.1966",
         note=N("Основан 27 апреля 1966; около 70 зданий, перенесённых из разных мест Грузии, на 52 га; на холме к западу от Черепашьего озера над Ваке. С 30 декабря 2004 в Национальном музее.",
                "Founded on 27 April 1966; about 70 buildings moved from across Georgia on 52 ha; on a hill west of Turtle Lake overlooking Vake. Part of the National Museum since 30 December 2004.",
                "დაარსდა 1966 წლის 27 აპრილს; დაახლოებით 70 შენობა, გადატანილი საქართველოს სხვადასხვა კუთხიდან, 52 ჰექტარზე; კუს ტბის დასავლეთით გორაზე, ვაკის თავზე. 2004 წლის 30 დეკემბრიდან ეროვნული მუზეუმის შემადგენლობაშია."),
         src=[U(EN, "Tbilisi Open Air Museum of Ethnography")]),
    dict(id="soviet_occupation", kind="culture", frm=2006, lat=dms(41, 41, 45), lon=dms(44, 48, 1),
         name=N("Музей советской оккупации", "Museum of Soviet Occupation", "საბჭოთა ოკუპაციის მუზეუმი"),
         founded="26.05.2006",
         note=N("Основан 26 мая 2006; рассказывает о советском периоде 1921–1991; проспект Руставели; в составе Национального музея. Здание страница не называет.",
                "Established on 26 May 2006; about the Soviet period of 1921-1991; Rustaveli Avenue; part of the National Museum. The page does not name the building.",
                "დაარსდა 2006 წლის 26 მაისს; მოგვითხრობს 1921–1991 წლების საბჭოთა პერიოდზე; რუსთაველის გამზირი; ეროვნული მუზეუმის შემადგენლობაშია. შენობას გვერდი არ ასახელებს."),
         src=[U(EN, "Museum of Soviet Occupation (Tbilisi)")]),
]


def main():
    out = []
    for it in ITEMS:
        o = {"id": it["id"], "kind": it["kind"], "from": it["frm"], "lat": it["lat"], "lon": it["lon"], "name": it["name"], "note": it["note"], "src": it["src"]}
        for k in ("sf", "approx"):
            if it.get(k):
                o[k] = it[k]
        for k in ("founded", "built"):
            if it.get(k):
                o[k] = it[k]
        out.append(o)
    ids = [o["id"] for o in out]
    assert len(ids) == len(set(ids))
    for o in out:
        assert all(o["name"][l] and o["note"][l] for l in ("ru", "en", "ka")), o["id"]
        assert 41.6 < o["lat"] < 41.9 and 44.6 < o["lon"] < 45.1, o["id"]
    p = os.path.join(ROOT, "site", "data", "science.json")
    open(p, "wb").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print("items:", len(out), "science:", sum(1 for o in out if o["kind"] == "science"), "culture:", sum(1 for o in out if o["kind"] == "culture"))


if __name__ == "__main__":
    main()
