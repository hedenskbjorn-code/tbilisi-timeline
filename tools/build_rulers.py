"""Build site/data/rulers.json: forms of state / government over Tbilisi and the rulers who held it (for the band "Who ruled" under the time scale).
Sources (read on 2026-11-19; the wikitext of the list pages was parsed through the Wikipedia API, the rest read on the pages):
 en.wikipedia: Emirate of Tbilisi (table of emirs), List of monarchs of Georgia (the table of the Bagrationi monarchs), Kingdom of Georgia, Kingdom of Kartli,
 Kingdom of Kartli-Kakheti, Kingdom of Iberia, Safavid Georgia, Mongol invasions of Georgia, Timurid invasions of Georgia, Caucasus Viceroyalty (1801-1917),
 List of Russian monarchs, Special Transcaucasian Committee, Transcaucasian Democratic Federative Republic, Democratic Republic of Georgia,
 Georgian Soviet Socialist Republic, President of Georgia, Prime Minister of Georgia, First Secretary of the Georgian Communist Party, Constitution of Georgia.
Rules: only those who ruled Tbilisi (Imereti and Kakheti kings are left out unless they also ruled Kartli); where pages disagree, the note says so.
Years are fractional where the month is known (a date d.m.y becomes y + (day of year)/365).
Usage: python -X utf8 -P tools/build_rulers.py
"""
import datetime
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W = "https://en.wikipedia.org/wiki/"


def y(d, m, yr):
    return round(yr + (datetime.date(yr, m, d).timetuple().tm_yday - 1) / 365.0, 3)


def N(ru, en, ka=None):
    return {"ru": ru, "en": en, "ka": ka or en}


GROUPS = {
    # states / forms of rule
    "monarchy": N("Монархия", "Monarchy", "მონარქია"),
    "emirate": N("Эмират", "Emirate", "საამირო"),
    "overlord": N("Сюзерен / внешняя власть", "Overlord / outside power", "სუზერენი / გარე ძალა"),
    "empire": N("Империя", "Empire", "იმპერია"),
    "republic": N("Республика", "Republic", "რესპუბლიკა"),
    "soviet": N("Советская власть", "Soviet rule", "საბჭოთა ხელისუფლება"),
    "transition": N("Переходный период", "Transitional period", "გარდამავალი პერიოდი"),
    # rulers
    "emir": N("Эмир Тбилиси", "Emir of Tbilisi", "თბილისის ამირა"),
    "king": N("Царь", "King", "მეფე"),
    "wali": N("Царь Картли, ставленник шаха/султана", "King of Kartli, appointed by the shah or the sultan", "ქართლის მეფე, შაჰის/სულთნის დანიშნული"),
    "emperor": N("Император России", "Emperor of Russia", "რუსეთის იმპერატორი"),
    "viceroy": N("Наместник на Кавказе", "Viceroy of the Caucasus", "კავკასიის მეფისნაცვალი"),
    "head": N("Глава правительства", "Head of government", "მთავრობის მეთაური"),
    "secretary": N("Первый секретарь ЦК КП Грузии", "First Secretary of the Communist Party of Georgia", "საქართველოს კპ ცკ პირველი მდივანი"),
    "president": N("Глава государства", "Head of state", "სახელმწიფოს მეთაური"),
}

STATES = []
RULERS = []


def S(id, a, b, kind, name, form, note="", src=(), lane=0, approx=False, date=""):
    STATES.append({"id": id, "from": a, "to": b, "kind": kind, "lane": lane, "name": name, "form": form, "note": note, "src": list(src), "approx": approx, "date": date})


def R(id, a, b, grp, name, note="", src=(), date="", title=None, lane=None):
    r = {"id": id, "from": a, "to": b, "grp": grp, "name": name, "note": note, "src": list(src), "date": date}
    if title:
        r["title"] = title
    if lane is not None:
        r["lane"] = lane
    RULERS.append(r)


E = lambda ru, en, ka=None: N(ru, en, ka)
KA_NAMES = {
    "Karl von Knorring": "კარლ ფონ კნორინგი",
    "Pavel Tsitsianov": "პავლე ციციანოვი (ციციშვილი)",
    "Ivan Gudovich": "ივან გუდოვიჩი",
    "Alexander Tormasov": "ალექსანდრე ტორმასოვი",
    "Philip Paulucci": "ფილიპო პაულუჩი",
    "Nikolay Rtishchev": "ნიკოლაი რტიშჩევი",
    "Aleksey Yermolov": "ალექსეი ერმოლოვი",
    "Ivan Paskevich": "ივან პასკევიჩი",
    "Gregor von Rosen": "გრიგორი როზენი",
    "Yevgeny Golovin": "ევგენი გოლოვინი",
    "Aleksandr Neidgardt": "ალექსანდრე ნეიდგარდტი",
    "Mikhail Vorontsov": "მიხეილ ვორონცოვი",
    "Nikolay Muravyov-Karsky": "ნიკოლაი მურავიოვ-კარსკი",
    "Aleksandr Baryatinsky": "ალექსანდრე ბარიატინსკი",
    "Grigol Orbeliani (acting)": "გრიგოლ ორბელიანი (მოვალეობის შემსრულებელი)",
    "Grand Duke Mikhail Nikolayevich": "დიდი მთავარი მიხეილ ნიკოლოზის ძე",
    "Aleksandr Dondukov-Korsakov": "ალექსანდრე დონდუკოვ-კორსაკოვი",
    "Sergei Sheremetyev": "სერგეი შერემეტევი",
    "Grigory Golitsyn": "გრიგორი გოლიცინი",
    "Yakov Malama (acting)": "იაკობ მალამა (მოვალეობის შემსრულებელი)",
    "Illarion Vorontsov-Dashkov": "ილარიონ ვორონცოვ-დაშკოვი",
    "Grand Duke Nikolay Nikolayevich": "დიდი მთავარი ნიკოლოზ ნიკოლოზის ძე",
    "Isma'il b. Shuab": "ისმაილ იბნ შუაბი",
    "Mohammed I b. Atab": "მუჰამედ I იბნ ატაბი",
    "Ali I b. Shuab": "ალი I იბნ შუაბი",
    "Ishaq b. Isma'il": "ისჰაკ იბნ ისმაილი",
    "Muhammad II b. Khalil": "მუჰამედ II იბნ ხალილი",
    "Isa b. al-Shaykh al-Shayban": "ისა იბნ ალ-შეიხ ალ-შაიბანი",
    "Ibrahim": "იბრაჰიმი",
    "Gabuloc": "გაბულოკი",
    "Jafar I b. Ali": "ჯაფარ I იბნ ალი",
    "Mansur I b. Jafar": "მანსურ I იბნ ჯაფარი",
    "Jafar II b. Mansur": "ჯაფარ II იბნ მანსური",
    "Ali II b. Jafar": "ალი II იბნ ჯაფარი",
    "Jafar III b. Ali": "ჯაფარ III იბნ ალი",
    "Mansur II b. Jafar": "მანსურ II იბნ ჯაფარი",
    "Abu'l-Hayja b. Jafar": "აბუ-ლ-ჰეჯა იბნ ჯაფარი",
    "Fadlun of Ganja": "ფადლუნ განჯელი",
}

