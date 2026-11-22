"""Builds the list of literature and sources from the data of the site.

  python tools/build_bibliography.py

Reads site/data/history_events.json (the links of the events and the citations in their notes) and writes
  site/data/bibliography.json  - for the window "Literature and sources" of the page;
  BIBLIOGRAPHY.md              - the same list for the repository.
The books are listed by hand below (the full reference in the language of the book, the links to the scans); the number of events that rely on a book
is counted from the data, so it cannot get out of date. A link of an event that does not belong to any book below falls into the lists of the web pages.
"""
import json
import os
import re
import collections
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EV = os.path.join(ROOT, "site", "data", "history_events.json")
OUT_JSON = os.path.join(ROOT, "site", "data", "bibliography.json")
OUT_MD = os.path.join(ROOT, "BIBLIOGRAPHY.md")
ARCH = "https://archive.org/details/"

# (id, reference in the language of the book, links [(label, url)], regular expression for the links and notes of the events)
BOOKS = [
    ("dubrovin", "Н. Ф. Дубровин. История войны и владычества русских на Кавказе. Т. II–IV. 1886.",
     [("т. II", ARCH + "dubrovinnfistorijavojnyivladychestvaru0"), ("т. III", ARCH + "dubrovinnfistorijavojnyivladychestvaru89"), ("т. IV", ARCH + "dubrovinnfistorijavojnyivladychestvaru62")], r"Дубровин"),
    ("kartlis", "«Картлис Цховреба». Русский перевод. Тбилиси, 2008.", [("scan", ARCH + "KartlisCxovreba")], r"Картлис Цховреба"),
    ("istoria2012", "«საქართველოს ისტორია» (ოთხტომეული) / Асатиани Н., Отхмезури Г., Самсонадзе М., Джамбурия Г. История Грузии. Т. II–IV. 2012.",
     [("ka.wikisource", "https://ka.wikisource.org/wiki/2012_-_%E1%83%A1%E1%83%90%E1%83%A5%E1%83%90%E1%83%A0%E1%83%97%E1%83%95%E1%83%94%E1%83%9A%E1%83%9D%E1%83%A1_%E1%83%98%E1%83%A1%E1%83%A2%E1%83%9D%E1%83%A0%E1%83%98%E1%83%90_(%E1%83%9D%E1%83%97%E1%83%AE%E1%83%A2%E1%83%9D%E1%83%9B%E1%83%94%E1%83%A3%E1%83%9A%E1%83%98)_-_%E1%83%A2%E1%83%9D%E1%83%9B%E1%83%98_III")],
     r"საქართველოს ისტორია|Асатиани|История Грузии» \(в 4|История Грузии» \(ოთხ"),
    # the textbooks of the history of Georgia (read in the text: the pages in the events are the PDF pages); no link: the books are not published
    ("history2006", "საქართველოს ისტორია, ტ. I. თბილისი: თსუ გამომცემლობა, 2006 (History of Georgia, vol. 1).", [], r"History of Georgia, vol\. 1"),
    ("mus2012", "დ. მუსხელიშვილი, მ. სამსონაძე, ა. დაუშვილი. საქართველოს ისტორია უძველესი დროიდან 2009 წლამდე. თბილისი, 2012.", [], r"Muskhelishvili"),
    ("ben1999", "ა. ბენდიანიშვილი. საქართველოს ისტორია 1801–1921. თბილისი, 1999.", [], r"Bendianishvili"),
    ("kacharava1973", "Ю. Качарава, А. Киквидзе, П. Ратиани, А. Сургуладзе. История Грузии (учебное пособие). Тбилиси: Ганатлеба, 1973.", [], r"Качарава"),
    ("school9", "საქართველოს ისტორია, IX კლასი (სასკოლო სახელმძღვანელო). თბილისი: ილიაუნის გამომცემლობა.", [], r"History of Georgia, 9th grade"),
    ("vakhushti", "ვახუშტი ბატონიშვილი. აღწერა აწინდელისა ქართლისა (აღწერა ტფილისისა) / Вахушти Багратиони. Описание города Тбилиси.", [], r"Вахушти|Vakhushti|აღწერა აწინდელისა"),
    ("lang1955", "D. M. Lang. Studies in the Numismatic History of Georgia in Transcaucasia. American Numismatic Society, 1955.", [("scan", ARCH + "lang-1955-georgian-numismatics")], r"Studies in the Numismatic|Ланг \(1955\)|Ланг, 1955"),
    ("lang_giorgi", "D. M. Lang. Georgia in the Reign of Giorgi the Brilliant (1314–1346). Bulletin of the School of Oriental and African Studies, 1955.", [("scan", ARCH + "GeorgiaInTheReignOfGiorgiTheBrilliant1314-1346")], r"Giorgi the Brilliant"),
    ("togoshvili", "Тогошвили. Избранные труды по кавказоведению. Т. 1–2. 2014.", [("scan", ARCH + "izbrannye_trudy_po_kavkazovedeniiu_tom_1_2")], r"Тогошвили"),
    ("rody", "Дворянские роды Грузии. Т. 4. 1998.", [("scan", ARCH + "4-1998_202212")], r"Дворянские роды"),
    ("brosset", "M.-F. Brosset. Histoire de la Géorgie (1849); Rapports sur un voyage archéologique dans la Géorgie et dans l'Arménie (1850); М.-Ф. Броссе. История Грузии, грузинский перевод, т. II, 1900.",
     [("Histoire, 1849", ARCH + "bub_gb_TmtpAAAAMAAJ"), ("Rapports, 1850", ARCH + "Travel1847to1848BrossetRapports")], r"Броссе|Brosset"),
    ("irgor", "Сборник статей на фарси «Взаимное историческое и культурное влияние Ирана и Грузии» (تأثیر متقابل تاریخی و فرهنگی ایران و گرجستان).", [("scan", ARCH + "abu-abdurahman-kurdi-f_barid_20180203_1115")], r"Взаимное историческое и культурное влияние Ирана"),
    ("ioseliani", "П. Иосселиани. Описание древностей города Тифлиса. 1866.", [("scan", ARCH + "sat_and_21_yahoo")], r"Иосселиани"),
    ("calendar", "Кавказский календарь на 1856 год; Кавказский календарь на 1886 год.", [("1856", ARCH + "kavkazskijkalendarna1856god51"), ("1886", ARCH + "kavkazskijkalendarna1886god60")], r"Кавказский календарь"),
    ("uckebani", "სალიტერატურონი ნაწილნი ტფილისის უწყებათანი (Литературные части Тифлисских ведомостей), 1832, № 2–3.", [], r"Литературные части|სალიტერატურონი"),
    ("woytinsky", "V. Woytinsky. La Georgia (una vera democrazia). 1920.", [("scan", ARCH + "lageorgiaunaver00schrgoog")], r"Войтинский|Woytinsky"),
    ("baye", "J. de Baye. Tiflis. Souvenirs d'une mission. Paris, 1900.", [("scan", ARCH + "BSG_8MSUP605")], r"Baye|Бэй"),
    ("potto", "В. А. Потто. Кавказская война. Т. 1–2.", [], r"Потто"),
    ("dumas", "А. Дюма. Кавказ (Le Caucase), 1859.", [], r"Дюма"),
    ("bakradze", "Д. Бакрадзе, Н. Берзенов. Тифлисъ въ историческомъ и этнографическомъ отношенiяхъ. Тифлис, 1870.", [], r"Бакрадзе"),
    ("allcaucasus", "Весь Кавказъ. Сборник (Тифлис), Административный отдел; год 1903 взят из прежних ссылок проекта, на прочитанных страницах он не указан.", [], r"Весь Кавказ"),
    ("museum", "Путеводитель по Кавказскому военно-историческому музею. Тифлис.", [], r"Путеводитель по Кавказскому военно-историческому музею"),
    ("majd", "Маджд ос-Салтане. Описание города Тбилиси (1894). Грузинский перевод и комментарии М. Мамацашвили. Тбилиси: Мецниереба, 1971.", [], r"Маджд"),
    ("wardrop", "O. Wardrop. The Kingdom of Georgia. London, 1888.", [("Project Gutenberg", "https://www.gutenberg.org/ebooks/48403")], r"Wardrop"),
    ("earthquakes", "О. Варазанашвили, Н. Церетели, Э. Церетели. Historical Earthquakes in Georgia (up to 1900). Тбилиси, 2011.", [], r"Historical Earthquakes"),
    ("floods", "А. Амиранашвили, Ц. Басилашвили, Э. Элизбарашвили, О. Варазанашвили. Катастрофические паводки в окрестностях Тбилиси. Труды Института гидрометеорологии.", [], r"Катастрофические паводки"),
]
DSP = "https://dspace.nplg.gov.ge/handle/1234/"
EXTRA = {
    "uckebani": [("№ 1", DSP + "1719"), ("№ 2", DSP + "380937"), ("№ 3", DSP + "1720"), ("№ 4", DSP + "380113"), ("№ 5", DSP + "380114")],
    "majd": [("scan", DSP + "406779")],
    "potto": [("т. 1 (переизд. 1994)", ARCH + "B-001-034-818-ALL"), ("т. 2 (переизд. 1993)", ARCH + "1-potto-2")],
    "dumas": [("Le Caucase (оригинал)", ARCH + "lecaucasejournal00duma")],
    "vakhushti": [("ka.wikisource", "https://ka.wikisource.org/wiki/%E1%83%90%E1%83%A6%E1%83%AC%E1%83%94%E1%83%A0%E1%83%90_%E1%83%90%E1%83%AC%E1%83%98%E1%83%9C%E1%83%93%E1%83%94%E1%83%9A%E1%83%98%E1%83%A1%E1%83%90_%E1%83%A5%E1%83%90%E1%83%A0%E1%83%97%E1%83%9A%E1%83%98%E1%83%A1%E1%83%90")],
}
# copies on the disk of the author of the project (paths relative to the folder of the project georgia-timeline, data/raw/books/..., or the folder tbilisi_books of the desktop); for the repository file only
B = "georgia-timeline/data/raw/books/"
TB = "desktop/tbilisi_books/"
LOCAL = {
    "dubrovin": [B + "ru/dubrovin_1886_t2.pdf", B + "ru/dubrovin_1886_t3.pdf", B + "ru/dubrovin_1886_t4.pdf"],
    "kartlis": [B + "ru/kartlis_tskhovreba_ru.pdf"],
    "istoria2012": [TB + "sakartvelos_istoria_2012_t1.pdf ... t4.pdf"],
    "vakhushti": [TB + "vakhushti_1913.pdf", TB + "vakhushti_istoria_1885.pdf"],
    "lang1955": [B + "en/lang_1955_georgian_numismatics.pdf"],
    "lang_giorgi": [B + "en/lang_giorgi_the_brilliant_1314_1346.pdf"],
    "togoshvili": [B + "ru/togoshvili_2014_t1_2.pdf"],
    "rody": [B + "ru/dvoryanskie_rody_t4_georgia_1998.pdf"],
    "brosset": [B + "fr/brosset_1849_histoire_de_la_georgie.pdf", B + "fr/brosset_1850_rapports_archeologiques.pdf", TB + "brosse_sakartvelos_istoria_t2_1900.pdf"],
    "ioseliani": [B + "ru/ioseliani_1866_opisanie_drevnostei_tiflisa.pdf"],
    "calendar": [B + "ru/kavkazskii_kalendar_1856.pdf", B + "ru/kavkazskii_kalendar_1886.pdf"],
    "uckebani": [TB + "tbilisis_uckebani_1832_n2.pdf ... n5.pdf"],
    "woytinsky": [B + "it/woytinsky_1920_la_georgia.pdf"],
    "baye": [B + "fr/baye_1900_tiflis_souvenirs.pdf"],
    "bakradze": ["desktop/Tiflis Bakradze.pdf"],
    "allcaucasus": [B + "ru/ves_kavkaz_1908.pdf"],
    "museum": [B + "ru/putevoditel_kavkazskii_voenno_istoricheskii_muzei.pdf"],
    "majd": ["desktop/Kalak Tbilisis Agtsera.pdf"],
    "wardrop": [B + "en/wardrop_1888_kingdom_of_georgia.pdf"],
    "earthquakes": ["desktop/Varazanashvili...Hist. Eq. in Georgia_En.pdf"],
    "irgor": [B + "fa/iran_ve_gorjestan_tarih.pdf"],
    "ferri": [B + "it/ferri_1704_istoria_missioni_teatini.pdf"],
    "lamberti": [B + "it/lamberti_1654_relatione_colchide_mengrella.pdf"],
    "zeidlits": [B + "ru/zeidlits_1871_sbornik_svedenii_o_kavkaze.pdf"],
    "evliya": [B + "tr/evliya_celebi_1896_seyahatname_c2.pdf"],
    "tcherny": [B + "he/Hebrewbooks_org_46832.pdf"],
    "abramovitch": [B + "yi/abramovitch_1925_teror_in_rusland_un_gruzye.pdf"],
    "pomerantz": [B + "yi/pomerantz_1943_kavkaz.pdf"],
}
# no copy and no public link: potto (read as an electronic text), dumas (Russian translation, fb2), floods (the DOI given in the events does not resolve)

