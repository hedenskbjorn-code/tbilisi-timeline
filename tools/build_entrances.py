"""Builds site/data/entrances.json: the walking route "Entrance halls of Tbilisi" (3 parts: Sololaki, the centre and Agmashenebeli Avenue, Vera).

What it does:
- takes the stops (addresses, facts, texts) from STOPS_* below; the coordinates of every stop are those of the object of the heritage register
  (site/data/monuments.json) that is nearest to the point given in the list of addresses, within 30 m, with the same house number in its address;
- asks the public pedestrian router Valhalla (valhalla1.openstreetmap.de, data of OpenStreetMap) for the walking times between the stops, finds
  the order with the least walking time (for every part) for the closed tour from the metro station Freedom Square back to it (exact search over all orders),
  and gets the line of the route street by street; everything is stored in the json, the page itself makes no request to a router;
- no codes of door locks are stored anywhere (and must never be).

Run: python -X utf8 tools/build_entrances.py   (needs a network; takes about a minute)
"""
import itertools, json, math, os, time, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE = os.path.join(ROOT, "site")
VALHALLA = "https://valhalla1.openstreetmap.de"
UA = {"Content-Type": "application/json", "User-Agent": "tbilisi-timeline-build/1.0"}

START = {"lat": 41.69349, "lon": 44.80119,
         "name": {"ru": "Метро «Площадь Свободы»", "en": "Freedom Square metro station", "ka": "მეტროსადგური „თავისუფლების მოედანი“"}}

DISS = {"label": "Т. Кутателадзе, «Монументально-декоративная живопись интерьеров жилых и общественных зданий Тбилиси XIX–XX веков» (Грузинский технический университет, 2015), таблица зданий, с. 88–96",
        "url": "https://dspace.nplg.gov.ge/bitstream/1234/178167/1/Disertacia.pdf"}
REG = {"label": "Реестр культурного наследия Грузии (данные этого сайта, monuments.json)", "url": ""}
GT = {"label": "Georgia Today, «Hidden relics of Tbilisi's 20th century bourgeoisie»", "url": "https://georgiatoday.ge/hidden-relics-of-tbilisis-20th-century-bourgeoisie"}
SCAN = {"label": "scantbilisi.ge, «G. Tabidze Street»", "url": "https://scantbilisi.ge/en/objects/262/satesto"}
COM = {"label": "Wikimedia Commons (описания файлов и категории)", "url": "https://commons.wikimedia.org/wiki/Category:Entrances_of_residential_buildings_in_Tbilisi"}
OSM = {"label": "OpenStreetMap (адреса домов № 3 и № 5; координаты точки)", "url": "https://www.openstreetmap.org/copyright"}
RUWP_ACAD = {"label": "ru.wikipedia, «Тбилисская государственная академия художеств» (координаты здания)", "url": "https://ru.wikipedia.org/wiki/%D0%A2%D0%B1%D0%B8%D0%BB%D0%B8%D1%81%D1%81%D0%BA%D0%B0%D1%8F_%D0%B3%D0%BE%D1%81%D1%83%D0%B4%D0%B0%D1%80%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F_%D0%B0%D0%BA%D0%B0%D0%B4%D0%B5%D0%BC%D0%B8%D1%8F_%D1%85%D1%83%D0%B4%D0%BE%D0%B6%D0%B5%D1%81%D1%82%D0%B2"}
WH = {"label": "en.wikipedia, «Writers' House of Georgia»", "url": "https://en.wikipedia.org/wiki/Writers%27_House_of_Georgia"}