NOTES_EN = {
    "david4": "Reigned from 1089; took Tbilisi in 1122; died on 24 January 1125.",
    "demetre1": "Abdicated in 1154; restored in 1155-1156.",
    "george3": "Reigned from 1155 (the list also names Demetrius I on the throne in 1155-1156).",
    "rusudan": "1226: Tbilisi taken by the Khwarazmian shah; 1236: Rusudan left Tbilisi before the Mongols; 1242-1243: the Mongol khan acknowledged as overlord.",
    "david7": "Eastern Georgia (David VI reigned in the west, 1245-1293).",
    "david8": "Reigned again in 1308-1311.",
    "bagrat5": "1386: Timur took Tbilisi (22 November) and captured Bagrat V.",
    "george7": "Years per the list 1393-1407; the page on Timur's invasions gives 1395-1405.",
    "demetre3": "Until December 1446.",
    "george8": "De facto 1446-1465 per the infobox; the list says until 1466.",
    "bagrat6": "Ruled Kartli until 1478 (the Kingdom of Kartli page); in the list a king of Imereti from 1463.",
    "david10": "Years per the list 1505-1526; George IX is named king in 1525-1527.",
    "george9": "Years per the list 1525-1527; cut here to 1526-1527 so that it does not overlap David X.",
    "simon1": "Reigned again in 1578-1600.",
    "david11": "Installed by the shah; the introduction of the Safavid Georgia page puts it in 1562, the 16th-century section in 1569-1578.",
    "simon1b": "Tbilisi was held by the Ottomans in 1578-1612; Simon ruled the rest of Kartli.",
    "luarsab2": "A wali of Persia; executed.",
    "bagrat7": "A governor appointed by the Safavids.",
    "simon2": "A khan and wali appointed by the Safavids.",
    "rostom": "Appointed in 1632/1633 (the pages differ).",
    "george11": "Reigned again in 1703-1709.",
    "jesse": "Again in 1724-1727.",
    "vakhtang6": "Exiled to Russia after the Ottoman invasion.",
    "jesse2": "The time of the Ottoman occupation.",
    "teimuraz2": "King of Kakheti until 1744 (1732-1744); king of Kartli 1744-1762 (the Kingdom of Kartli page).",
    "gamsakhurdia0": "Chairman of the Supreme Council (14 November 1990 - 14 April 1991).",
    "gamsakhurdia": "President; overthrown on 6 January 1992.",
    "council": "6 January - 10 March 1992 (per the table).",
    "shevardnadze1": "Chairman of the State Council (10 March - 4 November 1992), chairman of parliament and 'head of state' (6 November 1992 - 26 November 1995).",
    "shevardnadze2": "President; elected on 5 November 1995 (took office on 26 November 1995), re-elected on 9 April 2000; resigned on 23 November 2003 (the Rose Revolution).",
    "burjanadze1": "Acting president.",
    "saakashvili1": "Elected on 4 January 2004; resigned on 25 November 2007.",
    "burjanadze2": "Acting president.",
    "saakashvili2": "Re-elected on 5 January 2008.",
    "zourabichvili": "Start date: 'November 2018' in the text of the page, 16 December 2018 in its table. Her status after 2024 is disputed.",
    "kavelashvili": "Elected on 14 December 2024, inaugurated on 29 December 2024; his status is disputed (some parties consider Zourabichvili still the president).",
}

# ------------------------------------------------------------------ states
S("iberia", 364, 580, "monarchy", E("Иберийское царство (Картли)", "Kingdom of Iberia (Kartli)", "ივერიის სამეფო (ქართლი)"),
  E("монархия; вассал Сасанидов в 363-482 и 502-523, прямое сасанидское правление 523-580", "a monarchy; a vassal of Sasanian Persia in 363-482 and 502-523, direct Sasanian rule 523-580", "მონარქია; სასანიანთა ვასალი 363-482 და 502-523, უშუალო სასანიანური მმართველობა 523-580"),
  E("Отрезок начинается с начала шкалы (364: по странице Narikala крепость на месте будущего Тбилиси). 455 - год основания Тбилиси по инфобоксу «Tbilisi». Кто перенёс столицу в Тбилиси, страницы расходятся: Вахтанг I или Дачи (522-534).", "The segment starts at the beginning of the scale (364: per the Narikala page a fortress stood on the site of the future Tbilisi). 455 is the year of the founding in the Tbilisi infobox. Who moved the capital to Tbilisi differs between pages: Vakhtang I or Dachi (522-534).", "455 თბილისის დაარსების წელია. დედაქალაქის თბილისში გადატანა ვახტანგ I-ს ან დაჩის (522-534) მიეწერება."),
  [W + "Kingdom_of_Iberia", W + "Tbilisi"])
S("transition", 580, 736, "transition", E("Смена владык: Сасаниды, Византия, хазары, арабы", "Changing masters: the Sasanians, Byzantium, the Khazars, the Arabs", "ხელისუფლებათა ცვლა: სასანიანები, ბიზანტია, ხაზარები, არაბები"),
  E("Иберия теряет царя (580), провинция Сасанидов (марзпанство); арабы в Картли с 645, твёрдый контроль с 735", "Iberia loses its king (580), a Sasanian province under a marzpan; the Arabs in Kartli from 645, firm control from 735", "ივერია კარგავს მეფეს (580), სასანიანთა პროვინცია; არაბები ქართლში 645 წლიდან, მტკიცე კონტროლი 735 წლიდან"),
  E("Границы периода приблизительные: даты захвата Тбилиси в этот период на проверенных страницах не названы.", "The limits of the period are approximate: the pages read give no dates of the possession of Tbilisi in it.", "პერიოდის საზღვრები მიახლოებითია."),
  [W + "Kingdom_of_Iberia", W + "Emirate_of_Tbilisi"], approx=True)
S("emirate", 736, 1122, "emirate", E("Эмират Тбилиси", "Emirate of Tbilisi", "თბილისის საამირო"),
  E("эмират под властью Аббасидского халифата; эмиров утверждал халиф", "an emirate under the Abbasid Caliphate; the emirs were confirmed by the caliph", "საამირო აბასიანთა ხალიფატის ქვეშ"),
  E("Начало: 735 (взятие Тбилиси), 736 (инфобокс). Конец: 1122 (взятие Давидом IV), фактически с 1080 городской совет. Сельджуки: Алп-Арслан взял город в 1065.", "Start: 735 (the taking of Tbilisi) or 736 (infobox). End: 1122 (David IV), in effect a city council from 1080. Seljuks: Alp Arslan took the city in 1065.", ""),
  [W + "Emirate_of_Tbilisi", W + "Kingdom_of_Georgia"])
S("georgia", 1122, 1490, "monarchy", E("Грузинское царство (столица Тбилиси)", "Kingdom of Georgia (capital Tbilisi)", "საქართველოს სამეფო (დედაქალაქი თბილისი)"),
  E("феодальная монархия; золотой век 1122-1226; с 1463 распад, юридически конец в 1490", "a feudal monarchy; the Golden Age 1122-1226; broken up from 1463, de jure ended in 1490", "ფეოდალური მონარქია; ოქროს ხანა 1122-1226; 1463 წლიდან დაშლა, იურიდიულად 1490 წელს დასრულდა"),
  E("Столица Тбилиси с 1122 до 1490 (инфобокс). Давид IV взял Тбилиси в 1122. 1226: взятие хорезмшахом; 1236-1243: монгольское завоевание.", "Tbilisi was the capital from 1122 to 1490 (infobox). David IV took Tbilisi in 1122. 1226: taken by the Khwarazmian shah; 1236-1243: the Mongol conquest.", ""),
  [W + "Kingdom_of_Georgia", W + "Mongol_invasions_of_Georgia"])
