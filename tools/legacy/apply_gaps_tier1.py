"""Apply tier 1 of the Gemini gap-filling pass (2026-11-21): only what was checked against a source that could be opened.

 * five events get a note "checked against Kartlis Tskhovreba (Russian translation, 2008), page N" (pages verified in the PDF);
 * eleven new events from English Wikipedia articles whose text was read (a year in a table is not enough: the claim itself was read);
 * twelve dates of register objects taken from the Wikipedia page of the object (data/monument_date_overrides.json and site/data/monuments.json);
 * the founding year of eleven institutions goes into the note of the register object ('from' stays the year of the building, except the Apollo cinema:
   the register gave a quarter-century ending 1825, the page gives 1909).
Georgian texts were translated by Gemini and checked by the owner's rule (new ka phrases go through Gemini).

The script is idempotent: a text that is already there is not added again; run it twice and the second run changes nothing.
After it run: python -X utf8 -P tools/build_science.py ; python -X utf8 -P tools/build_education.py
Usage: python -X utf8 -P tools/apply_gaps_tier1.py [--dry-run]
"""
import bisect
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DRY = "--dry-run" in sys.argv
DATA = json.loads(r'''{
 "events_notes": [
  {
   "year": 523,
   "start": "Иран упраздняет",
   "mode": "append",
   "ru": "Сверено по книге: «Картлис Цховреба», рус. пер. (Тбилиси, 2008), комм. 5 (с. 130): в 523 г. персы запретили иметь суверенного правителя в Иберии-Картли (со ссылкой на «Очерки истории Грузии», т. II, с. 247); в 532 г. Грузия была разделена между Ираном и Византией. Марзпан и чеканка монеты на этой странице не названы.",
   "en": "Checked against the book: Kartlis Tskhovreba, Russian translation (Tbilisi, 2008), comm. 5 (p. 130): in 523 the Persians forbade a sovereign ruler in Iberia-Kartli (with a reference to 'Essays on the History of Georgia', vol. II, p. 247); in 532 Georgia was divided between Iran and Byzantium. The marzban and the coinage are not named on this page.",
   "ka": "შედარებულია წიგნთან: „ქართლის ცხოვრება“, რუს. თარგმანი (თბილისი, 2008), კომ. 5 (გვ. 130): 523 წ. სპარსელებმა იბერია-ქართლში სუვერენული მმართველის ყოლა აკრძალეს (მითითებით „საქართველოს ისტორიის ნარკვევებზე“, ტ. II, გვ. 247); 532 წ. საქართველო ირანსა და ბიზანტიას შორის გაიყო. მარზპანი და მონეტის მოჭრა ამ გვერდზე დასახელებული არ არის."
  },
  {
   "year": 1045,
   "start": "Умирает тбилисский эмир",
   "mode": "append",
   "ru": "Сверено по книге: «Картлис Цховреба», рус. пер. (Тбилиси, 2008), с. 155: когда царь Баграт осаждал Анакопию, к нему прибыли тбилисские бэры, «т. к. перед тем скончался тбилисский эмир Джафар», и обещали ему город. Год в этом фрагменте не назван.",
   "en": "Checked against the book: Kartlis Tskhovreba, Russian translation (Tbilisi, 2008), p. 155: while King Bagrat was besieging Anakopia, the beri of Tbilisi came to him, 'because the emir of Tbilisi, Jafar, had died before that', and promised him the city. The year is not named in this passage.",
   "ka": "შედარებულია წიგნთან: „ქართლის ცხოვრება“, რუს. თარგმანი (თბილისი, 2008), გვ. 155: როდესაც მეფე ბაგრატი ანაკოფიას უტევდა, მასთან თბილისელი ბერები (ქალაქის უხუცესები) მივიდნენ, „რადგან მანამდე გარდაიცვალა თბილისის ამირა ჯაფარი“, და ქალაქი აღუთქვეს. წელი ამ ფრაგმენტში დასახელებული არ არის."
  },
  {
   "year": 1046,
   "start": "Весной царь Баграт",
   "mode": "append",
   "ru": "Сверено по книге: «Картлис Цховреба», рус. пер. (Тбилиси, 2008), с. 155: царь пришёл в Тбилиси; городские бэры и дворцовые слуги вышли навстречу верхом на Дигомское поле, народ пешком; царя ввели в город. Год в этом фрагменте не назван.",
   "en": "Checked against the book: Kartlis Tskhovreba, Russian translation (Tbilisi, 2008), p. 155: the king came to Tbilisi; the city beri and the palace servants rode out to meet him on the Digomi field, the people on foot; the king was led into the city. The year is not named in this passage.",
   "ka": "შედარებულია წიგნთან: „ქართლის ცხოვრება“, რუს. თარგმანი (თბილისი, 2008), გვ. 155: მეფე თბილისში მივიდა; ქალაქის ბერები (უხუცესები) და სასახლის მსახურები ცხენებით შეეგებნენ დიღმის ველზე, ხალხი — ქვეითად; მეფე ქალაქში შეიყვანეს. წელი ამ ფრაგმენტში დასახელებული არ არის."
  },
  {
   "year": 1121,
   "start": "Битва при Дидгори",
   "mode": "append",
   "ru": "Сверено по книге: «Картлис Цховреба», рус. пер. (Тбилиси, 2008), с. 192–193: двенадцатого августа войска противников собрались в Триалети, Манглиси и Дидгори, царь Давид «в первой же битве» рассеял их стан; «в следующем же году» он взял Тбилиси, «четыреста лет бывший во владении персов» (с. 193). Год в этом фрагменте не назван.",
   "en": "Checked against the book: Kartlis Tskhovreba, Russian translation (Tbilisi, 2008), pp. 192-193: on the twelfth of August the enemy armies gathered in Trialeti, Manglisi and Didgori, King David 'in the very first battle' scattered their camp; 'in the very next year' he took Tbilisi, 'for four hundred years in the possession of the Persians' (p. 193). The year is not named in this passage.",
   "ka": "შედარებულია წიგნთან: „ქართლის ცხოვრება“, რუს. თარგმანი (თბილისი, 2008), გვ. 192–193: თორმეტ აგვისტოს მოწინააღმდეგეთა ჯარები თრიალეთში, მანგლისსა და დიდგორში შეიკრიბნენ, მეფე დავითმა „პირველსავე ბრძოლაში“ დაფანტა მათი ბანაკი; „მომდევნო წელსვე“ მან აიღო თბილისი, „ოთხას წელს სპარსელთა მფლობელობაში მყოფი“ (გვ. 193). წელი ამ ფრაგმენტში დასახელებული არ არის."
  },
  {
   "year": 1195,
   "start": "Битва при Шамкори",
   "mode": "replace_tail",
   "ru": "Сверено по книге: «Картлис Цховреба», рус. пер. (Тбилиси, 2008), с. 272–273: войска Давида вступили в область Шамхорскую 1 июня, «с четверга на пятницу»; жители Шамхора вынесли ключи от города. Год в этом фрагменте не назван.",
   "en": "Checked against the book: Kartlis Tskhovreba, Russian translation (Tbilisi, 2008), pp. 272-273: David's army entered the region of Shamkhor on 1 June, 'from Thursday to Friday'; the people of Shamkhor brought the keys of the city. The year is not named in this passage.",
   "ka": "შედარებულია წიგნთან: „ქართლის ცხოვრება“, რუს. თარგმანი (თბილისი, 2008), გვ. 272–273: დავითის ჯარები შამქორის მხარეში 1 ივნისს შევიდნენ, „ხუთშაბათიდან პარასკევზე“; შამქორის მცხოვრებლებმა ქალაქის გასაღებები გამოიტანეს. წელი ამ ფრაგმენტში დასახელებული არ არის."
  }
 ],
 "events_new": [
  {
   "year": 914,
   "date": "914",
   "cat": "invasion",
   "src": [
    "https://en.wikipedia.org/wiki/Sajid_invasion_of_Georgia"
   ],
   "ru": "Саджидский эмир Юсуф ибн Абу-с-Садж вторгается в грузинские земли: сначала доходит до Тбилиси, затем поворачивает на Кахети.",
   "en": "The Sajid emir Yusuf ibn Abi'l-Saj invades Georgian lands: he first reaches Tbilisi, then turns towards Kakheti.",
   "ka": "საჯიდების ამირა იუსუფ იბნ აბუ-ს-საჯი ქართულ მიწებზე იჭრება: ჯერ თბილისამდე აღწევს, შემდეგ კახეთისკენ უხვევს.",
   "note": {
    "ru": "По статье en.wikipedia «Sajid invasion of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Sajid invasion of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Sajid invasion of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1259,
   "date": "1259",
   "cat": "power",
   "src": [
    "https://en.wikipedia.org/wiki/David_VI_of_Georgia"
   ],
   "ru": "Давид VI Нарин, соправитель Давида VII Улу (с 1246), отделяется и до 1293 г. правит царством Западной Грузии; Давид VII остаётся царём уменьшенного Грузинского царства на востоке.",
   "en": "David VI Narin, co-king with David VII Ulu (from 1246), secedes and rules the Kingdom of Western Georgia until 1293; David VII remains king of the reduced Kingdom of Georgia in the east.",
   "ka": "დავით VI ნარინი, დავით VII ულუს თანამმართველი (1246 წლიდან), გამოეყოფა და 1293 წლამდე დასავლეთ საქართველოს სამეფოს მართავს; დავით VII აღმოსავლეთში შემცირებული საქართველოს სამეფოს მეფედ რჩება.",
   "note": {
    "ru": "По статье en.wikipedia «David VI of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'David VI of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „David VI of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1270,
   "date": "1270",
   "cat": "power",
   "src": [
    "https://en.wikipedia.org/wiki/Demetrius_II_of_Georgia"
   ],
   "ru": "Деметре II (род. 1259, сын Давида VII) становится царём Восточной Грузии (1270–1289) под властью монголов.",
   "en": "Demetre II (born 1259, son of David VII) becomes king of Eastern Georgia (1270-1289) under Mongol rule.",
   "ka": "დემეტრე II (დაბ. 1259, დავით VII-ის ძე) მონღოლთა ბატონობის ქვეშ აღმოსავლეთ საქართველოს მეფე ხდება (1270–1289).",
   "note": {
    "ru": "По статье en.wikipedia «Demetrius II of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Demetrius II of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Demetrius II of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1289,
   "date": "12.03.1289",
   "cat": "power",
   "src": [
    "https://en.wikipedia.org/wiki/Demetrius_II_of_Georgia"
   ],
   "ru": "Царь Деметре II казнён монгольскими ильханами.",
   "en": "King Demetre II is executed by the Mongol Ilkhans.",
   "ka": "მეფე დემეტრე II მონღოლი ილხანების მიერ სიკვდილით დაისაჯა.",
   "note": {
    "ru": "По статье en.wikipedia «Demetrius II of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Demetrius II of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Demetrius II of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1293,
   "date": "1293",
   "cat": "power",
   "src": [
    "https://en.wikipedia.org/wiki/David_VIII_of_Georgia"
   ],
   "ru": "Ильхан Гайхату назначает Давида VIII царём Грузии за военную службу во время восстания в Руме (Малая Азия); его власть распространяется только на восточную часть царства.",
   "en": "The Ilkhan Gaykhatu appoints David VIII king of Georgia as a reward for his military service during the uprising in Rum (Asia Minor); his rule extends only over the eastern part of the kingdom.",
   "ka": "ილხანი ქეღათუ დავით VIII-ს საქართველოს მეფედ ნიშნავს რუმში (მცირე აზია) აჯანყების დროს გაწეული სამხედრო სამსახურისთვის; მისი ძალაუფლება მხოლოდ სამეფოს აღმოსავლეთ ნაწილზე ვრცელდება.",
   "note": {
    "ru": "По статье en.wikipedia «David VIII of Georgia»; первоисточники не проверялись. Дата по en.wikipedia (1293); по ka.wikipedia («დავით VIII») Давид участвовал в походе Гайхату-хана против восстания в Руме (Малая Азия) в 1291 (1292) и после этого был утверждён царём.",
    "en": "From the en.wikipedia article 'David VIII of Georgia'; the primary sources were not checked. The date is from en.wikipedia (1293); according to ka.wikipedia ('დავით VIII') David took part in Gaykhatu's campaign against the uprising in Rum (Asia Minor) in 1291 (1292) and was confirmed king after it.",
    "ka": "en.wikipedia-ს სტატიის „David VIII of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა. თარიღი en.wikipedia-ს მიხედვით (1293); ka.wikipedia-ს („დავით VIII“) მიხედვით, დავითი მონაწილეობდა ქეღათუ-ხანის ლაშქრობაში რუმში (მცირე აზია) აჯანყების წინააღმდეგ 1291 (1292) წელს და ამის შემდეგ მეფედ დამტკიცდა."
   }
  },
  {
   "year": 1387,
   "date": "1387",
   "cat": "invasion",
   "src": [
    "https://en.wikipedia.org/wiki/Timur%27s_invasions_of_Georgia"
   ],
   "ru": "Весной 1387 г. начинается новый поход Тимура на Грузию (после разорения Тбилиси в 1386 г.).",
   "en": "In spring 1387 a new campaign of Timur against Georgia begins (after the sack of Tbilisi in 1386).",
   "ka": "1387 წლის გაზაფხულზე თემურლენგის ახალი ლაშქრობა იწყება საქართველოზე (1386 წელს თბილისის აოხრების შემდეგ).",
   "note": {
    "ru": "По статье en.wikipedia «Timur's invasions of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Timur's invasions of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Timur's invasions of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1403,
   "date": "1403",
   "cat": "invasion",
   "src": [
    "https://en.wikipedia.org/wiki/Timur%27s_invasions_of_Georgia"
   ],
   "ru": "Тимур берёт крепость Биртвиси (август 1403) и посылает войска разорять пограничные области Грузии; по его историку, разрушено 700 городов.",
   "en": "Timur captures the fortress of Birtvisi (August 1403) and sends his army to plunder the frontier regions of Georgia; his historian reports 700 towns destroyed.",
   "ka": "თემურლენგი იღებს ბირთვისის ციხეს (1403 წლის აგვისტო) და ჯარებს საქართველოს სასაზღვრო მხარეების ასაოხრებლად გზავნის; მისი ისტორიკოსის ცნობით, განადგურებულია 700 ქალაქი.",
   "note": {
    "ru": "По статье en.wikipedia «Timur's invasions of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Timur's invasions of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Timur's invasions of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1412,
   "date": "1412",
   "cat": "power",
   "src": [
    "https://en.wikipedia.org/wiki/Alexander_I_of_Georgia"
   ],
   "ru": "Александр I Великий становится царём Грузии (1412–1442); его правление отмечено масштабным восстановлением и строительством.",
   "en": "Alexander I the Great becomes king of Georgia (1412-1442); his reign is marked by extensive reconstruction and building projects.",
   "ka": "ალექსანდრე I დიდი საქართველოს მეფე ხდება (1412–1442); მისი მეფობა მასშტაბური აღდგენითა და მშენებლობით აღინიშნა.",
   "note": {
    "ru": "По статье en.wikipedia «Alexander I of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Alexander I of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Alexander I of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1466,
   "date": "1466",
   "cat": "power",
   "src": [
    "https://en.wikipedia.org/wiki/Kingdom_of_Georgia"
   ],
   "ru": "Баграт входит в Тбилиси и провозглашает себя царём Грузии (Баграт VI): в 1465 г. Георгий VIII взят в плен атабагом Самцхе Кваркваре II Джакели.",
   "en": "Bagrat enters Tbilisi and proclaims himself King of Georgia (Bagrat VI): in 1465 George VIII was captured by Qvarqvare II Jaqeli, the atabeg of Samtskhe.",
   "ka": "ბაგრატი თბილისში შედის და საქართველოს მეფედ (ბაგრატ VI) აცხადებს თავს: 1465 წელს გიორგი VIII სამცხის ათაბაგმა ყვარყვარე II ჯაყელმა ტყვედ ჩაიგდო.",
   "note": {
    "ru": "По статье en.wikipedia «Kingdom of Georgia»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Kingdom of Georgia'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Kingdom of Georgia“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1688,
   "date": "1688",
   "cat": "power",
   "src": [
    "https://en.wikipedia.org/wiki/Heraclius_I_of_Kakheti"
   ],
   "ru": "Ираклий I (Назар-Али-хан) становится царём Картли (1688–1703) под покровительством сефевидского Ирана.",
   "en": "Heraclius I (Nazar-Ali-Khan) becomes king of Kartli (1688-1703) under the protection of Safavid Iran.",
   "ka": "ერეკლე I (ნაზარ-ალი-ხანი) სეფიანთა ირანის მფარველობით ქართლის მეფე ხდება (1688–1703).",
   "note": {
    "ru": "По статье en.wikipedia «Heraclius I of Kakheti»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Heraclius I of Kakheti'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Heraclius I of Kakheti“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  },
  {
   "year": 1952,
   "date": "1952",
   "cat": "build",
   "src": [
    "https://en.wikipedia.org/wiki/Tbilisi_Metro"
   ],
   "ru": "Начато строительство Тбилисского метрополитена.",
   "en": "Construction of the Tbilisi Metro begins.",
   "ka": "დაიწყო თბილისის მეტროპოლიტენის მშენებლობა.",
   "note": {
    "ru": "По статье en.wikipedia «Tbilisi Metro»; первоисточники не проверялись.",
    "en": "From the en.wikipedia article 'Tbilisi Metro'; the primary sources were not checked.",
    "ka": "en.wikipedia-ს სტატიის „Tbilisi Metro“ მიხედვით; პირველწყაროები არ შემოწმებულა."
   }
  }
 ],
 "overrides": {
  "3863": {
   "year_from": 1818,
   "year_to": 1818,
   "year_est": 1818,
   "date_precision": "exact",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia: the Artsruni caravanserai was built in 1818 (or 1820); the register value 2000 contradicts the page (https://ka.wikipedia.org/wiki/არწრუნის_ქარვასლა)"
  },
  "6659": {
   "year_from": 1184,
   "year_to": 1213,
   "year_est": 1196,
   "date_precision": "era",
   "date_source": "ru.wikipedia.org",
   "why": "ru.wikipedia: Betania monastery, the church of St George built in 1196 under Tamar (the register gave the whole century) (https://ru.wikipedia.org/wiki/Грузинская_Бетания)"
  },
  "17904": {
   "year_from": 1184,
   "year_to": 1213,
   "year_est": 1196,
   "date_precision": "era",
   "date_source": "ru.wikipedia.org",
   "why": "ru.wikipedia: Betania monastery, built about 1196 under Tamar (the register gave the whole century) (https://ru.wikipedia.org/wiki/Грузинская_Бетания)"
  },
  "2764": {
   "year_from": 1831,
   "year_to": 1870,
   "year_est": 1850,
   "date_precision": "middle",
   "date_source": "ka.wikipedia.org",
   "why": "orthodoxy.ge and ka.wikipedia: built in the middle of the 19th century, renewed in 1991 (the register value was the 16th century) (https://ka.wikipedia.org/wiki/ჩუღურეთის_წმინდა_ნინოს_ეკლესია)"
  },
  "3303": {
   "year_from": 1909,
   "year_to": 1909,
   "year_est": 1909,
   "date_precision": "exact",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia: the Apollo cinema was opened in 1909 (the register gave a quarter-century ending 1825) (https://ka.wikipedia.org/wiki/აპოლო_(თბილისი))"
  },
  "3362": {
   "year_from": 1806,
   "year_to": 1808,
   "year_est": 1808,
   "date_precision": "decade",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia: Echmiadzin church built in 1806-1808, enlarged in 1846 (https://ka.wikipedia.org/wiki/ეჩმიაძინი_(თბილისი))"
  },
  "3364": {
   "year_from": 1278,
   "year_to": 1289,
   "year_est": 1289,
   "date_precision": "decade",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia: Metekhi church built in 1278-1289 under Demetre II (https://ka.wikipedia.org/wiki/მეტეხის_ღვთისმშობლის_შობის_ტაძარი)"
  },
  "3433": {
   "year_from": 501,
   "year_to": 700,
   "year_est": 700,
   "date_precision": "mixed",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia: Sioni cathedral founded in the 6th-7th century, rebuilt in the 12th-13th and 18th centuries (the register value was the 4th century) (https://ka.wikipedia.org/wiki/სიონის_ტაძარი)"
  },
  "3539": {
   "year_from": 1710,
   "year_to": 1710,
   "year_est": 1710,
   "date_precision": "exact",
   "date_source": "ru.wikipedia.org",
   "why": "ru.wikipedia: Kari church built in 1710 on an older foundation (https://ru.wikipedia.org/wiki/Церковь_Святого_Георгия_Кари)"
  },
  "3787": {
   "year_from": 1675,
   "year_to": 1675,
   "year_est": 1675,
   "date_precision": "exact",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia: the bell tower of Anchiskhati was built in 1675 under Catholicos Domenti (https://ka.wikipedia.org/wiki/ანჩისხატი)"
  },
  "4167": {
   "year_from": 1859,
   "year_to": 1859,
   "year_est": 1859,
   "date_precision": "exact",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia: Caucasian House built in 1859 (architect O. Simonson) (https://ka.wikipedia.org/wiki/კავკასიური_სახლი)"
  },
  "16057": {
   "year_from": 1903,
   "year_to": 1906,
   "year_est": 1906,
   "date_precision": "decade",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia / georgianencyclopedia: the old printing house of Avlabari built in 1903-1906 (https://ka.wikipedia.org/wiki/ავლაბრის_სტამბა)"
  }
 },
 "register": [
  {
   "id": "reg3469",
   "layer": "science",
   "ru": "По статье ka.wikipedia «თბილისის მარიონეტების თეატრი»: театр основан в 1981 г.",
   "en": "From the ka.wikipedia article 'თბილისის მარიონეტების თეატრი': the theatre was founded in 1981.",
   "ka": "ka.wikipedia-ს სტატიის „თბილისის მარიონეტების თეატრი“ მიხედვით: თეატრი 1981 წელს დაარსდა."
  },
  {
   "id": "reg3550",
   "layer": "science",
   "ru": "По статье ka.wikipedia «ნიკოლოზ ბარათაშვილის სახლ-მუზეუმი»: дом-музей открыт в 1982 г.",
   "en": "From the ka.wikipedia article 'ნიკოლოზ ბარათაშვილის სახლ-მუზეუმი': the house-museum was opened in 1982.",
   "ka": "ka.wikipedia-ს სტატიის „ნიკოლოზ ბარათაშვილის სახლ-მუზეუმი“ მიხედვით: სახლ-მუზეუმი 1982 წელს გაიხსნა."
  },
  {
   "id": "reg3968",
   "layer": "science",
   "ru": "По статье ka.wikipedia «სამეფო უბნის თეატრი»: театр открыт 18 июня 1997 г.",
   "en": "From the ka.wikipedia article 'სამეფო უბნის თეატრი': the theatre was opened on 18 June 1997.",
   "ka": "ka.wikipedia-ს სტატიის „სამეფო უბნის თეატრი“ მიხედვით: თეატრი 1997 წლის 18 ივნისს გაიხსნა."
  },
  {
   "id": "reg4075",
   "layer": "science",
   "ru": "По статье en.wikipedia «Tbilisi State University»: университет основан в 1918 г.",
   "en": "From the en.wikipedia article 'Tbilisi State University': the university was founded in 1918.",
   "ka": "en.wikipedia-ს სტატიის „Tbilisi State University“ მიხედვით: უნივერსიტეტი 1918 წელს დაარსდა."
  },
  {
   "id": "reg4171",
   "layer": "education",
   "ru": "По статье en.wikipedia «Tbilisi State Conservatoire»: консерватория основана в 1917 г.",
   "en": "From the en.wikipedia article 'Tbilisi State Conservatoire': the conservatoire was founded in 1917.",
   "ka": "en.wikipedia-ს სტატიის „Tbilisi State Conservatoire“ მიხედვით: კონსერვატორია 1917 წელს დაარსდა."
  },
  {
   "id": "reg5006",
   "layer": "science",
   "ru": "По статье ka.wikipedia «აბრეშუმის სახელმწიფო მუზეუმი»: музей основан в 1887 г. (при Кавказской шелководческой станции).",
   "en": "From the ka.wikipedia article 'აბრეშუმის სახელმწიფო მუზეუმი': the museum was founded in 1887 (at the Caucasian silk-breeding station).",
   "ka": "ka.wikipedia-ს სტატიის „აბრეშუმის სახელმწიფო მუზეუმი“ მიხედვით: მუზეუმი 1887 წელს დაარსდა (კავკასიის მეაბრეშუმეობის სადგურთან)."
  },
  {
   "id": "reg17461",
   "layer": "science",
   "ru": "По статье en.wikipedia «Tbilisi Open Air Museum of Ethnography»: музей основан в 1966 г.",
   "en": "From the en.wikipedia article 'Tbilisi Open Air Museum of Ethnography': the museum was founded in 1966.",
   "ka": "en.wikipedia-ს სტატიის „Tbilisi Open Air Museum of Ethnography“ მიხედვით: მუზეუმი 1966 წელს დაარსდა."
  },
  {
   "id": "reg17603",
   "layer": "science",
   "ru": "По статье ka.wikipedia «იაკობ ნიკოლაძის სახლ-მუზეუმი»: дом-музей основан в 1951 г.",
   "en": "From the ka.wikipedia article 'იაკობ ნიკოლაძის სახლ-მუზეუმი': the house-museum was founded in 1951.",
   "ka": "ka.wikipedia-ს სტატიის „იაკობ ნიკოლაძის სახლ-მუზეუმი“ მიხედვით: სახლ-მუზეუმი 1951 წელს დაარსდა."
  },
  {
   "id": "reg17753",
   "layer": "science",
   "ru": "По статье ru.wikipedia «Тбилисский театр музыки и драмы имени Васо Абашидзе»: театр основан в 1926 г.",
   "en": "From the ru.wikipedia article on the theatre: the theatre was founded in 1926.",
   "ka": "ru.wikipedia-ს სტატიის მიხედვით: თეატრი 1926 წელს დაარსდა."
  },
  {
   "id": "reg24678",
   "layer": "science",
   "ru": "По статье ka.wikipedia «თბილისის არქეოლოგიური მუზეუმი»: музей основан в 1988 г.",
   "en": "From the ka.wikipedia article 'თბილისის არქეოლოგიური მუზეუმი': the museum was founded in 1988.",
   "ka": "ka.wikipedia-ს სტატიის „თბილისის არქეოლოგიური მუზეუმი“ მიხედვით: მუზეუმი 1988 წელს დაარსდა."
  },
  {
   "id": "reg4811",
   "layer": "education",
   "ru": "По статье ka.wikipedia «თბილისის 43-ე საჯარო სკოლა»: школа открыта 1 июля 1911 г. как 3-е мужское коммерческое училище имени Манташева.",
   "en": "From the ka.wikipedia article 'თბილისის 43-ე საჯარო სკოლა': the school was opened on 1 July 1911 as the 3rd Mantashev Commercial School for boys.",
   "ka": "ka.wikipedia-ს სტატიის „თბილისის 43-ე საჯარო სკოლა“ მიხედვით: სკოლა 1911 წლის 1 ივლისს გაიხსნა, როგორც მანთაშევის სახელობის მე-3 ვაჟთა კომერციული სასწავლებელი."
  },
  {
   "id": "reg3303",
   "layer": "science",
   "ru": "Кинотеатр открыт в 1909 г. (по статье ka.wikipedia «აპოლო (თბილისი)»); год на шкале исправлен: реестр давал четверть века, оканчивающуюся 1825 г.",
   "en": "The cinema was opened in 1909 (from the ka.wikipedia article 'აპოლო (თბილისი)'); the year on the scale is corrected: the register gave a quarter-century ending in 1825.",
   "ka": "კინოთეატრი 1909 წელს გაიხსნა (ka.wikipedia-ს სტატიის „აპოლო (თბილისი)“ მიხედვით); დროის სკალაზე წელი გასწორებულია: რეესტრი 1825 წელს დასრულებულ მეოთხედ საუკუნეს უთითებდა.",
   "from": 1909,
   "from_was": 1825
  }
 ]
}''')
changes = []


