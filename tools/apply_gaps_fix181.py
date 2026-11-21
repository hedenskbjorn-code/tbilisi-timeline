"""Patch 1.8.1: only what was checked in the text of the source (the CyberLeninka articles were read in the PDF, the Wikipedia articles through the API).

 * eight new events from the CyberLeninka articles (1864, 1868, 1882, 1887, 1909, 1924, 1930, 1931-1932), each with a note naming the article and the PDF page;
 * additions to the notes of the cards: the Alexander Nevsky cathedral, the mosques Juma and Shia, the church Nor Echmiadzin, two churches of the register
   (data/religious_addenda.json for the curated ones, data/religious_register.json for the register ones), the Art Palace of Georgia (data/science_register.json);
 * two dates of register objects from the Wikipedia page of the object: the Art Palace (1895) and the Dry Bridge (1848-1851), through data/monument_date_overrides.json
   and site/data/monuments.json (the same formulas as tools/build_site_data.py).
Georgian texts: translated by Gemini. The script is idempotent: run twice, the second run changes nothing.
After it run: tools/build_science.py, tools/build_religious.py, tools/build_bibliography.py.
Usage: python -X utf8 -P tools/apply_gaps_fix181.py [--dry-run]
"""
import bisect
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DRY = "--dry-run" in sys.argv
DATA = json.loads(r'''{
 "events": [
  {
   "year": 1864,
   "date": "05.04.1864",
   "cat": "science",
   "src": {
    "url": "https://doi.org/10.24412/CL-37184-2024-7-379-404",
    "label": "Д. В. Аносов, 2024, DOI 10.24412/CL-37184-2024-7-379-404"
   },
   "ru": "Основано Кавказское медицинское общество (по инициативе врача П. И. Собольщикова, управляющего медицинской частью гражданского ведомства на Кавказе)",
   "en": "The Caucasian Medical Society is founded (on the initiative of the physician P. I. Sobolshchikov, head of the medical department of the civil administration in the Caucasus)",
   "ka": "დაარსდა კავკასიის საექიმო საზოგადოება (კავკასიაში სამოქალაქო უწყების სამედიცინო ნაწილის მმართველის, ექიმ პ. ი. სობოლშჩიკოვის თაოსნობით)",
   "note": {
    "ru": "Аносов Д. В., «К биографии председателя Кавказского медицинского общества и главного врача Тифлисской Михайловской больницы А. Г. Гурко» (2024), PDF с. 6 (с. 384), примеч. 13: «основано 05.04.1864 г.».",
    "en": "D. V. Anosov, 'On the biography of the chairman of the Caucasian Medical Society and chief physician of the Tiflis Mikhailovsky hospital A. G. Gurko' (2024), PDF p. 6 (p. 384), note 13: 'founded on 05.04.1864'.",
    "ka": "დ. ვ. ანოსოვი, „კავკასიის საექიმო საზოგადოების თავმჯდომარისა და ტფილისის მიხეილის საავადმყოფოს მთავარი ექიმის ა. გ. გურკოს ბიოგრაფიისათვის“ (2024), PDF გვ. 6 (გვ. 384), შენიშვნა 13: „დაარსდა 05.04.1864 წ.“."
   }
  },
  {
   "year": 1868,
   "date": "19.02.1868",
   "cat": "power",
   "src": {
    "url": "https://doi.org/10.24147/1990-5173.2021.18(1).24-34",
    "label": "А. А. Сапунков, 2021, DOI 10.24147/1990-5173.2021.18(1).24-34"
   },
   "ru": "Торжественно открыта Тифлисская судебная палата (судебная реформа на Кавказе; в тот же день суды открылись в четырёх городах Кавказа)",
   "en": "The Tiflis Judicial Chamber is solemnly opened (the judicial reform in the Caucasus; the courts opened the same day in four cities of the Caucasus)",
   "ka": "საზეიმოდ გაიხსნა ტფილისის სასამართლო პალატა (სასამართლო რეფორმა კავკასიაში; იმავე დღეს სასამართლოები გაიხსნა კავკასიის ოთხ ქალაქში)",
   "note": {
    "ru": "Сапунков А. А., «История создания Тифлисского судебного округа (1868–1880 гг.)», Вестник Омского университета. Серия «Право», 2021, т. 18, № 1, с. 24–34, PDF с. 4–5: циркуляр от 10 февраля 1868 г. рекомендовал 19 февраля как день открытия; церемония прошла в этот день одновременно в 4 городах Кавказа.",
    "en": "A. A. Sapunkov, 'The history of the creation of the Tiflis judicial district (1868-1880)', Bulletin of Omsk University, Law series, 2021, vol. 18, no. 1, pp. 24-34, PDF pp. 4-5: the circular of 10 February 1868 recommended 19 February as the day of the opening; the ceremony took place on that day in 4 cities of the Caucasus at once.",
    "ka": "ა. ა. საპუნკოვი, „ტფილისის სასამართლო ოლქის შექმნის ისტორია (1868–1880 წწ.)“, ომსკის უნივერსიტეტის მაცნე, სერია „სამართალი“, 2021, ტ. 18, № 1, გვ. 24–34, PDF გვ. 4–5: 1868 წლის 10 თებერვლის ცირკულარით გახსნის დღედ რეკომენდებული იყო 19 თებერვალი; ცერემონია იმავე დღეს გაიმართა კავკასიის 4 ქალაქში ერთდროულად."
   }
  },
  {
   "year": 1882,
   "date": "22.06.1882",
   "cat": "other",
   "src": {
    "url": "https://cyberleninka.ru/article/n/voennye-hramy-russkogo-tiflisa",
    "label": "М. Д. Гогитидзе, 2019, CyberLeninka"
   },
   "ru": "В Тифлисе открыт кадетский корпус (с домовой церковью на втором этаже)",
   "en": "A cadet corps is opened in Tiflis (with a house church on the second floor)",
   "ka": "ტფილისში გაიხსნა კადეტთა კორპუსი (მეორე სართულზე არსებული კარის ეკლესიით)",
   "note": {
    "ru": "Гогитидзе М. Д., «Военные храмы русского Тифлиса», Russian Colonial Studies, 2019, № 2, с. 41–55, PDF с. 3 (с. 43).",
    "en": "M. D. Gogitidze, 'Military churches of Russian Tiflis', Russian Colonial Studies, 2019, no. 2, pp. 41-55, PDF p. 3 (p. 43).",
    "ka": "მ. დ. გოგიტიძე, „რუსული ტფილისის სამხედრო ტაძრები“, Russian Colonial Studies, 2019, № 2, გვ. 41–55, PDF გვ. 3 (გვ. 43)."
   }
  },
  {
   "year": 1887,
   "date": "1887-1888",
   "cat": "other",
   "src": {
    "url": "https://cyberleninka.ru/article/n/sozdanie-tiflisskogo-okruzhnogo-obschestva-spasaniya-na-vodah",
    "label": "С. А. Воробьёва, А. В. Третьяков, 2021, CyberLeninka"
   },
   "ru": "Начинает работу Тифлисское окружное общество спасания на водах (на основе существовавшей с 1874 г. организации): спасательная станция на Куре и пост у Михайловского моста",
   "en": "The Tiflis district society for rescue on the water begins its work (on the basis of an organisation that had existed since 1874): a rescue station on the Kura and a post at the Mikhailovsky bridge",
   "ka": "მუშაობას იწყებს ტფილისის საოლქო წყალზე მაშველი საზოგადოება (1874 წლიდან არსებული ორგანიზაციის ბაზაზე): სამაშველო სადგური მტკვარზე და საგუშაგო მიხეილის ხიდთან",
   "note": {
    "ru": "Воробьёва С. А., Третьяков А. В., «Создание Тифлисского окружного общества спасания на водах» (2021), PDF с. 1–2, 5: «первым годом работы стал 1887–1888 г.».",
    "en": "S. A. Vorobyova, A. V. Tretyakov, 'The creation of the Tiflis district society for rescue on the water' (2021), PDF pp. 1-2, 5: 'the first year of work was 1887-1888'.",
    "ka": "ს. ა. ვორობიოვა, ა. ვ. ტრეტიაკოვი, „ტფილისის საოლქო წყალზე მაშველი საზოგადოების შექმნა“ (2021), PDF გვ. 1–2, 5: „მუშაობის პირველი წელი გახდა 1887–1888 წ.“."
   }
  },
  {
   "year": 1909,
   "date": "30.12.1909",
   "cat": "build",
   "src": {
    "url": "https://cyberleninka.ru/article/n/voennye-hramy-russkogo-tiflisa",
    "label": "М. Д. Гогитидзе, 2019, CyberLeninka"
   },
   "ru": "Торжественно освящено здание Тифлисского кадетского корпуса на Головинском проспекте (в 2005 г. здание передано Зурабу Церетели для Музея современного искусства)",
   "en": "The building of the Tiflis cadet corps on Golovin Avenue is solemnly consecrated (in 2005 the building was handed to Zurab Tsereteli for the Museum of Modern Art)",
   "ka": "საზეიმოდ ეკურთხა ტფილისის კადეტთა კორპუსის შენობა გოლოვინის პროსპექტზე (2005 წ. შენობა გადაეცა ზურაბ წერეთელს თანამედროვე ხელოვნების მუზეუმისთვის)",
   "note": {
    "ru": "Гогитидзе М. Д., «Военные храмы русского Тифлиса», Russian Colonial Studies, 2019, № 2, PDF с. 3 (с. 43).",
    "en": "M. D. Gogitidze, 'Military churches of Russian Tiflis', Russian Colonial Studies, 2019, no. 2, PDF p. 3 (p. 43).",
    "ka": "მ. დ. გოგიტიძე, „რუსული ტფილისის სამხედრო ტაძრები“, Russian Colonial Studies, 2019, № 2, PDF გვ. 3 (გვ. 43)."
   }
  },
  {
   "year": 1924,
   "date": "1924",
   "cat": "other",
   "src": {
    "url": "https://doi.org/10.18413/2687-0967-2020-47-1-91-96",
    "label": "Н. В. Парусова, 2020, DOI 10.18413/2687-0967-2020-47-1-91-96"
   },
   "ru": "Летом закрыта армянская церковь Св. Минаса в Авлабаре (1790 г.); здание передано организации «Молодые ленинцы», которая открыла в нём районный клуб",
   "en": "In the summer the Armenian church of St. Minas in Avlabari (built in 1790) is closed; the building is handed to the organisation 'Young Leninists', which opens a district club in it",
   "ka": "ზაფხულში დაიხურა წმ. მინასის სომხური ეკლესია ავლაბარში (აშენებული 1790 წ.); შენობა გადაეცა ორგანიზაციას „ახალგაზრდა ლენინელები“, რომელმაც მასში რაიონული კლუბი გახსნა",
   "note": {
    "ru": "Парусова Н. В., «История армянских церквей в квартале Авлабар в Тбилиси», Via in tempore. История. Политология, 2020, т. 47, № 1, с. 91–96, PDF с. 3 (с. 93).",
    "en": "N. V. Parusova, 'The history of the Armenian churches in the Avlabari quarter in Tbilisi', Via in tempore. History. Political science, 2020, vol. 47, no. 1, pp. 91-96, PDF p. 3 (p. 93).",
    "ka": "ნ. ვ. პარუსოვა, „თბილისის ავლაბრის უბნის სომხური ეკლესიების ისტორია“, Via in tempore. ისტორია. პოლიტოლოგია, 2020, ტ. 47, № 1, გვ. 91–96, PDF გვ. 3 (გვ. 93)."
   }
  },
  {
   "year": 1930,
   "date": "07.02.1930",
   "cat": "other",
   "src": {
    "url": "https://cyberleninka.ru/article/n/voennye-hramy-russkogo-tiflisa",
    "label": "М. Д. Гогитидзе, 2019, CyberLeninka"
   },
   "ru": "Начинается демонтаж Александро-Невского военного собора; он продлится до 1931 г.",
   "en": "The dismantling of the Alexander Nevsky military cathedral begins; it will last until 1931",
   "ka": "იწყება ალექსანდრე ნეველის სამხედრო ტაძრის დემონტაჟი; იგი 1931 წლამდე გაგრძელდება",
   "note": {
    "ru": "Гогитидзе М. Д., «Военные храмы русского Тифлиса», Russian Colonial Studies, 2019, № 2, PDF с. 2, 12–13: на месте собора в 1934–1938 гг. строился 1-й корпус Правительства Грузинской ССР.",
    "en": "M. D. Gogitidze, 'Military churches of Russian Tiflis', Russian Colonial Studies, 2019, no. 2, PDF pp. 2, 12-13: on the site of the cathedral the 1st block of the government of the Georgian SSR was built in 1934-1938.",
    "ka": "მ. დ. გოგიტიძე, „რუსული ტფილისის სამხედრო ტაძრები“, Russian Colonial Studies, 2019, № 2, PDF გვ. 2, 12–13: ტაძრის ადგილზე 1934–1938 წწ. შენდებოდა საქართველოს სსრ მთავრობის 1-ლი კორპუსი."
   }
  },
  {
   "year": 1931,
   "date": "1931-1932",
   "cat": "build",
   "src": {
    "url": "https://doi.org/10.54347/Lab.2021.4.4",
    "label": "В. Б. Калашников, 2021, DOI 10.54347/Lab.2021.4.4"
   },
   "ru": "Проходит Всесоюзный конкурс на проект Дворца культуры в Тифлисе: первое и последнее крупное мероприятие, в котором участвовала ассоциация пролетарских архитекторов Грузии",
   "en": "An All-Union competition for the design of a Palace of Culture in Tiflis takes place: the first and last large event in which the association of proletarian architects of Georgia took part",
   "ka": "ტარდება საკავშირო კონკურსი ტფილისში კულტურის სასახლის პროექტზე: პირველი და უკანასკნელი მსხვილი ღონისძიება, რომელშიც საქართველოს პროლეტარ არქიტექტორთა ასოციაცია მონაწილეობდა",
   "note": {
    "ru": "Калашников В. Б., «Тифлис — Москва: особенности взаимодействия „центра“ и „периферии“ на примере грузинской архитектуры 1920–1930-х гг.», Labyrinth, 2021, № 4, с. 69–82, PDF с. 7–8 (с. 75–76); 17 марта 1930 г. общество пролетарских архитекторов Грузии опубликовало в газете «Заря Востока» декларацию.",
    "en": "V. B. Kalashnikov, 'Tiflis - Moscow: the interaction of the centre and the periphery in the Georgian architecture of the 1920s-1930s', Labyrinth, 2021, no. 4, pp. 69-82, PDF pp. 7-8 (pp. 75-76); on 17 March 1930 the society of proletarian architects of Georgia published a declaration in the newspaper 'Zarya Vostoka'.",
    "ka": "ვ. ბ. კალაშნიკოვი, „ტფილისი — მოსკოვი: ‚ცენტრისა‘ და ‚პერიფერიის‘ ურთიერთქმედების თავისებურებები 1920–1930-იანი წლების ქართული არქიტექტურის მაგალითზე“, Labyrinth, 2021, № 4, გვ. 69–82, PDF გვ. 7–8 (გვ. 75–76); 1930 წლის 17 მარტს საქართველოს პროლეტარ არქიტექტორთა საზოგადოებამ გაზეთ „ზარია ვოსტოკაში“ დეკლარაცია გამოაქვეყნა."
   }
  }
 ],
 "cards": {
  "alexander_nevsky": {
   "ru": "Снос начался 7 февраля 1930 г. и продлился до 1931 г.; в 1921 г. с купола сняли крест и установили пятиконечную звезду, в храме разместился «Союз воинствующих безбожников», до 1930 г. там был Дворец шахмат; на этом месте в 1934–1938 гг. строился 1-й корпус Правительства Грузинской ССР (Гогитидзе, 2019, PDF с. 2, 12–13).",
   "en": "The demolition began on 7 February 1930 and lasted until 1931; in 1921 the cross was taken from the dome and a five-pointed star was put up, the 'Union of the Militant Godless' was placed in the church, until 1930 the Chess Palace was there; on this site the 1st block of the government of the Georgian SSR was built in 1934-1938 (Gogitidze, 2019, PDF pp. 2, 12-13).",
   "ka": "ნგრევა დაიწყო 1930 წლის 7 თებერვალს და გაგრძელდა 1931 წლამდე; 1921 წ. გუმბათიდან მოხსნეს ჯვარი და დადგეს ხუთქიმიანი ვარსკვლავი, ტაძარში განთავსდა „მებრძოლ უღმერთოთა კავშირი“, 1930 წლამდე იქ იყო ჭადრაკის სასახლე; ამ ადგილზე 1934–1938 წწ. შენდებოდა საქართველოს სსრ მთავრობის 1-ლი კორპუსი (გოგიტიძე, 2019, PDF გვ. 2, 12–13)."
  },
  "juma": {
   "ru": "По Абдуллину (2022, PDF с. 3–4): суннитская мечеть построена в 1723–1735 гг., в 1740 г. разрушена персами, в 1851–1864 гг. восстановлена по проекту Дж. Скудьери (по en.wikipedia здание 1846–1851), в 1895 г. отремонтирована на средства З. Тагиева, в 1998 г. реставрирована.",
   "en": "According to Abdullin (2022, PDF pp. 3-4): the Sunni mosque was built in 1723-1735, destroyed by the Persians in 1740, rebuilt in 1851-1864 to the design of G. Scudieri (en.wikipedia gives 1846-1851 for the building), repaired in 1895 at the expense of Z. Tagiev and restored in 1998.",
   "ka": "აბდულინის მიხედვით (2022, PDF გვ. 3–4): სუნიტური მეჩეთი აშენდა 1723–1735 წწ., 1740 წ. დაანგრიეს სპარსელებმა, 1851–1864 წწ. აღდგა ჯ. სკუდიერის პროექტით (en.wikipedia-ს მიხედვით შენობა 1846–1851 წწ.), 1895 წ. შეკეთდა ზ. თაღიევის სახსრებით, 1998 წ. რესტავრირებულია."
  },
  "shia_mosque": {
   "ru": "По Абдуллину (2022, PDF с. 3): шиитская мечеть разрушена в начале 1950-х гг.",
   "en": "According to Abdullin (2022, PDF p. 3): the Shia mosque was destroyed in the early 1950s.",
   "ka": "აბდულინის მიხედვით (2022, PDF გვ. 3): შიიტური მეჩეთი დაინგრა 1950-იანი წლების დასაწყისში."
  },
  "reg3362": {
   "ru": "По Парусовой (2020, PDF с. 3): церковь Св. Геворга (Эчмиадзин) построена в 1805 г. на средства местных жителей, перестраивалась с 1846 г. до конца 1850-х гг., реставрирована в 2006–2010 гг. (по ka.wikipedia построена в 1806–1808 гг.).",
   "en": "According to Parusova (2020, PDF p. 3): the church of St. Gevorg (Echmiadzin) was built in 1805 at the expense of local residents, rebuilt from 1846 to the end of the 1850s and restored in 2006-2010 (ka.wikipedia gives 1806-1808 for its construction).",
   "ka": "პარუსოვას მიხედვით (2020, PDF გვ. 3): წმ. გევორქის ეკლესია (ეჩმიაძინი) აშენდა 1805 წ. ადგილობრივი მცხოვრებლების სახსრებით, გადაკეთდა 1846 წლიდან 1850-იანი წლების ბოლომდე, რესტავრირდა 2006–2010 წწ. (ka.wikipedia-ს მიხედვით აშენდა 1806–1808 წწ.)."
  },
  "reg24768": {
   "ru": "По статье ka.wikipedia: армянская крестово-купольная церковь на правом берегу Куры, в старом районе Абанотубани; ныне разрушена.",
   "en": "According to the ka.wikipedia article: an Armenian cross-in-square church on the right bank of the Kura, in the old quarter Abanotubani; now destroyed.",
   "ka": "ka.wikipedia-ს სტატიის მიხედვით: სომხური ჯვარ-გუმბათოვანი ეკლესია მტკვრის მარჯვენა ნაპირზე, ძველ უბან აბანოთუბანში; ამჟამად დანგრეულია."
  },
  "reg24759": {
   "ru": "По статье ka.wikipedia: первая церковь Вознесения заложена 12 марта 1851 г., достроена 23 ноября 1852 г., снесена в 1968 г. при расширении Коджорской дороги; новая церковь (архитектор Реваз Джанашия) действует с 23 февраля 2003 г. Конфессия в статье не названа.",
   "en": "According to the ka.wikipedia article: the first Church of the Ascension was laid down on 12 March 1851, completed on 23 November 1852 and demolished in 1968 for the widening of the Kojori road; the new church (architect Revaz Janashia) has been in use since 23 February 2003. The article does not name the denomination.",
   "ka": "ka.wikipedia-ს სტატიის მიხედვით: პირველი ამაღლების ეკლესია ჩაეყარა 1851 წლის 12 მარტს, დასრულდა 1852 წლის 23 ნოემბერს, დაინგრა 1968 წ. კოჯრის გზის გაფართოებისას; ახალი ეკლესია (არქიტექტორი რევაზ ჯანაშია) მოქმედებს 2003 წლის 23 თებერვლიდან. სტატიაში კონფესია დასახელებული არ არის."
  },
  "reg3016": {
   "ru": "По статье ka.wikipedia: музей основан в 1927 г. (Давид Арсенишвили); здание построено в 1895 г. по проекту архитектора Пауля Штерна; год на шкале исправлен с 1825 (значение реестра по умолчанию) на 1895.",
   "en": "According to the ka.wikipedia article: the museum was founded in 1927 (David Arsenishvili); the building was built in 1895 to the design of the architect Paul Stern; the year on the scale is corrected from 1825 (the default value of the register) to 1895.",
   "ka": "ka.wikipedia-ს სტატიის მიხედვით: მუზეუმი დაარსდა 1927 წ. (დავით არსენიშვილი); შენობა აშენდა 1895 წ. არქიტექტორ პაულ შტერნის პროექტით; სკალაზე წელი გასწორდა 1825-დან (რეესტრის ნაგულისხმევი მნიშვნელობა) 1895-ზე."
  },
  "reg3049": {
   "ru": "Один и тот же храм записан в реестре дважды: объект 3049 (ул. Джавахишвили, 69; дата 1880, происхождение даты не выяснено) и объект 7998 (ул. Марджанишвили, 65; 1863–1864). По статье ru.wikipedia церковь построена в 1864 г. на пожертвования верующих и 5 000 руб. от Святейшего Синода (по ka.wikipedia в 1863–1864 гг.); в 1886 г. пристроена колокольня; в 1900 г. построена трапезная Николая Чудотворца в честь императора Николая II; в 1913 г. рядом возведена часовня в честь 300-летия дома Романовых. Карточка 7998 удалена как дубль.",
   "en": "The same church is entered twice in the register: object 3049 (Javakhishvili St. 69; date 1880, the origin of the date is not known) and object 7998 (Marjanishvili St. 65; 1863-1864). According to the ru.wikipedia article the church was built in 1864 with the donations of the believers and 5,000 roubles from the Holy Synod (ka.wikipedia gives 1863-1864); a bell tower was added in 1886; the refectory of St. Nicholas the Wonderworker was built in 1900 in honour of Emperor Nicholas II; in 1913 a chapel in honour of the 300th anniversary of the Romanov dynasty was put up beside the church. The card 7998 has been removed as a duplicate.",
   "ka": "ერთი და იგივე ტაძარი რეესტრში ორჯერ არის ჩაწერილი: ობიექტი 3049 (ჯავახიშვილის ქ. 69; თარიღი 1880, თარიღის წარმომავლობა დადგენილი არ არის) და ობიექტი 7998 (მარჯანიშვილის ქ. 65; 1863–1864). ru.wikipedia-ს სტატიის მიხედვით ეკლესია აშენდა 1864 წ. მორწმუნეთა შემოწირულობებითა და რუსეთის წმინდა სინოდის 5 000 მანეთით (ka.wikipedia-ს მიხედვით 1863–1864 წწ.); 1886 წ. მიუშენდა სამრეკლო; 1900 წ. აშენდა წმინდა ნიკოლოზ საკვირველმოქმედის ტრაპეზი იმპერატორ ნიკოლოზ II-ის პატივსაცემად; 1913 წ. გვერდით აიგო სამლოცველო რომანოვების დინასტიის 300 წლისთავის პატივსაცემად. ბარათი 7998 წაშლილია როგორც დუბლი."
  }
 },
 "overrides": {
  "3016": {
   "year_from": 1895,
   "year_to": 1895,
   "year_est": 1895,
   "date_precision": "exact",
   "date_source": "ka.wikipedia.org",
   "why": "ka.wikipedia 'Art Palace of Georgia': the palace was built in 1895 (architect Paul Stern); the register gave the beginning of the 19th century (https://ka.wikipedia.org/wiki/საქართველოს_ხელოვნების_სასახლე_–_კულტურის_ისტორიის_მუზეუმი)"
  },
  "4866": {
   "year_from": 1848,
   "year_to": 1851,
   "year_est": 1851,
   "date_precision": "decade",
   "date_source": "ru.wikipedia.org",
   "why": "ru.wikipedia 'Dry Bridge': built in 1848-1851 to the design of G. Scudieri; the register gave the middle of the 19th century (https://ru.wikipedia.org/wiki/Сухой_мост)"
  }
 }
}''')
changes = []
touched = {}
CYR = re.compile("[А-Яа-яЁё]")
for e in DATA["events"]:
    assert not CYR.search(e["en"] + e["ka"] + e["note"]["en"] + e["note"]["ka"]), "Cyrillic in the en or ka text of the event " + e["date"]