# read in full or in part, but no event of the site relies on them (yet)
CONSULTED = [
    ("ferri", "B. Ferri. Istoria delle missioni de' chierici regolari teatini. 1704.", [("scan", ARCH + "bub_gb_wAjrlgBz4hIC")]),
    ("lamberti", "A. Lamberti. Relatione della Colchide hoggi detta Mengrellia. 1654.", [("scan", ARCH + "bub_gb_tYxmx3czaloC")]),
    ("tcherny", "יוסף יהודה טשארני. ספר המסעות בארץ קוקז ובמדינות אשר מעבר לקוקז (Й. Я. Чёрный, Книга путешествий по Кавказу и Закавказью), Санкт-Петербург, 1884.", [("hebrewbooks", "https://www.hebrewbooks.org/46832")]),
    ("abramovitch", "R. Abramovitsh. Der ṭeror gegen sotsyalisṭen in Rusland un in Gruzye. 1925 (на идише).", [("scan", ARCH + "nybc202101")]),
    ("pomerantz", "A. Pomerantz. Ḳavḳaz. 1943 (на идише).", [("scan", ARCH + "nybc209214")]),
    ("zeidlits", "Сборник сведений о Кавказе. 1871.", [("scan", ARCH + "sborniksviedien00komigoog")]),
    ("evliya", "Evliya Çelebi. Seyahatname. Cilt 2 (Istanbul, 1896).", [("scan", ARCH + "evliyaelebisey02evliuoft")]),
    ("kutateladze", "თ. ქუთათელაძე. საცხოვრებელი და საზოგადოებრივი შენობების ინტერიერების მონუმენტურ-დეკორატიული ფერწერა თბილისში XIX–XX საუკუნეების მიჯნაზე (Т. Кутателадзе. Монументально-декоративная живопись интерьеров жилых и общественных зданий Тбилиси XIX–XX веков; диссертация, Грузинский технический университет, 2015; таблица зданий с. 88–96, страница «Парадные Тбилиси»).", [("pdf", "https://dspace.nplg.gov.ge/bitstream/1234/178167/1/Disertacia.pdf")]),
]
HOSTS = {
    "en.wikipedia.org": "Wikipedia (en)", "ru.wikipedia.org": "Wikipedia (ru)", "ka.wikipedia.org": "Wikipedia (ka)", "fr.wikipedia.org": "Wikipedia (fr)",
    "ka.wikisource.org": "Wikisource (ka)", "ru.wikisource.org": "Wikisource (ru)", "commons.wikimedia.org": "Wikimedia Commons",
    "openlibrary.ge": "openlibrary.ge", "www.gutenberg.org": "Project Gutenberg", "archive.org": "Internet Archive", "doi.org": "DOI",
}