S("kartli", 1490, 1762, "monarchy", E("Картлийское царство (столица Тбилиси)", "Kingdom of Kartli (capital Tbilisi)", "ქართლის სამეფო (დედაქალაქი თბილისი)"),
  E("царство; в разное время вассал Ирана и османов", "a kingdom; at different times a vassal of Persia and of the Ottomans", "სამეფო; სხვადასხვა დროს სპარსეთისა და ოსმალეთის ვასალი"),
  E("Инфобокс страницы: Картли 1478-1762. Здесь отрезок идёт от юридического конца единого царства (1490); картлийский царь Константин II правит с 1478.", "The infobox gives Kartli as 1478-1762. Here the segment starts from the de jure end of the united kingdom (1490); the Kartli king Constantine II ruled from 1478.", ""),
  [W + "Kingdom_of_Kartli"])
S("kartli_kakheti", 1762, 1801, "monarchy", E("Картли-Кахетинское царство", "Kingdom of Kartli-Kakheti", "ქართლ-კახეთის სამეფო"),
  E("абсолютная монархия; с 24.07.1783 российский протекторат (Георгиевский трактат)", "an absolute monarchy; a Russian protectorate from 24 July 1783 (the Treaty of Georgievsk)", "აბსოლუტური მონარქია; 1783 წლის 24 ივლისიდან რუსეთის პროტექტორატი"),
  E("1795: Ага-Мохаммед-хан взял и разорил Тбилиси (Крцаниси, 8-11 сентября). Присоединение: указ 18.12.1800, подтверждение 12.09.1801.", "1795: Agha Mohammad Khan took and sacked Tbilisi (Krtsanisi, 8-11 September). Annexation: decree of 18 December 1800, ratified on 12 September 1801.", ""),
  [W + "Kingdom_of_Kartli-Kakheti", W + "Battle_of_Krtsanisi"])
S("russia", 1801, y(18, 3, 1917), "empire", E("Российская империя (Кавказское наместничество)", "Russian Empire (the Caucasus Viceroyalty)", "რუსეთის იმპერია (კავკასიის მეფისნაცვლობა)"),
  E("империя; Тифлис - резиденция наместника на Кавказе", "an empire; Tiflis was the seat of the viceroy of the Caucasus", "იმპერია; ტფილისი კავკასიის მეფისნაცვლის რეზიდენცია"),
  E("Наместничество упразднено Временным правительством 18 марта 1917; власть перешла к Особому Закавказскому комитету.", "The viceroyalty was abolished by the Provisional Government on 18 March 1917; power passed to the Special Transcaucasian Committee.", ""),
  [W + "Caucasus_Viceroyalty_(1801%E2%80%931917)"])
S("tiflis_gov", 1846, 1917, "empire", E("Тифлисская губерния", "Tiflis Governorate", "ტფილისის გუბერნია"), E("губерния Кавказского наместничества", "a governorate of the Caucasus Viceroyalty", "კავკასიის მეფისნაცვლობის გუბერნია"),
  E("Образована в 1846 (страница); список губернаторов на странице начинается с 1847.", "Formed in 1846 (the page); the list of governors starts in 1847.", ""), [W + "Tiflis_Governorate"], lane=1)
S("ozakom", y(9, 3, 1917), y(14, 11, 1917), "transition", E("Особый Закавказский комитет (ОЗАКОМ)", "Special Transcaucasian Committee (Ozakom)", "ამიერკავკასიის სპეციალური კომიტეტი"),
  E("орган Временного правительства; председатель В. Харламов", "a body of the Russian Provisional Government; chairman V. Kharlamov", ""),
  E("Образован 9 марта 1917. Преемник - Закавказский комиссариат (11, 14 или 15 ноября 1917 - страницы расходятся).", "Established on 9 March 1917. Its successor was the Transcaucasian Commissariat (11, 14 or 15 November 1917: the pages differ).", ""),
  [W + "Special_Transcaucasian_Committee"])
S("commissariat", y(14, 11, 1917), y(22, 4, 1918), "transition", E("Закавказский комиссариат", "Transcaucasian Commissariat", "ამიერკავკასიის კომისარიატი"),
  E("временное региональное правительство", "a caretaker regional government", ""), E("Конец: заменён ЗДФР 22 апреля 1918 (точная дата распада в страницах не названа).", "Replaced by the TDFR on 22 April 1918 (the pages give no exact date of its end).", ""),
  [W + "Special_Transcaucasian_Committee", W + "Transcaucasian_Democratic_Federative_Republic"])
S("tdfr", y(22, 4, 1918), y(26, 5, 1918), "republic", E("Закавказская демократическая федеративная республика", "Transcaucasian Democratic Federative Republic", "ამიერკავკასიის დემოკრატიული ფედერაციული რესპუბლიკა"),
  E("федеративная парламентская республика", "a federal parliamentary republic", ""), E("22 апреля - 26 мая 1918 (по DRG; инфобокс TDFR называет 28 мая). Председатель Сейма Н. Чхеидзе, премьер А. Чхенкели.", "22 April - 26 May 1918 (per the DRG page; the TDFR infobox says 28 May). Chairman of the Seim N. Chkheidze, prime minister A. Chkhenkeli.", ""),
  [W + "Transcaucasian_Democratic_Federative_Republic", W + "Democratic_Republic_of_Georgia"])
S("drg", y(26, 5, 1918), y(25, 2, 1921), "republic", E("Демократическая Республика Грузия", "Democratic Republic of Georgia", "საქართველოს დემოკრატიული რესპუბლიკა"),
  E("унитарная парламентская республика (с исполнительным председателем)", "a unitary parliamentary republic with an executive presidency (the infobox wording)", ""),
  E("Акт независимости 26.05.1918. Выборы 14-16.02.1919; конституция принята 21.02.1921. Конец: советская оккупация 25.02.1921 (правительство в изгнании с 18.03.1921).", "Act of Independence on 26 May 1918. Elections on 14-16 February 1919; the constitution adopted on 21 February 1921. End: the Soviet occupation on 25 February 1921 (the government in exile from 18 March 1921).", ""),
  [W + "Democratic_Republic_of_Georgia"])
S("gssr", y(25, 2, 1921), y(14, 4, 1991), "soviet", E("Грузинская ССР", "Georgian Soviet Socialist Republic", "საქართველოს საბჭოთა სოციალისტური რესპუბლიკა"),
  E("коммунистическое государство; 1922-1936 в составе ЗСФСР (12.03.1922-5.12.1936), затем союзная республика; с 14.11.1990 «Республика Грузия»", "a communist state; in the Transcaucasian SFSR 1922-1936 (12 March 1922 - 5 December 1936), then a union republic; renamed Republic of Georgia on 14 November 1990", ""),
  E("Формирование 25.02.1921; в СССР с 30.12.1922. Независимость провозглашена 9.04.1991 (страница не даёт точной даты конца ССР).", "Formed on 25 February 1921; in the USSR from 30 December 1922. Independence declared on 9 April 1991 (the page gives no exact end date of the SSR).", ""),
  [W + "Georgian_Soviet_Socialist_Republic"])
S("rep1991", y(14, 4, 1991), y(6, 1, 1992), "republic", E("Республика Грузия: президентство Гамсахурдиа", "Republic of Georgia: the presidency of Gamsakhurdia", "საქართველოს რესპუბლიკა: გამსახურდიას პრეზიდენტობა"),
  E("независимость провозглашена 9.04.1991; пост президента учреждён 14.04.1991", "independence declared on 9 April 1991; the presidency created on 14 April 1991", ""),
  E("Конец: военный переворот 6 января 1992.", "End: the military coup on 6 January 1992.", ""), [W + "President_of_Georgia", W + "Georgian_Soviet_Socialist_Republic"])