for k, v in DATA["cards"].items():
    assert not CYR.search(v["en"] + v["ka"]), "Cyrillic in the en or ka text of the card " + k


def p(*a):
    return os.path.join(ROOT, *a)


def load_checked(path, **kw):
    raw = open(path, encoding="utf-8").read()
    doc = json.loads(raw)
    assert json.dumps(doc, ensure_ascii=False, **kw) == raw, "the file layout changed, refusing to rewrite " + path
    return doc


def write(path, doc, **kw):
    if not DRY:
        open(path, "wb").write(json.dumps(doc, ensure_ascii=False, **kw).encode("utf-8"))


def mark(path, msg):
    touched[path] = True
    changes.append(msg)


def add_note(o, add, label, path):
    note = o["note"]
    for l in ("ru", "en", "ka"):
        if add[l] not in note[l]:
            note[l] = (note[l].rstrip() + " " + add[l]).strip()
            mark(path, "note %s of %s" % (l, label))


# ---------------------------------------------------------------- events
EVP = p("site", "data", "history_events.json")
doc = load_checked(EVP, indent=1)
events = doc["events"]
for ne in DATA["events"]:
    if any(x["year"] == ne["year"] and x["ru"] == ne["ru"] for x in events):
        continue
    ev = {"year": ne["year"], "date": ne["date"], "cat": ne["cat"], "src": [ne["src"]], "ru": ne["ru"], "en": ne["en"], "ka": ne["ka"], "note": ne["note"]}
    events.insert(bisect.bisect_right([x["year"] for x in events], ne["year"]), ev)
    mark(EVP, "new event " + ne["date"])