ST = {  # street names in three languages
    "tab": ("ул. Галактиона Табидзе", "Galaktion Tabidze St.", "გალაკტიონ ტაბიძის ქ."),
    "dad": ("ул. Шалвы Дадиани", "Shalva Dadiani St.", "შალვა დადიანის ქ."),
    "asa": ("ул. Ладо Асатиани", "Lado Asatiani St.", "ლადო ასათიანის ქ."),
    "mac": ("ул. Ивана Мачабели", "Ivane Machabeli St.", "ივანე მაჩაბლის ქ."),
    "kik": ("ул. Геронти Кикодзе", "Geronti Kikodze St.", "გერონტი ქიქოძის ქ."),
    "cho": ("ул. Даниела Чонкадзе", "Daniel Chonkadze St.", "დანიელ ჭონქაძის ქ."),
    "cha": ("ул. Гии Чантурии", "Gia Chanturia St.", "გია ჭანტურიას ქ."),
    "ato": ("ул. Георгия Атонели", "Giorgi Atoneli St.", "გიორგი ათონელის ქ."),
    "agm": ("пр. Давида Агмашенебели", "David Aghmashenebeli Ave.", "დავით აღმაშენებლის გამზ."),
    "gri": ("ул. Александра Грибоедова", "Alexander Griboedov St.", "გრიბოედოვის ქ."),
    "aba": ("ул. Тамар Абакелия", "Tamar Abakelia St.", "თამარ აბაკელიას ქ."),
    "zub": ("ул. Дзмеби Зубалашвили", "Dzmebi Zubalashvilebi St.", "ძმები ზუბალაშვილების ქ."),
    "tch": ("ул. Тамар Човелидзе", "Tamar Chovelidze St.", "თამარ ჭოველიძის ქ."),
    "kos": ("ул. Мераба Костава", "Merab Kostava St.", "მერაბ კოსტავას ქ."),
    "tak": ("ул. Эквтиме Такаишвили", "Ekvtime Takaishvili St.", "ექვთიმე თაყაიშვილის ქ."),
    "bar": ("ул. Васила Барнова", "Vasil Barnov St.", "ვასილ ბარნოვის ქ."),
}
NOTE = {  # the same sentence on every card: no codes, the house is a home
    "ru": "Это жилой дом: подъезд может быть закрыт, доступ зависит от жильцов. Просьба не шуметь и уважать их покой. Кодов замков здесь нет и не будет.",
    "en": "This is a residential building: the entrance may be closed, access depends on the residents. Please keep quiet and respect their peace. There are no door codes here and there will be none.",
    "ka": "ეს საცხოვრებელი სახლია: სადარბაზო შეიძლება დაკეტილი იყოს, შესვლა მობინადრეებზეა დამოკიდებული. გთხოვთ, ნუ იხმაურებთ და მათი სიმშვიდე დაიცავით. კოდური საკეტების კოდები აქ არ არის და არც იქნება.",
}
DISS_LIST = {
    "ru": "Включён в список зданий Тбилиси с монументально-декоративной росписью интерьеров (Т. Кутателадзе, 2015).",
    "en": "It is in the list of the buildings of Tbilisi with monumental-decorative painting in the interiors (T. Kutateladze, 2015).",
    "ka": "ის შედის თბილისის იმ შენობების სიაში, რომელთა ინტერიერში მონუმენტურ-დეკორატიული მხატვრობაა (თ. ქუთათელაძე, 2015).",
}

