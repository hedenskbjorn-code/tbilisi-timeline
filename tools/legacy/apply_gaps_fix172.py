"""Corrections of the events found by the fact check of the live site (2026-11-21), version 1.7.2.

Every change rests on a Wikipedia page whose text was read (quotes checked): 523 (en.wikipedia 'Sasanian Iberia': no Kartvelo-Sasanian coins before 579, the
monarchy suppressed c. 580), 1045 and a new event of about 1080 (ru.wikipedia 'History of Tbilisi', en.wikipedia 'Emirate of Tbilisi'), 1259, 1490 (en.wikipedia
'Kingdom of Georgia': a royal council, not a peace treaty), notes of the funicular (ru.wikipedia) and of the cable car crash 1990 (en and ru differ: 19 / 20 dead).
Georgian texts: translated and checked by Gemini. The rulers (Heraclius I, 1688-1703) are in tools/build_rulers.py, not here.

The script is idempotent: run twice, the second run changes nothing.
Usage: python -X utf8 -P tools/apply_gaps_fix172.py [--dry-run]
"""
import bisect
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DRY = "--dry-run" in sys.argv
DATA = json.loads(r'''{
 "texts": {
  "E523": {
   "ru": "Иран запрещает иметь в Иберии-Картли суверенного правителя",
   "en": "Iran forbids a sovereign ruler in Iberia-Kartli",
   "ka": "ირანი იბერია-ქართლში სუვერენული მმართველის ყოლას კრძალავს"
  },
  "N523": {
   "ru": "Сверено по книге: «Картлис Цховреба», рус. пер. (Тбилиси, 2008), комм. 5 (с. 130): в 523 г. персы запретили иметь суверенного правителя в Иберии-Картли (со ссылкой на «Очерки истории Грузии», т. II, с. 247); в 532 г. Грузия была разделена между Ираном и Византией. По статье en.wikipedia «Sasanian Iberia» иберийская монархия упразднена сасанидами около 580 г. (датировка Туманова), а грузино-сасанидские монеты с грузинскими буквами известны только после 579 г.",
   "en": "Checked against the book: Kartlis Tskhovreba, Russian translation (Tbilisi, 2008), comm. 5 (p. 130): in 523 the Persians forbade a sovereign ruler in Iberia-Kartli (with a reference to 'Essays on the History of Georgia', vol. II, p. 247); in 532 Georgia was divided between Iran and Byzantium. According to the en.wikipedia article 'Sasanian Iberia' the Iberian monarchy was suppressed by the Sasanids about 580 (Toumanoff's dating), and Kartvelo-Sasanian coins with Georgian letters are known only after 579.",
   "ka": "შედარებულია წიგნთან: „ქართლის ცხოვრება“, რუსული თარგმანი (თბილისი, 2008), კომ. 5 (გვ. 130): 523 წ. სპარსელებმა იბერია-ქართლში სუვერენული მმართველის ყოლა აკრძალეს (მითითებით „საქართველოს ისტორიის ნარკვევებზე“, ტ. II, გვ. 247); 532 წ. საქართველო ირანსა და ბიზანტიას შორის გაიყო. en.wikipedia-ს სტატიის „Sasanian Iberia“ მიხედვით, იბერიის მონარქია სასანიანებმა დაახლოებით 580 წ. გააუქმეს (თუმანოვის დათარიღება), ხოლო ქართული ასოებიანი ქართულ-სასანური მონეტები მხოლოდ 579 წ. შემდეგ არის ცნობილი."
  },
  "E1045": {
   "ru": "Умирает тбилисский эмир Джафар; тбилисские старейшины («бэры») зовут к себе царя Баграта и обещают ему город",
   "en": "The emir of Tbilisi, Jafar, dies; the elders of Tbilisi (the 'beri') call King Bagrat to them and promise him the city",
   "ka": "კვდება თბილისის ამირა ჯაფარი; თბილისელი ბერები (ქალაქის უხუცესები) მეფე ბაგრატს იწვევენ და ქალაქს ჰპირდებიან"
  },
  "E1080": {
   "ru": "После 1080 г. упоминания о тбилисском эмире исчезают: по Ибн аль-Азраку власть переходит «в руки самого народа», по грузинским источникам городом правит совет старейшин; номинально эмират сохраняется до 1122 г.",
   "en": "After 1080 the emir of Tbilisi is no longer mentioned: according to Ibn al-Azraq the power passes 'into the hands of the people themselves', according to Georgian sources the city is ruled by a council of elders; the emirate remains nominally until 1122",
   "ka": "1080 წ. შემდეგ თბილისის ამირას ხსენება ქრება: იბნ ალ-აზრაყის მიხედვით, ძალაუფლება „თავად ხალხის ხელში“ გადადის, ქართული წყაროების მიხედვით კი ქალაქს უხუცესთა საბჭო მართავს; ნომინალურად საამირო 1122 წლამდე რჩება"
  },
  "E1080_note": {
   "ru": "По статье ru.wikipedia «История Тбилиси» и статье en.wikipedia «Emirate of Tbilisi» (эмиры правили с 736 до 1080, номинально до 1122); первоисточники не проверялись.",
   "en": "From the ru.wikipedia article on the history of Tbilisi and the en.wikipedia article 'Emirate of Tbilisi' (the emirs ruled from 736 to 1080, nominally to 1122); the primary sources were not checked.",
   "ka": "ru.wikipedia-ს სტატიის მიხედვით თბილისის ისტორიის შესახებ და en.wikipedia-ს სტატიის „Emirate of Tbilisi“ მიხედვით (ამირები მართავდნენ 736-დან 1080 წლამდე, ნომინალურად 1122 წლამდე); პირველწყაროები არ შემოწმებულა."
  },
  "E1259": {
   "ru": "Давид VI Нарин, соправитель Давида VII Улу, отделяется и до 1293 г. правит царством Западной Грузии; Давид VII остаётся царём уменьшенного Грузинского царства на востоке.",
   "en": "David VI Narin, co-king with David VII Ulu, secedes and rules the Kingdom of Western Georgia until 1293; David VII remains king of the reduced Kingdom of Georgia in the east.",
   "ka": "დავით VI ნარინი, დავით VII ულუს თანამეფე, გამოეყოფა და 1293 წლამდე დასავლეთ საქართველოს სამეფოს მართავს; დავით VII აღმოსავლეთში შემცირებული საქართველოს სამეფოს მეფედ რჩება."
  },
  "E1490": {
   "ru": "Царский совет при Константине II признаёт раздел Грузии на три царства (Картли, Кахети, Имерети) и самостоятельные княжества, в том числе Самцхе",
   "en": "The royal council under Constantine II recognizes the division of Georgia into three kingdoms (Kartli, Kakheti, Imereti) and independent principalities, including Samtskhe",
   "ka": "კონსტანტინე II-ის დროს სამეფო საბჭო აღიარებს საქართველოს დაყოფას სამ სამეფოდ (ქართლი, კახეთი, იმერეთი) და დამოუკიდებელ სამთავროებად, მათ შორის სამცხედ"
  },
  "N1490": {
   "ru": "По статье en.wikipedia «Kingdom of Georgia»: царский совет, созванный Константином II, признал существующее деление. Статья ru.wikipedia «История Грузии» называет это мирным договором.",
   "en": "From the en.wikipedia article 'Kingdom of Georgia': the royal council convened by Constantine II recognized the existing division. The ru.wikipedia article on the history of Georgia calls it a peace treaty.",
   "ka": "en.wikipedia-ს სტატიის „Kingdom of Georgia“ მიხედვით: კონსტანტინე II-ის მიერ მოწვეულმა სამეფო საბჭომ არსებული დაყოფა აღიარა. ru.wikipedia-ს სტატია საქართველოს ისტორიის შესახებ ამას სამშვიდობო ხელშეკრულებას უწოდებს."
  },
  "N1938": {
   "ru": "По статье ru.wikipedia «Тбилисский фуникулёр»: в 1938 г. на месте прежней верхней станции построена новая; сам фуникулёр действует с 1905 г.",
   "en": "From the ru.wikipedia article on the Tbilisi funicular: in 1938 a new upper station was built in place of the old one; the funicular itself has run since 1905.",
   "ka": "ru.wikipedia-ს სტატიის მიხედვით თბილისის ფუნიკულიორის შესახებ: 1938 წ. ძველი ზედა სადგურის ადგილას ახალი აშენდა; თავად ფუნიკულიორი 1905 წლიდან მოქმედებს."
  },
  "N2012": {
   "ru": "По статье ru.wikipedia «Тбилисский фуникулёр»: в октябре 2012 г. после модернизации введён в эксплуатацию, официально вновь открыт 30 января 2013 г.",
   "en": "From the ru.wikipedia article on the Tbilisi funicular: put into service in October 2012 after modernisation, officially reopened on 30 January 2013.",
   "ka": "ru.wikipedia-ს სტატიის მიხედვით თბილისის ფუნიკულიორის შესახებ: 2012 წ. ოქტომბერში მოდერნიზაციის შემდეგ ექსპლუატაციაში შევიდა, ოფიციალურად ხელახლა გაიხსნა 2013 წ. 30 იანვარს."
  },
  "N1990": {
   "ru": "Статья en.wikipedia «Tbilisi cable car crash» называет 19 погибших и не менее 42 раненых; статья ru.wikipedia «Катастрофа на канатной дороге в Тбилиси» — 20 погибших и не менее 15 тяжело раненых.",
   "en": "The en.wikipedia article 'Tbilisi cable car crash' gives 19 dead and at least 42 injured; the ru.wikipedia article on the crash gives 20 dead and at least 15 seriously injured.",
   "ka": "en.wikipedia-ს სტატია „Tbilisi cable car crash“ ასახელებს 19 დაღუპულს და არანაკლებ 42 დაშავებულს; ru.wikipedia-ს სტატია ამ კატასტროფის შესახებ — 20 დაღუპულს და არანაკლებ 15 მძიმედ დაშავებულს."
  }
 }
}''')
PATH = os.path.join(ROOT, "site", "data", "history_events.json")
raw = open(PATH, encoding="utf-8").read()
doc = json.loads(raw)
assert json.dumps(doc, ensure_ascii=False, indent=1) == raw, "the file layout changed, refusing to rewrite it"
events = doc["events"]
changes = []
CYR = re.compile("[А-Яа-яЁё]")
for k, v in DATA["texts"].items():
    assert not CYR.search(v["en"]) and not CYR.search(v["ka"]), "Cyrillic in the en or ka text of " + k