assert [x["year"] for x in events] == sorted(x["year"] for x in events)
if EVP in touched:
    write(EVP, doc, indent=1)

# ---------------------------------------------------------------- dates of two register objects
OV = p("data", "monument_date_overrides.json")
raw = open(OV, encoding="utf-8").read()
ovdoc = json.loads(raw)
new_lines = []
for k, v in DATA["overrides"].items():
    if k not in ovdoc["objects"]:
        ovdoc["objects"][k] = v
        new_lines.append("  %s: %s" % (json.dumps(k), json.dumps(v, ensure_ascii=False)))
        mark(OV, "date override of the object " + k)
if new_lines and not DRY:
    head, tail = raw.rstrip("\n").rsplit("\n }}", 1)
    assert tail == "", "unexpected layout of " + OV
    open(OV, "wb").write((head + ",\n" + ",\n".join(new_lines) + "\n }}\n").encode("utf-8"))
MON = p("site", "data", "monuments.json")
md = load_checked(MON, separators=(",", ":"))
byid = {str(f["properties"]["id"]): f["properties"] for f in md["features"]}
for k, v in DATA["overrides"].items():
    pr = byid[k]
    exact = v["date_precision"] == "exact"
    want = {"y0": v["year_from"], "y1": v["year_to"], "ye": v["year_est"] if exact else v["year_to"], "ym": v["year_est"], "prec": v["date_precision"], "src": v["date_source"]}
    if any(pr.get(a) != b for a, b in want.items()):
        pr.update(want)
        mark(MON, "monument " + k)