# the stops: key, the point of the list of addresses (lat, lon), the house number, the number of the street name, the texts
STOPS_1 = [
    dict(key="dad18", pt=(41.691464, 44.802186), num="18", st="dad",
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("конец XIX века", "late 19th century", "XIX საუკუნის ბოლო"), arch=(None, None, None),
         desc=("Жилой дом конца XIX века в Сололаки. Автор проекта в исследовании не назван. " + DISS_LIST["ru"],
               "A residential house of the late 19th century in Sololaki. The study does not name the architect. " + DISS_LIST["en"],
               "XIX საუკუნის ბოლოს აგებული საცხოვრებელი სახლი სოლოლაკში. კვლევაში არქიტექტორი დასახელებული არ არის. " + DISS_LIST["ka"]),
         src=[DISS, REG]),
    dict(key="tab18", pt=(41.690731, 44.801359), num="18", st="tab", photos=["File:Galaktion Tabidze 18.jpg"],
         name=("Дом братьев Сейлановых", "House of the Seilanov brothers", "ძმები სეილანოვების სახლი"),
         year=("1911", "1911", "1911"), arch=("Г. Саркисян", "G. Sarkisian", "გ. სარქისიანი"),
         desc=("Жилой дом табачных фабрикантов братьев Сейлановых. В парадной описаны настенные росписи с аллегорическими изображениями континентов и стран (Georgia Today). В другом источнике (scantbilisi.ge) дом датирован 1905 годом.",
               "The residential house of the tobacco manufacturers, the Seilanov brothers. Georgia Today describes wall paintings in the entrance with allegorical images of continents and countries. Another source (scantbilisi.ge) dates the house to 1905.",
               "თამბაქოს მწარმოებელ ძმები სეილანოვების საცხოვრებელი სახლი. Georgia Today აღწერს სადარბაზოს კედლის მხატვრობას კონტინენტებისა და ქვეყნების ალეგორიული გამოსახულებებით. სხვა წყარო (scantbilisi.ge) სახლს 1905 წლით ათარიღებს."),
         src=[DISS, GT, SCAN, REG]),
    dict(key="tab24", pt=(41.689906, 44.801414), num="24", st="tab", photos=["File:Building with stucco and wrought iron balcony at 24 Galaktion Tabidze St, Tbilisi.jpg"],
         name=("Жилой дом на углу с ул. Асатиани", "Residential house at the corner of Asatiani St.", "საცხოვრებელი სახლი ასათიანის ქუჩის კუთხეში"),
         year=("1896 (по реестру)", "1896 (by the register)", "1896 (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Угловой жилой дом (адрес по реестру: ул. Табидзе, 24 / ул. Асатиани, 21). Дата по реестру культурного наследия: 1896 год.",
               "A corner residential house (the address in the register: 24 Tabidze St. / 21 Asatiani St.). The date in the heritage register is 1896.",
               "კუთხის საცხოვრებელი სახლი (მისამართი რეესტრში: ტაბიძის ქ. 24 / ასათიანის ქ. 21). თარიღი კულტურული მემკვიდრეობის რეესტრში: 1896 წელი."),
         src=[REG]),
    dict(key="asa13", pt=(41.689906, 44.803417), num="13", st="asa", photos=["File:2023-06-29 Interior decorations of Shalimov House.jpg", "File:13 Lado Asatiani St, Tbilisi.jpg"],
         name=("Дом Шалимова", "Shalimov house", "შალიმოვის სახლი"),
         year=("1897", "1897", "1897"), arch=("И. Гарицилов", "I. Garitsilov", "ი. გარიცილოვი"),
         desc=("Жилой дом с мансардой, 1897 год, архитектор И. Гарицилов (по таблице диссертации); в реестре дата дана шире: конец XIX века. На Wikimedia Commons дом назван «Shalimov House»; в парадной сохранилась роспись по трафарету с путти. " + DISS_LIST["ru"],
               "A residential house with an attic, 1897, architect I. Garitsilov (by the table of the dissertation); the register gives a wider date: the late 19th century. Wikimedia Commons calls it 'Shalimov House'; the entrance hall keeps a stencil wall painting with putti. " + DISS_LIST["en"],
               "საცხოვრებელი სახლი სხვენით, 1897 წელი, არქიტექტორი ი. გარიცილოვი (დისერტაციის ცხრილის მიხედვით); რეესტრში თარიღი უფრო ფართოდ არის მითითებული: XIX საუკუნის ბოლო. Wikimedia Commons-ზე სახლი „Shalimov House“-ად არის დასახელებული; სადარბაზოში შემორჩენილია ტრაფარეტით შესრულებული კედლის მხატვრობა ანგელოზთა გამოსახულებით. " + DISS_LIST["ka"]),
         src=[DISS, REG, COM]),
    dict(key="mac17", pt=(41.689774, 44.799787), num="17", st="mac", photos=["File:მაჩაბლის ქუჩა 17, მოხატული სადარბაზო.jpg"],
         name=("Дом Калантарова", "Kalantarov house", "კალანტაროვის სახლი"),
         year=("1908 (по диссертации)", "1908 (by the dissertation)", "1908 (დისერტაციის მიხედვით)"), arch=("Г. Саркисян", "G. Sarkisian", "გ. სარქისიანი"),
         desc=("Жилой дом Калантарова на углу с ул. Асатиани (адрес в диссертации: Мачабели 17/27), 1908 год, архитектор Г. Саркисян. В реестре дата дана шире: конец XIX века. " + DISS_LIST["ru"],
               "The residential house of Kalantarov at the corner of Asatiani St. (the address in the dissertation: Machabeli 17/27), 1908, architect G. Sarkisian. The register gives a wider date: the late 19th century. " + DISS_LIST["en"],
               "კალანტაროვის საცხოვრებელი სახლი ასათიანის ქუჩის კუთხეში (მისამართი დისერტაციაში: მაჩაბლის 17/27), 1908 წელი, არქიტექტორი გ. სარქისიანი. რეესტრში თარიღი უფრო ფართოდ არის მითითებული: XIX საუკუნის ბოლო. " + DISS_LIST["ka"]),
         src=[DISS, REG]),
    dict(key="mac15", pt=(41.690076, 44.799776), num="15", st="mac",
         name=("Жилой дом, 1878", "Residential house, 1878", "საცხოვრებელი სახლი, 1878"),
         year=("1878 (по реестру)", "1878 (by the register)", "1878 (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Жилой дом второй половины XIX века (дата по реестру: 1878). Рядом, на № 13, стоит Дом писателей — бывший особняк Давида Сараджишвили (1903–1905, архитектор Карл Цаар; Википедия, диссертация).",
               "A residential house of the second half of the 19th century (the date in the register: 1878). Next door, at no. 13, stands the Writers' House, the former mansion of David Sarajishvili (1903-1905, architect Karl Zaar; Wikipedia, the dissertation).",
               "XIX საუკუნის მეორე ნახევრის საცხოვრებელი სახლი (თარიღი რეესტრში: 1878). გვერდით, მე-13 ნომერში, მწერალთა სახლია — დავით სარაჯიშვილის ყოფილი სასახლე (1903–1905, არქიტექტორი კარლ ცაარი; ვიკიპედია, დისერტაცია)."),
         src=[REG, WH, DISS]),
    dict(key="kik9", pt=(41.690809, 44.798451), num="9", st="kik",
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("конец XIX века (по реестру)", "late 19th century (by the register)", "XIX საუკუნის ბოლო (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Жилой дом конца XIX века в Сололаки (дата по реестру культурного наследия). В диссертации по этому адресу записи нет.",
               "A residential house of the late 19th century in Sololaki (the date in the heritage register). The dissertation has no entry for this address.",
               "XIX საუკუნის ბოლოს აგებული საცხოვრებელი სახლი სოლოლაკში (თარიღი კულტურული მემკვიდრეობის რეესტრის მიხედვით). დისერტაციაში ამ მისამართით ჩანაწერი არ არის."),
         src=[REG]),
    dict(key="asa58", pt=(41.689426, 44.797031), num="58", st="asa", photos=["File:ლადო ასათიანის 58.jpg"],
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("конец XIX – начало XX века", "late 19th - early 20th century", "XIX საუკუნის ბოლო – XX საუკუნის დასაწყისი"), arch=(None, None, None),
         desc=("Жилой дом конца XIX — начала XX века, автор проекта в исследовании не назван. " + DISS_LIST["ru"],
               "A residential house of the late 19th - early 20th century; the study does not name the architect. " + DISS_LIST["en"],
               "XIX საუკუნის ბოლოს – XX საუკუნის დასაწყისის საცხოვრებელი სახლი; კვლევაში არქიტექტორი დასახელებული არ არის. " + DISS_LIST["ka"]),
         src=[DISS, REG]),
    dict(key="cho4", pt=(41.690663, 44.795843), num="4", st="cho", photos=["File:Anna Madatova House 2023-07-13-1.jpg"],
         name=("Дом Мадатовой", "Madatova house", "მადათოვას სახლი"),
         year=("1902 (по диссертации)", "1902 (by the dissertation)", "1902 (დისერტაციის მიხედვით)"), arch=("М. Огаджанов", "M. Ogajanov", "მ. ოგაჯანოვი"),
         desc=("Жилой дом Мадатовой, 1902 год, архитектор М. Огаджанов (по таблице диссертации; там хозяйка названа «Аба Мадатова», на Wikimedia Commons дом называется «Anna Madatova House»). В реестре дата дана шире: конец XIX века. " + DISS_LIST["ru"],
               "The residential house of Madatova, 1902, architect M. Ogajanov (by the table of the dissertation, where the owner is called 'Aba Madatova'; Wikimedia Commons calls the house 'Anna Madatova House'). The register gives a wider date: the late 19th century. " + DISS_LIST["en"],
               "მადათოვას საცხოვრებელი სახლი, 1902 წელი, არქიტექტორი მ. ოგაჯანოვი (დისერტაციის ცხრილის მიხედვით, სადაც მფლობელი მოხსენიებულია, როგორც „აბა მადათოვა“; Wikimedia Commons-ზე სახლი „Anna Madatova House“-ადაა მოხსენიებული). რეესტრში თარიღი უფრო ფართოდ არის მითითებული: XIX საუკუნის ბოლო. " + DISS_LIST["ka"]),
         src=[DISS, REG, COM]),
    dict(key="cho12", pt=(41.692896, 44.795008), num="12", st="cho",
         name=("Дом Николоза Бозарджянца", "House of Nikoloz Bozarjyants", "ნიკოლოზ ბოზარჯიანცის სახლი"),
         year=("1917", "1917", "1917"), arch=("М. Огаджанов", "M. Ogajanov", "მ. ოგაჯანოვი"),
         desc=("Жилой дом Николоза Бозарджянца, 1917 год, архитектор М. Огаджанов (по таблице диссертации); в реестре дата: начало XX века. " + DISS_LIST["ru"],
               "The residential house of Nikoloz Bozarjyants, 1917, architect M. Ogajanov (by the table of the dissertation); the date in the register: the early 20th century. " + DISS_LIST["en"],
               "ნიკოლოზ ბოზარჯიანცის საცხოვრებელი სახლი, 1917 წელი, არქიტექტორი მ. ოგაჯანოვი (დისერტაციის ცხრილის მიხედვით); რეესტრში თარიღი: XX საუკუნის დასაწყისი. " + DISS_LIST["ka"]),
         src=[DISS, REG]),
]