def find(year, start):
    e = [x for x in events if x["year"] == year and x["ru"].startswith(start)]
    assert len(e) == 1, (year, start, len(e))
    return e[0]


def trio(k):
    return DATA["texts"][k]


def set_text(e, k, label):
    t = trio(k)
    if e["ru"] != t["ru"]:
        e["ru"], e["en"], e["ka"] = t["ru"], t["en"], t["ka"]
        changes.append("text of " + label)


def set_note(e, k, label, append=False):
    t = trio(k)
    note = e.setdefault("note", {"ru": "", "en": "", "ka": ""})
    for l in ("ru", "en", "ka"):
        cur = note.get(l, "")
        if t[l] in cur:
            continue
        note[l] = (cur + " " + t[l]).strip() if append else t[l]
        changes.append("note %s of %s" % (l, label))


e = find(523, "Иран ")
set_text(e, "E523", "523")
set_note(e, "N523", "523")
e = find(1045, "Умирает тбилисский эмир")
set_text(e, "E1045", "1045")
e = find(1259, "Давид VI Нарин")
set_text(e, "E1259", "1259")
e = find(1490, "Царский совет") if any(x["year"] == 1490 and x["ru"].startswith("Царский совет") for x in events) else find(1490, "Мирный договор")
set_text(e, "E1490", "1490")
set_note(e, "N1490", "1490")
en_url = "https://en.wikipedia.org/wiki/Kingdom_of_Georgia"
if en_url not in [s if isinstance(s, str) else s.get("url") for s in e["src"]]:
    e["src"].append(en_url)
    changes.append("source of 1490")