if MON in touched:
    write(MON, md, separators=(",", ":"))

# ---------------------------------------------------------------- the science layer: the Art Palace
SCP = p("data", "science_register.json")
sc = load_checked(SCP, indent=1)
o = [x for x in sc if x["id"] == "reg3016"][0]
add_note(o, DATA["cards"]["reg3016"], "reg3016", SCP)
if o["from"] != 1895:
    assert o["from"] == 1825, o["from"]
    o["from"] = 1895
    mark(SCP, "from of reg3016")
if SCP in touched:
    write(SCP, sc, indent=1)

# ---------------------------------------------------------------- the religious layer
RGP = p("data", "religious_register.json")
rg = load_checked(RGP, indent=1)
for rid in ("reg3362", "reg24768", "reg24759", "reg3049"):
    o = [x for x in rg if x["id"] == rid][0]
    add_note(o, DATA["cards"][rid], rid, RGP)
o = [x for x in rg if x["id"] == "reg24768"][0]
if o["rel"] != "armenian":          # an Armenian church by the Georgian article (the register gave only "christian")
    assert o["rel"] == "christian"
    o["rel"] = "armenian"
    mark(RGP, "rel of reg24768")
# the Alexander Nevsky church of Chugureti is entered in the register twice (objects 3049 and 7998): one card is kept, the duplicate goes
o = [x for x in rg if x["id"] == "reg3049"][0]
if o["from"] != 1864:
    assert o["from"] == 1880 and o["date"] == "1880", (o["from"], o["date"])
    o["from"], o["date"] = 1864, "1863\u20131864"
    mark(RGP, "from and date of reg3049")