STOPS_2 = [  # part 2: the centre and David Aghmashenebeli Avenue
    dict(key="cha6", pt=(41.699193, 44.798819), num="6", st="cha", photos=["File:Gia Chanturia street 6.jpg"],
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("середина XIX века (по реестру)", "mid-19th century (by the register)", "XIX საუკუნის შუა ხანები (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Жилой дом середины XIX века в центре Тбилиси (дата по реестру культурного наследия). В таблице диссертации по этому адресу записи нет.",
               "A residential house of the mid-19th century in the centre of Tbilisi (the date in the heritage register). The table of the dissertation has no entry for this address.",
               "XIX საუკუნის შუა ხანების საცხოვრებელი სახლი თბილისის ცენტრში (თარიღი კულტურული მემკვიდრეობის რეესტრის მიხედვით). დისერტაციის ცხრილში ამ მისამართით ჩანაწერი არ არის."),
         src=[REG]),
    dict(key="ato31", pt=(41.700123, 44.801896), num="31", st="ato", photos=["File:Giorgi Atoneli street 31 - Khidi street 2.jpg", "File:Hotel London, Tiflis. 1874.jpg"],
         name=("Бывшая гостиница «Лондон»", "The former Hotel London", "ყოფილი სასტუმრო „ლონდონი“"),
         year=("1872–1875", "1872-1875", "1872–1875"), arch=("Отто Якобсон-Симонсон", "Otto Jacobsohn-Simonson", "ოტო იაკობსონ-სიმონსონი"),
         desc=("Здание бывшей гостиницы «Лондон» (1872–1875, архитектор Отто Якобсон-Симонсон) на углу с ул. Хиди; в реестре числится жилым домом (1870 год). По описанию старой фотографии 1874 года на Wikimedia Commons, гостиница стояла на улице Мадатова (ныне Атонели) и принадлежала братьям Зубалашвили. " + DISS_LIST["ru"],
               "The building of the former Hotel London (1872-1875, architect Otto Jacobsohn-Simonson) at the corner of Khidi St.; the register lists it as a residential house (1870). According to the description of an old photograph of 1874 on Wikimedia Commons, the hotel stood in Madatov Street (now Atoneli Street) and belonged to the Zubalashvili brothers. " + DISS_LIST["en"],
               "ყოფილი სასტუმრო „ლონდონის“ შენობა (1872–1875, არქიტექტორი ოტო იაკობსონ-სიმონსონი) ხიდის ქუჩის კუთხეში; რეესტრში ის საცხოვრებელ სახლადაა ჩაწერილი (1870 წელი). Wikimedia Commons-ზე 1874 წლის ძველი ფოტოს აღწერის მიხედვით, სასტუმრო მადათოვის ქუჩაზე (ახლანდელი ათონელის ქუჩა) იდგა და ძმებ ზუბალაშვილებს ეკუთვნოდა. " + DISS_LIST["ka"]),
         src=[DISS, REG, COM]),
    dict(key="agm93", pt=(41.710542, 44.796861), num="93", st="agm", photos=["File:საცხოვრებელი სახლი, დავით აღმაშენებლის გამზირი 93.jpg", "File:დავით აღმაშენებლის გამზირი 93 (2).jpg"],
         name=("Жилой дом на проспекте Агмашенебели", "Residential house on Agmashenebeli Avenue", "საცხოვრებელი სახლი აღმაშენებლის გამზირზე"),
         year=("конец XIX – начало XX века", "late 19th - early 20th century", "XIX საუკუნის ბოლო – XX საუკუნის დასაწყისი"), arch=(None, None, None),
         desc=("Жилой дом с богато украшенным лепниной фасадом (см. фото). Дата в реестре — начало XX века, в таблице диссертации — конец XIX – начало XX века; автор проекта не назван. " + DISS_LIST["ru"],
               "A residential house with a facade richly decorated with stucco (see the photo). The date in the register is the early 20th century, in the table of the dissertation the late 19th - early 20th century; the architect is not named. " + DISS_LIST["en"],
               "საცხოვრებელი სახლი ნაძერწით მდიდრულად მორთული ფასადით (იხ. ფოტო). თარიღი რეესტრში: XX საუკუნის დასაწყისი, დისერტაციის ცხრილში: XIX საუკუნის ბოლო – XX საუკუნის დასაწყისი; არქიტექტორი დასახელებული არ არის. " + DISS_LIST["ka"]),
         src=[DISS, REG]),
    dict(key="gri27", pt=(41.701369, 44.793474), num="27", st="gri", photos=["File:გრიბოედოვის ქ. 27.jpg"],
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("конец XIX века (по реестру)", "late 19th century (by the register)", "XIX საუკუნის ბოლო (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Жилой дом конца XIX века (дата по реестру). В таблице диссертации по адресу Грибоедова, 27 записана Академия художеств (1850-е годы, архитекторы Г. Иванов и С. Клдиашвили), но по координатам Википедии здание Академии находится примерно в 70 м от этого дома; расхождение не снято, поэтому автор здесь не указан.",
               "A residential house of the late 19th century (the date in the register). The table of the dissertation lists the Academy of Arts at 27 Griboedov St. (1850s, architects G. Ivanov and S. Kldiashvili), but by the coordinates in Wikipedia the building of the Academy stands about 70 m from this house; the difference is not resolved, so no architect is given here.",
               "XIX საუკუნის ბოლოს აგებული საცხოვრებელი სახლი (თარიღი რეესტრის მიხედვით). დისერტაციის ცხრილში გრიბოედოვის ქ. 27-ის მისამართით ჩაწერილია სამხატვრო აკადემია (1850-იანი წლები, არქიტექტორები გ. ივანოვი და ს. კლდიაშვილი), მაგრამ ვიკიპედიის კოორდინატებით აკადემიის შენობა ამ სახლიდან დაახლოებით 70 მ-ში მდებარეობს; შეუსაბამობა გარკვეული არ არის, ამიტომ არქიტექტორი აქ მითითებული არ არის."),
         src=[DISS, REG, RUWP_ACAD]),
    dict(key="aba5", pt=(41.700630, 44.791940), num="5", st="aba", photos=["File:აბაკელია თამარის ქუჩა 5.jpg"],
         name=("Жилой дом с мансардой", "Residential house with an attic", "საცხოვრებელი სახლი სხვენით"),
         year=("1880–1890", "1880-1890", "1880–1890"), arch=(None, None, None),
         desc=("Жилой дом с мансардой, 1880–1890 годы, автор проекта неизвестен (таблица диссертации); в реестре дата — 1880 год. " + DISS_LIST["ru"],
               "A residential house with an attic, 1880-1890, the architect is unknown (the table of the dissertation); the date in the register is 1880. " + DISS_LIST["en"],
               "საცხოვრებელი სახლი სხვენით, 1880–1890 წლები, არქიტექტორი უცნობია (დისერტაციის ცხრილი); რეესტრში თარიღი: 1880 წელი. " + DISS_LIST["ka"]),
         src=[DISS, REG]),
    dict(key="zub4", pt=(41.696916, 44.796543), num="4", st="zub",
         name=("Угловой жилой дом", "Corner residential house", "კუთხის საცხოვრებელი სახლი"),
         year=("1899 (по реестру)", "1899 (by the register)", "1899 (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Угловой жилой дом (адрес по реестру: ул. Котетишвили, 2 / ул. Дзмеби Зубалашвили, 4), дата по реестру — 1899 год. В таблице диссертации по этому адресу записи нет.",
               "A corner residential house (the address in the register: 2 Kotetishvili St. / 4 Dzmebi Zubalashvilebi St.), the date in the register is 1899. The table of the dissertation has no entry for this address.",
               "კუთხის საცხოვრებელი სახლი (მისამართი რეესტრში: კოტეტიშვილის ქ. 2 / ძმები ზუბალაშვილების ქ. 4), თარიღი რეესტრში: 1899 წელი. დისერტაციის ცხრილში ამ მისამართით ჩანაწერი არ არის."),
         src=[REG]),
]

