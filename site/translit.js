// Names and addresses of register objects exist only in Georgian. For the English and Russian interface they are shown as:
//   1) the title of the Wikipedia article in that language, when the object has one (field wp);
//   2) a dictionary translation of frequent whole names;
//   3) otherwise word by word: known words are translated, the rest is transliterated from Georgian
//      (English: simplified national romanization system, Georgia 2002, without apostrophes; Russian: common practical transcription).
// The result is automatic and approximate; the page always shows the Georgian original next to it.
(function () {
  const LAT = { "ა": "a", "ბ": "b", "გ": "g", "დ": "d", "ე": "e", "ვ": "v", "ზ": "z", "თ": "t", "ი": "i", "კ": "k", "ლ": "l", "მ": "m", "ნ": "n", "ო": "o", "პ": "p", "ჟ": "zh", "რ": "r", "ს": "s", "ტ": "t", "უ": "u", "ფ": "p", "ქ": "k", "ღ": "gh", "ყ": "q", "შ": "sh", "ჩ": "ch", "ც": "ts", "ძ": "dz", "წ": "ts", "ჭ": "ch", "ხ": "kh", "ჯ": "j", "ჰ": "h" };
  const CYR = { "ა": "а", "ბ": "б", "გ": "г", "დ": "д", "ე": "е", "ვ": "в", "ზ": "з", "თ": "т", "ი": "и", "კ": "к", "ლ": "л", "მ": "м", "ნ": "н", "ო": "о", "პ": "п", "ჟ": "ж", "რ": "р", "ს": "с", "ტ": "т", "უ": "у", "ფ": "п", "ქ": "к", "ღ": "г", "ყ": "к", "შ": "ш", "ჩ": "ч", "ც": "ц", "ძ": "дз", "წ": "ц", "ჭ": "ч", "ხ": "х", "ჯ": "дж", "ჰ": "х" };

  // whole names (exact Georgian text, trimmed) -> [English, Russian]
  const NAMES = {
    "საცხოვრებელი სახლი": ["Residential building", "Жилой дом"],
    "საცხოვრებელი": ["Residential building", "Жилой дом"],
    "შერეული ფუნქციის შენობა": ["Mixed-use building", "Здание смешанного назначения"],
    "შერეული ფუნქციის ნაგებობა": ["Mixed-use structure", "Сооружение смешанного назначения"],
    "სამაროვანი": ["Burial ground", "Могильник"],
    "სასტუმრო": ["Hotel", "Гостиница"],
    "პრეზიდენტის რეზიდენცია": ["Presidential residence", "Резиденция президента"],
    "ხიდი": ["Bridge", "Мост"],
    "აბანო": ["Bathhouse", "Баня"],
    "კაფე": ["Cafe", "Кафе"],
    "თბილისის საკრებულოს შენობა": ["Tbilisi Sakrebulo building", "Здание Тбилисского сакребуло"],
    "სტომატოლოგიური კლინიკა": ["Dental clinic", "Стоматологическая клиника"],
    "მაღაზია": ["Shop", "Магазин"],
    "სახელოსნო": ["Workshop", "Мастерская"],
    "საზოგადოებრივი შენობა": ["Public building", "Общественное здание"],
    "კოშკი": ["Tower", "Башня"],
    "საშუალო სკოლა": ["Secondary school", "Средняя школа"],
    "ღვთისმშობლის ეკლესია": ["Church of the Mother of God", "Церковь Богородицы"],
    "წმ. ნინოს ეკლესია": ["St. Nino's Church", "Церковь Св. Нино"],
    "წმ. ნიკოლოზის ეკლესია": ["St. Nicholas's Church", "Церковь Св. Николая"],
    "წმ. გიორგის ეკლესია": ["St. George's Church", "Церковь Св. Георгия"],
    "წმ. სამების ეკლესია": ["Holy Trinity Church", "Церковь Св. Троицы"],
    "კვირაცხოვლის ეკლესია": ["Church of the Life-giving Pillar", "Церковь Животворящего столпа"],
    "გაერთიანებული ქართული ბანკი": ["United Georgian Bank", "Объединённый грузинский банк"],
    "საქართველოს ბანკი": ["Bank of Georgia", "Банк Грузии"],
    "მოსწავლე-ახალგაზრდობის სასახლე": ["Pupils' and Youth Palace", "Дворец школьников и молодёжи"],
    "ოფისი": ["Office", "Офис"],
    "განათლების სამინისტრო": ["Ministry of Education", "Министерство образования"],
    "საავადმყოფო": ["Hospital", "Больница"],
    "ლაბორატორია": ["Laboratory", "Лаборатория"],
    "პოლიკლინიკა": ["Polyclinic", "Поликлиника"],
    "კომპოზიტორთა კავშირი": ["Union of Composers", "Союз композиторов"],
    "სამრეკლო": ["Bell tower", "Колокольня"],
    "კაფე-ბარი": ["Cafe-bar", "Кафе-бар"],
    "ქარვასლა": ["Caravanserai", "Караван-сарай"],
    "საქართველოს სახელმწიფო მუზეუმი": ["Georgian State Museum", "Государственный музей Грузии"],
    "ლიტერატურის მუზეუმი": ["Museum of Literature", "Музей литературы"],
    "საგარეო საქმეთა სამინისტრო": ["Ministry of Foreign Affairs", "Министерство иностранных дел"],
    "კიბე-ქუჩა": ["Stair-street", "Улица-лестница"],
    "კიბე_ქუჩა": ["Stair-street", "Улица-лестница"],
    "ყოფილი თსს": ["Former Tbilisi State University", "Бывший ТГУ"],
  };
  // single words (as they appear; frequent genitives included) -> [English, Russian]
  const WORDS = {
    "ეკლესია": ["Church", "Церковь"], "ეკლესიის": ["Church", "Церкви"], "სოფ.": ["village", "с."], "შენობა": ["Building", "Здание"], "სახლი": ["House", "Дом"],
    "სახლი.": ["House", "Дом"], "სახლ": ["House", "Дом"], "წმ.": ["St.", "Св."], "ბაღი": ["Garden", "Сад"], "მუზეუმი": ["Museum", "Музей"],
    "საცხოვრებელი": ["Residential", "Жилой"], "სახელობის": ["named after", "имени"], "სახ.": ["named after", "им."], "თბილისის": ["Tbilisi", "Тбилисский"],
    "ყოფილი": ["Former", "Бывший"], "ყოფ.": ["Former", "Бывший"], "და": ["and", "и"], "სკოლა": ["School", "Школа"], "საქართველოს": ["Georgian", "Грузинский"],
    "საქ.": ["Georgian", "Грузинский"], "სამაროვანი": ["Burial ground", "Могильник"], "სასტუმრო": ["Hotel", "Гостиница"], "სასახლე": ["Palace", "Дворец"],
    "სახელმწიფო": ["State", "Государственный"], "შერეული": ["Mixed", "Смешанное"], "ფუნქციის": ["use", "назначения"], "ხიდი": ["Bridge", "Мост"],
    "კორპუსი": ["Block", "Корпус"], "ღვთისმშობლის": ["of the Mother of God", "Богородицы"], "გიორგის": ["of St. George", "Св. Георгия"],
    "თეატრი": ["Theatre", "Театр"], "კოშკი": ["Tower", "Башня"], "ნაგებობა": ["Structure", "Сооружение"], "აბანო": ["Bathhouse", "Баня"], "ძველი": ["Old", "Старый"],
    "ეროვნული": ["National", "Национальный"], "ინსტიტუტი": ["Institute", "Институт"], "საზოგადოებრივი": ["Public", "Общественное"], "უნივერსიტეტის": ["University", "Университета"],
    "ნასოფლარი": ["Deserted village", "Городище"], "ბანკი": ["Bank", "Банк"], "კაფე": ["Cafe", "Кафе"], "სამრეკლო": ["Bell tower", "Колокольня"],
    "სამინისტრო": ["Ministry", "Министерство"], "კიბე": ["Stair", "Лестница"], "ქუჩა": ["Street", "Улица"], "კათოლიკური": ["Catholic", "Католическая"],
    "საბავშვო": ["Children's", "Детский"], "საშუალო": ["Secondary", "Средняя"], "სახელოსნო": ["Workshop", "Мастерская"], "გალერეა": ["Gallery", "Галерея"],
    "მოედანი": ["Square", "Площадь"], "ნამოსახლარი": ["Settlement site", "Поселение"], "მონასტრის": ["Monastery", "Монастыря"], "მონასტერი": ["Monastery", "Монастырь"],
    "ოდა": ["Oda house", "Ода"], "ოფისი": ["Office", "Офис"], "ცენტრი": ["Centre", "Центр"], "საავადმყოფო": ["Hospital", "Больница"], "რეზიდენცია": ["Residence", "Резиденция"],
    "ზედა": ["Upper", "Верхний"], "პარკი": ["Park", "Парк"], "კომპლექსი": ["Complex", "Комплекс"], "აგარაკი": ["Villa", "Дача"], "სამზადი": ["Prep. building", "Хозпостройка"],
    "სინაგოგა": ["Synagogue", "Синагога"], "მეჩეთი": ["Mosque", "Мечеть"], "ტაძარი": ["Cathedral", "Собор"], "ბაზილიკა": ["Basilica", "Базилика"], "საკათედრო": ["Cathedral", "Кафедральный"],
    "სამების": ["Holy Trinity", "Святой Троицы"], "ნინოს": ["St. Nino's", "Св. Нино"], "ნიკოლოზის": ["St. Nicholas's", "Св. Николая"],
    "ციხე": ["Fortress", "Крепость"], "ციხესიმაგრე": ["Fortress", "Крепость"], "კედელი": ["Wall", "Стена"], "ბიბლიოთეკა": ["Library", "Библиотека"],
    "უბანი": ["Quarter", "Квартал"], "მოსაცდელი": ["Waiting room", "Зал ожидания"], "სადგური": ["Station", "Станция"], "ფაბრიკა": ["Factory", "Фабрика"],
  };
  // address abbreviations
  const ADDR = {
    "ქ.": ["St.", "ул."], "ქუჩა": ["St.", "ул."], "გამზ.": ["Ave.", "пр."], "გამზირი": ["Ave.", "пр."], "შეს.": ["Lane", "пер."], "შესახვევი": ["Lane", "пер."],
    "ჩიხი": ["Dead end", "тупик"], "მოედ.": ["Sq.", "пл."], "მოედანი": ["Sq.", "пл."], "კვ.": ["Quarter", "кв."], "მ/რ": ["Microdistrict", "мкр."], "ბულვ.": ["Blvd.", "бул."],
    "აღმ.": ["Aghm.", "Агм."], "ა": ["A.", "А."], "ს.": ["S.", "С."], "სოფ.": ["village", "с."], "კიბე": ["Stair", "Лестница"], "ბაქანი": ["Landing", "Площадка"],
  };

  const GEO = /[ა-ჿ]/;
  // given names whose nominative ends in a consonant ("დავითის" -> "დავით", not "დავითი")
  const CONS = new Set(["დავით", "მიხეილ", "ვახტანგ", "ზურაბ", "ნიკოლოზ", "თამარ", "გრიგოლ", "ბესარიონ", "ლევან", "ანტონ", "ვარლამ", "ტარიელ", "ქეთევან", "ზაალ", "არჩილ", "რომან", "სვიმონ", "იოსებ", "გერონტ", "ბაგრატ", "ალექსანდრ", "კონსტანტინ", "მელიტონ", "სამსონ"]);
  // genitive -> nominative guess: "...ის" -> "...ი" (or the bare stem for CONS), "...ას/ეს/ოს/უს" -> without "ს"
  function denom(w) {
    if (w.length > 4 && w.endsWith("ის")) { const st = w.slice(0, -2); return CONS.has(st) ? st : st + "ი"; }
    if (w.length > 3 && /[აეოუ]ს$/.test(w)) return w.slice(0, -1);
    return w;
  }
  function translit(word, i) {
    const map = i === 1 ? CYR : LAT;
    let out = "";
    for (const ch of word) out += GEO.test(ch) ? (map[ch] === undefined ? ch : map[ch]) : ch;
    return out.replace(/^([^A-Za-zЀ-ӿ]*)([A-Za-zЀ-ӿ])/, (m, p, c) => p + c.toUpperCase());
  }
  function piece(tok, dict, i) {
    if (tok in dict) return dict[tok][i];
    const core = tok.replace(/[.,;:)"”»]+$/g, "");
    const tail = tok.slice(core.length);
    if (core in dict) return dict[core][i] + tail;
    if (!GEO.test(core)) return tok;
    return translit(denom(core), i) + tail;
  }
  function words(s, dict, i) {
    return s.split(/\s+/).filter(Boolean).map((w) => piece(w, dict, i)).join(" ").replace(/\s+([,;:])/g, "$1");
  }
  const idx = (lang) => (lang === "ru" ? 1 : 0);

  // Translations made for this project (data/names_i18n.json, produced by an AI and spot-checked): {names: {ka: {en, ru}}, streets: {ka: {en, ru}}}
  let DICT = { names: {}, streets: {} };
  let STREETS = [];
  function setDict(d) {
    DICT = { names: (d && d.names) || {}, streets: (d && d.streets) || {} };
    STREETS = Object.keys(DICT.streets).sort((a, b) => b.length - a.length);
  }
  // Name for the interface language: Wikipedia title > whole-name dictionary > AI translation of the project > the Georgian original.
  // Word-by-word transliteration is NOT used for names: it produces unreadable pseudo-words. src: "wiki" | "dict" | "ai" | "orig".
  // wp: "ka:title|en:title|ru:title" (Wikipedia titles of the object, when matched)
  function nameInfo(ka, lang, wp) {
    if (lang !== "en" && lang !== "ru") return { text: ka, src: "orig" };
    const i = idx(lang);
    if (wp) {
      const m = String(wp).split("|").map((x) => x.split(/:(.+)/)).find((x) => x[0] === lang);
      if (m && m[1]) return { text: m[1].replace(/\s*\(.*?\)\s*$/, ""), src: "wiki" };
    }
    const s = (ka || "").trim();
    if (NAMES[s]) return { text: NAMES[s][i], src: "dict" };
    const d = DICT.names[s];
    if (d && d[lang]) return { text: d[lang], src: "ai" };
    return { text: ka, src: "orig" };
  }
  const name = (ka, lang, wp) => nameInfo(ka, lang, wp).text;
  // Address: known street names come from the project's translations; type words are translated and the rest of an unknown street
  // name is transliterated (this is how addresses are usually written on maps).
  function address(ka, lang) {
    if (lang !== "en" && lang !== "ru") return ka;
    if (!ka) return ka;
    const i = idx(lang);
    const hold = [];
    let s = ka;
    for (const ph of STREETS) {
      const tr = DICT.streets[ph][lang];
      if (tr && s.includes(ph)) { s = s.split(ph).join("\u0001" + hold.length + "\u0001"); hold.push(tr); }
    }
    s = s.split(/(\/)/).map((part) => (part === "/" ? part : words(part.replace(/\.(?=[ა-ჿ])/g, ". "), ADDR, i))).join("").replace(/\s+/g, " ").replace(/\.\s+(?=\d)/g, ".");
    return s.replace(/\u0001(\d+)\u0001/g, (m, k) => hold[+k]).replace(/\s*\/\s*$/, "");
  }
  // "date in register" is a templated Georgian phrase: century + part of it, sometimes a year
  const ROM = [[10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]];
  function roman(n) { let r = ""; for (const [v, s] of ROM) while (n >= v) { r += s; n -= v; } return r; }
  function ord(n) { const v = n % 100; return n + (["th", "st", "nd", "rd"][(v - 20) % 10] || ["th", "st", "nd", "rd"][v] || "th"); }
  const GE = "[\u10d0-\u10ff]";
  function dateSeg(seg, i) {
    let t = seg.trim();
    if (!t) return "";
    if (/^ადრე შუასაუკუნეები/.test(t)) return i ? "раннее Средневековье" : "Early Middle Ages";
    if (/^შუა საუკუნეები/.test(t)) return i ? "Средние века" : "Middle Ages";
    const parts = [];
    const cm = t.match(new RegExp("(\\d{1,2})(?:-ე)?\\s*(?:საუკუნ|ს-ის|ს\\.|ს(?!" + GE + "))"));
    if (cm) {
      const n = +cm[1];
      const part = /დასაწყის/.test(t) ? "b" : /დასასრულ|მიწურულ/.test(t) ? "e" : /მეორე ნახევარ/.test(t) ? "h2" : /პირველი ნახევარ/.test(t) ? "h1" : /შუა/.test(t) ? "m" : "";
      if (i) {
        const c = roman(n) + " века";
        parts.push({ b: "начало " + c, e: "конец " + c, m: "середина " + c, h1: "первая половина " + c, h2: "вторая половина " + c, "": roman(n) + " век" }[part]);
      } else {
        const c = ord(n) + " century";
        parts.push({ b: "beginning of the " + c, e: "end of the " + c, m: "mid-" + c, h1: "first half of the " + c, h2: "second half of the " + c, "": c }[part]);
      }
    }
    const dec = t.match(/(\d{3,4})-იანი/);
    if (dec) parts.push(i ? dec[1] + "-е годы" : dec[1] + "s");
    else for (const y of t.match(/(?<!\d)\d{3,4}(?!\d)(?:-\d{3,4})?/g) || []) parts.push(y);
    return parts.length ? parts.join(", ") : null;
  }
  function date(raw, lang) {
    if (lang !== "en" && lang !== "ru") return raw;
    if (!raw || !GEO.test(raw)) return raw;
    const i = idx(lang);
    const segs = raw.split(/[;/]/).map((x) => dateSeg(x, i));
    if (segs.some((x) => x === null)) return raw;               // anything not recognised: keep the register text
    return segs.filter(Boolean).join("; ");
  }
  window.GeoTr = { name, nameInfo, address, date, setDict };
})();