def p(*a):
    return os.path.join(ROOT, *a)


def load(path):
    return json.loads(open(path, encoding="utf-8").read())


def check_roundtrip(path, doc, **kw):
    raw = open(path, encoding="utf-8").read()
    assert json.dumps(doc, ensure_ascii=False, **kw) == raw, "the file layout changed, refusing to rewrite " + path


def save(path, doc, **kw):
    if DRY or not changes_in_file.get(path):
        return
    open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(doc, ensure_ascii=False, **kw))


changes_in_file = {}


def mark(path, msg):
    changes_in_file[path] = True
    changes.append(msg)


# ---------------------------------------------------------------- events
EV = p("site", "data", "history_events.json")
doc = load(EV)
check_roundtrip(EV, doc, indent=1)
events = doc["events"]
OLD_TAIL = {  # the sentence of the Shamkor note that the book check replaces
    "ru": " В доступных книгах не найдено, остаётся только статья en.wikipedia.",
    "en": " Not found in the available books, only the en.wikipedia article remains.",
    "ka": " ხელმისაწვდომ წიგნებში ვერ მოიძებნა, რჩება მხოლოდ en.wikipedia-ს სტატია.",
}
for n in DATA["events_notes"]:
    e = [x for x in events if x["year"] == n["year"] and x["ru"].startswith(n["start"])]
    assert len(e) == 1, (n["year"], len(e))
    e = e[0]
    note = e.setdefault("note", {"ru": "", "en": "", "ka": ""})
    for l in ("ru", "en", "ka"):
        cur = note.get(l, "")
        if n[l] in cur:
            continue
        if n["mode"] == "replace_tail" and cur.endswith(OLD_TAIL[l]):
            cur = cur[: -len(OLD_TAIL[l])]
        note[l] = (cur + " " + n[l]).strip()
        mark(EV, "note %s of the event %d" % (l, n["year"]))