S("council1992", y(6, 1, 1992), y(26, 11, 1995), "transition", E("Военный совет и Госсовет, затем председатель парламента", "The Military Council and the State Council, then the chairman of parliament", "სამხედრო საბჭო და სახელმწიფო საბჭო"),
  E("переходный период без президента", "a transitional period without a president", ""),
  E("6.01.1992 Военный совет и временное правительство; Госсовет учреждён в 1992 (точная дата в страницах не названа); с 6.11.1992 Шеварднадзе - председатель парламента и «глава государства».", "On 6 January 1992 the Military Council and a provisional government; the State Council was set up in 1992 (no exact date in the pages); from 6 November 1992 Shevardnadze was chairman of parliament and 'head of state'.", ""),
  [W + "President_of_Georgia", W + "Constitution_of_Georgia_(country)"])
S("rep1995", y(26, 11, 1995), y(17, 11, 2013), "republic", E("Республика Грузия по конституции 1995", "Republic of Georgia under the 1995 constitution", "საქართველოს რესპუბლიკა 1995 წლის კონსტიტუციით"),
  E("конституция принята 24.08.1995, в силе с 17.10.1995; пост премьер-министра вновь введён в феврале 2004", "the constitution adopted on 24 August 1995, in force from 17 October 1995; the post of prime minister reintroduced in February 2004", ""),
  E("2003: Революция роз, отставка Шеварднадзе 23.11.2003. Поправки 15.10.2010 сокращают полномочия президента; вступили в силу 17.11.2013.", "2003: the Rose Revolution, Shevardnadze resigned on 23 November 2003. The amendments of 15 October 2010 reduce the presidential powers; in force from 17 November 2013.", ""),
  [W + "President_of_Georgia", W + "Constitution_of_Georgia_(country)", W + "Prime_Minister_of_Georgia"])
S("rep2013", y(17, 11, 2013), 2026.9, "republic", E("Парламентская республика", "Parliamentary republic", "საპარლამენტო რესპუბლიკა"),
  E("унитарная парламентская республика (по последней поправке); президент - церемониальный глава государства", "a unitary parliamentary republic (according to the last amendment); the president is a ceremonial head of state", ""),
  E("Переход оформлен поправками 2013-2018 (страницы называют 2012-2018, 2013-2018); 26.09.2017 принята отмена прямых президентских выборов.", "The transition was made by the amendments of 2013-2018 (the pages say 2012-2018 and 2013-2018); on 26 September 2017 parliament abolished direct presidential elections.", ""),
  [W + "Constitution_of_Georgia_(country)", W + "President_of_Georgia", W + "Prime_Minister_of_Georgia"])

# overlords / outside powers (second lane of the states)
OV = [
  ("ov_mongol", 1243, 1329, E("Монгольское сюзеренство", "Mongol overlordship", "მონღოლთა სუზერენობა"), E("формальное подчинение Великому хану в 1243; царь утверждается ханом; «до конца 1330-х»", "formal submission to the Great Khan in 1243; the king confirmed by the Khan; 'until the late 1330s'", ""), "Конец: 1329 (инфобокс: воссоединение) или конец 1330-х; начало 1243 (формальное подчинение), полномасштабное вторжение 1236.", "End: 1329 (the infobox: reunification) or the late 1330s; start 1243 (the formal submission), the full-scale invasion 1236.", [W + "Mongol_invasions_of_Georgia", W + "Kingdom_of_Georgia"]),
  ("ov_timur", 1386, 1403, E("Тимур: вторжения, дань", "Timur: invasions and tribute", "თემურლენგის შემოსევები"), E("Грузия - данник; царь сохраняет власть", "Georgia a tributary state; the king kept his power", ""), "22 ноября 1386 Тимур взял и разорил Тбилиси, взят в плен Баграт V.", "On 22 November 1386 Timur took and sacked Tbilisi; Bagrat V was captured.", [W + "Timurid_invasions_of_Georgia"]),
  ("ov_safavid1", 1555, 1578, E("Сефевиды (Амасийский мир)", "The Safavids (the Peace of Amasya)", "სეფიანები"), E("Картли - вассал Ирана", "Kartli a vassal of Persia", ""), "Мир в Амасье 1555 разделил Грузию между Ираном (восток) и османами (запад); Шах Исмаил I держал гарнизон в Тбилиси с 1522.", "The Peace of Amasya (1555) divided Georgia between Persia (east) and the Ottomans (west); Shah Ismail I garrisoned Tbilisi in 1522.", [W + "Kingdom_of_Kartli", W + "Safavid_Georgia"]),
  ("ov_ottoman1", 1578, 1612, E("Османская оккупация и вассалитет", "Ottoman occupation and vassalage", "ოსმალთა ბატონობა"), E("Тбилиси взят османами 21-24.08.1578 (Осман-паша и Мустафа-паша)", "Tbilisi captured by the Ottomans on 21-24 August 1578 (Osman Pasha and Mustafa Pasha)", ""), "Конец 1612 по инфобоксу Картли; договор 1590 признал за османами эту область.", "End 1612 per the Kartli infobox; the Treaty of Constantinople (1590) recognised the Ottoman possession.", [W + "Kingdom_of_Kartli", W + "Safavid_Georgia"]),
  ("ov_safavid2", 1612, 1723, E("Сефевиды: вассалитет Картли", "The Safavids: Kartli a vassal", "სეფიანები"), E("цари Картли - вали Ирана", "the kings of Kartli were walis of Persia", ""), "1614-1617: походы Аббаса I, Тбилиси разорён.", "1614-1617: the campaigns of Abbas I, Tbilisi sacked.", [W + "Kingdom_of_Kartli", W + "Safavid_Georgia"]),
  ("ov_ottoman2", 1723, 1736, E("Османская оккупация", "Ottoman occupation", "ოსმალთა ბატონობა"), E("вассалитет Картли у османов", "Kartli a vassal of the Ottomans", ""), "Инфобокс Kingdom of Kartli: 1723-1736.", "The Kartli infobox: 1723-1736.", [W + "Kingdom_of_Kartli"]),
  ("ov_persia", 1736, 1747, E("Иран (Надир-шах)", "Persia (Nader Shah)", "სპარსეთი (ნადირ-შაჰი)"), E("вассалитет Картли; после смерти Надир-шаха (1747) Теймураз II и Ираклий II провозгласили фактическую независимость", "Kartli a vassal; after Nader Shah's death (1747) Teimuraz II and Heraclius II declared de facto independence", ""), "", "", [W + "Kingdom_of_Kartli"]),
  ("ov_russia", y(24, 7, 1783), 1801, E("Российский протекторат", "Russian protectorate", "რუსეთის პროტექტორატი"), E("Георгиевский трактат 24.07.1783", "the Treaty of Georgievsk of 24 July 1783", ""), "Российский контингент в Тбилиси 1784-1787.", "A Russian contingent in Tbilisi in 1784-1787.", [W + "Kingdom_of_Kartli-Kakheti"]),
]
for oid, a, b, nm, fm, nr, ne, src in OV:
    S(oid, a, b, "overlord", nm, fm, E(nr, ne), src, lane=1)