dup = [x for x in rg if x["id"] == "reg7998"]
if dup:
    assert dup[0]["name"]["ru"] == o["name"]["ru"], "the names differ: not a duplicate"
    rg.remove(dup[0])
    mark(RGP, "removed the duplicate reg7998")
if RGP in touched:
    write(RGP, rg, indent=1)
ADP = p("data", "religious_addenda.json")
ad = json.load(open(ADP, encoding="utf-8")) if os.path.exists(ADP) else {}
for k in ("alexander_nevsky", "juma", "shia_mosque"):
    if ad.get(k) != DATA["cards"][k]:
        ad[k] = DATA["cards"][k]
        mark(ADP, "addendum of the card " + k)
if ADP in touched and not DRY:
    open(ADP, "wb").write(json.dumps(ad, ensure_ascii=False, indent=1).encode("utf-8"))
BRP = p("tools", "build_religious.py")
bs = open(BRP, encoding="utf-8").read()
if "religious_addenda.json" not in bs:
    old = '''        if it["id"] in PHOTOS["objects"]:
            o["ph"] = "|".join(PHOTOS["objects"][it["id"]])
        out.append(o)'''
    new = '''        if it["id"] in PHOTOS["objects"]:
            o["ph"] = "|".join(PHOTOS["objects"][it["id"]])
        if it["id"] in ADDENDA:        # sentences added to the note after the check against articles (data/religious_addenda.json)
            o["note"] = {l: (o["note"][l].rstrip() + " " + ADDENDA[it["id"]][l]).strip() for l in ("ru", "en", "ka")}
        out.append(o)'''
    assert bs.count(old) == 1
    bs = bs.replace(old, new)
    old2 = "def main():\n    out = []"
    assert bs.count(old2) == 1
    bs = bs.replace(old2, '_ap = os.path.join(ROOT, "data", "religious_addenda.json")\nADDENDA = json.load(open(_ap, encoding="utf-8")) if os.path.exists(_ap) else {}\n\n\ndef main():\n    out = []')
    if not DRY:
        open(BRP, "wb").write(bs.encode("utf-8"))
    mark(BRP, "build_religious.py reads the addenda")

print(("DRY RUN: " if DRY else "") + "%d changes in %d files" % (len(changes), len(touched)))
for c in changes:
    print("  ", c)