set_note(find(1938, "В Тбилиси торжественно открыто сооружение фуникулёра"), "N1938", "1938", append=True)
e2012 = [x for x in events if x["year"] == 2012 and "фуникулёр" in x["ru"]]
assert len(e2012) == 1
set_note(e2012[0], "N2012", "2012")
set_note(find(1990, "Крушение двух кабин"), "N1990", "1990")
if not any(x["year"] == 1080 and x["ru"] == trio("E1080")["ru"] for x in events):
    t, n = trio("E1080"), trio("E1080_note")
    ev = {"year": 1080, "date": "1080", "cat": "power",
          "src": ["https://ru.wikipedia.org/wiki/%D0%98%D1%81%D1%82%D0%BE%D1%80%D0%B8%D1%8F_%D0%A2%D0%B1%D0%B8%D0%BB%D0%B8%D1%81%D0%B8", "https://en.wikipedia.org/wiki/Emirate_of_Tbilisi"],
          "ru": t["ru"], "en": t["en"], "ka": t["ka"], "note": {"ru": n["ru"], "en": n["en"], "ka": n["ka"]}}
    events.insert(bisect.bisect_right([x["year"] for x in events], 1080), ev)
    changes.append("new event of about 1080")
assert [x["year"] for x in events] == sorted(x["year"] for x in events)
if changes and not DRY:
    open(PATH, "w", encoding="utf-8", newline="\n").write(json.dumps(doc, ensure_ascii=False, indent=1))
print(("DRY RUN: " if DRY else "") + "%d changes" % len(changes))
for c in changes:
    print("  ", c)