def labels(e):
    out = []
    for s in e["src"]:
        out.append(s if isinstance(s, str) else s["label"])
        out.append(s if isinstance(s, str) else s.get("url", ""))   # a book without a link has no url
    out.append(e.get("note", {}).get("ru", ""))
    return " \n ".join(urllib.parse.unquote(x) for x in out)


def main():
    d = json.load(open(EV, encoding="utf-8"))
    events = d["events"]
    texts = [labels(e) for e in events]
    books = []
    for bid, ref, links, rx in BOOKS:
        n = sum(1 for t in texts if re.search(rx, t))
        books.append({"id": bid, "ref": ref, "links": [{"t": a, "u": b} for a, b in links + [x for x in EXTRA.get(bid, []) if x[1] not in [y[1] for y in links]]], "events": n})
    books.sort(key=lambda b: (-b["events"], b["ref"]))
    consulted = [{"id": i, "ref": r, "links": [{"t": a, "u": b} for a, b in l], "events": 0} for i, r, l in CONSULTED]
    hosts = collections.Counter()
    pages = collections.defaultdict(set)
    for e in events:
        for s in e["src"]:
            u = s if isinstance(s, str) else s.get("url", "")
            if not u:
                continue
            h = re.sub(r"^https?://([^/]+)/.*", r"\1", u)
            hosts[h] += 1
            pages[h].add(u)
    web = [{"host": h, "name": HOSTS.get(h, h), "pages": len(pages[h]), "events": n} for h, n in hosts.most_common()]
    data = {"updated": "2026-11-20", "events": len(events), "books": books, "consulted": consulted, "web": web}
    json.dump(data, open(OUT_JSON, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(OUT_JSON, "a", encoding="utf-8", newline="\n").write("\n")

    md = ["# Literature and sources", "",
          "Generated by `tools/build_bibliography.py` from the data of the site (`site/data/history_events.json`); do not edit by hand. "
          "The same list is shown on the page (About and sources, button Literature and sources).",
          "Sources of the maps, plans, photographs, boundaries and other layers are listed in the panel About and sources of the page and in `sources.md`.", "",
          f"Events of the timeline: {len(events)}. Every event has at least one link; where a book was read, the note of the event gives the page.", "",
          "## Books and documents (the number of events that rely on the work)", ""]
    for i, b in enumerate(books, 1):
        ln = "; ".join(f"[{x['t']}]({x['u']})" for x in b["links"])
        loc = "; ".join(f"`{x}`" for x in LOCAL.get(b["id"], []))
        md.append(f"{i}. {b['ref']} — {b['events']} event(s)" + (f". Public link: {ln}" if ln else ". Public link: none found") + (f". Copy of the author of the project: {loc}" if loc else ". Copy of the author of the project: none"))
    md += ["", "## Read, but no event relies on them yet", ""]
    for i, b in enumerate(consulted, 1):
        ln = "; ".join(f"[{x['t']}]({x['u']})" for x in b["links"])
        loc = "; ".join(f"`{x}`" for x in LOCAL.get(b["id"], []))
        md.append(f"{i}. {b['ref']}" + (f" Public link: {ln}" if ln else "") + (f" Copy of the author of the project: {loc}" if loc else ""))
    md += ["", "## Web pages that the events link to", "", "| Site | Pages | Events |", "|---|---|---|"]
    for w in web:
        md.append(f"| {w['name']} | {w['pages']} | {w['events']} |")
    md += ["", "## Known problems with links", "",
           "- `openlibrary.ge` (the collection 'Ves Kavkaz', the earthquake catalogue): the certificate of the site has expired, so a browser shows a warning; the pages could not be opened by the tool that checks links, therefore these links are NOT used in the list above (they are still in the links of 11 events).",
           "- The DOI `10.36073/1512-0902-2023-133-56-61` (the paper on the floods near Tbilisi, 11 events) does not resolve (HTTP 404, not found by Crossref); the paper itself could not be confirmed there.",
           "- The Bakradze-Berzenov book of 1870: a copy in the library of the University of Bonn was suggested by a search, but its page is closed by a bot check, so it is not listed.", "",
           "## How the texts were read", "",
           "- Wikipedia and Wikisource pages were opened and read; the link is given in the event. Where a page is only a bibliographic record of a book, the note says so.",
           "- Books: the text of a PDF (text layer, or OCR with Tesseract 5.4; Ottoman and Persian print with Kraken and the OpenITI models) was used only to find a place; "
           "every fact that is shown on the site was read on the image of the page, and the note of the event gives the page.",
           "- Where two sources disagree, the event keeps the date of the source that was read and the note names the other date.",
           "- Texts in Georgian were written by the project with the help of an AI and checked by a second AI (Gemini); they have not been checked by a native speaker.", ""]
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write("\n".join(md))
    print("books", len(books), "with events:", sum(1 for b in books if b["events"]), "web hosts", len(web))
    for b in books:
        print(b["events"], b["id"])


if __name__ == "__main__":
    main()