STOPS_3 = [  # part 3: Vera
    dict(key="tch7", pt=(41.705644, 44.786911), num="7", st="tch", photos=["File:Tbilisi, T. Chovelidze st. 7.jpg"],
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("конец XIX – начало XX века (по реестру)", "late 19th - early 20th century (by the register)", "XIX საუკუნის ბოლო – XX საუკუნის დასაწყისი (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Жилой дом конца XIX — начала XX века на Вере (дата по реестру культурного наследия). В таблице диссертации по этому адресу записи нет.",
               "A residential house of the late 19th - early 20th century in Vera (the date in the heritage register). The table of the dissertation has no entry for this address.",
               "XIX საუკუნის ბოლოს – XX საუკუნის დასაწყისის საცხოვრებელი სახლი ვერაზე (თარიღი კულტურული მემკვიდრეობის რეესტრის მიხედვით). დისერტაციის ცხრილში ამ მისამართით ჩანაწერი არ არის."),
         src=[REG]),
    dict(key="kos41", pt=(41.708406, 44.785824), num="41", st="kos", photos=["File:კოსტავას ქუჩა 41.jpg"],
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("начало XX века (по реестру)", "early 20th century (by the register)", "XX საუკუნის დასაწყისი (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Жилой дом начала XX века (дата по реестру). В таблице диссертации по этому адресу записи нет.",
               "A residential house of the early 20th century (the date in the register). The table of the dissertation has no entry for this address.",
               "XX საუკუნის დასაწყისის საცხოვრებელი სახლი (თარიღი რეესტრის მიხედვით). დისერტაციის ცხრილში ამ მისამართით ჩანაწერი არ არის."),
         src=[REG]),
    dict(key="tak35", pt=(41.708483, 44.777505), num="3–5", st="tak", xy=(41.708483, 44.777505),
         name=("Жилой дом", "Residential house", "საცხოვრებელი სახლი"),
         year=("конец XIX – начало XX века", "late 19th - early 20th century", "XIX საუკუნის ბოლო – XX საუკუნის დასაწყისი"), arch=(None, None, None),
         desc=("Жилой дом конца XIX — начала XX века (таблица диссертации, адрес: Такаишвили, 3–5; в первоначальном списке адресов — № 1, 3, 5). В данных реестра этого сайта объектов на этой улице нет, координаты точки взяты по адресам № 3 и № 5 в OpenStreetMap. " + DISS_LIST["ru"],
               "A residential house of the late 19th - early 20th century (the table of the dissertation, the address: Takaishvili 3-5; in the first list of addresses: nos. 1, 3, 5). The register data of this site has no objects on this street; the coordinates of the point are taken from the addresses no. 3 and no. 5 in OpenStreetMap. " + DISS_LIST["en"],
               "XIX საუკუნის ბოლოს – XX საუკუნის დასაწყისის საცხოვრებელი სახლი (დისერტაციის ცხრილი, მისამართი: თაყაიშვილის ქ. 3–5; მისამართების საწყის სიაში — № 1, 3, 5). ამ საიტის რეესტრის მონაცემებში ამ ქუჩაზე ობიექტები არ არის, წერტილის კოორდინატები OpenStreetMap-ის № 3 და № 5 მისამართებიდანაა აღებული. " + DISS_LIST["ka"]),
         src=[DISS, OSM]),
    dict(key="bar16", pt=(41.703302, 44.786582), num="16", st="bar",
         name=("Угловой жилой дом", "Corner residential house", "კუთხის საცხოვრებელი სახლი"),
         year=("1903 (по реестру)", "1903 (by the register)", "1903 (რეესტრის მიხედვით)"), arch=(None, None, None),
         desc=("Угловой жилой дом (адрес по реестру: ул. Барнова, 16 / ул. Чиградзе, 2), дата по реестру — 1903 год. В таблице диссертации по этому адресу записи нет.",
               "A corner residential house (the address in the register: 16 Barnov St. / 2 Chigradze St.), the date in the register is 1903. The table of the dissertation has no entry for this address.",
               "კუთხის საცხოვრებელი სახლი (მისამართი რეესტრში: ბარნოვის ქ. 16 / ჩიგრაძის ქ. 2), თარიღი რეესტრში: 1903 წელი. დისერტაციის ცხრილში ამ მისამართით ჩანაწერი არ არის."),
         src=[REG]),
]