# ------------------------------------------------------------------ rulers
# emirs of Tbilisi (the table on the page "Emirate of Tbilisi")
EM = [("Исмаил ибн Шуайб", "Isma'il b. Shuab", None, 736, 813), ("Мухаммад I ибн Атаб", "Mohammed I b. Atab", None, 813, 829), ("Али I ибн Шуайб", "Ali I b. Shuab", None, 829, 833),
      ("Исхак ибн Исмаил", "Ishaq b. Isma'il", None, 833, 853), ("Мухаммад II ибн Халил", "Muhammad II b. Khalil", None, 853, 870), ("Иса ибн аш-Шайх аш-Шайбани", "Isa b. al-Shaykh al-Shayban", None, 870, 876),
      ("Ибрахим", "Ibrahim", None, 876, 878), ("Габулок", "Gabuloc", None, 878, 880), ("Джафар I ибн Али", "Jafar I b. Ali", None, 880, 914), ("Мансур I ибн Джафар", "Mansur I b. Jafar", None, 914, 952),
      ("Джафар II ибн Мансур", "Jafar II b. Mansur", None, 952, 981), ("Али II ибн Джафар", "Ali II b. Jafar", None, 981, 1032), ("Джафар III ибн Али", "Jafar III b. Ali", None, 1032, 1046),
      ("Мансур II ибн Джафар", "Mansur II b. Jafar", None, 1046, 1054), ("Абу-ль-Хайджа ибн Джафар", "Abu'l-Hayja b. Jafar", None, 1054, 1062),
      ("Фадлун Гянджинский", "Fadlun of Ganja", None, 1068, 1080)]
for i, (ru, en, ka, a, b) in enumerate(EM):
    nt = "Начало правления Исмаила в списке не указано (начало эмирата 736), конец «до 813»." if i == 0 else ("Назначен Алп-Арсланом." if a == 1068 else "")
    nte = "The list gives no start for Isma'il (the emirate began in 736), only 'until 813'." if i == 0 else ("Appointed by Alp Arslan." if a == 1068 else "")
    R("emir%d" % i, a, b, "emir", E(ru, en, KA_NAMES.get(en)), E(nt, nte), [W + "Emirate_of_Tbilisi"])
R("council1", 1062, 1068, "emir", E("Городской совет", "City council", "ქალაქის საბჭო"), E("Между эмирами (список эмиров)", "Between the emirs (the list of emirs)"), [W + "Emirate_of_Tbilisi"], title=N("Самоуправление", "Self-government"))
R("council2", 1080, 1122, "emir", E("Городской совет", "City council", "ქალაქის საბჭო"), E("До взятия Тбилиси Давидом IV (1122)", "Until David IV took Tbilisi (1122)"), [W + "Emirate_of_Tbilisi"], title=N("Самоуправление", "Self-government"))

# kings of Iberia who held Tbilisi (the list of monarchs of Georgia; Tbilisi was founded in the 5th century by tradition)
KI0 = [("aspacures2", 363, 365, "Аспагур II", "Aspacures II", "ასპაგურ II", ""), ("mihrdat3", 365, 380, "Мирдат III", "Mihrdat III", "მირდატ III", "В 370-378 соправительство (по списку: diarch 370-378)."),
       ("aspacures3", 380, 394, "Аспагур III", "Aspacures III", "ასპაგურ III", ""), ("trdat", 394, 406, "Трдат", "Trdat", "თრდატ", ""), ("pharasmanes4", 406, 409, "Фарсман IV", "Pharasmanes IV", "ფარსმან IV", ""),
       ("mihrdat4", 409, 411, "Мирдат IV", "Mihrdat IV", "მირდატ IV", ""), ("archil1", 411, 435, "Арчил I", "Archil I", "არჩილ I", ""), ("mihrdat5", 435, 447, "Мирдат V", "Mihrdat V", "მირდატ V", "")]
for rid, a, b, ru, en, ka, nt in KI0:
    nte = "A joint rule in 370-378 (the list: diarch 370-378)." if rid == "mihrdat3" else ""
    R(rid, a, b, "king", E(ru, en, ka), E(nt, nte), [W + "List_of_monarchs_of_Georgia"], title=N("Царь Иберии", "King of Iberia", "ივერიის მეფე"))
EARLY = E("Тбилиси по преданию ещё не основан (455); эти цари правили землёй Картли, на которой он возник.", "By tradition Tbilisi was not yet founded (455); these kings ruled the land of Kartli on which it arose.")
for r in RULERS:
    if r["id"] in [k[0] for k in KI0]:
        r["note"] = {l: ((r["note"].get(l) + " ") if r["note"].get(l) else "") + EARLY[l] for l in ("ru", "en", "ka")}
KI = [("vakhtang1", 447, 522, "Вахтанг I Горгасали", "Vakhtang I Gorgasali", "ვახტანგ I გორგასალი", "Годы по списку 447-522; по странице Kingdom of Iberia 447-502 (расхождение). По преданию основатель Тбилиси."),
      ("dachi", 522, 534, "Дачи", "Dachi", "დაჩი", "Правление c. 522-534; по Tbilisi перенёс столицу из Мцхеты."),
      ("bacurius2", 534, 547, "Бакур II", "Bacurius II", "ბაკური II", ""), ("pharasmanes5", 547, 561, "Фарсман V", "Pharasmanes V", "ფარსმან V", "")]
for rid, a, b, ru, en, ka, nt in KI:
    R(rid, a, b, "king", E(ru, en, ka), E(nt, nt and ("Years per the list 447-522; the Kingdom of Iberia page gives 447-502 (a disagreement). Founder of Tbilisi by tradition." if rid == "vakhtang1" else ("c. 522-534; per the Tbilisi page he moved the capital from Mtskheta." if rid == "dachi" else ""))), [W + "List_of_monarchs_of_Georgia", W + "Tbilisi"], title=N("Царь Иберии", "King of Iberia", "ივერიის მეფე"))
R("pharasmanes6", 561, 580, "king", E("Фарсман VI и Бакур III", "Pharasmanes VI and Bacurius III", "ფარსმან VI და ბაკური III"), E("Конец иберийской монархии (580); годы каждого по списку неполные («561-?» и «?-580»).", "The end of the Iberian monarchy (580); the years of each are incomplete in the list ('561-?' and '?-580')."), [W + "List_of_monarchs_of_Georgia"], title=N("Цари Иберии", "Kings of Iberia", "ივერიის მეფეები"))