for ne in DATA["events_new"]:
    if any(x["year"] == ne["year"] and x["ru"] == ne["ru"] for x in events):
        continue
    ev = {"year": ne["year"], "date": ne["date"], "cat": ne["cat"], "src": ne["src"], "ru": ne["ru"], "en": ne["en"], "ka": ne["ka"], "note": ne["note"]}
    events.insert(bisect.bisect_right([x["year"] for x in events], ne["year"]), ev)
    mark(EV, "new event %s" % ne["date"])
assert [x["year"] for x in events] == sorted(x["year"] for x in events)
save(EV, doc, indent=1)

# ---------------------------------------------------------------- dates of the register objects
OV = p("data", "monument_date_overrides.json")
raw = open(OV, encoding="utf-8").read()
ovdoc = json.loads(raw)
new_lines = []
for k, v in DATA["overrides"].items():
    if k not in ovdoc["objects"]:
        ovdoc["objects"][k] = v
        new_lines.append('  %s: %s' % (json.dumps(k), json.dumps(v, ensure_ascii=False)))
        mark(OV, "date override of the object " + k)
if new_lines and not DRY:
    head, tail = raw.rstrip("\n").rsplit("\n }}", 1)
    assert tail == "", "unexpected layout of " + OV
    note_add = " Since 2026-11-21 also the dates taken from the Wikipedia page of the object (the field why names it) where the register gave a placeholder or a coarser range."
    head = head.replace('"note": "Dates fixed by hand', '"note": "Dates fixed by hand', 1)
    i = head.index('",\n "objects"')
    if note_add not in head:
        head = head[:i] + note_add + head[i:]
    open(OV, "w", encoding="utf-8", newline="\n").write(head + ",\n" + ",\n".join(new_lines) + "\n }}\n")