PARTS = [
    dict(id="sololaki", title={"ru": "Сололаки", "en": "Sololaki", "ka": "სოლოლაკი"}, stops=STOPS_1),
    dict(id="center", title={"ru": "Центр и проспект Агмашенебели", "en": "The centre and Agmashenebeli Avenue", "ka": "ცენტრი და აღმაშენებლის გამზირი"}, stops=STOPS_2),
    dict(id="vera", title={"ru": "Вера", "en": "Vera", "ka": "ვერა"}, stops=STOPS_3),
]


def commons(title):
    import html, re, urllib.parse
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "extmetadata|url|size", "iiurlwidth": "800", "format": "json"})
    for k in range(6):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tbilisi-timeline-build/1.0"}), timeout=60)); break
        except Exception as e:
            print("retry commons", e); time.sleep(20 * (k + 1))
    time.sleep(3)
    p = list(d["query"]["pages"].values())[0]
    ii = p["imageinfo"][0]; m = ii["extmetadata"]
    g = lambda key: html.unescape(re.sub("<[^>]+>", "", (m.get(key) or {}).get("value", ""))).strip()
    lic = g("LicenseShortName")
    if not lic.startswith("CC BY"):
        raise SystemExit("not a free licence for " + title + ": " + lic)
    return {"thumb": ii["thumburl"], "w": ii["thumbwidth"], "h": ii["thumbheight"], "page": ii["descriptionurl"], "author": g("Artist").replace("AnonymousUnknown author", "Unknown author"), "license": lic, "license_url": g("LicenseUrl")}