# kings of Georgia (the table of the Bagrationi monarchs); from David IV the years in which Tbilisi was in his hands
KG = [
 ("david4", 1122, 1125, "Давид IV Строитель", "David IV the Builder", "დავით IV აღმაშენებელი", "Правит с 1089; Тбилиси взят в 1122; умер 24.01.1125."),
 ("demetre1", 1125, 1154, "Деметре I", "Demetrius I", "დემეტრე I", "Отрёкся в 1154; восстановлен 1155-1156."),
 ("david5", 1154, 1155, "Давид V", "David V", "დავით V", ""),
 ("demetre1b", 1155, 1156, "Деметре I (повторно)", "Demetrius I (again)", "დემეტრე I", ""),
 ("george3", 1156, 1184, "Георгий III", "George III", "გიორგი III", "Правит с 1155 (в списке Деметре I также назван на троне в 1155-1156)."),
 ("tamar", 1184, 1213, "Тамара", "Tamar I the Great", "თამარ მეფე", ""),
 ("george4", 1213, 1223, "Георгий IV Лаша", "George IV the Resplendent", "გიორგი IV ლაშა", ""),
 ("rusudan", 1223, 1245, "Русудан", "Rusudan", "რუსუდან მეფე", "1226: Тбилиси взят хорезмшахом; 1236: Русудан покидает Тбилиси перед монголами; 1242-1243: признание власти монгольского хана."),
 ("david7", 1248, 1270, "Давид VII Улу", "David VII the Elder", "დავით VII", "Восточная Грузия (в Западной - Давид VI, 1245-1293)."),
 ("demetre2", 1270, 1289, "Деметре II Самопожертвователь", "Demetrius II the Devoted", "დემეტრე II თავდადებული", ""),
 ("vakhtang2", 1289, 1292, "Вахтанг II", "Vakhtang II", "ვახტანგ II", ""),
 ("david8", 1292, 1302, "Давид VIII", "David VIII", "დავით VIII", "Повторно правит 1308-1311."),
 ("vakhtang3", 1302, 1308, "Вахтанг III", "Vakhtang III", "ვახტანგ III", ""),
 ("david8b", 1308, 1311, "Давид VIII (повторно)", "David VIII (again)", "დავით VIII", ""),
 ("george6", 1311, 1318, "Георгий VI Малый", "George VI the Minor", "გიორგი VI", ""),
 ("george5", 1318, 1346, "Георгий V Блистательный", "George V the Brilliant", "გიორგი V ბრწყინვალე", "Воссоединение Грузии 1329 (инфобокс)."),
 ("david9", 1346, 1360, "Давид IX", "David IX", "დავით IX", ""),
 ("bagrat5", 1360, 1393, "Баграт V Великий", "Bagrat V the Great", "ბაგრატ V დიდი", "1386: Тимур взял Тбилиси (22 ноября) и пленил Баграта V."),
 ("george7", 1393, 1407, "Георгий VII", "George VII", "გიორგი VII", "Годы по списку 1393-1407; страница о вторжениях Тимура даёт 1395-1405."),
 ("constantine1", 1407, 1412, "Константин I", "Constantine I", "კონსტანტინე I", ""),
 ("alexander1", 1412, 1442, "Александр I Великий", "Alexander I the Great", "ალექსანდრე I დიდი", ""),
 ("demetre3", 1442, y(1, 12, 1446), "Деметре III", "Demetrius III", "დემეტრე III", "До декабря 1446."),
 ("george8", y(1, 12, 1446), 1466, "Георгий VIII", "George VIII", "გიორგი VIII", "Фактически 1446-1465 по инфобоксу; в списке до 1466."),
 ("bagrat6", 1466, 1478, "Баграт VI", "Bagrat VI", "ბაგრატ VI", "Правил Картли до 1478 (страница Kingdom of Kartli); в списке царь Имерети с 1463."),
]
for rid, a, b, ru, en, ka, nt in KG:
    R(rid, a, b, "king", E(ru, en, ka), E(nt, NOTES_EN.get(rid, nt)), [W + "List_of_monarchs_of_Georgia", W + "Kingdom_of_Georgia"], title=N("Царь Грузии", "King of Georgia", "საქართველოს მეფე"))
RULERS[-1]["src"].append(W + "Kingdom_of_Kartli")

# kings of Kartli (the list of monarchs; the gaps are the years for which the list names nobody for Kartli)
KK = [
 ("constantine2", 1478, 1505, "Константин II", "Constantine II", "კონსტანტინე II", "king", ""),
 ("david10", 1505, 1526, "Давид X", "David X", "დავით X", "king", "Годы по списку: 1505-1526; Георгий IX назван царём в 1525-1527."),
 ("george9", 1526, 1527, "Георгий IX", "George IX", "გიორგი IX", "king", "Годы по списку 1525-1527; здесь обрезаны до 1526-1527, чтобы не накладываться на Давида X."),
 ("luarsab1", 1527, 1556, "Луарсаб I", "Luarsab I", "ლუარსაბ I", "king", ""),
 ("simon1", 1556, 1569, "Симон I Великий", "Simon I the Great", "სიმონ I დიდი", "king", "Правит также в 1578-1600."),
 ("david11", 1569, 1578, "Давид XI (Дауд-хан)", "David XI (Daud Khan)", "დავით XI (დაუდ-ხანი)", "wali", "Поставлен шахом; во вводной части страницы Safavid Georgia поставлен в 1562, в разделе о XVI веке 1569-1578."),
 ("simon1b", 1578, 1600, "Симон I Великий (повторно)", "Simon I the Great (again)", "სიმონ I დიდი", "king", "Тбилиси в 1578-1612 занят османами; Симон правит остальным Картли."),
 ("george10", 1600, y(7, 9, 1606), "Георгий X", "George X", "გიორგი X", "king", ""),
 ("luarsab2", y(7, 9, 1606), y(1, 7, 1615), "Луарсаб II Святой Мученик", "Luarsab II the Holy Martyr", "ლუარსაბ II", "wali", "Вали Ирана; казнён."),
 ("bagrat7", 1616, 1619, "Баграт VII", "Bagrat VII", "ბაგრატ VII", "wali", "Губернатор, назначенный сефевидами."),
 ("simon2", 1619, 1631, "Симон II", "Simon II", "სიმონ II", "wali", "Хан и вали, назначенный сефевидами."),
 ("rostom", 1633, y(17, 11, 1658), "Ростом", "Rostom", "როსტომ", "wali", "Назначен в 1632/1633 (расхождение внутри страниц)."),
 ("vakhtang5", y(17, 11, 1658), 1676, "Вахтанг V", "Vakhtang V", "ვახტანგ V", "wali", ""),
 ("george11", 1676, 1688, "Георгий XI", "George XI", "გიორგი XI", "wali", "Правит также в 1703-1709."),
 ("george11b", 1703, y(21, 4, 1709), "Георгий XI (повторно)", "George XI (again)", "გიორგი XI", "wali", ""),
 ("kaikhosro", y(21, 4, 1709), y(27, 9, 1711), "Кайхосро", "Kaikhosro", "ქაიხოსრო", "wali", ""),
 ("jesse", 1714, 1716, "Иесей", "Jesse", "იესე", "wali", "Повторно в 1724-1727."),
 ("vakhtang6", 1716, 1724, "Вахтанг VI Учёный", "Vakhtang VI the Scholar", "ვახტანგ VI", "king", "Изгнан в Россию после османского вторжения."),
 ("jesse2", 1724, 1727, "Иесей (повторно)", "Jesse (again)", "იესე", "wali", "Время османской оккупации."),
 ("teimuraz2", 1744, 1762, "Теймураз II", "Teimuraz II", "თეიმურაზ II", "king", "До 1744 царь Кахети (1732-1744); царь Картли 1744-1762 (страница Kingdom of Kartli)."),
]
TTL = {"king": N("Царь Картли", "King of Kartli", "ქართლის მეფე"), "wali": N("Царь Картли (вали Ирана/османов)", "King of Kartli (a wali of Persia or the Ottomans)", "ქართლის მეფე (შაჰის/სულთნის ვალი)")}
for rid, a, b, ru, en, ka, g, nt in KK:
    R(rid, a, b, g, E(ru, en, ka), E(nt, NOTES_EN.get(rid, nt)), [W + "List_of_monarchs_of_Georgia", W + "Kingdom_of_Kartli"], title=TTL[g])