MON = p("site", "data", "monuments.json")
md = load(MON)
check_roundtrip(MON, md, separators=(",", ":"))
byid = {str(f["properties"]["id"]): f["properties"] for f in md["features"]}
for k, v in DATA["overrides"].items():
    pr = byid[k]
    exact = v["date_precision"] == "exact"
    want = {"y0": v["year_from"], "y1": v["year_to"], "ye": v["year_est"] if exact else v["year_to"], "ym": v["year_est"],
            "prec": v["date_precision"], "src": v["date_source"]}  # the same formulas as tools/build_site_data.py
    if any(pr.get(a) != b for a, b in want.items()):
        pr.update(want)
        mark(MON, "monument " + k)
save(MON, md, separators=(",", ":"))

# ---------------------------------------------------------------- register objects (founding year in the note)
for layer, fn in (("science", "science_register.json"), ("education", "education_register.json")):
    path = p("data", fn)
    reg = load(path)
    check_roundtrip(path, reg, indent=1)
    for r in DATA["register"]:
        if r["layer"] != layer:
            continue
        o = [x for x in reg if x["id"] == r["id"]]
        assert len(o) == 1, r["id"]
        o = o[0]
        for l in ("ru", "en", "ka"):
            if r[l] not in o["note"][l]:
                o["note"][l] = o["note"][l].rstrip() + " " + r[l]
                mark(path, "note %s of %s" % (l, r["id"]))
        if "from" in r and o["from"] != r["from"]:
            assert o["from"] == r["from_was"], (r["id"], o["from"])
            o["from"] = r["from"]
            mark(path, "from of " + r["id"])
    save(path, reg, indent=1)

print(("DRY RUN: " if DRY else "") + "%d changes in %d files" % (len(changes), len(changes_in_file)))
for c in changes:
    print("  ", c)