def post(path, body, tries=4):
    for k in range(tries):
        try:
            rq = urllib.request.Request(VALHALLA + path, data=json.dumps(body).encode(), headers=UA)
            return json.load(urllib.request.urlopen(rq, timeout=90))
        except Exception as e:
            print("retry", path, e)
            time.sleep(3)
    raise SystemExit("the router does not answer")


def decode6(s):
    out, i, lat, lon = [], 0, 0, 0
    while i < len(s):
        for which in (0, 1):
            shift = res = 0
            while True:
                b = ord(s[i]) - 63; i += 1
                res |= (b & 31) << shift; shift += 5
                if b < 32: break
            d = ~(res >> 1) if res & 1 else res >> 1
            if which == 0: lat += d
            else: lon += d
        out.append([round(lon / 1e6, 6), round(lat / 1e6, 6)])
    return out


def build_part(part, offset, feats):
    stops = []
    for s in part["stops"]:
        if s.get("xy"):                                           # an address that is not in the register (the coordinates from OpenStreetMap)
            s["lat"], s["lon"] = s["xy"]; s["reg_id"] = s["reg_date"] = s["reg_addr"] = None; s["shift_m"] = None
            stops.append(s); continue
        best = None
        for f in feats:
            c = f["geometry"]["coordinates"]; p = f["properties"]
            d = math.hypot((c[1] - s["pt"][0]) * 111320, (c[0] - s["pt"][1]) * 83000)
            addr = p.get("address") or ""
            ok = any(part_.split(".")[0].strip() == s["num"] or part_.strip() == s["num"] for part_ in addr.split("/")[1:2] + [addr.split("/")[-1]]) if "/" in addr else False
            if d < 30 and ok and p.get("cls") == "architecture" and (best is None or d < best[0]):
                best = (d, f)
        if not best:
            raise SystemExit("no register object for " + s["key"])
        f = best[1]; p = f["properties"]
        s["lon"], s["lat"] = f["geometry"]["coordinates"]
        s["reg_id"], s["reg_date"], s["reg_addr"] = p["id"], p.get("raw_date"), p.get("address")
        s["shift_m"] = round(best[0])
        stops.append(s)
    # the matrix of the walking times: start + stops
    pts = [START] + stops
    T = []
    for p in pts:
        r = post("/sources_to_targets", {"sources": [{"lat": p["lat"], "lon": p["lon"]}], "targets": [{"lat": q["lat"], "lon": q["lon"]} for q in pts], "costing": "pedestrian"})
        T.append([c["time"] for c in r["sources_to_targets"][0]])
        time.sleep(0.4)
    n = len(stops)
    best = (1e18, None)
    for perm in itertools.permutations(range(1, n + 1)):
        t = T[0][perm[0]] + sum(T[perm[i]][perm[i + 1]] for i in range(n - 1)) + T[perm[-1]][0]
        if t < best[0]: best = (t, perm)
    order = best[1]
    print(part["id"], "closed tour: %.0f min walking" % (best[0] / 60))
    seq = [0] + list(order) + [0]
    coords, legs = [], []
    for a, b in zip(seq, seq[1:]):
        r = post("/route", {"locations": [{"lat": pts[a]["lat"], "lon": pts[a]["lon"]}, {"lat": pts[b]["lat"], "lon": pts[b]["lon"]}], "costing": "pedestrian", "directions_options": {"units": "kilometers"}})
        leg = r["trip"]["legs"][0]
        shape = decode6(leg["shape"])
        coords += shape if not coords else shape[1:]
        legs.append({"min": round(leg["summary"]["time"] / 60, 1), "m": round(leg["summary"]["length"] * 1000)})
        time.sleep(0.4)
    out_stops = []
    for k, idx in enumerate(order, 1):
        s = stops[idx - 1]
        ns = ST[s["st"]]
        out_stops.append({
            "n": offset + k, "lat": round(s["lat"], 6), "lon": round(s["lon"], 6),
            "name": dict(zip(("ru", "en", "ka"), s["name"])),
            "address": {"ru": f"{ns[0]}, {s['num']}", "en": f"{s['num']} {ns[1]}", "ka": f"{ns[2]} {s['num']}"},
            "year": dict(zip(("ru", "en", "ka"), s["year"])),
            "architect": dict(zip(("ru", "en", "ka"), s["arch"])) if s["arch"][0] else None,
            "desc": dict(zip(("ru", "en", "ka"), s["desc"])),
            "src": s["src"], "reg_id": s["reg_id"], "reg_date": s["reg_date"],
            "photos": [commons(t) for t in s.get("photos", [])],
            "leg_min": legs[k - 1]["min"], "leg_m": legs[k - 1]["m"],       # from the previous point (the start for the first stop)
        })
    total_m = sum(l["m"] for l in legs); total_min = sum(l["min"] for l in legs)
    print("  stops:", [(s["n"], s["address"]["en"], s["leg_min"]) for s in out_stops])
    print("  total %.1f km, %d min walking; shift of the point from the list to the register, m: %s" % (total_m / 1000, total_min, [stops[i - 1]["shift_m"] for i in order]))
    return {"id": part["id"], "title": part["title"], "start": START,
            "route": {"coords": coords, "length_km": round(total_m / 1000, 1), "walk_min": round(total_min), "back_min": round(legs[-1]["min"], 1), "back_m": legs[-1]["m"]},
            "stops": out_stops}


def main():
    feats = json.load(open(os.path.join(SITE, "data", "monuments.json"), encoding="utf-8"))["features"]
    parts, offset = [], 0
    for part in PARTS:
        parts.append(build_part(part, offset, feats))
        offset += len(part["stops"])                  # the numbers of the stops run through all the parts
    data = {
        "note": "Built by tools/build_entrances.py. The addresses of the stops come from the list of the owner of the site and the dissertation of T. Kutateladze (2015); the coordinates are those of the heritage register (one point from OpenStreetMap); the routes and the times are from the pedestrian router Valhalla (OpenStreetMap). No codes of door locks.",
        "door_note": NOTE,
        "parts": parts,
    }
    p = os.path.join(SITE, "data", "entrances.json")
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("size", os.path.getsize(p))


if __name__ == "__main__":
    main()