R("heraclius2", 1762, y(11, 1, 1798), "king", E("Ираклий II", "Heraclius II", "ერეკლე II"), E("Царь Кахети с 1744, с 1762 Картли-Кахети (в списке до 11.01.1798).", "King of Kakheti from 1744, of Kartli-Kakheti from 1762 (to 11 January 1798 in the list)."), [W + "Kingdom_of_Kartli-Kakheti", W + "List_of_monarchs_of_Georgia"], title=N("Царь Картли-Кахети", "King of Kartli-Kakheti", "ქართლ-კახეთის მეფე"))
R("george12", y(11, 1, 1798), y(28, 12, 1800), "king", E("Георгий XII", "George XII", "გიორგი XII"), E("", ""), [W + "Kingdom_of_Kartli-Kakheti", W + "List_of_monarchs_of_Georgia"], title=N("Царь Картли-Кахети", "King of Kartli-Kakheti", "ქართლ-კახეთის მეფე"))
R("david_regent", y(28, 12, 1800), 1801, "king", E("Давид Багратиони (регент)", "David Bagrationi (regent)", "დავით ბატონიშვილი (რეგენტი)"), E("Регент 1800-1801 (инфобокс).", "Regent 1800-1801 (infobox)."), [W + "Kingdom_of_Kartli-Kakheti"], title=N("Регент", "Regent", "რეგენტი"))

# Russian emperors (the dates of the reigns from the page "List of Russian monarchs")
EMP = [("paul1", y(23, 3, 1801), y(23, 3, 1801), "Павел I", "Paul I", "პავლე I", ""), ("alexander1r", y(23, 3, 1801), y(1, 12, 1825), "Александр I", "Alexander I", "ალექსანდრე I", ""),
       ("nicholas1", y(1, 12, 1825), y(2, 3, 1855), "Николай I", "Nicholas I", "ნიკოლოზ I", ""), ("alexander2", y(2, 3, 1855), y(13, 3, 1881), "Александр II", "Alexander II", "ალექსანდრე II", ""),
       ("alexander3", y(13, 3, 1881), y(1, 11, 1894), "Александр III", "Alexander III", "ალექსანდრე III", ""), ("nicholas2", y(1, 11, 1894), y(15, 3, 1917), "Николай II", "Nicholas II", "ნიკოლოზ II", "Отрёкся во время Февральской революции (15.03.1917).")]
for rid, a, b, ru, en, ka, nt in EMP:
    if rid == "paul1":
        continue          # Paul I reigned 17.11.1796-23.03.1801: only the months before the annexation of 1801 are in the band, left out
    R(rid, a, b, "emperor", E(ru, en, ka), E(nt, "Abdicated during the February Revolution (15 March 1917)." if nt else ""), [W + "List_of_Russian_monarchs"], title=N("Император России", "Emperor of Russia", "რუსეთის იმპერატორი"), lane=0)
R("paul1", 1801, y(23, 3, 1801), "emperor", E("Павел I", "Paul I", "პავლე I"), E("Правил с 17.11.1796 до 23.03.1801; присоединение Картли-Кахети - указ от 18.12.1800.", "Reigned from 17 November 1796 to 23 March 1801; Kartli-Kakheti annexed by the decree of 18 December 1800."), [W + "List_of_Russian_monarchs", W + "Kingdom_of_Kartli-Kakheti"], title=N("Император России", "Emperor of Russia", "რუსეთის იმპერატორი"), lane=0)

# viceroys / high commissioners of the Caucasus (the list on "Caucasus Viceroyalty (1801-1917)")
VR = [("Карл фон Кнорринг", "Karl von Knorring", 1801, 1802), ("Павел Цицианов", "Pavel Tsitsianov", 1802, 1806), ("Иван Гудович", "Ivan Gudovich", 1806, 1809), ("Александр Тормасов", "Alexander Tormasov", 1809, 1811),
      ("Филипп Паулуччи", "Philip Paulucci", 1811, 1812), ("Николай Ртищев", "Nikolay Rtishchev", 1812, 1816), ("Алексей Ермолов", "Aleksey Yermolov", 1816, 1827), ("Иван Паскевич", "Ivan Paskevich", 1827, 1831),
      ("Григорий фон Розен", "Gregor von Rosen", 1831, 1838), ("Евгений Головин", "Yevgeny Golovin", 1838, 1842), ("Александр Нейдгардт", "Aleksandr Neidgardt", 1842, 1844), ("Михаил Воронцов", "Mikhail Vorontsov", 1844, 1854),
      ("Николай Муравьёв-Карский", "Nikolay Muravyov-Karsky", 1854, 1856), ("Александр Барятинский", "Aleksandr Baryatinsky", 1856, 1862), ("Григол Орбелиани (временно)", "Grigol Orbeliani (acting)", 1862, 1862.9),
      ("Великий князь Михаил Николаевич", "Grand Duke Mikhail Nikolayevich", 1862.9, 1882), ("Александр Дондуков-Корсаков", "Aleksandr Dondukov-Korsakov", 1882, 1890), ("Сергей Шереметев", "Sergei Sheremetyev", 1890, 1896),
      ("Григорий Голицын", "Grigory Golitsyn", 1896, 1904), ("Яков Малама (временно)", "Yakov Malama (acting)", 1904, 1904.5), ("Илларион Воронцов-Дашков", "Illarion Vorontsov-Dashkov", 1904.5, 1916),
      ("Великий князь Николай Николаевич", "Grand Duke Nikolay Nikolayevich", 1916, y(18, 3, 1917))]
for i, (ru, en, a, b) in enumerate(VR):
    R("viceroy%d" % i, a, b, "viceroy", E(ru, en, KA_NAMES.get(en)), E("Годы по списку; месяцы внутри года страница не называет (для границ внутри 1862 и 1904 годы разделены условно).", "Years as in the list; the page gives no months (the limits inside 1862 and 1904 are conventional)."), [W + "Caucasus_Viceroyalty_(1801%E2%80%931917)"], title=N("Наместник на Кавказе", "Viceroy of the Caucasus", "კავკასიის მეფისნაცვალი"), lane=1)

# the Democratic Republic of Georgia, 1918-1921 (the table in "Prime Minister of Georgia")
R("ramishvili", y(26, 5, 1918), y(24, 6, 1918), "head", E("Ной Рамишвили", "Noe Ramishvili", "ნოე რამიშვილი"), E("Председатель правительства.", "Chairman of the government."), [W + "Prime_Minister_of_Georgia"], title=N("Председатель правительства", "Chairman of the government", "მთავრობის თავმჯდომარე"))
R("zhordania", y(24, 6, 1918), y(18, 3, 1921), "head", E("Ной Жордания", "Noe Zhordania", "ნოე ჟორდანია"), E("Председатель правительства; срок кончился 18.03.1921.", "Chairman of the government; his term ended on 18 March 1921."), [W + "Prime_Minister_of_Georgia", W + "Democratic_Republic_of_Georgia"], title=N("Председатель правительства", "Chairman of the government", "მთავრობის თავმჯდომარე"))

