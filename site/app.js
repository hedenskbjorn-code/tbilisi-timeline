(() => {
  "use strict";
  // The timeline starts at the earliest written evidence of the fortress (about 364, see "About"); the long early period is
  // compressed: slider units 0..1000 map piecewise-linearly to years (364-1000 -> 0-90, 1000-1700 -> 90-200, 1700-2025 -> 200-1000)
  const MIN = 364, MAX = 2025, NEW_YEARS = 25;
  const KNOTS = [[364, 0], [1000, 90], [1700, 200], [2025, 1000]];
  const y2v = (y) => { for (let i = 1; i < KNOTS.length; i++) if (y <= KNOTS[i][0]) { const [y0, v0] = KNOTS[i - 1], [y1, v1] = KNOTS[i]; return v0 + ((y - y0) / (y1 - y0)) * (v1 - v0); } return 1000; };
  const v2y = (v) => { for (let i = 1; i < KNOTS.length; i++) if (v <= KNOTS[i][1]) { const [y0, v0] = KNOTS[i - 1], [y1, v1] = KNOTS[i]; return Math.round(y0 + ((v - v0) / (v1 - v0)) * (y1 - y0)); } return MAX; };
  const PLAN_AFTER = 10; // the last plan is shown at most this many years after its date
  const COARSE = new Set(["century", "half", "mixed"]);

  const T = {
    ru: {
      title: "Тбилиси во времени",
      showPlan: "Старый план на карте", planOpacity: "Прозрачность плана",
      showBnd: "Границы застройки по годам", showAdmin: "Современная административная граница (2019, для сравнения)", showDistricts: "Районы и их названия", oldAdmin: "Старая граница (1973–2005): по положению посёлков согласуется с границей до реформы 2006 года (≈330 км² против 354 км² по диссертации; дата набора данных не подтверждена)", distNone: "Для этого времени сведений о делении на районы в проекте нет.", distNote: "Названия и периоды пересказаны ИИ по вторичным источникам, не проверены по первоисточникам; границ прошлых районов в открытых данных не найдено.", distTitle: (lbl) => `Районы: ${lbl}`, distMod: "ныне", showFilter: "Показывать объекты реестра", showNat: "национального значения", showMon: "памятники", showObj: "объекты культурного наследия",
      legNew: "Построено за последние 25 лет", legOld: "Построено раньше", legNat: "Национального значения",
      legCoarse: "Точная дата неизвестна (век, половина века)",
      count: (n, y) => `${n} объектов к ${y} году`,
      noPlan: (first, last, y) => y < first ? `Планов этого времени пока нет (первый — ${first}).` : `Для этого периода плана пока нет (последний — ${last}). Фон — современная карта.`,
      plan: (y, m) => `План ${y} года, точность привязки ≈ ${m} м`,
      bnd: (y) => `Граница застройки по плану ${y} (по глазу, приблизительно)`,
      bndPartial: (y) => `Граница города по плану ${y}: нанесены только уверенно видимые участки (север и восток), запад и юг не нанесены`,
      noBnd: (y) => `Границы по плану ${y} года ещё не нанесены.`,
      area: (km, y, src) => `Территория города ≈ ${km} км² (данные на ${y}; ${src === "sec" ? "вторичный источник, не проверено по оригиналу" : "Харебава 2024"})`,
      note: (undated) => `Даты объектов — по записям реестра; для диапазона дат (четверть века, век и т. д.) на шкале берётся конец диапазона, то есть «не позже». ${undated} объектов без даты не показаны. Фоновая карта — OpenFreeMap / OpenStreetMap.`,
      name: "Название", address: "Адрес", cls: "Тип", date: "Дата в реестре", est: "На шкале с года", range: "диапазон", prec: "точность",
      reg: "Реестр №", photo: "Фото рядом с точкой (может показывать соседнее здание)", photoBy: "Фото", unc: "Положение на карте приблизительное", national: "национального значения", object: "объект культурного наследия", monument: "памятник",
      precision: { exact: "год", quarter: "четверть века", middle: "середина века", half: "половина века", century: "век", mixed: "смешанная", years: "годы", unknown: "—" },
      src: { ExactDate: "поле «точная дата»", Period: "поле «период»", DateRange: "диапазон дат" },
      classes: { architecture: "архитектура", archaeology: "археология", ethnography: "этнография", memorial: "мемориальный", urban: "градостроительство",
                 monumental_art: "монументальное искусство", garden: "садово-парковое", science: "наука", engineering: "инженерное", other: "другое" },
      aboutTitle: "О проекте и источниках",
      about: [
        "Некоммерческий хобби-проект на открытых данных. Даты, границы и привязка планов — приблизительные оценки, а не официальные сведения.",
        "Объекты: публичные сведения реестра недвижимых памятников культурного наследия Грузии (Национальное агентство по сохранению культурного наследия). Письменной открытой лицензии на эти данные найти не удалось; в некоммерческих целях используется сокращённая выборка (название, адрес, координаты, даты, номер). Даты — оценка по записям реестра.",
        "Планы Тифлиса 1735 (Вахушти, схематичный), 1785 (Пищевич), 1800 (Чуйко), 1821 (Швецов), 1844 (Военно-топографическое депо), 1850 (Генеральный штаб), 1887 (А. Ильин) 1911 (топографический лист окрестностей) и 1913 (землемерный отдел городской управы): сканы Wikimedia Commons, общественное достояние. Планы привязаны к современной карте по контрольным точкам (точность около 50 м, у плана 1735 года около 150 м), границы застройки обведены по ним вручную.",
        "Исторические виды Тифлиса (1578–1910-е): миниатюра «Нусрет-наме» (British Library), гравюры по рисункам Шардена и Турнефора, картины Чернецова, Лермонтова, Франкена и Айвазовского, фотографии Ермакова и Прокудина-Горского; файлы Wikimedia Commons, общественное достояние; уменьшенные копии. Это рисунки и снимки с одной точки, к карте они не привязаны.",
        "Приватность: страница не использует cookie и аналитику; в браузере хранится только выбранный язык. При открытии браузер обращается к tiles.openfreemap.org (подложка карты) и к wikimedia.org (превью фотографий), поэтому им виден адрес посетителя. Форма обратной связи через GitHub создаёт публичный Issue.",
        "Плотность застройки: доля площади, занятая контурами зданий OpenStreetMap (© участники OpenStreetMap, ODbL), в ячейках около 100×100 м; это состояние на момент выгрузки (ноябрь 2026), у зданий в OSM нет годов постройки, поэтому слой показывается только для современных лет.",
        "Административная граница Тбилиси (2019): OCHA COD-AB Georgia (HDX), источник — Национальная статистическая служба Грузии, лицензия CC BY-IGO. Площадь 502,5 км² совпадает с данными диссертации для периода после 2006 года.",
        "Границы районов и их названия: © участники OpenStreetMap, лицензия ODbL (этот набор данных — производная база; при повторном использовании сохраняйте ту же лицензию и атрибуцию). Показано современное деление на 10 районов.",
        "Серая пунктирная линия 1973–2005 годов — граница из geoBoundaries (ADM2, метаданные: 2007). Проверка по положению посёлков: присоединённые в 2006 году (Цхнети, Цавкиси, Окрокана, Кикети, Бетания, Диди Дигоми, Загэси) лежат вне неё, присоединённые раньше (Поничала, Орхеви, Глдани, Варкетили) внутри, то есть она соответствует границе до реформы 2006 года. Её площадь ≈ 330 км² меньше 354 км² из диссертации, причина не установлена. Деление на районы и их названия по периодам (без границ) пересказаны ИИ по вторичным источникам и не проверены по первоисточникам.",
        "Площадь города: Н. Харебава, диссертация, Тбилисский государственный университет им. Ив. Джавахишвили, 2024.",
        "Фото: Wikimedia Commons, с указанием автора и лицензии; подбираются по координатам и могут показывать соседнее здание.",
        "Шкала времени начинается с IV века: по общим обзорам (Википедия, не проверено по первоисточникам), самые ранние письменные сведения о крепости на месте города относятся к середине–второй половине IV века (около 364 г.), а традиционная дата основания города по грузинским летописям — 458 г. (Вахтанг Горгасали). До 1700 года шкала сжата, до 1735 года планов и границ нет, показаны только объекты реестра.",
        "Утраченные здания: список составлен ИИ (Gemini) по Wikidata, Википедии (ka, ru, en) и легендам исторических планов; даты и положение приблизительны, значок показывает, найден ли год утраты на странице источника. Не является официальным реестром.",
        "Границы застройки с 1972 года: GUSV — Mapping of 30 m global urban boundaries from 1972 to 2021 (Zenodo, doi:10.5281/zenodo.14523232), лицензия CC BY 4.0; сглажены и упрощены проектом. Контур 1954 года: заливка застройки на листе NK 38-8 Army Map Service (США, 1:250 000), общественное достояние; положение приблизительное.",
        "Фоновая карта: OpenFreeMap, © OpenMapTiles, данные © участники OpenStreetMap. Библиотека карты: MapLibre GL JS.",
      ],
      urbanNone: (first) => `Границ застройки для этого времени пока нет (первая — ${first}).`,
      urbanLine: (snap, src, partial, y, acc) => `Граница застройки на ${snap} год${snap !== y ? " (ближайшая к " + y + " году)" : ""}: ${src}${partial ? ". Показаны только уверенно видимые участки (север и восток)" : ""}${acc ? ". Положение может отличаться на ~" + acc + " м" : ""}`,
      urbanSrc: { ams: "заливка застройки на американской карте 1954 г. (1:250 000, по съёмкам 1920–40-х, показывает состояние примерно 1940-х), приблизительно", traced: "обводка по старому плану, вручную, приблизительно", gusv: "спутниковая оценка (GUSV, Landsat): сглаженная огибающая застройки, не административная граница" },
      showSettle: "Посёлки, вошедшие в состав города",
      settleJoined: (y, from, geomNote) => `Включён в состав города: ${y} г.${from ? " (из " + from + ")" : ""}`,
      settleUnknown: "Год включения в проекте не указан",
      settleSrc: "Год и основание пересказаны ИИ по вторичным источникам (Какурия 1979, БСЭ, постановление парламента 2006), не проверены по первоисточникам.",
      settleGeom: { inside_old: "По положению лежит внутри границы города до 2006 года.", outside_old_inside_2019: "По положению лежит вне границы до 2006 года и внутри современной: это согласуется с присоединением в 2006 году.", outside_2019: "Лежит вне современной границы города." },
      settleFrom: { Gardabani: "Гардабанского района", Mtskheta: "Мцхетского района" },
      settleNow: (y, inCity) => `В ${y} году: ${inCity === null ? "год включения неизвестен" : inCity ? "входит в состав города (административно; это не значит, что он застроен)" : "ещё не входил в состав города"}`,
      settleConflict: "⚠ Положение противоречит году: лежит вне границы до 2006 года (либо год в пересказе неверен, либо граница набора данных не охватывает это село).",
      legRuin: "Руины или остатки (по названию в реестре)", ruinRow: "Состояние", ruinTxt: "руины, остатки или место объекта (по названию в реестре)",
      legTitle: "Легенда", legObjects: "Объекты реестра (точки)", legBounds: "Линии и области", legNames: "Подписи",
      legFill: "Область застройки/территории города на выбранный год (заливка с обводкой)",
      legSat: "Сплошная линия: спутниковая оценка застройки (с 1972 года)",
      legTraced: "Пунктир: обводка вручную по старому плану или карте",
      legAdmin: "Тёмный пунктир: современная административная граница (2019)",
      legOldAdmin: "Серый пунктир: граница до 2006 года (1973–2005)",
      legDistLine: "Тонкая линия: границы современных районов",
      legPlan: "Старый план (если включён «Старый план на карте»)",
      legDistName: "Название района (современные)",
      legSetBefore: "Посёлок: ещё не включён в город",
      legSetAfter: "Посёлок: уже включён в город",
      legSetUnk: "Посёлок: год включения неизвестен",
      legSetName: "Название посёлка (клик по точке: когда и откуда включён)",
      fbBtn: "Сообщить об ошибке", fbTitle: "Сообщить об ошибке или недочёте",
      fbHint: "Опишите, что неверно или чего не хватает. Страница ничего не отправляет сама: сообщение откроется как обращение (issue) в репозитории проекта на GitHub (нужен аккаунт GitHub), либо уйдёт через форму, если она подключена.",
      fbType: "Что не так", fbK1: "Ошибка в данных объекта (название, дата, адрес, положение)", fbK2: "Старый план лежит не там (привязка)", fbK3: "Граница города или застройки", fbK4: "Ошибка в переводе или названии", fbK5: "Вопрос по правам, прошу убрать данные", fbK6: "Другое",
      fbText: "Описание", fbCtx: "Контекст (подставляется автоматически)", fbContact: "Как с вами связаться (по желанию)", fbSend: "Отправить", fbCancel: "Отмена",
      fbSent: "Спасибо! Обращение отправлено.", fbOpened: "Открыто окно GitHub: подтвердите отправку обращения там.", fbPopup: "Сообщить об ошибке по этому объекту",
      showLost: "Утраченные здания (снесены или разрушены)", showGhost: "показывать и после утраты (бледно)",
      legLostOn: "Утраченное здание: ещё стоит в этот год", legLostUnc: "Утраченное: год постройки или сноса неточен", legLostOff: "Утраченное: уже снесено (бледный «призрак»)",
      lostKinds: { church: "церковь", cathedral: "собор", mosque: "мечеть", synagogue: "синагога", caravanserai: "караван-сарай", theatre: "театр", gate: "ворота", wall: "стена", tower: "башня", bridge: "мост", station: "вокзал", barracks: "казармы/замок", palace: "дворец", house: "дом", other: "другое" },
      lostWhy: { demolished: "снесён", destroyed: "разрушен", rebuilt: "перестроен", flooded: "затоплен", unknown: "причина неизвестна" },
      lostBuilt: "Построен", lostLost: "Утрачен", lostRepl: "Сейчас на месте", lostState: { stand: "в этот год ещё стоит", unc: "в этот год мог уже быть снесён (дата утраты неточна)", gone: "в этот год уже утрачен", early: "в этот год мог ещё не существовать (дата постройки неточна)" },
      lostAcc: (m, pos) => `Положение ${pos === "plan" ? "снято с исторического плана" : "по координатам из источника"}, погрешность ≈ ${m} м`,
      lostChk: "Год утраты найден на странице источника (слабая проверка)", lostNoChk: "Год утраты на странице источника не найден автоматически",
      lostSrc: "Список составлен ИИ по Wikidata, Википедии и легендам планов; не является официальным.", lostSources: "Источники",
      showWater: "Тбилисское море и озёра (исторические)",
      legWater: "Тбилисское море (водохранилище, с 1951–1953)", legLake: "Солёные озёра до водохранилища (по топографическому листу ок. 1911 г.)",
      waterRes: "Тбилисское море (Тбилисское водохранилище)", waterLake: "Солёное озеро (на месте или рядом с будущим Тбилисским морем)",
      waterTxtRes: (y) => y < 1951 ? "В этот год моря ещё не было: на месте залитой позже долины были солёные озёра (серая заливка показывает будущую акваторию)." : y < 1953 ? "Водохранилище заполнялось: источники расходятся в дате открытия (1951 или 1953)." : "Водохранилище существует (контур по OpenStreetMap; площадь по литературе 11,2–11,6 км²).",
      waterTxtLake: (y) => y < 1953 ? "Озеро обведено по топографическому листу окрестностей Тифлиса около 1911 г. (1:42 000); как выглядели озёра раньше и как менялись до 1951 г., не проверено. Положение около ±70 м." : "К этому году озёра затоплены водохранилищем.",
      waterSrc: "Источники: OpenStreetMap (контур моря, ODbL); лист NK 38-8 Army Map Service (озёра).",
      viewsTitle: "Исторические виды (рисунки, не планы)",
      viewClose: "Закрыть",
      viewLicense: "лицензия",
      viewSource: "источник",
      trNote: "Название и улицы переведены автоматически (ИИ) с грузинского оригинала из реестра и могут быть неточными.",
      trOrig: "оригинал",
      fbContactWarn: "Внимание: при отправке через GitHub контакт попадёт в публичный Issue и будет виден всем. Не указывайте то, что не хотите публиковать.",
      infoBtn: "Источники и подробности",
      infoTitle: "Источники и подробности",
      infoRegister: "Данные объекта: публичные сведения реестра недвижимых памятников культурного наследия Грузии (Национальное агентство сохранения культурного наследия), сокращённая выжимка для некоммерческого использования. Условия и полный список источников: «О проекте и источниках» на боковой панели.",
      infoPhotos: "Фотографии",
      showDensity: "Плотность застройки (OSM, сейчас)",
      legDensity: "Плотность застройки по зданиям OSM (с 2015): светлее — реже, тёмно-красный — очень плотно",
      typesTitle: "Назначение (сейчас — по названию, иначе по реестру)", func: "Современное назначение (по названию)", func0: "Первоначальное назначение (по реестру)", wiki: "Статья в Википедии",
      types: { residential: "Жилые дома", religious: "Религиозные", defense: "Оборонительные", culture: "Образование, наука, культура",
               public: "Общественные и торговые", transport: "Транспорт и инженерия", memorial: "Мемориалы и парки", rural: "Археология и сельское", other: "Прочие" },
    },
    en: {
      title: "Tbilisi through time",
      showPlan: "Old plan on the map", planOpacity: "Plan opacity",
      showBnd: "Built-up outlines by year", showAdmin: "Current administrative boundary (2019, for comparison)", showDistricts: "Districts and their names", oldAdmin: "Older boundary (1973–2005): by the position of settlements it matches the pre-2006 limit (≈330 km² versus 354 km² in the thesis; dataset date not confirmed)", distNone: "The project has no information on the district division for this period.", distNote: "Names and periods were relayed by an AI from secondary sources and are not checked against the originals; boundaries of past districts were not found in open data.", distTitle: (lbl) => `Districts: ${lbl}`, distMod: "now", showFilter: "Show register objects", showNat: "of national significance", showMon: "monuments", showObj: "cultural heritage objects",
      legNew: "Built in the last 25 years", legOld: "Built earlier", legNat: "National significance",
      legCoarse: "Exact date unknown (century, half-century)",
      count: (n, y) => `${n} objects by ${y}`,
      noPlan: (first, last, y) => y < first ? `No plan for this period yet (the first is ${first}).` : `No plan for this period yet (the last is ${last}). Background: modern map.`,
      plan: (y, m) => `Plan of ${y}, registration accuracy ≈ ${m} m`,
      bnd: (y) => `Built-up boundary from the ${y} plan (traced by eye, approximate)`,
      bndPartial: (y) => `City limit from the ${y} plan: only the clearly visible stretches (north and east) are traced; west and south are not`,
      noBnd: (y) => `The boundary on the ${y} plan has not been traced yet.`,
      area: (km, y, src) => `City territory ≈ ${km} km² (data for ${y}; ${src === "sec" ? "secondary source, not checked against the original" : "Kharebava 2024"})`,
      note: (undated) => `Object dates come from register entries; for a date range (quarter-century, century, etc.) the end of the range is used on the timeline, i.e. "not later than". ${undated} undated objects are not shown. Base map: OpenFreeMap / OpenStreetMap.`,
      name: "Name", address: "Address", cls: "Type", date: "Date in register", est: "Shown on the timeline from", range: "range", prec: "precision",
      reg: "Register no.", photo: "Photo near this point (may show a neighbouring building)", photoBy: "Photo", unc: "Map position is approximate", national: "national significance", object: "cultural heritage object", monument: "monument",
      precision: { exact: "year", quarter: "quarter-century", middle: "mid-century", half: "half-century", century: "century", mixed: "mixed", years: "years", unknown: "—" },
      src: { ExactDate: "“exact date” field", Period: "“period” field", DateRange: "date range" },
      classes: { architecture: "architecture", archaeology: "archaeology", ethnography: "ethnography", memorial: "memorial", urban: "urban planning",
                 monumental_art: "monumental art", garden: "garden / landscape", science: "science", engineering: "engineering", other: "other" },
      aboutTitle: "About and sources",
      about: [
        "A non-commercial hobby project built on open data. Dates, boundaries and plan registration are approximations, not official information.",
        "Objects: public information from the register of immovable cultural heritage of Georgia (National Agency for Cultural Heritage Preservation). No written open licence for this data could be found; a reduced extract (name, address, coordinates, dates, number) is used for non-commercial purposes. Dates are estimated from register records.",
        "Plans of Tiflis, 1735 (Vakhushti, schematic), 1785 (Pishchevich), 1800 (Chuiko), 1821 (Shvetsov), 1844 (Military Topographic Depot), 1850 (General Staff), 1887 (A. Ilyin) 1911 (topographic sheet of the environs) and 1913 (city survey department): scans from Wikimedia Commons, public domain. The plans are registered to the modern map with control points (accuracy about 50 m, about 150 m for 1735) and the built-up outlines are traced by hand from them.",
        "Historical views of Tiflis (1578 to the 1910s): a miniature from the Nusretname (British Library), engravings after drawings by Chardin and Tournefort, paintings by Chernetsov, Lermontov, Franken and Aivazovsky, photographs by Yermakov and Prokudin-Gorsky; Wikimedia Commons files, public domain; reduced copies. They are drawings and photographs from a single viewpoint and are not tied to the map.",
        "Privacy: the page uses no cookies or analytics; only the chosen language is stored in the browser. On loading, the browser contacts tiles.openfreemap.org (basemap) and wikimedia.org (photo previews), so these services can see the visitor's address. The feedback form through GitHub creates a public Issue.",
        "Building density: the share of ground covered by OpenStreetMap building footprints (© OpenStreetMap contributors, ODbL) in cells of about 100×100 m; it shows the state at the time of export (November 2026); OSM buildings have no construction years, so the layer is shown only for recent years.",
        "Administrative boundary of Tbilisi (2019): OCHA COD-AB Georgia (HDX), source: National Statistics Office of Georgia, licence CC BY-IGO. Its area of 502.5 km² matches the thesis figure for the period after 2006.",
        "District boundaries and names: © OpenStreetMap contributors, ODbL (this dataset is a derived database; keep the same licence and attribution if you reuse it). The current division into 10 districts is shown.",
        "The grey dashed line for 1973–2005 is a boundary from geoBoundaries (ADM2, metadata: 2007). Checked by the position of settlements: those annexed in 2006 (Tskneti, Tsavkisi, Okrokana, Kiketi, Betania, Didi Dighomi, Zahesi) lie outside it, those annexed earlier (Ponichala, Orkhevi, Gldani, Varketili) inside, so it matches the pre-2006 limit. Its area of about 330 km² is smaller than the 354 km² in the thesis, the reason is not established. The district divisions and names by period (without boundaries) were relayed by an AI from secondary sources and are not checked against the originals.",
        "City area: N. Kharebava, PhD thesis, Ivane Javakhishvili Tbilisi State University, 2024.",
        "Photos: Wikimedia Commons, shown with author and licence; matched by coordinates and may show a neighbouring building.",
        "The timeline starts in the 4th century: according to general surveys (Wikipedia, not checked against the primary sources), the earliest written evidence of a fortress at the site dates to the mid to late 4th century (about 364), and the traditional date of the city’s foundation in the Georgian chronicles is 458 (Vakhtang Gorgasali). The scale is compressed before 1700; there are no plans or outlines before 1735, only register objects are shown.",
        "Lost buildings: the list was compiled by an AI (Gemini) from Wikidata, Wikipedia (ka, ru, en) and the legends of historical plans; dates and positions are approximate, and the popup says whether the year of loss was found on a source page. It is not an official register.",
        "Built-up outlines since 1972: GUSV — Mapping of 30 m global urban boundaries from 1972 to 2021 (Zenodo, doi:10.5281/zenodo.14523232), licence CC BY 4.0; smoothed and simplified by the project. The 1954 outline: built-up fill on sheet NK 38-8 of the U.S. Army Map Service (1:250 000), public domain; position is approximate.",
        "Base map: OpenFreeMap, © OpenMapTiles, data © OpenStreetMap contributors. Map library: MapLibre GL JS.",
      ],
      urbanNone: (first) => `No built-up outline for this period yet (the first is ${first}).`,
      urbanLine: (snap, src, partial, y, acc) => `Built-up outline for ${snap}${snap !== y ? " (nearest to " + y + ")" : ""}: ${src}${partial ? ". Only the clearly visible stretches (north and east) are shown" : ""}${acc ? ". Position may be off by ~" + acc + " m" : ""}`,
      urbanSrc: { ams: "built-up fill on the American 1954 map (1:250 000, from 1920s-40s surveys, showing about the 1940s), approximate", traced: "traced by hand from an old plan, approximate", gusv: "satellite estimate (GUSV, Landsat): a smoothed envelope of built-up land, not an administrative boundary" },
      showSettle: "Settlements annexed to the city",
      settleJoined: (y, from, geomNote) => `Annexed to the city: ${y}${from ? " (from " + from + ")" : ""}`,
      settleUnknown: "The year of annexation is not given in the project",
      settleSrc: "The year and the basis were relayed by an AI from secondary sources (Kakuria 1979, Great Soviet Encyclopedia, 2006 parliament resolution) and are not checked against the originals.",
      settleGeom: { inside_old: "Its position is inside the pre-2006 city limit.", outside_old_inside_2019: "Its position is outside the pre-2006 limit and inside the current one: consistent with annexation in 2006.", outside_2019: "It lies outside the current city limit." },
      settleFrom: { Gardabani: "Gardabani district", Mtskheta: "Mtskheta district" },
      settleNow: (y, inCity) => `In ${y}: ${inCity === null ? "year of annexation unknown" : inCity ? "part of the city administratively (this does not mean it is built up)" : "not yet part of the city"}`,
      settleConflict: "⚠ The position contradicts the year: it lies outside the pre-2006 limit (either the year in the report is wrong, or the dataset boundary does not include this village).",
      legRuin: "Ruins or remains (by the register name)", ruinRow: "Condition", ruinTxt: "ruins, remains or site of an object (by the register name)",
      legTitle: "Legend", legObjects: "Register objects (dots)", legBounds: "Lines and areas", legNames: "Labels",
      legFill: "Built-up area / city territory for the selected year (fill with outline)",
      legSat: "Solid line: satellite estimate of built-up land (from 1972)",
      legTraced: "Dashed: traced by hand from an old plan or map",
      legAdmin: "Dark dashed: current administrative boundary (2019)",
      legOldAdmin: "Grey dashed: boundary before 2006 (1973–2005)",
      legDistLine: "Thin line: boundaries of the current districts",
      legPlan: "Old plan (when “Old plan on the map” is on)",
      legDistName: "District name (current)",
      legSetBefore: "Settlement: not yet part of the city",
      legSetAfter: "Settlement: already part of the city",
      legSetUnk: "Settlement: year of annexation unknown",
      legSetName: "Settlement name (click the dot: when and from where annexed)",
      fbBtn: "Report a problem", fbTitle: "Report an error or a shortcoming",
      fbHint: "Describe what is wrong or missing. The page sends nothing by itself: your message opens as an issue in the project's GitHub repository (a GitHub account is needed), or goes through a form if one is connected.",
      fbType: "What is wrong", fbK1: "Error in an object's data (name, date, address, position)", fbK2: "An old plan is misplaced (registration)", fbK3: "City or built-up boundary", fbK4: "Error in a translation or a name", fbK5: "Rights question, please remove data", fbK6: "Other",
      fbText: "Description", fbCtx: "Context (filled in automatically)", fbContact: "How to reach you (optional)", fbSend: "Send", fbCancel: "Cancel",
      fbSent: "Thank you! The report was sent.", fbOpened: "A GitHub window was opened: confirm sending the issue there.", fbPopup: "Report a problem with this object",
      showLost: "Lost buildings (demolished or destroyed)", showGhost: "also show after the loss (faint)",
      legLostOn: "Lost building: still standing in this year", legLostUnc: "Lost: date of construction or loss is imprecise", legLostOff: "Lost: already gone (faint “ghost”)",
      lostKinds: { church: "church", cathedral: "cathedral", mosque: "mosque", synagogue: "synagogue", caravanserai: "caravanserai", theatre: "theatre", gate: "gate", wall: "wall", tower: "tower", bridge: "bridge", station: "station", barracks: "barracks/castle", palace: "palace", house: "house", other: "other" },
      lostWhy: { demolished: "demolished", destroyed: "destroyed", rebuilt: "rebuilt", flooded: "flooded", unknown: "reason unknown" },
      lostBuilt: "Built", lostLost: "Lost", lostRepl: "Now on the site", lostState: { stand: "still standing in this year", unc: "may already have been demolished in this year (loss date imprecise)", gone: "already lost in this year", early: "may not yet have existed in this year (construction date imprecise)" },
      lostAcc: (m, pos) => `Position ${pos === "plan" ? "read from a historical plan" : "from a source coordinate"}, error ≈ ${m} m`,
      lostChk: "The year of loss was found on a cited source page (weak check)", lostNoChk: "The year of loss was not found automatically on the cited pages",
      lostSrc: "The list was compiled by an AI from Wikidata, Wikipedia and plan legends; it is not official.", lostSources: "Sources",
      showWater: "Tbilisi Sea and lakes (historical)",
      legWater: "Tbilisi Sea (reservoir, from 1951–1953)", legLake: "Salt lakes before the reservoir (from the topographic sheet of c.1911)",
      waterRes: "Tbilisi Sea (Tbilisi Reservoir)", waterLake: "Salt lake (on or next to the site of the future Tbilisi Sea)",
      waterTxtRes: (y) => y < 1951 ? "The sea did not exist in this year: the valley flooded later held salt lakes (the grey fill marks the future water surface)." : y < 1953 ? "The reservoir was being filled: sources disagree on the opening date (1951 or 1953)." : "The reservoir exists (outline from OpenStreetMap; the literature gives 11.2–11.6 km²).",
      waterTxtLake: (y) => y < 1953 ? "The lake is outlined from the topographic sheet of the Tiflis environs of about 1911 (1:42,000); how the lakes looked earlier, and how they changed before 1951, has not been checked. Position about ±70 m." : "By this year the lakes were flooded by the reservoir.",
      waterSrc: "Sources: OpenStreetMap (outline of the sea, ODbL); topographic sheet of c.1911 (lakes).",
      viewsTitle: "Historical views (drawings, not plans)",
      viewClose: "Close",
      viewLicense: "licence",
      viewSource: "source",
      trNote: "The name and streets were translated automatically (AI) from the Georgian original in the register and may be inexact.",
      trOrig: "original",
      fbContactWarn: "Note: when sent through GitHub, the contact goes into a public Issue and is visible to everyone. Leave it empty if you do not want that.",
      infoBtn: "Sources and details",
      infoTitle: "Sources and details",
      infoRegister: "Object data: public records of the register of immovable cultural heritage monuments of Georgia (National Agency for Cultural Heritage Preservation), a reduced extract for non-commercial use. Terms and the full list of sources: “About and sources” in the side panel.",
      infoPhotos: "Photographs",
      showDensity: "Building density (OSM, today)",
      legDensity: "Building density from OSM footprints (from 2015): lighter is sparser, dark red is very dense",
      typesTitle: "Use (today — by name, otherwise per register)", func: "Present-day use (by name)", func0: "Original function (per register)", wiki: "Wikipedia article",
      types: { residential: "Residential houses", religious: "Religious", defense: "Defensive", culture: "Education, science, culture",
               public: "Public and commercial", transport: "Transport and engineering", memorial: "Memorials and parks", rural: "Archaeology and rural", other: "Other" },
    },
    ka: {
      title: "თბილისი დროში",
      showPlan: "ძველი გეგმა რუკაზე", planOpacity: "გეგმის გამჭვირვალობა",
      showBnd: "განაშენიანების საზღვრები წლების მიხედვით", showAdmin: "თანამედროვე ადმინისტრაციული საზღვარი (2019, შესადარებლად)", showDistricts: "რაიონები და მათი სახელები", oldAdmin: "ძველი საზღვარი (1973–2005): დასახლებების მდებარეობით ემთხვევა 2006 წლამდე არსებულ საზღვარს (≈330 კმ², დისერტაციაში 354 კმ²; ნაკრების თარიღი დადასტურებული არ არის)", distNone: "ამ პერიოდისთვის რაიონული დაყოფის შესახებ ინფორმაცია პროექტში არ არის.", distNote: "სახელები და პერიოდები გადმოცემულია ხელოვნური ინტელექტის მიერ მეორადი წყაროებიდან და ორიგინალებთან შემოწმებული არ არის; წარსულის რაიონების საზღვრები ღია მონაცემებში ვერ მოიძებნა.", distTitle: (lbl) => `რაიონები: ${lbl}`, distMod: "დღეს", showFilter: "რეესტრის ობიექტების ჩვენება", showNat: "ეროვნული მნიშვნელობის", showMon: "ძეგლები", showObj: "კულტურული მემკვიდრეობის ობიექტები",
      legNew: "აშენებულია ბოლო 25 წლის განმავლობაში", legOld: "აშენებულია უფრო ადრე", legNat: "ეროვნული მნიშვნელობის",
      legCoarse: "ზუსტი თარიღი უცნობია (საუკუნე, საუკუნის ნახევარი)",
      count: (n, y) => `${n} ობიექტი ${y} წლისთვის`,
      noPlan: (first, last, y) => y < first ? `ამ პერიოდის გეგმა ჯერ არ არის (პირველი — ${first}).` : `ამ პერიოდისთვის გეგმა ჯერ არ არის (ბოლო — ${last}). ფონი — თანამედროვე რუკა.`,
      plan: (y, m) => `${y} წლის გეგმა, მიბმის სიზუსტე ≈ ${m} მ`,
      bnd: (y) => `ქალაქის განაშენიანების საზღვარი ${y} წლის გეგმით (თვალით, მიახლოებით)`,
      bndPartial: (y) => `ქალაქის საზღვარი ${y} წლის გეგმით: დატანილია მხოლოდ კარგად ხილული მონაკვეთები (ჩრდილოეთი და აღმოსავლეთი), დასავლეთი და სამხრეთი არ არის დატანილი`,
      noBnd: (y) => `${y} წლის გეგმის საზღვარი ჯერ არ არის დატანილი.`,
      area: (km, y, src) => `ქალაქის ტერიტორია ≈ ${km} კმ² (${y} წლის მონაცემი; ${src === "sec" ? "მეორადი წყარო, ორიგინალთან არ არის შემოწმებული" : "ხარებავა 2024"})`,
      note: (undated) => `ობიექტების თარიღები რეესტრის ჩანაწერებიდანაა; თარიღთა დიაპაზონისთვის (საუკუნის მეოთხედი, საუკუნე და ა. შ.) შკალაზე აღებულია დიაპაზონის ბოლო, ე. ი. „არაუგვიანეს“. ${undated} თარიღის არმქონე ობიექტი ნაჩვენები არ არის. ფონური რუკა — OpenFreeMap / OpenStreetMap.`,
      name: "სახელწოდება", address: "მისამართი", cls: "ტიპი", date: "თარიღი რეესტრში", est: "შკალაზე ჩანს", range: "დიაპაზონი", prec: "სიზუსტე",
      reg: "რეესტრის №", unc: "მდებარეობა რუკაზე სავარაუდოა", national: "ეროვნული მნიშვნელობის", object: "კულტურული მემკვიდრეობის ობიექტი", monument: "ძეგლი",
      photo: "ფოტო წერტილის სიახლოვეს (შეიძლება მეზობელ შენობას აჩვენებდეს)", photoBy: "ფოტო",
      precision: { exact: "წელი", quarter: "საუკუნის მეოთხედი", middle: "საუკუნის შუა", half: "საუკუნის ნახევარი", century: "საუკუნე", mixed: "შერეული", years: "წლები", unknown: "—" },
      src: { ExactDate: "„ზუსტი თარიღის“ ველი", Period: "„პერიოდის“ ველი", DateRange: "თარიღთა დიაპაზონი" },
      classes: { architecture: "არქიტექტურა", archaeology: "არქეოლოგია", ethnography: "ეთნოგრაფია", memorial: "მემორიალური", urban: "ქალაქთმშენებლობა",
                 monumental_art: "მონუმენტური ხელოვნება", garden: "საბაღე-საპარკო", science: "მეცნიერება", engineering: "საინჟინრო", other: "სხვა" },
      aboutTitle: "პროექტის შესახებ და წყაროები",
      about: [
        "არაკომერციული ჰობი-პროექტი ღია მონაცემებზე. თარიღები, საზღვრები და გეგმების მიბმა მიახლოებითია და არ წარმოადგენს ოფიციალურ ინფორმაციას.",
        "ობიექტები: საქართველოს უძრავი კულტურული მემკვიდრეობის ძეგლთა რეესტრის საჯარო ინფორმაცია (კულტურული მემკვიდრეობის დაცვის ეროვნული სააგენტო). ამ მონაცემებისთვის წერილობითი ღია ლიცენზია ვერ მოიძებნა; არაკომერციული მიზნით გამოყენებულია შემოკლებული ამონარიდი (სახელწოდება, მისამართი, კოორდინატები, თარიღები, ნომერი). თარიღები რეესტრის ჩანაწერებზე დაფუძნებული შეფასებაა.",
        "ტფილისის გეგმები, 1735 (ვახუშტი, სქემატური), 1785 (პიშჩევიჩი), 1800 (ჩუიკო), 1821 (შვეცოვი), 1844 (სამხედრო-ტოპოგრაფიული დეპო), 1850 (გენშტაბი), 1887 (ა. ილინი) 1911 (შემოგარენის ტოპოგრაფიული ფურცელი) და 1913 (საქალაქო სამმართველოს მიწისმზომელთა განყოფილება): Wikimedia Commons-ის სკანები, საჯარო სივრცე. გეგმები თანამედროვე რუკაზე მიბმულია საკონტროლო წერტილებით (სიზუსტე დაახლოებით 50 მ, 1735 წლის გეგმისთვის დაახლოებით 150 მ), განაშენიანების საზღვრები მათ მიხედვით ხელით არის დატანილი.",
        "ტფილისის ისტორიული ხედები (1578–1910-იანი წლები): „ნუსრეთნამეს“ მინიატურა (British Library), გრავიურები შარდენისა და ტურნეფორის ნახატებით, ჩერნეცოვის, ლერმონტოვის, ფრანკენისა და აივაზოვსკის ნახატები, ერმაკოვისა და პროკუდინ-გორსკის ფოტოები; Wikimedia Commons-ის ფაილები, საჯარო სივრცე; შემცირებული ასლები. ესენი ერთი წერტილიდან შესრულებული ნახატები და ფოტოებია და რუკას არ უკავშირდება.",
        "კონფიდენციალურობა: გვერდი არ იყენებს cookie-ს და ანალიტიკას; ბრაუზერში მხოლოდ არჩეული ენა ინახება. ჩატვირთვისას ბრაუზერი მიმართავს tiles.openfreemap.org-ს (რუკის ფონი) და wikimedia.org-ს (ფოტოების გადახედვა), ამიტომ ამ სერვისებს ეხილვებათ სტუმრის მისამართი. GitHub-ით გაგზავნილი უკუკავშირი საჯარო Issue-ს ქმნის.",
        "განაშენიანების სიმჭიდროვე: OpenStreetMap-ის შენობების კონტურებით დაკავებული ფართობის წილი (© OpenStreetMap contributors, ODbL), დაახლოებით 100×100 მ უჯრედებში; ნაჩვენებია ექსპორტის მომენტის მდგომარეობა (2026 წლის ნოემბერი); OSM-ის შენობებს აგების წლები არ აქვს, ამიტომ ფენა მხოლოდ თანამედროვე წლებისთვის ჩანს.",
        "თბილისის ადმინისტრაციული საზღვარი (2019): OCHA COD-AB Georgia (HDX), წყარო — საქართველოს სტატისტიკის ეროვნული სამსახური, ლიცენზია CC BY-IGO. ფართობი 502,5 კმ² ემთხვევა დისერტაციის მონაცემს 2006 წლის შემდგომი პერიოდისთვის.",
        "რაიონების საზღვრები და სახელები: © OpenStreetMap-ის მონაწილეები, ლიცენზია ODbL (ეს მონაცემთა ნაკრები წარმოებული ბაზაა; გამოყენებისას შეინარჩუნეთ იგივე ლიცენზია და ატრიბუცია). ნაჩვენებია 10 რაიონად დღევანდელი დაყოფა.",
        "1973–2005 წლების ნაცრისფერი წყვეტილი ხაზი — geoBoundaries-ის საზღვარია (ADM2, მეტამონაცემები: 2007). შემოწმება დასახლებების მდებარეობით: 2006 წელს მიერთებული (წყნეთი, წავკისი, ოქროყანა, კიკეთი, ბეთანია, დიდი დიღომი, ზაჰესი) მის გარეთაა, ადრე მიერთებული (პონიჭალა, ორხევი, გლდანი, ვარკეთილი) — შიგნით, ანუ ის შეესაბამება 2006 წლამდე არსებულ საზღვარს. მისი ფართობი დაახლოებით 330 კმ² დისერტაციის 354 კმ²-ზე ნაკლებია, მიზეზი დადგენილი არ არის. რაიონული დაყოფა და სახელები პერიოდების მიხედვით (საზღვრების გარეშე) გადმოცემულია ხელოვნური ინტელექტის მიერ მეორადი წყაროებიდან და ორიგინალებთან შემოწმებული არ არის.",
        "ქალაქის ფართობი: ნ. ხარებავა, სადოქტორო დისერტაცია, ივანე ჯავახიშვილის სახელობის თბილისის სახელმწიფო უნივერსიტეტი, 2024.",
        "ფოტოები: Wikimedia Commons, ავტორისა და ლიცენზიის მითითებით; შერჩეულია კოორდინატებით და შეიძლება მეზობელ შენობას აჩვენებდეს.",
        "დროის შკალა იწყება IV საუკუნიდან: ზოგადი მიმოხილვების მიხედვით (ვიკიპედია, პირველწყაროებთან შემოწმებული არ არის), ქალაქის ადგილას ციხესიმაგრის შესახებ უძველესი წერილობითი ცნობები IV საუკუნის შუა და მეორე ნახევარს (დაახლოებით 364 წელი) განეკუთვნება, ხოლო ქალაქის დაარსების ტრადიციული თარიღი ქართული მატიანეების მიხედვით 458 წელია (ვახტანგ გორგასალი). 1700 წლამდე შკალა შეკუმშულია, 1735 წლამდე გეგმები და საზღვრები არ არის, ნაჩვენებია მხოლოდ რეესტრის ობიექტები.",
        "დაკარგული შენობები: სია შედგენილია ხელოვნური ინტელექტის (Gemini) მიერ Wikidata-ს, ვიკიპედიის (ka, ru, en) და ისტორიული გეგმების ლეგენდების მიხედვით; თარიღები და მდებარეობა მიახლოებითია, ბუშტი აჩვენებს, ნაპოვნია თუ არა დაკარგვის წელი წყაროს გვერდზე. ეს არ არის ოფიციალური რეესტრი.",
        "განაშენიანების საზღვრები 1972 წლიდან: GUSV — Mapping of 30 m global urban boundaries from 1972 to 2021 (Zenodo, doi:10.5281/zenodo.14523232), ლიცენზია CC BY 4.0; გასწორებული და გამარტივებულია პროექტის მიერ. 1954 წლის კონტური: აშშ-ის არმიის რუკების სამსახურის NK 38-8 ფურცელზე განაშენიანების შევსება (1:250 000), საჯარო სივრცე; მდებარეობა მიახლოებითია.",
        "ფონური რუკა: OpenFreeMap, © OpenMapTiles, მონაცემები © OpenStreetMap-ის მონაწილეები. რუკის ბიბლიოთეკა: MapLibre GL JS.",
      ],
      urbanNone: (first) => `ამ პერიოდისთვის განაშენიანების საზღვარი ჯერ არ არის (პირველი — ${first}).`,
      urbanLine: (snap, src, partial, y, acc) => `განაშენიანების საზღვარი ${snap} წლისთვის${snap !== y ? " (უახლოესი " + y + " წელთან)" : ""}: ${src}${partial ? ". ნაჩვენებია მხოლოდ კარგად ხილული მონაკვეთები (ჩრდილოეთი და აღმოსავლეთი)" : ""}${acc ? ". მდებარეობის ცდომილება შეიძლება ~" + acc + " მ იყოს" : ""}`,
      urbanSrc: { ams: "განაშენიანების შევსება 1954 წლის ამერიკულ რუკაზე (1:250 000, 1920–40-იანი წლების აგეგმვებით, დაახლოებით 1940-იანების მდგომარეობა), მიახლოებით", traced: "ძველი გეგმიდან ხელით დატანილი, მიახლოებით", gusv: "თანამგზავრული შეფასება (GUSV, Landsat): განაშენიანების გასწორებული კონტური, არა ადმინისტრაციული საზღვარი" },
      showSettle: "ქალაქს შეერთებული დასახლებები",
      settleJoined: (y, from, geomNote) => `ქალაქს შეუერთდა: ${y} წელი${from ? " (" + from + ")" : ""}`,
      settleUnknown: "შეერთების წელი პროექტში მითითებული არ არის",
      settleSrc: "წელი და საფუძველი გადმოცემულია ხელოვნური ინტელექტის მიერ მეორადი წყაროებიდან (ქაქურია 1979, საბჭოთა დიდი ენციკლოპედია, 2006 წლის პარლამენტის დადგენილება) და ორიგინალებთან შემოწმებული არ არის.",
      settleGeom: { inside_old: "მდებარეობით 2006 წლამდე არსებული საქალაქო საზღვრის შიგნითაა.", outside_old_inside_2019: "მდებარეობით 2006 წლამდე არსებული საზღვრის გარეთაა და დღევანდელის შიგნით: ეს შეესაბამება 2006 წელს მიერთებას.", outside_2019: "დღევანდელი საქალაქო საზღვრის გარეთაა." },
      settleFrom: { Gardabani: "გარდაბნის რაიონიდან", Mtskheta: "მცხეთის რაიონიდან" },
      settleNow: (y, inCity) => `${y} წელს: ${inCity === null ? "შეერთების წელი უცნობია" : inCity ? "ადმინისტრაციულად ქალაქის ნაწილია (ეს არ ნიშნავს, რომ განაშენიანებულია)" : "ჯერ არ შედიოდა ქალაქში"}`,
      settleConflict: "⚠ მდებარეობა წელს ეწინააღმდეგება: 2006 წლამდე არსებული საზღვრის გარეთაა (ან გადმოცემული წელი არასწორია, ან ნაკრების საზღვარი ამ სოფელს არ მოიცავს).",
      legRuin: "ნანგრევები ან ნაშთები (რეესტრის სახელის მიხედვით)", ruinRow: "მდგომარეობა", ruinTxt: "ნანგრევები, ნაშთები ან ობიექტის ადგილი (რეესტრის სახელის მიხედვით)",
      legTitle: "პირობითი ნიშნები", legObjects: "რეესტრის ობიექტები (წერტილები)", legBounds: "ხაზები და არეები", legNames: "წარწერები",
      legFill: "განაშენიანება / ქალაქის ტერიტორია არჩეული წლისთვის (შევსება კონტურით)",
      legSat: "უწყვეტი ხაზი: განაშენიანების თანამგზავრული შეფასება (1972-დან)",
      legTraced: "წყვეტილი: ძველი გეგმიდან ან რუკიდან ხელით დატანილი",
      legAdmin: "მუქი წყვეტილი: თანამედროვე ადმინისტრაციული საზღვარი (2019)",
      legOldAdmin: "რუხი წყვეტილი: საზღვარი 2006 წლამდე (1973–2005)",
      legDistLine: "თხელი ხაზი: თანამედროვე რაიონების საზღვრები",
      legPlan: "ძველი გეგმა (როცა ჩართულია „ძველი გეგმა რუკაზე“)",
      legDistName: "რაიონის დასახელება (თანამედროვე)",
      legSetBefore: "დასახლება: ქალაქში ჯერ არ შედის",
      legSetAfter: "დასახლება: უკვე ქალაქის ნაწილია",
      legSetUnk: "დასახლება: შეერთების წელი უცნობია",
      legSetName: "დასახლების დასახელება (დააწკაპუნეთ წერტილზე: როდის და საიდან შეუერთდა)",
      fbBtn: "შეცდომის შეტყობინება", fbTitle: "შეატყობინეთ შეცდომა ან ნაკლოვანება",
      fbHint: "აღწერეთ, რა არის არასწორი ან რა აკლია. გვერდი თავად არაფერს აგზავნის: შეტყობინება გაიხსნება როგორც issue პროექტის GitHub-რეპოზიტორიაში (საჭიროა GitHub-ის ანგარიში), ან გაიგზავნება ფორმით, თუ ის მიერთებულია.",
      fbType: "რა არის არასწორი", fbK1: "შეცდომა ობიექტის მონაცემებში (სახელი, თარიღი, მისამართი, მდებარეობა)", fbK2: "ძველი გეგმა არასწორ ადგილასაა (მიბმა)", fbK3: "ქალაქის ან განაშენიანების საზღვარი", fbK4: "შეცდომა თარგმანში ან სახელში", fbK5: "უფლებების საკითხი, გთხოვთ წაშალოთ მონაცემები", fbK6: "სხვა",
      fbText: "აღწერა", fbCtx: "კონტექსტი (ივსება ავტომატურად)", fbContact: "როგორ დაგიკავშირდეთ (სურვილისამებრ)", fbSend: "გაგზავნა", fbCancel: "გაუქმება",
      fbSent: "გმადლობთ! შეტყობინება გაიგზავნა.", fbOpened: "გაიხსნა GitHub-ის ფანჯარა: დაადასტურეთ იქ გაგზავნა.", fbPopup: "შეატყობინეთ ამ ობიექტის შესახებ შეცდომა",
      showLost: "დაკარგული შენობები (დანგრეული ან განადგურებული)", showGhost: "დაკარგვის შემდეგაც ჩვენება (მკრთალად)",
      legLostOn: "დაკარგული შენობა: ამ წელს ჯერ დგას", legLostUnc: "დაკარგული: აშენების ან დაკარგვის თარიღი ზუსტი არ არის", legLostOff: "დაკარგული: უკვე აღარ არის (მკრთალი „აჩრდილი“)",
      lostKinds: { church: "ეკლესია", cathedral: "ტაძარი", mosque: "მეჩეთი", synagogue: "სინაგოგა", caravanserai: "ქარვასლა", theatre: "თეატრი", gate: "კარიბჭე", wall: "გალავანი", tower: "კოშკი", bridge: "ხიდი", station: "სადგური", barracks: "ყაზარმა/ციხე", palace: "სასახლე", house: "სახლი", other: "სხვა" },
      lostWhy: { demolished: "დანგრეულია", destroyed: "განადგურებულია", rebuilt: "გადაკეთებულია", flooded: "დატბორილია", unknown: "მიზეზი უცნობია" },
      lostBuilt: "აშენდა", lostLost: "დაიკარგა", lostRepl: "ამჟამად ადგილზე", lostState: { stand: "ამ წელს ჯერ დგას", unc: "ამ წელს შეიძლება უკვე დანგრეული ყოფილიყო (დაკარგვის თარიღი ზუსტი არ არის)", gone: "ამ წელს უკვე დაკარგულია", early: "ამ წელს შეიძლება ჯერ არ არსებულიყო (აშენების თარიღი ზუსტი არ არის)" },
      lostAcc: (m, pos) => `მდებარეობა ${pos === "plan" ? "აღებულია ისტორიული გეგმიდან" : "წყაროს კოორდინატებით"}, ცდომილება ≈ ${m} მ`,
      lostChk: "დაკარგვის წელი ნაპოვნია მითითებულ წყაროს გვერდზე (სუსტი შემოწმება)", lostNoChk: "დაკარგვის წელი მითითებულ გვერდებზე ავტომატურად ვერ მოიძებნა",
      lostSrc: "სია შედგენილია ხელოვნური ინტელექტის მიერ Wikidata-ს, ვიკიპედიისა და გეგმების ლეგენდების მიხედვით; ოფიციალური არ არის.", lostSources: "წყაროები",
      showWater: "თბილისის ზღვა და ტბები (ისტორიული)",
      legWater: "თბილისის ზღვა (წყალსაცავი, 1951–1953-დან)", legLake: "მლაშე ტბები წყალსაცავამდე (დაახლოებით 1911 წლის ტოპოგრაფიული ფურცლიდან)",
      waterRes: "თბილისის ზღვა (თბილისის წყალსაცავი)", waterLake: "მლაშე ტბა (მომავალი თბილისის ზღვის ადგილას ან გვერდით)",
      waterTxtRes: (y) => y < 1951 ? "ამ წელს ზღვა ჯერ არ არსებობდა: მოგვიანებით დატბორილ ველზე მლაშე ტბები იყო (ნაცრისფერი შევსება მომავალ აკვატორიას აჩვენებს)." : y < 1953 ? "წყალსაცავი ივსებოდა: წყაროები გახსნის თარიღზე ერთმანეთს არ ემთხვევა (1951 ან 1953)." : "წყალსაცავი არსებობს (კონტური OpenStreetMap-იდან; ლიტერატურაში 11,2–11,6 კმ²).",
      waterTxtLake: (y) => y < 1953 ? "ტბა შემოხაზულია დაახლოებით 1911 წლის თბილისის შემოგარენის ტოპოგრაფიული ფურცლით (1:42 000); ტბების უფრო ადრინდელი სახე და 1951 წლამდე ცვლილებები არ შემოწმებულა. მდებარეობა დაახლოებით ±70 მ." : "ამ წლისთვის ტბები წყალსაცავმა დატბორა.",
      waterSrc: "წყაროები: OpenStreetMap (ზღვის კონტური, ODbL); ტოპოგრაფიული ფურცელი დაახლოებით 1911 წლიდან (ტბები).",
      viewsTitle: "ისტორიული ხედები (ნახატები, არა გეგმები)",
      viewClose: "დახურვა",
      viewLicense: "ლიცენზია",
      viewSource: "წყარო",
      fbContactWarn: "ყურადღება: GitHub-ის გავლით გაგზავნისას კონტაქტი საჯარო Issue-ში მოხვდება და ყველას დაენახება. თუ არ გსურთ, ნუ მიუთითებთ.",
      infoBtn: "წყაროები და დეტალები",
      infoTitle: "წყაროები და დეტალები",
      infoRegister: "ობიექტის მონაცემები: საქართველოს კულტურული მემკვიდრეობის უძრავი ძეგლების რეესტრის საჯარო ცნობები (კულტურული მემკვიდრეობის დაცვის ეროვნული სააგენტო), შემოკლებული ამონარიდი არაკომერციული გამოყენებისთვის. პირობები და წყაროების სრული სია: „პროექტის შესახებ და წყაროები“ გვერდით პანელში.",
      infoPhotos: "ფოტოები",
      showDensity: "განაშენიანების სიმჭიდროვე (OSM, დღეს)",
      legDensity: "განაშენიანების სიმჭიდროვე OSM-ის შენობების მიხედვით (2015-დან): ღია — იშვიათი, მუქი წითელი — ძალიან მჭიდრო",
      typesTitle: "დანიშნულება (დღეს — სახელის მიხედვით, სხვა შემთხვევაში რეესტრით)", func: "დღევანდელი დანიშნულება (სახელის მიხედვით)", func0: "თავდაპირველი დანიშნულება (რეესტრის მიხედვით)", wiki: "სტატია ვიკიპედიაში",
      types: { residential: "საცხოვრებელი სახლები", religious: "რელიგიური", defense: "თავდაცვითი", culture: "განათლება, მეცნიერება, კულტურა",
               public: "საზოგადოებრივი და სავაჭრო", transport: "ტრანსპორტი და ინჟინერია", memorial: "მემორიალები და პარკები", rural: "არქეოლოგია და სოფლის", other: "სხვა" },
    },
  };

  const LANGS = ["ka", "en", "ru"];
  let lang = "en";
  const nav = (navigator.language || "en").slice(0, 2);
  if (LANGS.includes(nav)) lang = nav;
  try { const s = localStorage.getItem("lang"); if (LANGS.includes(s)) lang = s; } catch (e) {}
  const q = new URLSearchParams(location.search).get("lang");
  if (LANGS.includes(q)) lang = q;
  const $ = (id) => document.getElementById(id);
  const t = () => T[lang];

  const TYPES = ["residential", "religious", "defense", "culture", "public", "transport", "memorial", "rural", "other"];
  const activeTypes = new Set(TYPES);
  let plans = [], monuments = null, undated = 0, areas = [];
  let urbanSnaps = [], urbanMeta = {}, distHist = null, distModern = [];
  let year = 1887;
  const h = parseInt((location.hash || "").slice(1), 10);
  if (h >= MIN && h <= MAX) year = h;

  const map = new maplibregl.Map({
    container: "map",
    // OpenFreeMap vector tiles (free, no key; data © OpenStreetMap contributors, © OpenMapTiles; attribution added by MapLibre)
    // OpenFreeMap "liberty" style, same in light and dark system themes (free, no key; attribution is added by MapLibre)
    style: "https://tiles.openfreemap.org/styles/liberty",
    center: (() => { const c = (new URLSearchParams(location.search).get("c") || "").split(",").map(Number); return c.length >= 2 && c.every(isFinite) ? [c[0], c[1]] : [44.8085, 41.6955]; })(),
    zoom: (() => { const c = (new URLSearchParams(location.search).get("c") || "").split(",").map(Number); return c.length >= 3 && isFinite(c[2]) ? c[2] : 13.2; })(), minZoom: 9, maxZoom: 19, hash: false,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

  function currentPlan(y) {
    // a plan is shown from its own year until the next plan (or PLAN_AFTER years if it is the last one)
    let p = null, next = null;
    plans.forEach((pl, i) => { if (pl.year <= y) { p = pl; next = plans[i + 1] || null; } });
    if (!p) return null;
    const until = next ? next.year : p.year + PLAN_AFTER;
    return y < until ? p : null;
  }

  function getCss(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim() || "#b4412c"; }

  function filterExpr() {
    const f = ["all", ["<=", ["get", "ye"], year]];
    const tiers = [];                                   // a ticked box SHOWS that group
    if ($("showNat").checked) tiers.push("nat");
    if ($("showMon").checked) tiers.push("mon");
    if ($("showObj").checked) tiers.push("obj");
    f.push(["in", ["case", ["get", "national"], "nat", ["get", "monument"], "mon", "obj"], ["literal", tiers]]);
    if (activeTypes.size < TYPES.length) f.push(["in", ["get", "fn"], ["literal", [...activeTypes]]]);
    return f;
  }

  function countVisible() {
    const okTier = { nat: $("showNat").checked, mon: $("showMon").checked, obj: $("showObj").checked };
    let n = 0;
    for (const f of monuments.features) {
      const p = f.properties;
      if (p.ye > year) continue;
      if (!okTier[p.national ? "nat" : p.monument ? "mon" : "obj"]) continue;
      if (!activeTypes.has(p.fn)) continue;
      n++;
    }
    return n;
  }

  let bndText = "";
  function updateUrban() {
    if (!map.getLayer("urban-fill")) return;
    let snap = null;
    for (const s of urbanSnaps) if (s <= year) snap = s;
    const on = $("showBnd").checked && snap !== null;
    const traced = ["==", ["get", "src"], "traced"];
    const filters = {
      "urban-fill": ["==", ["get", "snap"], snap === null ? -1 : snap],
      "urban-line": ["all", ["==", ["get", "snap"], snap === null ? -1 : snap], ["!", traced]],
      "urban-line-approx": ["all", ["==", ["get", "snap"], snap === null ? -1 : snap], traced],
    };
    for (const id of Object.keys(filters)) {
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, filters[id]);
    }
    if (!urbanSnaps.length) bndText = "";
    else if (snap === null) bndText = t().urbanNone(urbanSnaps[0]);
    else bndText = t().urbanLine(snap, t().urbanSrc[urbanMeta[snap].src] || "", urbanMeta[snap].partial, year, urbanMeta[snap].acc);
  }

  function updateDistInfo() {
    const sum = $("distsum"), body = $("distbody");
    if (!sum || !body) return;
    body.textContent = "";
    if (!distHist) { sum.textContent = ""; return; }
    const per = distHist.periods.find((p) => year >= p.from && year <= p.to);
    if (!per) { sum.textContent = t().distTitle("—"); const m = document.createElement("p"); m.className = "small"; m.textContent = t().distNone; body.appendChild(m); return; }
    sum.textContent = t().distTitle(per.label[lang]);
    const modName = (en) => { const d = distModern.find((x) => x.name_en === en); return d ? d["name_" + lang] || d.name_en : en; };
    const items = per.items === "modern" ? distModern.map((d) => ({ [lang]: d["name_" + lang] || d.name_en, modern: null })) : per.items;
    const ul = document.createElement("ul");
    for (const it of items) {
      const li = document.createElement("li");
      li.textContent = it[lang] || it.en;
      if (it.modern) li.textContent += " — " + t().distMod + ": " + it.modern.map(modName).join(", ");
      ul.appendChild(li);
    }
    body.appendChild(ul);
    if (per.items !== "modern") { const n = document.createElement("p"); n.className = "small"; n.textContent = t().distNote; body.appendChild(n); }
  }

  // plan rasters are added to the map only when a plan is first needed (keeps the first page load light)
  function ensurePlan(p) {
    if (map.getLayer("plan-" + p.id)) return;
    map.addSource("plan-" + p.id, { type: "image", url: p.image, coordinates: p.corners });
    map.addLayer({ id: "plan-" + p.id, type: "raster", source: "plan-" + p.id, layout: { visibility: "none" },
                   paint: { "raster-opacity": $("op").value / 100, "raster-fade-duration": 0 } }, "admin-line");
  }

  function update() {
    $("year").textContent = year;
    if ($("yearchip")) $("yearchip").textContent = year;
    $("slider").value = Math.round(y2v(year));
    try { history.replaceState(null, "", "#" + year); } catch (e) {}
    if (!map.getLayer("mon")) return;
    map.setFilter("mon", filterExpr());
    if (map.getLayer("mon-ruin")) map.setFilter("mon-ruin", ["all", filterExpr(), ["==", ["get", "ruin"], true]]);
    map.setPaintProperty("mon", "circle-color", ["case",
      ["==", ["get", "national"], true], getCss("--nat"),
      ["<=", ["-", year, ["get", "ye"]], NEW_YEARS], getCss("--accent"),
      getCss("--old")]);
    $("count").textContent = t().count(countVisible(), year);

    const pl = currentPlan(year);
    for (const p of plans) {
      const on = pl && p.id === pl.id && $("showPlan").checked;
      if (on) ensurePlan(p);
      if (map.getLayer("plan-" + p.id)) map.setLayoutProperty("plan-" + p.id, "visibility", on ? "visible" : "none");
    }
    updateUrban();
    updateSettle();
    updateWater();
    updateDensity();
    updateViews();
    updateLost();
    if (map.getLayer("admin-line")) map.setLayoutProperty("admin-line", "visibility", $("showAdmin").checked ? "visible" : "none");
    const oldOn = $("showAdmin").checked && year >= 1973 && year <= 2005;
    if (map.getLayer("admin-old-line")) map.setLayoutProperty("admin-old-line", "visibility", oldOn ? "visible" : "none");
    const dOn = $("showDistricts").checked ? "visible" : "none";
    for (const id of ["districts-line", "districts-label"]) if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", dOn);
    if (map.getLayer("districts-label")) map.setLayoutProperty("districts-label", "text-field", ["get", "name_" + lang]);
    let ar = null;
    for (const x of areas) if (x.year <= year) ar = x;
    $("arealine").textContent = (ar ? t().area(ar.km2, ar.year, ar.src) : "") + ($("showAdmin").checked && year >= 1973 && year <= 2005 ? " · " + t().oldAdmin : "");
    updateDistInfo();
    $("planline").textContent = pl ? t().plan(pl.year, pl.accuracy_m) : t().noPlan(plans[0].year, plans[plans.length - 1].year, year);
    $("bndline").textContent = bndText;
  }

  function applyLang() {
    document.documentElement.lang = lang;
    document.title = t().title;
    if (typeof feedbackRefreshCtx === "function") feedbackRefreshCtx();
    $("title").textContent = t().title;
    $("lang").value = lang;
    document.querySelectorAll("[data-i]").forEach((el) => { el.textContent = t()[el.dataset.i]; });
    $("note").textContent = t().note(undated);
    buildTypes();
    buildAbout();
    update();
  }

  function buildAbout() {
    const box = $("abouttext");
    box.textContent = "";
    for (const para of t().about) {
      const p = document.createElement("p");
      p.className = "small";
      p.textContent = para;
      box.appendChild(p);
    }
  }

  function buildTypes() {
    const box = $("typelist");
    box.textContent = "";
    for (const k of TYPES) {
      const lab = document.createElement("label");
      lab.className = "row";
      const cb = document.createElement("input");
      cb.type = "checkbox"; cb.checked = activeTypes.has(k);
      cb.addEventListener("change", () => { if (cb.checked) activeTypes.add(k); else activeTypes.delete(k); update(); });
      lab.appendChild(cb);
      lab.appendChild(document.createTextNode(" " + t().types[k]));
      box.appendChild(lab);
    }
  }

  function buildTicks() {
    const box = $("ticks");
    box.textContent = "";
    const add = (y, cls) => {
      const s = document.createElement("span");
      s.textContent = y;
      s.title = String(y);
      if (cls) s.className = cls;
      s.style.left = `calc(8px + (100% - 16px) * ${y2v(y) / 1000})`;
      s.addEventListener("click", () => { year = y; update(); });
      box.appendChild(s);
    };
    // every year that has a data snapshot (built-up outline or old plan) is marked and clickable; round years fill gaps
    const marked = [...new Set([...urbanSnaps, ...plans.map((p) => p.year), ...views.map((v) => v.year)])].sort((a, b) => a - b);
    const round = [];
    for (let y = 400; y < 1700; y += 200) round.push(y);                  // the compressed early period: every 200 years
    for (let y = 1750; y <= MAX; y += 50) if (!marked.some((p) => Math.abs(p - y) < 12)) round.push(y);
    if (!marked.some((p) => Math.abs(p - MAX) < 12)) round.push(MAX);
    round.unshift(MIN);
    const width = Math.max(box.clientWidth - 16, 300);
    const rows = [[], []];                                   // x positions of labels already placed on each of two rows
    const fits = (r, x) => rows[r].every((q) => Math.abs(q - x) >= 34);
    const items = [];
    for (const y of marked) {                                // snapshot years first: always get a tick, a label if there is room
      const x = (y2v(y) / 1000) * width;
      const r = fits(0, x) ? 0 : fits(1, x) ? 1 : -1;
      if (r >= 0) rows[r].push(x);
      items.push({ y, cls: "plan", r, label: r >= 0 });
    }
    for (const y of round) {                                 // round years only where they do not collide
      const x = (y2v(y) / 1000) * width;
      const r = fits(0, x) ? 0 : fits(1, x) ? 1 : -1;
      if (r >= 0) { rows[r].push(x); items.push({ y, cls: "", r, label: true }); }
    }
    for (const it of items) add(it.y, (it.cls + (it.r === 1 ? " r2" : "") + (it.label ? "" : " nl")).trim());
  }

  let photoInfo = null;
  // Details that do not belong on the card (licences, sources, register notes) live in a separate window opened by a button.
  function openInfo(build) {
    $("imTitle").textContent = t().infoTitle;
    const body = $("imBody");
    body.textContent = "";
    build(body);
    $("infoModal").hidden = false;
  }
  function closeInfo() { $("infoModal").hidden = true; }
  $("imClose").addEventListener("click", closeInfo);
  $("infoModal").addEventListener("click", (e) => { if (e.target === $("infoModal")) closeInfo(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("infoModal").hidden) closeInfo(); });
  function infoLine(body, text, cls) { const d = document.createElement("div"); d.className = cls || "small"; d.textContent = text; body.appendChild(d); return d; }
  function actions(el, openDetails, fbObj) {
    const box = document.createElement("div");
    box.className = "actions";
    const a1 = document.createElement("a");
    a1.href = "#"; a1.className = "fb"; a1.textContent = t().infoBtn;
    a1.addEventListener("click", (ev) => { ev.preventDefault(); openDetails(); });
    const a2 = document.createElement("a");
    a2.href = "#"; a2.className = "fb"; a2.textContent = t().fbPopup;
    a2.addEventListener("click", (ev) => { ev.preventDefault(); openFeedback(fbObj); });
    box.appendChild(a1); box.appendChild(a2);
    el.appendChild(box);
  }

  async function addPhotos(el, p) {
    if (!p.ph) return;
    const box = document.createElement("div");
    box.className = "photos";
    el.appendChild(box);
    try {
      if (!photoInfo) photoInfo = await getJSON("data/photos.json");
    } catch (e) { return; }
    const titles = String(p.ph).split("|").filter((x) => photoInfo[x] && photoInfo[x].thumb);
    if (!titles.length) return;
    titles.forEach((ti, i) => {
      const f = photoInfo[ti];
      const fig = document.createElement("figure");
      fig.className = i === 0 ? "ph main" : "ph small";
      const a = document.createElement("a");
      a.href = f.page; a.target = "_blank"; a.rel = "noopener";
      const img = document.createElement("img");
      img.src = f.thumb; img.loading = "lazy"; img.alt = p.name || "";
      a.appendChild(img);
      fig.appendChild(a);
      a.title = [f.author || "", f.license || ""].filter(Boolean).join(" · ");
      box.appendChild(fig);
    });
  }
  async function photoCredits(body, p) {
    if (!p.ph) return;
    try { if (!photoInfo) photoInfo = await getJSON("data/photos.json"); } catch (e) { return; }
    const titles = String(p.ph).split("|").filter((x) => photoInfo[x] && photoInfo[x].thumb);
    if (!titles.length) return;
    const h = document.createElement("h4");
    h.textContent = t().infoPhotos;
    body.appendChild(h);
    titles.forEach((ti) => {
      const f = photoInfo[ti];
      const d = document.createElement("div");
      d.className = "small";
      d.appendChild(document.createTextNode([f.author || "?", f.license || ""].filter(Boolean).join(" · ") + " · "));
      const a = document.createElement("a");
      a.href = f.page; a.target = "_blank"; a.rel = "noopener"; a.textContent = "Wikimedia Commons";
      d.appendChild(a);
      body.appendChild(d);
    });
    infoLine(body, t().photo);
  }

  // Wikipedia link in the interface language; if there is no article in it: English, then Georgian, Russian only as the last resort
  function wikiLink(p) {
    if (!p.wp) return null;
    const links = {};
    String(p.wp).split("|").forEach((x) => { const i = x.indexOf(":"); if (i > 0) links[x.slice(0, i)] = x.slice(i + 1); });
    const l = [lang, "en", "ka", "ru"].find((c) => links[c]);
    if (!l) return null;
    const a = document.createElement("a");
    a.href = "https://" + l + ".wikipedia.org/wiki/" + encodeURIComponent(links[l].replace(/ /g, "_"));
    a.target = "_blank"; a.rel = "noopener";
    a.textContent = t().wiki + " (" + l + ")";
    return a;
  }

  function addWiki(el, p) {
    const a = wikiLink(p);
    if (!a) return;
    const d = document.createElement("div");
    d.appendChild(a);
    el.appendChild(d);
  }

  function settlePopup(p, lngLat) {
    const L = t();
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = p["name_" + lang] || p.name_en;
    el.appendChild(h3);
    const add = (txt, cls) => { const d = document.createElement("div"); if (cls) d.className = cls; d.textContent = txt; el.appendChild(d); };
    const j = p.joined === null || p.joined === undefined || p.joined === "null" ? null : Number(p.joined);
    add(j ? L.settleJoined(j, p.from && p.from !== "null" ? (L.settleFrom[p.from] || p.from) : "") : L.settleUnknown);
    add(L.settleNow(year, j ? j <= year : null));
    if (p.note && p.note !== "null") add(p.note, "k small");
    add(L.settleGeom[p.geom] || "", "k small");
    if (p.conflict === true || p.conflict === "true") add(L.settleConflict, "k small");
    add(L.settleSrc, "k small");
    new maplibregl.Popup({ maxWidth: "300px" }).setLngLat(lngLat).setDOMContent(el).addTo(map);
  }

  let lostFeats = [];
  // state of a lost building in the selected year: early (before construction is certain), stand, unc (loss date imprecise), gone
  function lostState(p) {
    const n = (v) => (v === null || v === undefined || v === "null" ? null : Number(v));
    const b0 = n(p.b0), b1 = n(p.b1) ?? b0, l0 = n(p.l0), l1 = n(p.l1) ?? l0;
    if (b0 !== null && year < b0) return null;                       // certainly not built yet: not shown
    if (l1 !== null && year >= l1) return "gone";
    if (l0 !== null && year >= l0) return "unc";
    if (b1 !== null && year < b1) return "early";
    return "stand";
  }
  function updateLost() {
    if (!map.getLayer("lost-dot")) return;
    const on = $("showLost").checked, ghost = $("showGhost").checked;
    map.setLayoutProperty("lost-dot", "visibility", on ? "visible" : "none");
    if (!on) return;
    const feats = lostFeats;
    const ids = { stand: [], unc: [], early: [], gone: [] };
    feats.forEach((f, i) => { const s = lostState(f.properties); if (s) ids[s].push(i); });
    const idx = (a) => ["literal", a];
    map.setFilter("lost-dot", ["any", ["in", ["id"], idx(ids.stand)], ["in", ["id"], idx(ids.unc)], ["in", ["id"], idx(ids.early)], ...(ghost ? [["in", ["id"], idx(ids.gone)]] : [])]);
    map.setPaintProperty("lost-dot", "circle-stroke-opacity", ["case", ["in", ["id"], idx(ids.stand)], 1, ["in", ["id"], idx(ids.gone)], 0.35, 0.65]);
    map.setPaintProperty("lost-dot", "circle-stroke-color", ["case", ["in", ["id"], idx(ids.gone)], "#999999", "#8b5a2b"]);
    map.setPaintProperty("lost-dot", "circle-opacity", ["case", ["in", ["id"], idx(ids.gone)], 0.04, 0.14]);
  }

  function lostPopup(p, lngLat) {
    const L = t();
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = p["name_" + lang] || p.name_ru || p.name_en || "—";
    el.appendChild(h3);
    const add = (txt, cls) => { const d = document.createElement("div"); if (cls) d.className = cls; d.textContent = txt; el.appendChild(d); return d; };
    const rng = (a, b) => (a === null || a === undefined || a === "null" ? "?" : (b === null || b === undefined || b === "null" || b === a ? String(a) : a + "–" + b));
    add((L.lostKinds[p.kind] || p.kind) + " · " + (L.lostWhy[p.why] || p.why));
    add(L.lostBuilt + ": " + rng(p.b0, p.b1) + " · " + L.lostLost + ": " + rng(p.l0, p.l1));
    const st = lostState(p);
    if (st) add(year + ": " + L.lostState[st], "k small");
    if (p.repl && p.repl !== "null") add(L.lostRepl + ": " + p.repl);
    let srcs = [];
    try { srcs = JSON.parse(p.src || "[]"); } catch (e) {}
    addWiki(el, p);
    actions(el, () => openInfo((body) => {
      infoLine(body, L.lostAcc(p.acc, p.pos));
      infoLine(body, p.chk === true || p.chk === "true" ? L.lostChk : L.lostNoChk);
      infoLine(body, L.lostSrc);
      const wl = wikiLink(p);
      if (wl || srcs.length) {
        const d = infoLine(body, L.lostSources + ": ");
        if (wl) d.appendChild(wl);
        srcs.slice(0, 4).forEach((u, i) => { const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = (i || wl ? ", " : "") + decodeURIComponent(u.split("/")[2].replace("www.", "")); d.appendChild(a); });
      }
    }), { id: "lost", name: p.name_ru || p.name_en, reg: "-" });
    new maplibregl.Popup({ maxWidth: "320px" }).setLngLat(lngLat).setDOMContent(el).addTo(map);
  }

  function updateWater() {
    if (!map.getLayer("res-cover")) return;
    const on = $("showWater").checked;
    const early = year < 1951, mid = year >= 1951 && year < 1953, late = year >= 1953;
    const vis = (id, v) => map.setLayoutProperty(id, "visibility", on && v ? "visible" : "none");
    vis("res-cover", early || mid);                      // the area of the future sea: land-coloured before filling
    vis("res-line", late || mid);
    vis("lake54-fill", early || mid);                    // the old salt lakes
    map.setPaintProperty("res-cover", "fill-opacity", mid ? 0.4 : 0.95);
    map.setPaintProperty("lake54-fill", "fill-opacity", mid ? 0.4 : 0.85);
  }

  function waterPopup(p, lngLat) {
    const L = t();
    const el = document.createElement("div");
    el.className = "pop";
    const isRes = p.t === "res";
    const h3 = document.createElement("h3");
    h3.textContent = isRes ? L.waterRes : L.waterLake;
    el.appendChild(h3);
    const add = (txt, cls) => { const d = document.createElement("div"); if (cls) d.className = cls; d.textContent = txt; el.appendChild(d); };
    add(isRes ? L.waterTxtRes(year) : L.waterTxtLake(year));
    add(L.waterSrc, "k small");
    new maplibregl.Popup({ maxWidth: "300px" }).setLngLat(lngLat).setDOMContent(el).addTo(map);
  }

  let views = [];
  const VIEW_WINDOW = 150;                       // a view is offered for 150 years after its date

  function updateViews() {
    const box = $("viewsline");
    if (!box) return;
    const list = views.filter((v) => year >= v.year && year < v.year + (v.window || VIEW_WINDOW));
    box.textContent = "";
    box.hidden = !list.length;
    if (!list.length) return;
    const h = document.createElement("div");
    h.className = "vl-h";
    h.textContent = t().viewsTitle;
    box.appendChild(h);
    for (const v of list) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = v.year + " · " + (v.title[lang] || v.title.en);
      b.addEventListener("click", () => openView(v));
      box.appendChild(b);
    }
  }

  function openView(v) {
    const L = t();
    $("vmTitle").textContent = v.title[lang] || v.title.en;
    const img = $("vmImg");
    img.src = v.image;
    img.alt = v.title[lang] || v.title.en;
    $("vmAuthor").textContent = v.author[lang] || v.author.en;
    $("vmNote").textContent = v.note[lang] || v.note.en;
    const src = $("vmSrc");
    src.textContent = L.viewLicense + ": " + v.license + " · " + L.viewSource + ": ";
    const a = document.createElement("a");
    a.href = v.page; a.target = "_blank"; a.rel = "noopener"; a.textContent = "Wikimedia Commons";
    src.appendChild(a);
    $("viewModal").hidden = false;
  }
  function closeView() { $("viewModal").hidden = true; }
  $("vmClose").addEventListener("click", closeView);
  $("viewModal").addEventListener("click", (e) => { if (e.target === $("viewModal")) closeView(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("viewModal").hidden) closeView(); });

  function updateDensity() {
    if (map.getLayer("density-img")) map.setLayoutProperty("density-img", "visibility", $("showDensity").checked && year >= 2015 ? "visible" : "none");
  }

  function updateSettle() {
    if (!map.getLayer("settle-dot")) return;
    const vis = $("showSettle").checked ? "visible" : "none";
    for (const id of ["settle-dot", "settle-label"]) map.setLayoutProperty(id, "visibility", vis);
    map.setLayoutProperty("settle-label", "text-field", ["get", "name_" + lang]);
    map.setPaintProperty("settle-dot", "circle-color", ["case",
      ["==", ["to-number", ["get", "joined"], -1], -1], "#6a7f99",
      ["<=", ["to-number", ["get", "joined"], -1], year], getCss("--accent"),
      "#b8b8b8"]);
  }

  // ---------- feedback ----------
  let fbObject = null;       // object the user clicked "report" for
  const cfg = window.TT_CONFIG || {};
  function feedbackContext() {
    const c = map.getCenter();
    const parts = [`year=${year}`, `lang=${lang}`, `view=${c.lng.toFixed(4)},${c.lat.toFixed(4)} z${map.getZoom().toFixed(1)}`];
    if (fbObject) parts.push(`object=${fbObject.name || "?"} (reg ${fbObject.reg || "-"}, id ${fbObject.id})`);
    return parts.join("; ");
  }
  function feedbackRefreshCtx() { if ($("fbCtx")) $("fbCtx").value = feedbackContext(); }
  function openFeedback(obj) {
    fbObject = obj || null;
    $("fbStatus").textContent = "";
    $("fbMsg").value = "";
    feedbackRefreshCtx();
    $("fbModal").hidden = false;
    $("fbMsg").focus();
  }
  function closeFeedback() { $("fbModal").hidden = true; }
  $("fbOpen").addEventListener("click", () => openFeedback(null));
  $("fbCancel").addEventListener("click", closeFeedback);
  $("fbModal").addEventListener("click", (e) => { if (e.target === $("fbModal")) closeFeedback(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("fbModal").hidden) closeFeedback(); });
  $("fbForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if ($("fbTrap").value) return;                                   // honeypot: bots fill the hidden field
    const kindLabel = $("fbKind").selectedOptions[0].textContent;
    const body = $("fbMsg").value.trim();
    const contact = $("fbContactInput").value.trim();
    const ctx = feedbackContext();
    const payload = { kind: $("fbKind").value, kindLabel, message: body, contact, context: ctx, page: location.href.split("#")[0] };
    if (cfg.feedbackEndpoint) {
      try {
        await fetch(cfg.feedbackEndpoint, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(payload) });
        $("fbStatus").textContent = t().fbSent;
        setTimeout(closeFeedback, 1800);
        return;
      } catch (err) { /* fall through to GitHub */ }
    }
    if (cfg.repo) {
      const title = `[${payload.kind}] ${body.slice(0, 70).replace(/\s+/g, " ")}`;
      const text = `${body}\n\n---\nType: ${kindLabel}\nContext: ${ctx}\nPage: ${payload.page}${contact ? "\nContact: " + contact : ""}`;
      window.open(`https://github.com/${cfg.repo}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(text)}`, "_blank", "noopener");
      $("fbStatus").textContent = t().fbOpened;
    }
  });
  // mobile: collapsible panel
  $("menu").addEventListener("click", () => {
    const open = document.body.classList.toggle("panel-open");
    $("menu").setAttribute("aria-expanded", open ? "true" : "false");
  });

  function popup(p, lngLat) {
    const L = t();
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    const nmInfo = window.GeoTr ? window.GeoTr.nameInfo(p.name, lang, p.wp) : { text: p.name, src: "orig" };
    const shownName = nmInfo.text;
    h3.textContent = shownName || "—";
    el.appendChild(h3);
    if (p.name && shownName !== p.name) {                       // Georgian original under the translated name
      const o = document.createElement("div");
      o.className = "k small";
      o.textContent = L.trOrig + ": " + p.name;
      el.appendChild(o);
    }
    const row = (k, v) => {
      if (v === null || v === undefined || v === "" || v === "null") return;
      const d = document.createElement("div");
      const kk = document.createElement("span");
      kk.className = "k";
      kk.textContent = k + ": ";
      d.appendChild(kk);
      d.appendChild(document.createTextNode(v));
      el.appendChild(d);
    };
    row(L.address, window.GeoTr ? window.GeoTr.address(p.address, lang) : p.address);
    row(L.cls, (L.classes[p.cls] || p.cls) + " · " + (p.national ? L.national : p.monument ? L.monument : L.object));
    if (p.fo) { row(L.func, L.types[p.fn]); row(L.func0, L.types[p.fo]); }
    else row(L.func0, L.types[p.fn]);
    if (p.ruin === true || p.ruin === "true") row(L.ruinRow, L.ruinTxt);
    row(L.date, window.GeoTr ? window.GeoTr.date(p.raw_date, lang) : p.raw_date);
    if (p.unc === true || p.unc === "true") row("⚠", L.unc);
    addWiki(el, p);
    addPhotos(el, p);
    actions(el, () => openInfo((body) => {
      infoLine(body, L.est + ": " + `${p.ye} (${L.range} ${p.y0}–${p.y1}, ${L.prec}: ${L.precision[p.prec] || p.prec}; ${L.src[p.src] || p.src || "—"})`);
      infoLine(body, L.reg + ": " + p.reg);
      infoLine(body, L.infoRegister);
      if (lang !== "ka" && nmInfo.src === "ai" && L.trNote) infoLine(body, L.trNote);
      photoCredits(body, p);
    }), { id: p.id, name: p.name, reg: p.reg });
    new maplibregl.Popup({ maxWidth: "300px" }).setLngLat(lngLat).setDOMContent(el).addTo(map);
  }

  // JSON loader with retries (a dropped connection must not leave a layer silently empty)
  async function getJSON(url, tries = 4) {
    for (let k = 0; ; k++) {
      try {
        const r = await fetch(url);
        if (!r.ok) throw new Error(r.status);
        return await r.json();
      } catch (e) {
        if (k >= tries - 1) throw e;
        await new Promise((res) => setTimeout(res, 400 * (k + 1)));
      }
    }
  }

  map.on("load", async () => {
    const [pl, mon] = await Promise.all([
      getJSON("data/plans.json"),
      getJSON("data/monuments.json"),
    ]);
    plans = pl;
    try { areas = (await getJSON("data/city_area.json")).areas; } catch (e) { areas = []; }
    try { views = await getJSON("data/views.json"); } catch (e) { views = []; }
    try { if (window.GeoTr) window.GeoTr.setDict(await getJSON("data/names_i18n.json", 1)); } catch (e) { /* not produced yet: names stay Georgian */ }
    const feats = [];
    for (const f of mon.features) {
      const p = f.properties;
      if (typeof p.ye !== "number") { undated++; continue; }
      p.coarse = COARSE.has(p.prec);
      feats.push(f);
    }
    monuments = { type: "FeatureCollection", features: feats };

    let urban = { type: "FeatureCollection", features: [] };
    try { urban = await getJSON("data/urban.json"); } catch (e) {}
    for (const f of urban.features) {
      const s = f.properties.snap;
      if (!urbanMeta[s]) urbanMeta[s] = { src: f.properties.src, partial: false, acc: 0 };
      if (f.properties.partial) urbanMeta[s].partial = true;
      if (f.properties.acc) urbanMeta[s].acc = Math.max(urbanMeta[s].acc, f.properties.acc);
    }
    urbanSnaps = Object.keys(urbanMeta).map(Number).sort((a, b) => a - b);
    let water = { type: "FeatureCollection", features: [] };
    try { water = await getJSON("data/water.json"); } catch (e) {}
    map.addSource("water", { type: "geojson", data: water });
    // before the reservoir: a land-coloured cover over its modern outline (the basemap draws today's water)
    map.addLayer({ id: "res-cover", type: "fill", source: "water", filter: ["==", ["get", "t"], "res"], layout: { visibility: "none" },
                   paint: { "fill-color": "#e6e4da", "fill-opacity": 0.95 } });
    map.addLayer({ id: "res-line", type: "line", source: "water", filter: ["==", ["get", "t"], "res"], layout: { visibility: "none" },
                   paint: { "line-color": "#4a86c8", "line-width": 1.5 } });
    map.addLayer({ id: "lake54-fill", type: "fill", source: "water", filter: ["==", ["get", "t"], "lake54"], layout: { visibility: "none" },
                   paint: { "fill-color": "#7db0ea", "fill-opacity": 0.85, "fill-outline-color": "#3b78bd" } });
    for (const id of ["res-cover", "lake54-fill"]) {
      map.on("click", id, (e) => { if (e.features && e.features[0]) waterPopup(e.features[0].properties, e.lngLat); });
      map.on("mouseenter", id, () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", id, () => { map.getCanvas().style.cursor = ""; });
    }
    try {                                            // building density today (OSM footprints), shown only for recent years
      const dm = await getJSON("data/density.json", 1);
      map.addSource("density", { type: "image", url: "data/density.png", coordinates: dm.coordinates });
      map.addLayer({ id: "density-img", type: "raster", source: "density", layout: { visibility: "none" }, paint: { "raster-opacity": 0.8, "raster-fade-duration": 0 } });
    } catch (e) { /* no density layer */ }
    let admin = { type: "FeatureCollection", features: [] };
    try { admin = await getJSON("data/admin.json"); } catch (e) {}
    map.addSource("admin", { type: "geojson", data: admin });
    map.addLayer({ id: "admin-line", type: "line", source: "admin",
                   paint: { "line-color": "#2b2b2b", "line-width": 1.6, "line-dasharray": [6, 3], "line-opacity": 0.8 } });
    let adminOld = { type: "FeatureCollection", features: [] };
    try { adminOld = await getJSON("data/admin_old.json"); } catch (e) {}
    map.addSource("admin-old", { type: "geojson", data: adminOld });
    map.addLayer({ id: "admin-old-line", type: "line", source: "admin-old", layout: { visibility: "none" },
                   paint: { "line-color": "#777777", "line-width": 1.6, "line-dasharray": [2, 2] } });
    let districts = { type: "FeatureCollection", features: [] };
    try { districts = await getJSON("data/districts.json"); } catch (e) {}
    distModern = districts.features.filter((f) => f.geometry.type === "Point").map((f) => f.properties);
    try { distHist = await getJSON("data/district_history.json"); } catch (e) {}
    map.addSource("districts", { type: "geojson", data: districts });
    map.addLayer({ id: "districts-line", type: "line", source: "districts", filter: ["!=", ["geometry-type"], "Point"],
                   paint: { "line-color": "#555555", "line-width": 1, "line-opacity": 0.7 } });
    map.addLayer({ id: "districts-label", type: "symbol", source: "districts", filter: ["==", ["geometry-type"], "Point"],
                   layout: { "text-field": ["get", "name_" + lang], "text-font": ["Noto Sans Regular"], "text-size": 13 },
                   paint: { "text-color": "#333333", "text-halo-color": "#ffffffcc", "text-halo-width": 1.5 } });
    let settle = { type: "FeatureCollection", features: [] };
    try { settle = await getJSON("data/settlements.json"); } catch (e) {}
    map.addSource("settle", { type: "geojson", data: settle });
    map.addLayer({ id: "settle-dot", type: "circle", source: "settle",
                   paint: { "circle-radius": 5, "circle-stroke-width": 1.5, "circle-stroke-color": "#ffffff",
                            "circle-color": "#888888" } });
    map.addLayer({ id: "settle-label", type: "symbol", source: "settle",
                   layout: { "text-field": ["get", "name_" + lang], "text-font": ["Noto Sans Regular"], "text-size": 12, "text-offset": [0, 1.1], "text-anchor": "top", "text-optional": true },
                   paint: { "text-color": "#222222", "text-halo-color": "#ffffffdd", "text-halo-width": 1.4 } });
    map.on("click", "settle-dot", (e) => { if (e.features && e.features[0]) settlePopup(e.features[0].properties, e.lngLat); });
    map.on("mouseenter", "settle-dot", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "settle-dot", () => { map.getCanvas().style.cursor = ""; });
    let lost = { type: "FeatureCollection", features: [] };
    try { lost = await getJSON("data/lost.json"); } catch (e) {}
    lostFeats = lost.features;
    map.addSource("lost", { type: "geojson", data: lost });
    map.addLayer({ id: "lost-dot", type: "circle", source: "lost",
                   paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 5, 15, 9, 18, 13], "circle-color": "#8b5a2b", "circle-opacity": 0.12,
                            "circle-stroke-width": 2.5, "circle-stroke-color": "#8b5a2b", "circle-stroke-opacity": 1 } });
    map.on("click", "lost-dot", (e) => { if (e.features && e.features[0]) lostPopup(e.features[0].properties, e.lngLat); });
    map.on("mouseenter", "lost-dot", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "lost-dot", () => { map.getCanvas().style.cursor = ""; });
    map.addSource("urban", { type: "geojson", data: urban });
    map.addLayer({ id: "urban-fill", type: "fill", source: "urban",
                   paint: { "fill-color": "#b4412c", "fill-opacity": ["case", ["==", ["get", "kind"], "other"], 0.05, 0.12] } });
    map.addLayer({ id: "urban-line", type: "line", source: "urban",
                   paint: { "line-color": "#b4412c", "line-width": 2, "line-opacity": ["case", ["==", ["get", "kind"], "other"], 0.5, 1] } });
    map.addLayer({ id: "urban-line-approx", type: "line", source: "urban",
                   paint: { "line-color": "#b4412c", "line-width": 2.5, "line-dasharray": [3, 2] } });

    map.addSource("mon", { type: "geojson", data: monuments });
    map.addLayer({
      id: "mon", type: "circle", source: "mon",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, ["case", ["get", "national"], 4, 2], 15, ["case", ["get", "national"], 8, 5], 18, ["case", ["get", "national"], 11, 8]],
        "circle-color": getCss("--old"),
        "circle-opacity": ["case", ["get", "coarse"], 0.45, 0.9],
        "circle-stroke-width": ["case", ["get", "coarse"], 1.2, 0.8],
        "circle-stroke-color": ["case", ["get", "coarse"], getCss("--old"), "#ffffff"],
      },
    });
    map.addLayer({
      id: "mon-ruin", type: "circle", source: "mon", filter: ["==", ["get", "ruin"], true],
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 4, 15, 9, 18, 13],
        "circle-color": "rgba(0,0,0,0)", "circle-stroke-width": 2, "circle-stroke-color": "#555555",
      },
    }, "mon");
    map.on("click", "mon", (e) => { if (e.features && e.features[0]) popup(e.features[0].properties, e.lngLat); });
    map.on("mouseenter", "mon", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "mon", () => { map.getCanvas().style.cursor = ""; });

    buildTicks();
    applyLang();
  });

  $("slider").addEventListener("input", (e) => { const y = v2y(+e.target.value); if (y !== year) { year = y; update(); } });
  for (const id of ["showPlan", "showBnd", "showAdmin", "showDistricts", "showSettle", "showWater", "showDensity", "showLost", "showGhost", "showNat", "showMon", "showObj"]) $(id).addEventListener("change", update);
  $("op").addEventListener("input", (e) => {
    $("opv").textContent = e.target.value + "%";
    for (const p of plans) if (map.getLayer("plan-" + p.id)) map.setPaintProperty("plan-" + p.id, "raster-opacity", e.target.value / 100);
  });
  $("lang").addEventListener("change", (e) => {
    lang = e.target.value;
    try { localStorage.setItem("lang", lang); } catch (e) {}
    applyLang();
  });

  let timer = null;
  $("play").addEventListener("click", () => {
    if (timer) { clearInterval(timer); timer = null; $("play").textContent = "▶"; return; }
    if (year >= MAX) year = MIN;
    $("play").textContent = "❚❚";
    timer = setInterval(() => {
      year = Math.min(MAX, year + (year < 1000 ? 25 : year < 1700 ? 10 : 1));
      update();
      if (year >= MAX) { clearInterval(timer); timer = null; $("play").textContent = "▶"; }
    }, 80);
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", update);
  window.addEventListener("resize", () => { if (urbanSnaps.length || plans.length) buildTicks(); });
  $("slider").value = Math.round(y2v(year));
  $("year").textContent = year;
})();