# first secretaries of the Communist Party of Georgia (the page "First Secretary of the Georgian Communist Party")
FS = [("Мамия Орахелашвили", "Mamia Orakhelashvili", "მამია ორახელაშვილი", y(1, 3, 1921), y(1, 4, 1922)), ("Михаил Окуджава", "Mikheil Okujava", "მიხეილ ოკუჯავა", y(1, 4, 1922), y(22, 10, 1922)),
      ("Виссарион Ломинадзе", "Vissarion Lominadze", "ვისარიონ ლომინაძე", y(25, 10, 1922), y(1, 8, 1924)), ("Михаил Кахиани", "Mikheil Kakhiani", "მიხეილ კახიანი", y(1, 8, 1924), y(1, 5, 1930)),
      ("Леван Гогоберидзе", "Levan Gogoberidze", "ლევან გოგობერიძე", y(1, 5, 1930), y(19, 11, 1930)), ("Самсон Мамулия", "Samson Mamulia", "სამსონ მამულია", y(20, 11, 1930), y(11, 9, 1931)),
      ("Лаврентий Картвелишвили", "Lavrenty Kartvelishvili", "ლავრენტი ქართველიშვილი", y(11, 9, 1931), y(14, 11, 1931)), ("Лаврентий Берия", "Lavrenti Beria", "ლავრენტი ბერია", y(14, 11, 1931), y(18, 10, 1932)),
      ("Пётр Агниашвили", "Petre Agniashvili", "პეტრე აგნიაშვილი", y(18, 10, 1932), y(15, 1, 1934)), ("Лаврентий Берия (повторно)", "Lavrenti Beria (again)", "ლავრენტი ბერია", y(15, 1, 1934), y(31, 8, 1938)),
      ("Кандид Чарквиани", "Candide Charkviani", "კანდიდ ჩარკვიანი", y(31, 8, 1938), y(2, 4, 1952)), ("Акакий Мгеладзе", "Akaki Mgeladze", "აკაკი მგელაძე", y(2, 4, 1952), y(14, 4, 1953)),
      ("Александр Мирцхулава", "Aleksandre Mirtskhulava", "ალექსანდრე მირცხულავა", y(14, 4, 1953), y(19, 9, 1953)), ("Василий Мжаванадзе", "Vasil Mzhavanadze", "ვასილ მჟავანაძე", y(20, 9, 1953), y(29, 9, 1972)),
      ("Эдуард Шеварднадзе", "Eduard Shevardnadze", "ედუარდ შევარდნაძე", y(29, 9, 1972), y(6, 7, 1985)), ("Джумбер Патиашвили", "Jumber Patiashvili", "ჯუმბერ პატიაშვილი", y(6, 7, 1985), y(14, 4, 1989)),
      ("Гиви Гумбаридзе", "Givi Gumbaridze", "გივი გუმბარიძე", y(14, 4, 1989), y(7, 12, 1990)), ("Автандил Маргиани", "Avtandil Margiani", "ავთანდილ მარგიანი", y(7, 12, 1990), y(19, 2, 1991)),
      ("Джемал Микеладзе", "Jemal Mikeladze", "ჯემალ მიქელაძე", y(20, 2, 1991), y(14, 4, 1991))]
for i, (ru, en, ka, a, b) in enumerate(FS):
    R("secretary%d" % i, a, b, "secretary", E(ru, en, ka), E("Страница-список помечена как не прошедшая проверку; в инфобоксе Грузинской ССР конец списка указан иначе (Гумбаридзе 1989-1990 как последний).", "The list page carries a verification warning; the infobox of the Georgian SSR ends the list differently (Gumbaridze 1989-1990 as the last one)."), [W + "First_Secretary_of_the_Georgian_Communist_Party"], title=N("Первый секретарь ЦК КП Грузии", "First Secretary of the Communist Party of Georgia", "საქართველოს კპ ცკ პირველი მდივანი"), lane=1)

# heads of state since 1990 (the tables of "President of Georgia")
PR = [("gamsakhurdia0", y(14, 11, 1990), y(14, 4, 1991), "Звиад Гамсахурдиа", "Zviad Gamsakhurdia", "ზვიად გამსახურდია", "Председатель Верховного совета (14.11.1990-14.04.1991).", N("Председатель Верховного совета", "Chairman of the Supreme Council", "უზენაესი საბჭოს თავმჯდომარე")),
      ("gamsakhurdia", y(14, 4, 1991), y(6, 1, 1992), "Звиад Гамсахурдиа", "Zviad Gamsakhurdia", "ზვიად გამსახურდია", "Президент; свергнут 6.01.1992.", None),
      ("council", y(6, 1, 1992), y(10, 3, 1992), "Военный совет (Иоселиани, Китовани)", "The Military Council (Ioseliani, Kitovani)", "სამხედრო საბჭო (იოსელიანი, კიტოვანი)", "6.01.1992-10.03.1992 (по таблице).", N("Руководство Военного совета", "Leaders of the Military Council", "სამხედრო საბჭოს ხელმძღვანელები")),
      ("shevardnadze1", y(10, 3, 1992), y(26, 11, 1995), "Эдуард Шеварднадзе", "Eduard Shevardnadze", "ედუარდ შევარდნაძე", "Председатель Госсовета (10.03-4.11.1992), председатель парламента и «глава государства» (6.11.1992-26.11.1995).", N("Глава государства (переходный период)", "Head of state (transition)", "სახელმწიფოს მეთაური")),
      ("shevardnadze2", y(26, 11, 1995), y(23, 11, 2003), "Эдуард Шеварднадзе", "Eduard Shevardnadze", "ედუარდ შევარდნაძე", "Президент; избран 5.11.1995 (вступил 26.11.1995), переизбран 9.04.2000; ушёл в отставку 23.11.2003 (Революция роз).", None),
      ("burjanadze1", y(23, 11, 2003), y(25, 1, 2004), "Нино Бурджанадзе", "Nino Burjanadze", "ნინო ბურჯანაძე", "Исполняющая обязанности президента.", N("И. о. президента", "Acting president", "პრეზიდენტის მოვალეობის შემსრულებელი")),
      ("saakashvili1", y(25, 1, 2004), y(25, 11, 2007), "Михаил Саакашвили", "Mikheil Saakashvili", "მიხეილ სააკაშვილი", "Избран 4.01.2004; ушёл в отставку 25.11.2007.", None),
      ("burjanadze2", y(25, 11, 2007), y(20, 1, 2008), "Нино Бурджанадзе", "Nino Burjanadze", "ნინო ბურჯანაძე", "Исполняющая обязанности президента.", N("И. о. президента", "Acting president", "პრეზიდენტის მოვალეობის შემსრულებელი")),
      ("saakashvili2", y(20, 1, 2008), y(17, 11, 2013), "Михаил Саакашвили", "Mikheil Saakashvili", "მიხეილ სააკაშვილი", "Переизбран 5.01.2008.", None),
      ("margvelashvili", y(17, 11, 2013), y(16, 12, 2018), "Георгий Маргвелашвили", "Giorgi Margvelashvili", "გიორგი მარგველაშვილი", "", None),
      ("zourabichvili", y(16, 12, 2018), y(29, 12, 2024), "Саломе Зурабишвили", "Salome Zourabichvili", "სალომე ზურაბიშვილი", "Дата начала: в тексте страницы «ноябрь 2018», в таблице 16.12.2018. Статус после 2024 оспаривается.", None),
      ("kavelashvili", y(29, 12, 2024), 2026.9, "Михаил Кавелашвили", "Mikheil Kavelashvili", "მიხეილ ყაველაშვილი", "Избран 14.12.2024, вступил 29.12.2024; статус оспаривается (часть сторон считает президентом З. Зурабишвили).", None)]
for rid, a, b, ru, en, ka, nt, ttl in PR:
    R(rid, a, b, "president", E(ru, en, ka), E(nt, NOTES_EN.get(rid, nt)), [W + "President_of_Georgia"], title=ttl, lane=0)

DATA = {"note": "Built by tools/build_rulers.py on 2026-11-19; every entry cites the English Wikipedia page(s) it was taken from. Only those who ruled Tbilisi are listed.",
        "groups": GROUPS, "states": STATES, "rulers": RULERS}


def main():
    p = os.path.join(ROOT, "site", "data", "rulers.json")
    data = json.dumps(DATA, ensure_ascii=False, indent=0).encode("utf-8")
    open(p, "wb").write(data)
    print("states:", len(STATES), "rulers:", len(RULERS), "bytes:", len(data))


if __name__ == "__main__":
    main()
