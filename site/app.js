(() => {
  "use strict";
  // The timeline starts at the earliest written evidence of the fortress (about 364, see "About"); the long early period is
  // compressed: slider units 0..1000 map piecewise-linearly to years (364-1000 -> 0-90, 1000-1700 -> 90-200, 1700-2026 -> 200-1000)
  const MIN = 364, MAX = 2026, NEW_YEARS = 25;
  const FULL_KNOTS = [[364, 0], [1000, 90], [1700, 200], [2026, 1000]];
  const ZOOM_W = [0, 1000, 600, 330, 230, 150, 90, 50, 26];   // width in years of the window of the zoomed time scale (0 = the whole scale)
  let zoomIx = 0, zoomLo = 364, zoomHi = 2026;
  let runData = null;                                                  // the run route and its sights (data/run_trc2026.json), see addRun
  let rulersMedia = null;                                              // portraits of the rulers and flags of the states (data/rulers_media.json, made by tools/fetch_rulers_media.py)
  let rulersData = null;                                               // forms of state and rulers (data/rulers.json), see buildRulersBand
  let reopenPopup = null, reopenInfo = null, openPop = null;          // the open card (a popup or the modal) and how to build it again, when the language is switched
  let science = [];                                                    // science and culture buildings (data/science.json), see addScience
  let religious = [];                                                  // religious buildings (data/religious.json), see addReligious
  let searchIndex = null, searchRows = [], searchSel = -1;      // search (see the block "search" below)
  let KNOTS = FULL_KNOTS;                         // zoomed scale: one linear piece over the window zoomLo..zoomHi (see applyWindow)
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
        "Топографические карты (слой «Топокарта Генштаба»): серии 1:10 000–1:100 000 издания 1952–2007 годов, открытые тайлы Национального агентства публичного реестра Грузии (maps.gov.ge, район Тбилиси, плюс городской план 1:2 000); тайлы района Тбилиси скачаны в ноябре 2026 года и лежат на этом сайте; карты принадлежат агентству.",
        "Транспорт: линии метро, железной дороги, фуникулёра, подвесных дорог, проспектов и мостов; геометрия © участники OpenStreetMap (ODbL), годы по страницам Википедии и Wikidata (источники в окнах событий и в карточках линий). Трамвай: конка 1883–1910 и улицы маршрутов 1962–2006 по спискам грузинской Википедии; улица рисуется целиком, поэтому линия длиннее настоящей колеи, а у некоторых маршрутов есть разрывы.",
        "События на ползунке и названия улиц по годам: только то, что подтверждено открытой страницей Википедии (ссылка показана в окне события и рядом со строкой улицы). Черновики и поиск готовил ИИ (Gemini), затем каждое утверждение проверялось по странице; неподтверждённое отброшено. Годы переименований в разных статьях иногда расходятся, это указано в примечаниях.",
        "Старые фотографии в «Исторических видах» (Ермаков, Энгель и др.): Wikimedia Commons, общественное достояние; подпись и год по описанию на Commons; к карте не привязаны.",
        "Приватность: страница не использует cookie и аналитику; в браузере хранится только выбранный язык и состояние панелей. При открытии браузер обращается к tiles.openfreemap.org (подложка карты) и к wikimedia.org (превью фотографий), поэтому им виден адрес посетителя. Форма обратной связи через GitHub создаёт публичный Issue.",
        "Плотность застройки: доля площади, занятая контурами зданий OpenStreetMap (© участники OpenStreetMap, ODbL), в ячейках около 100×100 м; это состояние на момент выгрузки (ноябрь 2026), у зданий в OSM нет годов постройки, поэтому слой показывается только для современных лет.",
        "Административная граница Тбилиси (2019): OCHA COD-AB Georgia (HDX), источник — Национальная статистическая служба Грузии, лицензия CC BY-IGO. Площадь 502,5 км² совпадает с данными диссертации для периода после 2006 года.",
        "Границы районов и их названия: © участники OpenStreetMap, лицензия ODbL (этот набор данных — производная база; при повторном использовании сохраняйте ту же лицензию и атрибуцию). Показано современное деление на 10 районов.",
        "Серая пунктирная линия 1973–2005 годов — граница из geoBoundaries (ADM2, метаданные: 2007). Проверка по положению посёлков: присоединённые в 2006 году (Цхнети, Цавкиси, Окрокана, Кикети, Бетания, Диди Дигоми, Загэси) лежат вне неё, присоединённые раньше (Поничала, Орхеви, Глдани, Варкетили) внутри, то есть она соответствует границе до реформы 2006 года. Её площадь ≈ 330 км² меньше 354 км² из диссертации, причина не установлена. Деление на районы и их названия по периодам (без границ) пересказаны ИИ по вторичным источникам и не проверены по первоисточникам.",
        "Площадь города: Н. Харебава, диссертация, Тбилисский государственный университет им. Ив. Джавахишвили, 2024.",
        "Фото: Wikimedia Commons, с указанием автора и лицензии; подбираются по координатам (не дальше 30 м, более дальние только после проверки) и всё же могут показывать соседнее здание.",
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
      showRel: "Религиозные сооружения (появляются и исчезают по годам)", relNames: { orthodox: "Грузинская православная", russian: "Русская православная", lutheran: "Лютеранская", yazidi: "Езидская", armenian: "Армянская апостольская", catholic: "Католическая", jewish: "Иудейская", muslim: "Мусульманская", zoroastrian: "Зороастрийская" }, relApprox: "точка на карте приблизительная", relBuilt: "Построено", relGone: "Утрачено", relStatus: "Сейчас", relSrc: "Источники",
      showRulers: "Правители и формы власти (полоса под шкалой)", ruleNow: "Кто правил", ruleState: "Государство", ruleOver: "Внешняя власть", ruleAdmin: "Единица управления", ruleForm: "Форма власти", ruleYears: "Годы", ruleNoData: "нет данных",
      showRun: "Tbilisi Running Club: маршрут City Run 2026 и что увидеть по пути (сегодняшний город)", runStats: (r, n) => `${r.length_km} км, высота ${r.ele_min}-${r.ele_max} м, ${n} достопримечательностей`, runKm: "Километр", runDist: "От трассы", runYear: "Дата по реестру", runWiki: "Википедия", runStart: "Старт и финиш", runList: "По порядку вдоль маршрута", runNote: "В список входят объекты данных сайта, чья точка лежит не дальше 150 м от трассы: национального значения, со статьёй в Википедии, церкви, мосты, театры, музеи, стены и крепости. Расстояние считается от точки объекта до линии трассы, поэтому крупные здания могут быть ближе. Это не проверка видимости.", runSrc: "Маршрут (геометрия)",
      topoPlanOpt: "1:2 000 · городской план (z17)", legDistEx: "Мтацминда", legSetEx: "Коджори", ariaLang: "Язык", ariaClose: "закрыть", fbContactPh: "email или telegram (необязательно)",
      showSci: "Наука и культура: институты, университеты, музеи, театры (появляются по годам)", sciKinds: { science: "Наука и образование", culture: "Культура" }, sciFounded: "Основано", sciBuilt: "Здание", sciFrom: "Появляется", sciSrc: "Источники", sciFaint: "бледная точка: здание ещё не построено или учреждение было в другом месте",
      loadMap: "Загрузка карты и данных…", loadPlan: "Загрузка плана…", loadFail: "Не удалось загрузить данные. Обновите страницу (Ctrl+F5).",
      topoAutoNote: "Сейчас топокарта включена автоматически (годы 1953–2005, вместо плана). Чтобы скрыть её, снимите галочку «С 1953 по 2005 год показывать топокарту вместо плана» ниже.",
      trRoutes62: "Маршруты по списку 1962 г.", trRoutes86: "Маршруты по списку 1986 г.",
      chgTitle: "Что нового", chgNew: "Новое", chgFix: "Исправлено", chgFail: "Не удалось загрузить журнал изменений.",
      trGapEarly: "С 25 декабря 1904 в Тбилиси ходил электрический трамвай. Его линии на карте показаны с плана 1913 года, на этот год не нанесены.", trGapMid: (km, y) => `Трамвай в эти годы был (около ${km} км сети на ${y} год, ru.wikipedia), но его линии на карте не нанесены: данных об улицах нет.`,
      runPage: "Страница маршрута: карта, описания и фото", runCopy: "Скопировать ссылку", runCopied: "Ссылка скопирована",
      searchBtn: "Поиск", searchPh: "Название, адрес, событие или год", searchNone: "Ничего не найдено", searchYear: "Перейти к году", searchMore: "Показаны первые результаты, уточните запрос",
      zoomL: "Сдвинуть шкалу к более ранним годам", zoomR: "Сдвинуть шкалу к более поздним годам",
      zoomAll: "Всё", zoomIn: "Приблизить шкалу времени", zoomOut: "Отдалить шкалу времени",
      viewPrev: "Предыдущее фото",
      viewNext: "Следующее фото",
      viewLicense: "лицензия",
      viewSource: "источник",
      trNote: "Название и улицы переведены автоматически (ИИ) с грузинского оригинала из реестра и могут быть неточными.",
      trOrig: "оригинал",
      fbContactWarn: "Внимание: при отправке через GitHub контакт попадёт в публичный Issue и будет виден всем. Не указывайте то, что не хотите публиковать.",
      infoBtn: "Источники и подробности",
      infoTitle: "Источники и подробности",
      evCats: { unrest: "Протест и насилие", oldest: "Старейшая сохранившаяся постройка", build: "Строительство и достижения", invasion: "Нашествие, осада, взятие", earthquake: "Землетрясение", fire: "Пожар", flood: "Наводнение", power: "Смена власти, политическое событие", other: "Событие" },
      evSrc: "Источники",
      evNote: "Дата и подробности из статей Википедии (en, ru).",
      infoRegister: "Данные объекта: публичные сведения реестра недвижимых памятников культурного наследия Грузии (Национальное агентство сохранения культурного наследия), сокращённая выжимка для некоммерческого использования. Условия и полный список источников: «О проекте и источниках» на боковой панели.",
      infoPhotos: "Фотографии",
      showDensity: "Плотность застройки (OSM, сейчас)",
      legDensity: "Плотность застройки по зданиям OSM (с 2015): светлее — реже, тёмно-красный — очень плотно",
      showTransport: "Транспорт: метро, ж/д, фуникулёр, проспекты",
      legTransport: "Транспорт по годам: метро (красная линия Ахметели — Варкетили, зелёная Сабурталинская), проспекты и мосты (оранжевый и синий), конка 1883–1910 (коричневая), железная дорога (серый), фуникулёр и канатная дорога (фиолетовый пунктир)",
      trKinds: { metro_line: "линия метро", metro_station: "станция метро", railway: "железная дорога", funicular: "фуникулёр", cablecar: "канатная дорога", avenue: "проспект", bridge: "мост", tram: "трамвай (конка, улицы маршрутов)" },
      trPeriod: (a, b, c, d) => "с " + a + (b < 9999 ? " до " + b : "") + (c > 0 ? ", затем с " + c + (d < 9999 ? " до " + d : "") : ""),
      trEvents: "Транспорт и дороги в эти годы",
      showTopo: "Топокарта Генштаба (НАПР, Грузия) поверх карты",
      topoNote: "Советские топокарты разных изданий (издания указаны в списке); открытые тайлы maps.gov.ge (район Тбилиси). Участки листов могут быть разных лет.",
      swLeft: "старый план (слева от полосы)", swRight: "современная карта (справа)",
      autoTopo: "С 1953 по 2005 год показывать топокарту вместо плана",
      topoLine: (name) => "Топокарта Генштаба (НАПР): " + name + ". Листы разных изданий, участки могут быть разных лет.",
      showStLabels: "Названия улиц того года на карте (по проверенным данным)",
      howTitle: "Как пользоваться",
      how: [
        "Ползунок внизу задаёт год; ▶ запускает анимацию. Значки над ползунком отмечают исторические события: нажмите, чтобы перейти к году и прочитать источник.",
        "Нажмите на точку объекта, чтобы открыть карточку. Адрес страницы запоминает объект, год и место на карте: ссылкой можно поделиться.",
        "Окно «Фильтры» справа включает слои: старый план, топокарту (с 1953 года она заменяет план), транспорт, названия улиц того года.",
        "«Шторка»: слева от белой полосы старый план или топокарта, справа сегодняшняя карта. «Что было здесь»: клик по карте показывает эту точку на всех старых планах.",
        "Окна «Справка» и «Фильтры» можно скрыть кнопками вверху.",
      ],
      roadLabels: "Названия современных улиц поверх старого плана",
      popTitle: "Население города",
      popNote: "Город в границах разных лет, данные и методики разные: ряд ориентировочный. Тёмные точки: переписи и статистика, светлые: оценки (не подтверждены).",
      popBefore: "Данных о населении на этот год нет (самая ранняя оценка: 1803).",
      show94: "Объекты 1894 года по описанию иранского путешественника (гостиницы, театры, баня, музеи)",
      c94Title: "Из описания Тбилиси 1894 года",
      c94Pos: "Положение",
      c94Conf: { high: "уверенность высокая", medium: "уверенность средняя (около 100-150 м)", low: "уверенность низкая (200 м и больше)" },
      c94Src: "Источник",
      btnInfo: "Справка", btnFilters: "Фильтры", evCluster: "События рядом на шкале (выберите)", btnViews: "Виды", viewsAll: "Все виды (не только к выбранному году)", viewsNone: "К этому году видов нет: для части лет свободных фото не нашлось. Включите «Все виды».", filtersTitle: "Фильтры и слои",
      stTitle: "Как назывались улицы в этом году (проверено по Википедии)",
      stNow: "сейчас",
      stMore: "Названия по годам известны не для всех улиц.",
      baseOff: "Подложка карты (OpenFreeMap) недоступна из вашей сети, показан упрощённый фон без улиц и зданий. Исторические слои, планы и названия работают.",
      showStreets: "Улицы по плану 1913 г. (проба, автоматическая обводка)",
      showSwipe: "Шторка: слева старый план, справа современная карта (двигай полосу)",
      showHere: "Что было здесь: клик по карте показывает эту точку на всех планах",
      hereTitle: "Эта точка на старых планах",
      hereLoad: "Планы загружаются по очереди…",
      hereNone: "Эта точка за пределами всех планов.",
      hereAcc: (m) => "точность привязки ±" + m + " м",
      hereNote: "Окно около 260 м. Каждый план привязан к карте со своей погрешностью, поэтому сдвиг в десятки метров возможен.",
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
        "Topographic maps (the General Staff topo layer): 1:10 000 to 1:100 000 series, editions 1952-2007, open tiles of the National Agency of Public Registry of Georgia (maps.gov.ge); tiles of the Tbilisi area were downloaded in November 2026 and are served from this site; the maps belong to the agency.",
        "Transport: metro, railway, funicular, cable car, avenue and bridge lines; geometry (c) OpenStreetMap contributors (ODbL), years from Wikipedia and Wikidata pages (sources in the event windows and on the line cards). Tram: the horse tram of 1883-1910 and the streets of the routes of 1962-2006 from the Georgian Wikipedia lists; a street is drawn over its whole length, so the line is longer than the real track and some routes have gaps.",
        "Events on the slider and street names by year: only what an open Wikipedia page confirms (the link is shown in the event window and next to the street line). Drafts and searches were prepared by an AI (Gemini), then every statement was checked against the page; unconfirmed items were dropped. The years of renaming sometimes differ between articles; this is noted.",
        "Old photographs in the Historical views (Yermakov, Engel and others): Wikimedia Commons, public domain; the caption and the year are as given on Commons; not tied to the map.",
        "Privacy: the page uses no cookies or analytics; only the chosen language and the state of the panels are stored in the browser. On loading, the browser contacts tiles.openfreemap.org (basemap) and wikimedia.org (photo previews), so these services can see the visitor's address. The feedback form through GitHub creates a public Issue.",
        "Building density: the share of ground covered by OpenStreetMap building footprints (© OpenStreetMap contributors, ODbL) in cells of about 100×100 m; it shows the state at the time of export (November 2026); OSM buildings have no construction years, so the layer is shown only for recent years.",
        "Administrative boundary of Tbilisi (2019): OCHA COD-AB Georgia (HDX), source: National Statistics Office of Georgia, licence CC BY-IGO. Its area of 502.5 km² matches the thesis figure for the period after 2006.",
        "District boundaries and names: © OpenStreetMap contributors, ODbL (this dataset is a derived database; keep the same licence and attribution if you reuse it). The current division into 10 districts is shown.",
        "The grey dashed line for 1973–2005 is a boundary from geoBoundaries (ADM2, metadata: 2007). Checked by the position of settlements: those annexed in 2006 (Tskneti, Tsavkisi, Okrokana, Kiketi, Betania, Didi Dighomi, Zahesi) lie outside it, those annexed earlier (Ponichala, Orkhevi, Gldani, Varketili) inside, so it matches the pre-2006 limit. Its area of about 330 km² is smaller than the 354 km² in the thesis, the reason is not established. The district divisions and names by period (without boundaries) were relayed by an AI from secondary sources and are not checked against the originals.",
        "City area: N. Kharebava, PhD thesis, Ivane Javakhishvili Tbilisi State University, 2024.",
        "Photos: Wikimedia Commons, shown with author and licence; matched by coordinates (not farther than 30 m; farther ones only after a check) and may still show a neighbouring building.",
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
      showRel: "Religious buildings (appear and disappear by year)", relNames: { orthodox: "Georgian Orthodox", russian: "Russian Orthodox", lutheran: "Lutheran", yazidi: "Yazidi", armenian: "Armenian Apostolic", catholic: "Catholic", jewish: "Jewish", muslim: "Muslim", zoroastrian: "Zoroastrian" }, relApprox: "the point on the map is approximate", relBuilt: "Built", relGone: "Lost", relStatus: "Today", relSrc: "Sources",
      showRulers: "Rulers and forms of government (a band under the scale)", ruleNow: "Who ruled", ruleState: "State", ruleOver: "Outside power", ruleAdmin: "Administrative unit", ruleForm: "Form of rule", ruleYears: "Years", ruleNoData: "no data",
      showRun: "Tbilisi Running Club: the City Run 2026 route and what to see on the way (today's city)", runStats: (r, n) => `${r.length_km} km, elevation ${r.ele_min}-${r.ele_max} m, ${n} sights`, runKm: "Kilometre", runDist: "From the route", runYear: "Date in the register", runWiki: "Wikipedia", runStart: "Start and finish", runList: "In order along the route", runNote: "The list holds the objects of the data of this site whose point lies within 150 m of the track: of national significance, with a Wikipedia article, churches, bridges, theatres, museums, walls and fortresses. The distance is from the point of the object to the line of the track, so large buildings may be closer. This is not a check of visibility.", runSrc: "Route (geometry)",
      topoPlanOpt: "1:2 000 · city plan (z17)", legDistEx: "Mtatsminda", legSetEx: "Kojori", ariaLang: "Language", ariaClose: "close", fbContactPh: "email or telegram (optional)",
      showSci: "Science and culture: institutes, universities, museums, theatres (appear by year)", sciKinds: { science: "Science and education", culture: "Culture" }, sciFounded: "Founded", sciBuilt: "Building", sciFrom: "Appears", sciSrc: "Sources", sciFaint: "a faint point: the building is not yet built or the institution was elsewhere",
      loadMap: "Loading the map and data…", loadPlan: "Loading the plan…", loadFail: "The data could not be loaded. Reload the page (Ctrl+F5).",
      topoAutoNote: "The topographic map is on automatically now (the years 1953-2005, instead of a plan). To hide it, clear the box \"From 1953 to 2005 show the topographic map instead of a plan\" below.",
      trRoutes62: "Routes of the list of 1962", trRoutes86: "Routes of the list of 1986",
      chgTitle: "What is new", chgNew: "New", chgFix: "Fixed", chgFail: "The log of changes could not be loaded.",
      trGapEarly: "An electric tram ran in Tbilisi from 25 December 1904. Its lines are shown on the map from the plan of 1913, they are not drawn for this year.", trGapMid: (km, y) => `There was a tram in these years (about ${km} km of network in ${y}, ru.wikipedia), but its lines are not drawn on the map: there are no data on the streets.`,
      runPage: "The page of the route: map, descriptions and photos", runCopy: "Copy link", runCopied: "Link copied",
      searchBtn: "Search", searchPh: "Name, address, event or year", searchNone: "Nothing found", searchYear: "Go to the year", searchMore: "Only the first results are shown, narrow the query",
      zoomL: "Move the scale to earlier years", zoomR: "Move the scale to later years",
      zoomAll: "All", zoomIn: "Zoom the time scale in", zoomOut: "Zoom the time scale out",
      viewPrev: "Previous photo",
      viewNext: "Next photo",
      viewLicense: "licence",
      viewSource: "source",
      trNote: "The name and streets were translated automatically (AI) from the Georgian original in the register and may be inexact.",
      trOrig: "original",
      fbContactWarn: "Note: when sent through GitHub, the contact goes into a public Issue and is visible to everyone. Leave it empty if you do not want that.",
      infoBtn: "Sources and details",
      infoTitle: "Sources and details",
      evCats: { unrest: "Protest and violence", oldest: "Oldest surviving building", build: "Construction and achievements", invasion: "Invasion, siege, capture", earthquake: "Earthquake", fire: "Fire", flood: "Flood", power: "Change of power, political event", other: "Event" },
      evSrc: "Sources",
      evNote: "Date and details from Wikipedia articles (en, ru).",
      infoRegister: "Object data: public records of the register of immovable cultural heritage monuments of Georgia (National Agency for Cultural Heritage Preservation), a reduced extract for non-commercial use. Terms and the full list of sources: “About and sources” in the side panel.",
      infoPhotos: "Photographs",
      showDensity: "Building density (OSM, today)",
      legDensity: "Building density from OSM footprints (from 2015): lighter is sparser, dark red is very dense",
      showTransport: "Transport: metro, railway, funicular, avenues",
      legTransport: "Transport by year: metro (red Akhmeteli-Varketili line, green Saburtalo line), avenues and bridges (orange and blue), horse tram 1883-1910 (brown), railway (grey), funicular and cable car (violet dashes)",
      trKinds: { metro_line: "metro line", metro_station: "metro station", railway: "railway", funicular: "funicular", cablecar: "cable car", avenue: "avenue", bridge: "bridge", tram: "tram (konka, route streets)" },
      trPeriod: (a, b, c, d) => "from " + a + (b < 9999 ? " until " + b : "") + (c > 0 ? ", then from " + c + (d < 9999 ? " until " + d : "") : ""),
      trEvents: "Transport and roads in these years",
      showTopo: "General Staff topographic map (NAPR, Georgia) over the map",
      topoNote: "Soviet topographic maps of various editions (the editions are in the list); open tiles of maps.gov.ge (Tbilisi area). Parts of a sheet can be from different years.",
      swLeft: "old plan (left of the bar)", swRight: "today's map (right)",
      autoTopo: "From 1953 to 2005 show the topographic map instead of a plan",
      topoLine: (name) => "General Staff topographic map (NAPR): " + name + ". Sheets of various editions; parts can be from different years.",
      showStLabels: "Street names of that year on the map (checked data only)",
      howTitle: "How to use",
      how: [
        "The slider at the bottom sets the year; ▶ plays the animation. The icons above it mark historical events: click one to jump to that year and read the source.",
        "Click an object dot to open its card. The address of the page remembers the object, the year and the place on the map, so the link can be shared.",
        "The Filters window on the right switches layers: old plan, topographic map (from 1953 it replaces the plan), transport, street names of that year.",
        "Swipe: left of the white bar is the old plan or topographic map, right of it today's map. What was here: a click on the map shows that point on every old plan.",
        "The Info and Filters windows can be hidden with the buttons at the top.",
      ],
      roadLabels: "Names of present-day streets over the old plan",
      popTitle: "Population of the city",
      popNote: "The city within its borders of each year; sources and methods differ, so the series is approximate. Dark dots: censuses and statistics, hollow dots: estimates (not confirmed).",
      popBefore: "No population figure for this year (the earliest estimate is 1803).",
      show94: "Objects of 1894 from the Persian traveller's description (hotels, theatres, bath, museums)",
      c94Title: "From the 1894 description of Tbilisi",
      c94Pos: "Position",
      c94Conf: { high: "high confidence", medium: "medium confidence (about 100-150 m)", low: "low confidence (200 m or more)" },
      c94Src: "Source",
      btnInfo: "Info", btnFilters: "Filters", evCluster: "Events close together on the scale (choose one)", btnViews: "Views", viewsAll: "All views (not only for the chosen year)", viewsNone: "No views for this year: for some years no freely licensed photographs were found. Tick \"All views\".", filtersTitle: "Filters and layers",
      stTitle: "Street names in this year (checked against Wikipedia)",
      stNow: "today",
      stMore: "Names by year are known only for some streets.",
      baseOff: "The basemap (OpenFreeMap) is not reachable from your network, so a simplified background without streets and buildings is shown. The historical layers, plans and names work.",
      showStreets: "Streets on the 1913 plan (experiment, automatic trace)",
      showSwipe: "Swipe: old plan on the left, today's map on the right (drag the bar)",
      showHere: "What was here: click the map to see that point on every plan",
      hereTitle: "This point on the old plans",
      hereLoad: "Plans are loading one by one…",
      hereNone: "This point is outside every plan.",
      hereAcc: (m) => "georeferencing accuracy ±" + m + " m",
      hereNote: "The window is about 260 m wide. Every plan is fitted to the map with its own error, so a shift of tens of metres is possible.",
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
        "ტოპოგრაფიული რუკები (გენშტაბის ტოპორუკის ფენა): 1:10 000–1:100 000 სერიები, 1952–2007 წლების გამოცემები, საჯარო ტაილები საქართველოს საჯარო რეესტრის ეროვნული სააგენტოსგან (maps.gov.ge); თბილისის ტერიტორიის ტაილები გადმოწერილია 2026 წლის ნოემბერში და ინახება ამ საიტზე; რუკები სააგენტოს ეკუთვნის.",
        "ტრანსპორტი: მეტროს, რკინიგზის, ფუნიკულიორის, საბაგიროს, გამზირებისა და ხიდების ხაზები; გეომეტრია (c) OpenStreetMap-ის მონაწილეები (ODbL), წლები ვიკიპედიისა და Wikidata-ს გვერდებიდან (წყაროები მოვლენების ფანჯრებსა და ხაზის ბარათებშია). ტრამვაი: 1883-1910 წლების კონკა და 1962-2006 წლების მარშრუტების ქუჩები ქართული ვიკიპედიის სიებიდან; ქუჩა მთლიანადაა დახატული, ამიტომ ხაზი რეალურ ლიანდაგზე გრძელია და ზოგ მარშრუტს წყვეტები აქვს.",
        "მოვლენები სლაიდერზე და ქუჩების სახელები წლების მიხედვით: მხოლოდ ის, რასაც ვიკიპედიის ღია გვერდი ადასტურებს (ბმული ნაჩვენებია მოვლენის ფანჯარასა და ქუჩის სტრიქონთან). ნახაზებსა და ძიებას ხელოვნური ინტელექტი (Gemini) ამზადებდა, შემდეგ თითოეული დებულება გვერდის მიხედვით მოწმდებოდა; დაუდასტურებელი ამოვარდა. გადარქმევის წლები სტატიებს შორის ზოგჯერ განსხვავდება; ეს აღნიშნულია.",
        "ძველი ფოტოები «ისტორიულ ხედებში» (ერმაკოვი, ენგელი და სხვ.): Wikimedia Commons, საჯარო სივრცე; წარწერა და წელი Commons-ის აღწერის მიხედვით; რუკას არ უკავშირდება.",
        "კონფიდენციალურობა: გვერდი არ იყენებს cookie-ს და ანალიტიკას; ბრაუზერში მხოლოდ არჩეული ენა და პანელების მდგომარეობა ინახება. ჩატვირთვისას ბრაუზერი მიმართავს tiles.openfreemap.org-ს (რუკის ფონი) და wikimedia.org-ს (ფოტოების გადახედვა), ამიტომ ამ სერვისებს ეხილვებათ სტუმრის მისამართი. GitHub-ით გაგზავნილი უკუკავშირი საჯარო Issue-ს ქმნის.",
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
      showRel: "რელიგიური ნაგებობები (ჩნდება და ქრება წლების მიხედვით)", relNames: { orthodox: "ქართული მართლმადიდებლური", russian: "რუსული მართლმადიდებლური", lutheran: "ლუთერანული", yazidi: "ეზიდური", armenian: "სომხური სამოციქულო", catholic: "კათოლიკური", jewish: "ებრაული", muslim: "მუსლიმური", zoroastrian: "ზოროასტრული" }, relApprox: "წერტილი რუკაზე მიახლოებითია", relBuilt: "აშენდა", relGone: "დაკარგულია", relStatus: "დღეს", relSrc: "წყაროები",
      showRulers: "მმართველები და მმართველობის ფორმები (ზოლი სკალის ქვეშ)", ruleNow: "ვინ მართავდა", ruleState: "სახელმწიფო", ruleOver: "გარე ძალა", ruleAdmin: "ადმინისტრაციული ერთეული", ruleForm: "მმართველობის ფორმა", ruleYears: "წლები", ruleNoData: "მონაცემი არ არის",
      showRun: "Tbilisi Running Club: City Run 2026-ის მარშრუტი და რა ჩანს გზაზე (დღევანდელი ქალაქი)", runStats: (r, n) => `${r.length_km} კმ, სიმაღლე ${r.ele_min}-${r.ele_max} მ, ${n} ღირსშესანიშნაობა`, runKm: "კილომეტრი", runDist: "ტრასიდან", runYear: "თარიღი რეესტრში", runWiki: "ვიკიპედია", runStart: "სტარტი და ფინიში", runList: "მარშრუტის გასწვრივ თანმიმდევრობით", runNote: "სიაში შედის საიტის მონაცემთა ობიექტები, რომელთა წერტილი ტრასიდან 150 მ-ს არ აცილდება: ეროვნული მნიშვნელობის, ვიკიპედიის სტატიით, ეკლესიები, ხიდები, თეატრები, მუზეუმები, გალავნები და ციხეები. მანძილი ობიექტის წერტილიდან ტრასის ხაზამდეა. ეს ხილვადობის შემოწმება არ არის.", runSrc: "მარშრუტი (გეომეტრია)",
      topoPlanOpt: "1:2 000 · ქალაქის გეგმა (z17)", legDistEx: "მთაწმინდა", legSetEx: "კოჯორი", ariaLang: "ენა", ariaClose: "დახურვა", fbContactPh: "ელფოსტა ან ტელეგრამი (არასავალდებულო)",
      showSci: "მეცნიერება და კულტურა: ინსტიტუტები, უნივერსიტეტები, მუზეუმები, თეატრები (ჩნდება წლების მიხედვით)", sciKinds: { science: "მეცნიერება და განათლება", culture: "კულტურა" }, sciFounded: "დაარსდა", sciBuilt: "შენობა", sciFrom: "ჩნდება", sciSrc: "წყაროები", sciFaint: "ფერმკრთალი წერტილი: შენობა ჯერ არ არის აშენებული ან დაწესებულება სხვაგან იყო",
      loadMap: "რუკა და მონაცემები იტვირთება…", loadPlan: "გეგმა იტვირთება…", loadFail: "მონაცემების ჩატვირთვა ვერ მოხერხდა. განაახლეთ გვერდი (Ctrl+F5).",
      topoAutoNote: "ტოპოგრაფიული რუკა ახლა ავტომატურად არის ჩართული (1953–2005 წლები, გეგმის ნაცვლად). გასაქრობად მოხსენით ქვემოთ მოცემული ნიშნული „1953-2005 წლებში გეგმის ნაცვლად ტოპორუკის ჩვენება“.",
      trRoutes62: "მარშრუტები 1962 წლის სიით", trRoutes86: "მარშრუტები 1986 წლის სიით",
      chgTitle: "რა არის ახალი", chgNew: "ახალი", chgFix: "გასწორდა", chgFail: "ცვლილებათა ჟურნალის ჩატვირთვა ვერ მოხერხდა.",
      trGapEarly: "თბილისში ელექტრო ტრამვაი 1904 წლის 25 დეკემბრიდან დადიოდა. მისი ხაზები რუკაზე 1913 წლის გეგმიდან ჩანს, ამ წლისთვის დატანილი არ არის.", trGapMid: (km, y) => `ამ წლებში ტრამვაი იყო (ქსელის დაახლოებით ${km} კმ ${y} წელს, ru.wikipedia), მაგრამ მისი ხაზები რუკაზე დატანილი არ არის: ქუჩების შესახებ მონაცემები არ გვაქვს.`,
      runPage: "მარშრუტის გვერდი: რუკა, აღწერები და ფოტოები", runCopy: "ბმულის კოპირება", runCopied: "ბმული დაკოპირდა",
      searchBtn: "ძებნა", searchPh: "სახელი, მისამართი, მოვლენა ან წელი", searchNone: "ვერაფერი მოიძებნა", searchYear: "გადასვლა წელზე", searchMore: "ნაჩვენებია პირველი შედეგები, დააზუსტეთ მოთხოვნა",
      zoomL: "სკალის გადაწევა ადრეული წლებისკენ", zoomR: "სკალის გადაწევა გვიანდელი წლებისკენ",
      zoomAll: "ყველა", zoomIn: "დროის სკალის გაზრდა", zoomOut: "დროის სკალის დაპატარავება",
      viewPrev: "წინა ფოტო",
      viewNext: "შემდეგი ფოტო",
      viewLicense: "ლიცენზია",
      viewSource: "წყარო",
      fbContactWarn: "ყურადღება: GitHub-ის გავლით გაგზავნისას კონტაქტი საჯარო Issue-ში მოხვდება და ყველას დაენახება. თუ არ გსურთ, ნუ მიუთითებთ.",
      infoBtn: "წყაროები და დეტალები",
      infoTitle: "წყაროები და დეტალები",
      evCats: { unrest: "პროტესტი და ძალადობა", oldest: "უძველესი შემორჩენილი ნაგებობა", build: "მშენებლობა და მიღწევები", invasion: "შემოსევა, ალყა, აღება", earthquake: "მიწისძვრა", fire: "ხანძარი", flood: "წყალდიდობა", power: "ხელისუფლების ცვლილება, პოლიტიკური მოვლენა", other: "მოვლენა" },
      evSrc: "წყაროები",
      evNote: "თარიღი და დეტალები ვიკიპედიის სტატიებიდან (en, ru).",
      infoRegister: "ობიექტის მონაცემები: საქართველოს კულტურული მემკვიდრეობის უძრავი ძეგლების რეესტრის საჯარო ცნობები (კულტურული მემკვიდრეობის დაცვის ეროვნული სააგენტო), შემოკლებული ამონარიდი არაკომერციული გამოყენებისთვის. პირობები და წყაროების სრული სია: „პროექტის შესახებ და წყაროები“ გვერდით პანელში.",
      infoPhotos: "ფოტოები",
      showDensity: "განაშენიანების სიმჭიდროვე (OSM, დღეს)",
      legDensity: "განაშენიანების სიმჭიდროვე OSM-ის შენობების მიხედვით (2015-დან): ღია — იშვიათი, მუქი წითელი — ძალიან მჭიდრო",
      showTransport: "ტრანსპორტი: მეტრო, რკინიგზა, ფუნიკულიორი, გამზირები",
      legTransport: "ტრანსპორტი წლების მიხედვით: მეტრო (წითელი ახმეტელი-ვარკეთილის ხაზი, მწვანე საბურთალოს ხაზი), გამზირები და ხიდები (ნარინჯისფერი და ლურჯი), კონკა 1883–1910 (ყავისფერი), რკინიგზა (ნაცრისფერი), ფუნიკულიორი და საბაგირო (იისფერი პუნქტირი)",
      trKinds: { metro_line: "მეტროს ხაზი", metro_station: "მეტროს სადგური", railway: "რკინიგზა", funicular: "ფუნიკულიორი", cablecar: "საბაგირო", avenue: "გამზირი", bridge: "ხიდი", tram: "ტრამვაი (კონკა, მარშრუტების ქუჩები)" },
      trPeriod: (a, b, c, d) => a + "-დან" + (b < 9999 ? " " + b + "-მდე" : "") + (c > 0 ? ", შემდეგ " + c + "-დან" + (d < 9999 ? " " + d + "-მდე" : "") : ""),
      trEvents: "ტრანსპორტი და გზები ამ წლებში",
      showTopo: "გენშტაბის ტოპოგრაფიული რუკა (სსიპ, საქართველო) რუკის თავზე",
      topoNote: "საბჭოთა ტოპორუკები სხვადასხვა გამოცემისა (გამოცემები სიაშია); maps.gov.ge-ს საჯარო ტაილები (თბილისის რაიონი). ფურცლის ნაწილები შეიძლება სხვადასხვა წლისა იყოს.",
      swLeft: "ძველი გეგმა (ზოლის მარცხნივ)", swRight: "თანამედროვე რუკა (მარჯვნივ)",
      autoTopo: "1953-2005 წლებში გეგმის ნაცვლად ტოპორუკის ჩვენება",
      topoLine: (name) => "გენშტაბის ტოპოგრაფიული რუკა (სსიპ): " + name + ". სხვადასხვა გამოცემის ფურცლები, ნაწილები შეიძლება სხვადასხვა წლისა იყოს.",
      showStLabels: "ქუჩების იმ წლის სახელები რუკაზე (შემოწმებული მონაცემები)",
      howTitle: "როგორ გამოვიყენოთ",
      how: [
        "ქვედა ბოლოში სლაიდერი წელს არჩევს; ▶ ანიმაციას ჩართავს. სლაიდერის ზემოთ ხატები ისტორიულ მოვლენებს აღნიშნავს: დააწკაპუნეთ, რომ წელზე გადახვიდეთ და წყარო წაიკითხოთ.",
        "ობიექტის წერტილზე დაწკაპუნებით იხსნება ბარათი. გვერდის მისამართი ობიექტს, წელს და ადგილს იმახსოვრებს, ამიტომ ბმულის გაზიარება შეიძლება.",
        "მარჯვენა ფანჯარა «ფილტრები და ფენები» ფენებს რთავს: ძველი გეგმა, ტოპორუკა (1953 წლიდან გეგმის ნაცვლადაა), ტრანსპორტი, იმ წლის ქუჩების სახელები.",
        "შედარება: თეთრი ზოლის მარცხნივ ძველი გეგმა ან ტოპორუკაა, მარჯვნივ დღევანდელი რუკა. «რა იყო აქ»: რუკაზე დაწკაპუნება ამ წერტილს ყველა ძველ გეგმაზე აჩვენებს.",
        "«ცნობა» და «ფილტრები» ფანჯრების დამალვა ზედა ღილაკებით შეიძლება.",
      ],
      roadLabels: "დღევანდელი ქუჩების სახელები ძველი გეგმის თავზე",
      popTitle: "ქალაქის მოსახლეობა",
      popNote: "ქალაქი თითოეული წლის საზღვრებში; წყაროები და მეთოდები განსხვავდება, ამიტომ რიგი მიახლოებითია. მუქი წერტილები: აღწერები და სტატისტიკა, ღია წერტილები: შეფასებები (დაუდასტურებელი).",
      popBefore: "ამ წლის მოსახლეობის მონაცემი არ არის (უადრესი შეფასება: 1803).",
      show94: "1894 წლის ობიექტები ირანელი მოგზაურის აღწერის მიხედვით (სასტუმროები, თეატრები, აბანო, მუზეუმები)",
      c94Title: "თბილისის 1894 წლის აღწერიდან",
      c94Pos: "მდებარეობა",
      c94Conf: { high: "მაღალი სიზუსტე", medium: "საშუალო სიზუსტე (დაახლოებით 100-150 მ)", low: "დაბალი სიზუსტე (200 მ და მეტი)" },
      c94Src: "წყარო",
      btnInfo: "ცნობა", btnFilters: "ფილტრები", evCluster: "მოვლენები სკალაზე ახლოს (აირჩიეთ)", btnViews: "ხედები", viewsAll: "ყველა ხედი (არა მხოლოდ არჩეული წლისთვის)", viewsNone: "ამ წლისთვის ხედები არ არის: ზოგი წლისთვის თავისუფალი ლიცენზიის ფოტო ვერ ვიპოვეთ. ჩართეთ „ყველა ხედი“.", filtersTitle: "ფილტრები და ფენები",
      stTitle: "ქუჩების სახელები ამ წელს (შემოწმებულია ვიკიპედიით)",
      stNow: "დღეს",
      stMore: "სახელები წლების მიხედვით ცნობილია არა ყველა ქუჩისთვის.",
      baseOff: "რუკის ფონი (OpenFreeMap) თქვენი ქსელიდან მიუწვდომელია, ნაჩვენებია გამარტივებული ფონი ქუჩებისა და შენობების გარეშე. ისტორიული ფენები, გეგმები და სახელები მუშაობს.",
      showStreets: "ქუჩები 1913 წლის გეგმით (ექსპერიმენტი, ავტომატური გადახაზვა)",
      showSwipe: "შედარება: მარცხნივ ძველი გეგმა, მარჯვნივ თანამედროვე რუკა (გადაადგილეთ ზოლი)",
      showHere: "რა იყო აქ: დააწკაპუნეთ რუკაზე, რომ ნახოთ ეს წერტილი ყველა გეგმაზე",
      hereTitle: "ეს წერტილი ძველ გეგმებზე",
      hereLoad: "გეგმები იტვირთება თანმიმდევრულად…",
      hereNone: "ეს წერტილი ყველა გეგმის გარეთაა.",
      hereAcc: (m) => "მიბმის სიზუსტე ±" + m + " მ",
      hereNote: "ფანჯარა დაახლოებით 260 მ-ია. თითოეული გეგმა რუკას საკუთარი ცდომილებით ერგება, ამიტომ ათეულობით მეტრით გადახრა შესაძლებელია.",
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

  // Basemap: OpenFreeMap. If it cannot be loaded (blocked or throttled in some countries), the map falls back to a plain background
  // with our own glyphs, so that all historical layers still work. ?base=off forces the fallback, ?base=bad simulates an unreachable basemap.
  const BASE_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";
  const baseParam = new URLSearchParams(location.search).get("base");
  function offlineStyle() {
    return { version: 8, glyphs: location.origin + location.pathname.replace(/[^/]*$/, "") + "fonts/{fontstack}/{range}.pbf", sources: {},
             layers: [{ id: "bg-offline", type: "background", paint: { "background-color": "#ece9df" } }] };
  }
  let baseStyle = baseParam === "off" ? offlineStyle() : baseParam === "bad" ? "https://tiles.invalid/styles/liberty" : BASE_STYLE_URL;
  let baseOffline = baseParam === "off", mapLoaded = false;
  const map = new maplibregl.Map({
    container: "map",
    // OpenFreeMap vector tiles (free, no key; data © OpenStreetMap contributors, © OpenMapTiles; attribution added by MapLibre)
    // OpenFreeMap "liberty" style, same in light and dark system themes (free, no key; attribution is added by MapLibre)
    style: baseStyle,
    center: (() => { const c = (new URLSearchParams(location.search).get("c") || "").split(",").map(Number); return c.length >= 2 && c.every(isFinite) ? [c[0], c[1]] : [44.8085, 41.6955]; })(),
    zoom: (() => { const c = (new URLSearchParams(location.search).get("c") || "").split(",").map(Number); return c.length >= 3 && isFinite(c[2]) ? c[2] : 13.2; })(), minZoom: 9, maxZoom: 19, hash: false,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.on("moveend", () => {                       // permalink: ?c=lng,lat,zoom (the year stays in the hash)
    try {
      const u = new URL(location.href), c = map.getCenter();
      u.searchParams.set("c", c.lng.toFixed(5) + "," + c.lat.toFixed(5) + "," + map.getZoom().toFixed(1));
      history.replaceState(null, "", u.pathname + u.search + u.hash);
    } catch (e) {}
  });

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

  // topographic maps of the National Agency of Public Registry of Georgia (maps.gov.ge): tiles of the Tbilisi area were downloaded (tools/fetch_napr_topo.py) and are served from site/topo
  const TOPO = {
    t2: { max: 17 },
    t10: { max: 16 },
    t25: { max: 16 },
    t50: { max: 15 },
    t100: { max: 14 },
  };
  const TOPO_BOUNDS = [44.60, 41.55, 45.05, 41.88];
  let topoShown = null;
  const TOPO_FROM = 1953, TOPO_TO = 2005;
  // the topographic map takes the place of the old plan from 1953 (the last plan is of 1913), or whenever the owner switches it on
  const autoTopoOn = () => $("autoTopo").checked && year >= TOPO_FROM && year <= TOPO_TO && !currentPlan(year);
  const topoWanted = () => $("showTopo").checked || autoTopoOn();
  const topoOpacity = () => ($("showSwipe").checked ? 1 : $("topoOp").value / 100);
  function updateTopo() {
    const on = topoWanted(), key = $("topoSel").value;
    $("topobox").hidden = !on;
    const auto = autoTopoOn() && !$("showTopo").checked;         // shown by itself: the box "on top of the map" is then half-ticked and says why
    $("showTopo").indeterminate = auto;
    $("topoAutoNote").hidden = !auto;
    if (topoShown && (!on || topoShown !== key)) {
      if (map.getLayer("topo")) map.removeLayer("topo");
      if (map.getSource("topo")) map.removeSource("topo");
      topoShown = null;
    }
    if (!on) return;
    if (!topoShown) {
      const c = TOPO[key], base = new URL("topo/" + key + "/", document.baseURI).href;
      map.addSource("topo", { type: "raster", tiles: [base + "{z}/{x}/{y}.webp"], tileSize: 256, minzoom: 11, maxzoom: c.max, bounds: TOPO_BOUNDS, attribution: "\u00A9 NAPR (maps.gov.ge)" });
      map.addLayer({ id: "topo", type: "raster", source: "topo", paint: { "raster-opacity": topoOpacity(), "raster-fade-duration": 0 } }, "admin-line");
      liftTransport();
      topoShown = key;
    }
    map.setPaintProperty("topo", "raster-opacity", topoOpacity());
  }
  for (const id of ["showTopo", "topoSel", "topoOp"]) $(id).addEventListener("input", () => { updateTopo(); updatePlanLine(); });

  // ---- swipe comparison: a second, non-interactive map with today's basemap only lies over the first one, clipped from the bar to the right edge
  let map2 = null, swipeFrac = 0.5;
  function planOpacity() { return $("showSwipe").checked ? 1 : $("op").value / 100; }
  function syncMap2() { if (map2) map2.jumpTo({ center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() }); }
  function layoutSwipe() {
    const on = $("showSwipe").checked;
    $("map2").style.display = on ? "block" : "none";
    $("swipebar").hidden = !on;
    $("swl").hidden = $("swr").hidden = !on;
    if (!on) return;
    const w = $("map").clientWidth, x = Math.round(w * swipeFrac);
    $("swl").textContent = "← " + t().swLeft; $("swr").textContent = t().swRight + " →";
    $("swl").style.left = $("swr").style.left = x + "px";
    $("map2").style.clipPath = "inset(0 0 0 " + x + "px)";
    $("swipebar").style.left = x + "px";
  }
  function updateSwipe() {
    if ($("showSwipe").checked && !map2) {
      map2 = new maplibregl.Map({ container: "map2", style: baseStyle, center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch(),
                                  interactive: false, attributionControl: false, minZoom: 9, maxZoom: 19, fadeDuration: 0 });
    }
    layoutSwipe();
    if (map2) { map2.resize(); syncMap2(); }
    for (const p of plans) if (map.getLayer("plan-" + p.id)) map.setPaintProperty("plan-" + p.id, "raster-opacity", planOpacity());
  }
  map.on("move", syncMap2);
  window.addEventListener("resize", () => { layoutSwipe(); if (map2) map2.resize(); });
  {
    const bar = $("swipebar");
    const move = (ev) => { const r = $("map").getBoundingClientRect(); swipeFrac = Math.min(0.97, Math.max(0.03, (ev.clientX - r.left) / r.width)); layoutSwipe(); };
    bar.addEventListener("pointerdown", (ev) => { bar.setPointerCapture(ev.pointerId); move(ev); ev.preventDefault(); });
    bar.addEventListener("pointermove", (ev) => { if (bar.hasPointerCapture(ev.pointerId)) move(ev); });
  }

  // ---- "what was here": a click shows the clicked point cut out of every plan that covers it (plans are loaded one by one, only on demand)
  const HERE_M = 260, HERE_PX = 360;
  const imgCache = {};
  let hereToken = 0;
  function loadImg(url) {
    if (!imgCache[url]) imgCache[url] = new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = url; });
    return imgCache[url];
  }
  const mercY = (lat) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
  async function showHere(ll) {
    const L = t();
    $("imTitle").textContent = L.hereTitle;
    const body = $("imBody");
    body.textContent = "";
    body.className = "herebox";
    infoLine(body, ll.lat.toFixed(5) + ", " + ll.lng.toFixed(5));
    const cover = plans.filter((p) => {
      const c = p.corners, lngs = [c[0][0], c[1][0]], lats = [c[3][1], c[0][1]];
      return ll.lng >= Math.min(...lngs) && ll.lng <= Math.max(...lngs) && ll.lat >= Math.min(...lats) && ll.lat <= Math.max(...lats);
    });
    const wait = infoLine(body, cover.length ? L.hereLoad : L.hereNone);
    $("infoModal").hidden = false;
    const mine = ++hereToken;
    for (const p of cover) {
      let im;
      try { im = await loadImg(p.image); } catch (e) { continue; }
      if (mine !== hereToken || $("infoModal").hidden) return;
      const c = p.corners, lng0 = c[0][0], lng1 = c[1][0], latT = c[0][1], latB = c[3][1];
      const px = ((ll.lng - lng0) / (lng1 - lng0)) * im.naturalWidth;
      const py = ((mercY(latT) - mercY(ll.lat)) / (mercY(latT) - mercY(latB))) * im.naturalHeight;
      const mPerPx = ((lng1 - lng0) * 111320 * Math.cos((ll.lat * Math.PI) / 180)) / im.naturalWidth;
      const side = HERE_M / mPerPx;
      const cv = document.createElement("canvas");
      cv.width = cv.height = HERE_PX;
      const g = cv.getContext("2d");
      g.fillStyle = "#ddd"; g.fillRect(0, 0, HERE_PX, HERE_PX);
      g.drawImage(im, px - side / 2, py - side / 2, side, side, 0, 0, HERE_PX, HERE_PX);
      g.strokeStyle = "#d6336c"; g.lineWidth = 2;
      g.beginPath(); g.moveTo(HERE_PX / 2 - 12, HERE_PX / 2); g.lineTo(HERE_PX / 2 + 12, HERE_PX / 2); g.moveTo(HERE_PX / 2, HERE_PX / 2 - 12); g.lineTo(HERE_PX / 2, HERE_PX / 2 + 12); g.stroke();
      const fig = document.createElement("figure");
      fig.appendChild(cv);
      const cap = document.createElement("figcaption");
      cap.textContent = p.year + (p.accuracy_m ? " · " + L.hereAcc(p.accuracy_m) : "");
      fig.appendChild(cap);
      body.appendChild(fig);
    }
    if (mine === hereToken && cover.length) wait.textContent = L.hereNote;
  }
  map.on("click", (e) => { if ($("showHere").checked) showHere(e.lngLat); });
  $("showHere").addEventListener("change", () => { $("map").classList.toggle("here", $("showHere").checked); });

  // plan rasters are added to the map only when a plan is first needed (keeps the first page load light)
  // transport (tram, metro, railway, bridges, avenues) lies above the old plans and the topographic map: layers added later go in just under "admin-line", i.e. above the transport
  // that was added earlier, so the transport is lifted again after every plan or topographic map is added (found out 2026-11-19: the tram was hidden under the topographic map)
  function liftTransport() {
    for (const id of ["tr-line", "tr-aerial", "tr-pt"]) if (map.getLayer(id) && map.getLayer("admin-line")) map.moveLayer(id, "admin-line");
  }
  function ensurePlan(p) {
    if (map.getLayer("plan-" + p.id)) return;
    map.addSource("plan-" + p.id, { type: "image", url: p.image, coordinates: p.corners });
    map.addLayer({ id: "plan-" + p.id, type: "raster", source: "plan-" + p.id, layout: { visibility: "none" },
                   paint: { "raster-opacity": planOpacity(), "raster-fade-duration": 0 } }, "admin-line");
    liftTransport();
    if (dataReady) { setLoading("loadPlan", true); map.once("idle", hideLoading); }
  }

  function update() {
    ensureInWindow();
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
    updateTransport();
    updateTopo();
    updateStNames();
    updatePop();
    updateC94();
    updateReligious();
    updateScience();
    updateNoPhoto();
    updateRuleLine();
    updateStreets();
    updateViews();
    updateSwipe();
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
    updatePlanLine();
    $("bndline").textContent = bndText;
  }

  function updatePlanLine() {
    const pl = currentPlan(year), sel = $("topoSel");
    $("planline").textContent = pl ? t().plan(pl.year, pl.accuracy_m) : topoWanted() ? t().topoLine(sel.options[sel.selectedIndex].text) : t().noPlan(plans[0].year, plans[plans.length - 1].year, year);
  }

  function applyLang() {
    document.documentElement.lang = lang;
    document.title = t().title;
    if (typeof feedbackRefreshCtx === "function") feedbackRefreshCtx();
    $("title").textContent = t().title;
    $("lang").value = lang;
    if ($("loading") && !$("loading").hidden) $("loadingTxt").textContent = t()[loadKey];
    $("lang").setAttribute("aria-label", t().ariaLang);
    document.querySelectorAll(".pclose").forEach((b) => b.setAttribute("aria-label", t().ariaClose));
    if ($("fbContactInput")) $("fbContactInput").placeholder = t().fbContactPh;
    updateVersionBtn();
    updatePhotoUi();
    if (window.TT_PWA) window.TT_PWA.retext();
    document.querySelectorAll("[data-i]").forEach((el) => { el.textContent = t()[el.dataset.i]; });
    $("fbOpen").title = t().fbBtn; $("fbOpen").setAttribute("aria-label", t().fbBtn);
    updateZoomUi();
    updateSearchUi();
    updateRelUi();
    buildRulersBand();
    updateRunUi();
    updateSciUi();
    $("note").textContent = t().note(undated);
    buildTypes();
    buildAbout();
    buildHow();
    update();
  }

  function buildHow() {
    const box = $("howtext");
    if (!box) return;
    box.textContent = "";
    for (const para of t().how) {
      const p = document.createElement("p");
      p.className = "small";
      p.textContent = para;
      box.appendChild(p);
    }
    let seen = false;
    try { seen = localStorage.getItem("howSeen") === "1"; } catch (e) {}
    if (!seen) {                                          // opened once on the first visit
      $("how").open = true;
      try { localStorage.setItem("howSeen", "1"); } catch (e) {}
    }
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
    const lo = zoomLo, hi = zoomHi, zoomed = KNOTS !== FULL_KNOTS;
    const marked = [...new Set([...urbanSnaps, ...plans.map((p) => p.year), ...views.map((v) => v.year)])].filter((y) => y >= lo && y <= hi).sort((a, b) => a - b);
    const round = [];
    let last = MAX;
    if (!zoomed) {
      for (let y = 400; y < 1700; y += 200) round.push(y);                  // the compressed early period: every 200 years
      for (let y = 1750; y <= MAX; y += 50) if (!marked.some((p) => Math.abs(p - y) < 12)) round.push(y);
    } else {
      const span = hi - lo, st = span <= 40 ? 2 : span <= 70 ? 5 : span <= 120 ? 10 : span <= 260 ? 25 : 50;   // zoomed: round years with a finer step
      for (let y = Math.ceil(lo / st) * st; y <= hi; y += st) if (!marked.some((p) => Math.abs(p - y) < st / 2)) round.push(y);
      last = hi;
    }
    if (!marked.some((p) => Math.abs(p - last) < 12)) round.push(last);
    round.unshift(lo);
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

  // historical events (invasions, earthquakes, floods, changes of power): icons above the slider; every event has a source (data/history_events.json)
  let histEvents = [];
  // objects named in the 1894 description of Tbilisi (Majd-os-Saltaneh): a small layer, shown 1894-1899
  let c94 = null;
  function updateC94() {
    if (!c94 || !map.getLayer("c94-pt")) return;
    const on = $("show94").checked && year >= c94.y0 && year < c94.y1;
    for (const id of ["c94-pt", "c94-lb"]) map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
  }
  function addC94() {
    if (!c94 || map.getSource("c94")) return;
    map.addSource("c94", { type: "geojson", data: c94 });
    map.addLayer({ id: "c94-pt", type: "circle", source: "c94", layout: { visibility: "none" }, paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 5, 17, 10], "circle-color": "#0b7285", "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });
    map.addLayer({ id: "c94-lb", type: "symbol", source: "c94", minzoom: 14.5, layout: { visibility: "none", "text-field": ["get", "short"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.2], "text-anchor": "top", "text-optional": true }, paint: { "text-color": "#0b4a56", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    for (const f of c94.features) f.properties.short = (f.properties.name[lang] || f.properties.name.en).split(":")[0];
    map.getSource("c94").setData(c94);
    map.on("click", "c94-pt", (e) => { if (e.features && e.features[0]) popupC94(e.features[0].properties, e.lngLat); });
    map.on("mouseenter", "c94-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "c94-pt", () => { map.getCanvas().style.cursor = ""; });
    updateC94();
  }
  function popupC94(p, lngLat) {
    const L = t();
    const el = document.createElement("div");
    el.className = "pop";
    const nm = typeof p.name === "string" ? JSON.parse(p.name) : p.name;
    const h3 = document.createElement("h3");
    h3.textContent = nm[lang] || nm.en;
    el.appendChild(h3);
    const k = document.createElement("div");
    k.className = "k";
    k.textContent = L.c94Title;
    el.appendChild(k);
    const w = document.createElement("div");
    w.textContent = pickName(p.what);
    el.appendChild(w);
    if (p.note && p.note !== "null") { const n = document.createElement("div"); n.className = "small"; n.textContent = pickName(p.note); el.appendChild(n); }
    const ps = document.createElement("div");
    ps.className = "small";
    ps.textContent = L.c94Pos + ": " + pickName(p.pos) + " (" + (L.c94Conf[p.conf] || p.conf) + ")";
    el.appendChild(ps);
    const sr = document.createElement("div");
    sr.className = "small";
    const a = document.createElement("a");
    a.href = c94.src_url; a.target = "_blank"; a.rel = "noopener"; a.textContent = pickName(c94.source) + ", " + pickName(p.page);
    sr.appendChild(document.createTextNode(L.c94Src + ": "));
    sr.appendChild(a);
    el.appendChild(sr);
    showPopup("320px", lngLat, el);
  }
  let popData = null;
  function updatePop() {
    const box = $("popbox");
    if (!box || !popData) return;
    const L = t(), P = popData.points;
    box.textContent = "";
    const prev = P.filter((p) => p.y <= year);
    if (!prev.length) { box.hidden = true; return; }
    box.hidden = false;
    const cur = prev[prev.length - 1];
    const h = document.createElement("div");
    const b = document.createElement("b");
    b.textContent = L.popTitle + ": ";
    h.appendChild(b);
    h.appendChild(document.createTextNode("~" + cur.v.toLocaleString(lang === "ru" ? "ru-RU" : lang === "ka" ? "ka-GE" : "en-US") + " (" + cur.y + ")"));
    box.appendChild(h);
    const ssrc = popData.sources[cur.s];
    const d = document.createElement("div");
    d.className = "src";
    const a = document.createElement("a");
    a.href = ssrc.url; a.target = "_blank"; a.rel = "noopener"; a.textContent = "[src]";
    d.appendChild(document.createTextNode((cur.u && pickName(cur.u) || (cur.ref && pickName(cur.ref)) || "") + " "));
    d.appendChild(a);
    box.appendChild(d);
    // chart: linear years 1800-2026, population in thousands
    const W = 260, H = 70, x0 = 4, x1 = W - 4, ymax = 1400000, Y0 = 1800, Y1 = 2026;
    const X = (y) => x0 + ((y - Y0) / (Y1 - Y0)) * (x1 - x0), Yv = (v) => H - 4 - (v / ymax) * (H - 10);
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    const sol = P.filter((p) => p.q !== "outlier" && p.q !== "uncertain");
    const pl = document.createElementNS(ns, "polyline");
    pl.setAttribute("points", sol.map((p) => X(p.y).toFixed(1) + "," + Yv(p.v).toFixed(1)).join(" "));
    pl.setAttribute("fill", "none"); pl.setAttribute("stroke", getCss("--old")); pl.setAttribute("stroke-width", "1.5");
    svg.appendChild(pl);
    for (const p of P) {
      const c = document.createElementNS(ns, "circle");
      c.setAttribute("cx", X(p.y)); c.setAttribute("cy", Yv(p.v)); c.setAttribute("r", p === cur ? 4 : 2.4);
      const hollow = p.q === "outlier" || p.q === "uncertain";
      c.setAttribute("fill", hollow ? "none" : p === cur ? getCss("--accent") : getCss("--old"));
      c.setAttribute("stroke", p === cur ? getCss("--accent") : getCss("--old")); c.setAttribute("stroke-width", "1.2");
      svg.appendChild(c);
    }
    if (year >= Y0 && year <= Y1) {
      const ln = document.createElementNS(ns, "line");
      ln.setAttribute("x1", X(year)); ln.setAttribute("x2", X(year)); ln.setAttribute("y1", 2); ln.setAttribute("y2", H - 2);
      ln.setAttribute("stroke", getCss("--accent")); ln.setAttribute("stroke-dasharray", "2 2");
      svg.appendChild(ln);
    }
    box.appendChild(svg);
    const n = document.createElement("div");
    n.className = "src";
    n.textContent = L.popNote;
    box.appendChild(n);
  }
  // a text that may be a plain string, a {ru,en,ka} object, or such an object as a JSON string (MapLibre stringifies nested feature properties)
  const pickName = (o) => {
    if (typeof o === "string") { if (o[0] !== "{") return o; try { o = JSON.parse(o); } catch (e) { return o; } }
    return o ? o[lang] || o.en || o.ru || "" : "";
  };
  let stNames = [], stGeom = {};
  function updateStLabelsLayer() {
    const src = map.getSource("stlabels");
    if (!src) return;
    const feats = [];
    if ($("showStLabels").checked) {
      for (const st of stNames) {
        const g = stGeom[st.now.en], iv = st.iv.find((x) => year >= x[0] && year < x[1] && x[2]);
        if (g && iv) feats.push({ type: "Feature", geometry: g, properties: { t: pickName(iv[2]) } });
      }
    }
    src.setData({ type: "FeatureCollection", features: feats });
  }
  // the road-name labels of the basemap lie under the old plan; they can be lifted above it (below the object dots)
  const ROAD_LABELS = ["highway-name-path", "highway-name-minor", "highway-name-major"];
  let roadOrigin = null;
  function updateRoadLabels() {
    const ids = ROAD_LABELS.filter((id) => map.getLayer(id));
    if (!ids.length) return;
    if (!roadOrigin) {
      const order = map.getStyle().layers.map((l) => l.id);
      roadOrigin = ids.map((id) => [id, order[order.indexOf(id) + 1]]);
    }
    if ($("roadLabels").checked) {
      const before = map.getLayer("mon") ? "mon" : undefined;
      for (const id of ids) map.moveLayer(id, before);
    } else {
      for (const [id, next] of roadOrigin) if (map.getLayer(id)) map.moveLayer(id, next);
    }
  }
  function addStLabelsLayer() {
    if (map.getSource("stlabels")) return;
    map.addSource("stlabels", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    const paint = { "text-color": "#8b0a0a", "text-halo-color": "#ffffff", "text-halo-width": 3.2 };
    map.addLayer({ id: "stl-line", type: "symbol", source: "stlabels", filter: ["!=", ["geometry-type"], "Point"],
                   layout: { "symbol-placement": "line", "text-field": ["get", "t"], "text-font": ["Noto Sans Bold"], "text-size": 16, "text-letter-spacing": 0.04, "text-max-angle": 40, "symbol-spacing": 350, "text-allow-overlap": true, "text-ignore-placement": true }, paint });
    map.addLayer({ id: "stl-pt", type: "symbol", source: "stlabels", filter: ["==", ["geometry-type"], "Point"],
                   layout: { "text-field": ["get", "t"], "text-font": ["Noto Sans Bold"], "text-size": 15, "text-anchor": "center", "text-allow-overlap": true, "text-ignore-placement": true }, paint });
  }
  function updateStNames() {
    updateStLabelsLayer();
    updateRoadLabels();
    const box = $("stnames");
    if (!box) return;
    const L = t(), rows = [];
    for (const s of stNames) {
      const iv = s.iv.find((x) => year >= x[0] && year < x[1] && x[2]);
      if (iv) rows.push([pickName(iv[2]), s.now[lang] || s.now.en, s.src]);
    }
    box.textContent = "";
    box.hidden = !rows.length;
    if (!rows.length) return;
    const h = document.createElement("div");
    h.textContent = L.stTitle;
    box.appendChild(h);
    for (const [old, now, src] of rows) {
      const d = document.createElement("div");
      const b = document.createElement("b");
      b.textContent = old;
      d.appendChild(b);
      d.appendChild(document.createTextNode(" \u2192 " + L.stNow + ": " + now + " "));
      const a = document.createElement("a");
      a.href = src; a.target = "_blank"; a.rel = "noopener"; a.className = "src"; a.textContent = "[src]";
      d.appendChild(a);
      box.appendChild(d);
    }
    const m = document.createElement("div");
    m.className = "src";
    m.textContent = L.stMore;
    box.appendChild(m);
  }
  const EV_ICON = { unrest: "\uD83D\uDD6F\uFE0F", oldest: "\uD83C\uDFF0", build: "\uD83C\uDFD7\uFE0F", invasion: "\u2694\uFE0F", earthquake: "\uD83C\uDFDA\uFE0F", fire: "\uD83D\uDD25", flood: "\uD83C\uDF0A", power: "\uD83C\uDFDB\uFE0F", other: "\uD83D\uDCCC" };
  function buildEvMarks() {
    const box = $("evmarks");
    if (!box) return;
    box.textContent = "";
    // markers that would overlap on the scale are merged into one marker with a count; a click on it lists the events
    const W = Math.max(0, box.clientWidth - 16), GAP = 19;
    const items = histEvents.filter((ev) => ev.year >= zoomLo && ev.year <= zoomHi).map((ev) => ({ ev, x: 8 + W * (y2v(ev.year) / 1000) })).sort((a, b) => a.x - b.x || a.ev.year - b.ev.year);
    const groups = [];
    for (const it of items) {
      const g = groups[groups.length - 1];
      if (g && it.x - g.x0 < GAP) g.list.push(it.ev); else groups.push({ x0: it.x, list: [it.ev] });
    }
    for (const g of groups) {
      const b = document.createElement("button");
      b.type = "button";
      const first = g.list[0];
      b.textContent = EV_ICON[first.cat] || EV_ICON.other;
      b.style.left = `calc(8px + (100% - 16px) * ${y2v(first.year) / 1000})`;
      if (g.list.length === 1) {
        b.title = first.date + " \u00B7 " + (first[lang] || first.en);
        b.addEventListener("click", () => { year = first.year; update(); showHistEvent(first); });
      } else {
        const last = g.list[g.list.length - 1];
        b.className = "cl";
        b.dataset.n = g.list.length;
        b.title = g.list.length + " \u00B7 " + first.year + (last.year !== first.year ? "\u2013" + last.year : "");
        b.addEventListener("click", () => showEventList(g.list));
      }
      b.setAttribute("aria-label", b.title);
      box.appendChild(b);
    }
  }
  function showEventList(list) {
    reopenInfo = () => showEventList(list);
    const L = t();
    openInfo((body) => {
      for (const ev of list) {
        const d = document.createElement("div");
        d.className = "evrow";
        const txt = ev[lang] || ev.en;
        d.textContent = (EV_ICON[ev.cat] || EV_ICON.other) + " " + ev.date + " \u00B7 " + (txt.length > 130 ? txt.slice(0, 127) + "\u2026" : txt);
        d.tabIndex = 0;
        d.addEventListener("click", () => { year = ev.year; update(); showHistEvent(ev); });
        d.addEventListener("keydown", (e) => { if (e.key === "Enter") d.click(); });
        body.appendChild(d);
      }
    });
    $("imTitle").textContent = L.evCluster;
  }
  { let rz = null; window.addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(() => { if (histEvents.length) buildEvMarks(); }, 150); }); }
  let evMarker = null;
  function showEventPlace(ev) {
    if (evMarker) { evMarker.remove(); evMarker = null; }
    if (!ev.place) return;
    const dot = document.createElement("div");
    dot.className = "evpulse";
    evMarker = new maplibregl.Marker({ element: dot }).setLngLat([ev.place.lng, ev.place.lat]).addTo(map);
    map.flyTo({ center: [ev.place.lng, ev.place.lat], zoom: ev.place.zoom || 15, duration: 1200 });
  }
  function showHistEvent(ev) {
    reopenInfo = () => showHistEvent(ev);
    const L = t();
    showEventPlace(ev);
    openInfo((body) => {
      infoLine(body, ev.date + " \u00B7 " + (L.evCats[ev.cat] || ""), "small");
      infoLine(body, ev[lang] || ev.en, "");
      if (ev.note) infoLine(body, pickName(ev.note));
      if (ev.place) infoLine(body, "\uD83D\uDCCD " + (ev.place[lang] || ev.place.en));
      if (ev.src.some((u) => /wikipedia/i.test(typeof u === "string" ? u : u.url))) infoLine(body, L.evNote);
      infoLine(body, L.evSrc + ":");
      for (const u of ev.src) {
        const d = document.createElement("div");
        d.className = "small";
        const a = document.createElement("a");
        const url = typeof u === "string" ? u : u.url;
        a.href = url; a.target = "_blank"; a.rel = "noopener"; a.textContent = typeof u === "string" ? decodeURI(u) : u.label + " \u2014 " + decodeURI(url);
        d.appendChild(a);
        body.appendChild(d);
      }
    });
  }

  let photoInfo = null;
  // Details that do not belong on the card (licences, sources, register notes) live in a separate window opened by a button.
  function openInfo(build) {
    $("imTitle").textContent = t().infoTitle;
    const body = $("imBody");
    body.textContent = "";
    body.className = "";
    build(body);
    $("infoModal").hidden = false;
  }
  function closeInfo() { reopenInfo = null; $("infoModal").hidden = true; if (evMarker) { evMarker.remove(); evMarker = null; } }
  $("imClose").addEventListener("click", closeInfo);
  $("infoModal").addEventListener("click", (e) => { if (e.target === $("infoModal")) closeInfo(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("infoModal").hidden) closeInfo(); });
  function infoLine(body, text, cls) { const d = document.createElement("div"); d.className = cls || "small"; d.textContent = text; body.appendChild(d); return d; }
  // "photo hunt": the ring layer and the list of the nearest objects without a photo (only where the photo form is switched on with ?club=1)
  const photoOn = () => !!(window.TT_PHOTO && window.TT_PHOTO.enabled());
  function updateNoPhoto() {
    if (!map.getLayer("nophoto")) return;
    const on = photoOn() && $("showNoPhoto").checked;
    map.setLayoutProperty("nophoto", "visibility", on ? "visible" : "none");
    if (on) map.setFilter("nophoto", ["all", filterExpr(), ["!", ["has", "ph"]]]);
  }
  function updatePhotoUi() {
    const on = photoOn();
    $("rowNoPhoto").hidden = !on; $("rowNear").hidden = !on;
    if (on) { const S = window.TT_PHOTO.s(lang); $("noPhotoL").textContent = S.noPhotoL; $("btnNear").textContent = S.nearBtn; }
  }
  let lastPos = null, picker = null;
  window.TT_APP = { pickObject: (cb) => { picker = cb; }, info: (title, lines) => openInfo((body) => { $("imTitle").textContent = title; for (const l of lines) infoLine(body, l); }) };
  function showNearby(pos) {
    const S = window.TT_PHOTO.s(lang);
    reopenInfo = () => showNearby(pos);
    const k = Math.cos(pos.lat * Math.PI / 180), list = [];
    for (const f of monuments.features) {
      const p = f.properties;
      if (p.ph) continue;
      const [lng, lat] = f.geometry.coordinates;
      list.push({ p, lng, lat, d: Math.hypot((lng - pos.lng) * k * 111320, (lat - pos.lat) * 111320) });
    }
    list.sort((a, b) => a.d - b.d);
    openInfo((body) => {
      $("imTitle").textContent = S.nearTitle;
      infoLine(body, S.nearHint, "small");
      if (!list.length) { infoLine(body, S.nearNone); return; }
      for (const it of list.slice(0, 15)) {
        let nm = it.p.name || "", ad = it.p.address || "";
        try { if (window.GeoTr) { nm = window.GeoTr.nameInfo(it.p.name, lang, it.p.wp).text || nm; ad = window.GeoTr.address(it.p.address, lang) || ad; } } catch (e) {}
        const b = document.createElement("button");
        b.type = "button"; b.className = "chip"; b.style.cssText = "display:block;width:100%;text-align:left;margin:4px 0";
        b.textContent = (it.d < 1000 ? Math.round(it.d) + " m" : (it.d / 1000).toFixed(1) + " km") + " \u00B7 " + nm + (ad ? " \u00B7 " + ad : "");
        b.addEventListener("click", () => { closeInfo(); map.flyTo({ center: [it.lng, it.lat], zoom: 17, duration: 1000 }); popup(it.p, { lng: it.lng, lat: it.lat }); });
        body.appendChild(b);
      }
    });
  }
  $("btnNear").addEventListener("click", () => {
    const S = window.TT_PHOTO.s(lang);
    if (!navigator.geolocation) { openInfo((body) => { $("imTitle").textContent = S.nearTitle; infoLine(body, S.nearDenied); }); return; }
    navigator.geolocation.getCurrentPosition((g) => { lastPos = { lat: g.coords.latitude, lng: g.coords.longitude }; showNearby(lastPos); },
      () => openInfo((body) => { $("imTitle").textContent = S.nearTitle; infoLine(body, S.nearDenied); }), { enableHighAccuracy: true, timeout: 15000 });
  });
  // the link "send a photo of this object" (photo.js): only in a browser where the form was switched on with ?club=1
  function addPhotoLink(el, obj, need) {
    if (!window.TT_PHOTO || !window.TT_PHOTO.enabled()) return;
    if (need) { const n = document.createElement("div"); n.className = "small"; n.style.cssText = "margin-top:8px;color:#f76707"; n.textContent = window.TT_PHOTO.s(lang).need; el.appendChild(n); }
    const h = el.querySelector("h3"), d = document.createElement("div"), a = document.createElement("a");
    d.className = "actions"; a.href = "#"; a.className = "fb"; a.textContent = window.TT_PHOTO.text(lang);
    a.addEventListener("click", (ev) => {
      ev.preventDefault();
      let lat = NaN, lon = NaN;
      if (obj.startsWith("mon:") && monuments) { const f = monuments.features.find((x) => String(x.properties.id) === obj.slice(4)); if (f) { lon = f.geometry.coordinates[0]; lat = f.geometry.coordinates[1]; } }
      window.TT_PHOTO.open({ obj, name: h ? h.textContent : obj, lang, lat, lon });
    });
    d.appendChild(a); el.appendChild(d);
  }
  function actions(el, openDetails, fbObj) {
    const box = document.createElement("div");
    box.className = "actions";
    const a1 = document.createElement("a");
    a1.href = "#"; a1.className = "fb"; a1.textContent = t().infoBtn;
    a1.addEventListener("click", (ev) => {
      ev.preventDefault();
      const rp = reopenPopup;
      openDetails();
      reopenInfo = rp ? () => { if (openPop) openPop.remove(); rp(); const b = document.querySelector(".maplibregl-popup .actions a.fb"); if (b) b.click(); } : null;
    });
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
    reopenPopup = () => settlePopup(p, lngLat);
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
    showPopup("300px", lngLat, el);
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
    reopenPopup = () => lostPopup(p, lngLat);
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
    if (p.repl && p.repl !== "null") add(L.lostRepl + ": " + (p["repl_" + lang] || p.repl));
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
    showPopup("320px", lngLat, el);
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
    reopenPopup = () => waterPopup(p, lngLat);
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
    showPopup("300px", lngLat, el);
  }

  let views = [];
  let viewsSig = "";
  let shownViews = [];                           // the photos offered now (the arrows of the viewer go through them)
  let curView = null;
  const viewTiles = new Map();
  const VIEW_WINDOW = 150;                       // a view is offered for 150 years after its date

  function updateViews() {
    const box = $("vgrid");
    if (!box || $("views").hidden) return;                       // tiles (and their images) are built only while the panel is open
    const all = $("viewsAll").checked;
    const list = all ? views : views.filter((v) => year >= (v.from !== undefined ? v.from : v.year) && year < v.year + (v.window || VIEW_WINDOW));   // "from": the start of the five-year period of the later photographs
    shownViews = list;
    const sig = lang + "|" + (list.length ? list.map((v) => v.id).join(",") : "-");
    if (sig === viewsSig && box.childNodes.length) return;       // the same set of tiles: leave the DOM alone, so the pictures do not flicker while the slider moves
    viewsSig = sig;
    if (!list.length) {
      const m = document.createElement("div");
      m.className = "vnone";
      m.textContent = t().viewsNone;
      box.replaceChildren(m);
      return;
    }
    const tiles = [];
    for (const v of list) {
      let tile = viewTiles.get(v.id);                              // a tile (with its loaded image) is built once and then reused
      if (!tile) {
        const b = document.createElement("button");
        b.type = "button";
        const im = document.createElement("img");
        im.src = v.image; im.loading = "lazy"; im.alt = "";
        const cap = document.createElement("span");
        cap.className = "vcap";
        const yr = document.createElement("span");
        yr.className = "vyear";
        yr.textContent = v.year + " · ";
        const txt = document.createTextNode("");
        cap.appendChild(yr); cap.appendChild(txt);
        b.appendChild(im); b.appendChild(cap);
        b.addEventListener("click", () => openView(v));
        tile = { b, txt };
        viewTiles.set(v.id, tile);
      }
      tile.txt.nodeValue = v.title[lang] || v.title.en;
      tiles.push(tile.b);
    }
    box.replaceChildren(...tiles);
  }
  $("viewsAll").addEventListener("change", updateViews);

  function openView(v) {
    const L = t();
    curView = v;
    const idx = shownViews.indexOf(v), many = idx >= 0 && shownViews.length > 1;
    $("vmPrev").hidden = $("vmNext").hidden = !many;
    $("vmPrev").setAttribute("aria-label", L.viewPrev); $("vmPrev").title = L.viewPrev;
    $("vmNext").setAttribute("aria-label", L.viewNext); $("vmNext").title = L.viewNext;
    $("vmCount").textContent = many ? (idx + 1) + " / " + shownViews.length : "";
    $("vmTitle").textContent = v.title[lang] || v.title.en;
    const img = $("vmImg");
    img.src = v.image;
    img.alt = v.title[lang] || v.title.en;
    $("vmAuthor").textContent = v.author[lang] || v.author.en;
    $("vmNote").textContent = v.note[lang] || v.note.en;
    const src = $("vmSrc");
    const lic = typeof v.license === "object" ? (v.license[lang] || v.license.en) : v.license;
    src.textContent = L.viewLicense + ": " + lic + " · " + L.viewSource + ": ";
    if (v.page) {
      const a = document.createElement("a");
      a.href = v.page; a.target = "_blank"; a.rel = "noopener"; a.textContent = v.page_label ? (v.page_label[lang] || v.page_label.en) : "Wikimedia Commons";
      src.appendChild(a);
    } else src.textContent = L.viewLicense + ": " + lic;
    $("viewModal").hidden = false;
  }
  function closeView() { $("viewModal").hidden = true; }
  $("vmClose").addEventListener("click", closeView);
  $("viewModal").addEventListener("click", (e) => { if (e.target === $("viewModal")) closeView(); });
  function stepView(d) {
    const n = shownViews.length, i = shownViews.indexOf(curView);
    if (n < 2 || i < 0) return;
    openView(shownViews[(i + d + n) % n]);
  }
  $("vmPrev").addEventListener("click", () => stepView(-1));
  $("vmNext").addEventListener("click", () => stepView(1));
  document.addEventListener("keydown", (e) => {
    if ($("viewModal").hidden) return;
    if (e.key === "Escape") closeView();
    else if (e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); stepView(-1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); stepView(1); }
  }, true);
  let swipeX = null;                                   // a swipe on the picture turns it on a touch screen
  $("vmImg").addEventListener("touchstart", (e) => { swipeX = e.changedTouches[0].clientX; }, { passive: true });
  $("vmImg").addEventListener("touchend", (e) => {
    if (swipeX === null) return;
    const dx = e.changedTouches[0].clientX - swipeX; swipeX = null;
    if (Math.abs(dx) > 50) stepView(dx < 0 ? 1 : -1);
  }, { passive: true });

  function updateDensity() {
    if (map.getLayer("density-img")) map.setLayoutProperty("density-img", "visibility", $("showDensity").checked && year >= 2015 ? "visible" : "none");
  }

  let trEvents = [];
  function trFilter() {
    return ["any", ["all", [">=", year, ["get", "y0"]], ["<", year, ["get", "y1"]]], ["all", [">=", year, ["get", "y2"]], ["<", year, ["get", "y3"]]]];
  }
  // the years for which the map has no tram lines, though there was a tram (found out 2026-11-19): a note instead of silence
  // lengths of the network by year (ru.wikipedia "Tbilisi tram": single-track count with depots); electric tram from 25 December 1904, the lines of the plan of 1913 are drawn from 1913
  const TRAM_KM = { 1930: 65, 1940: 84, 1952: 98, 1961: 101 };
  function trGapNote() {
    const L = t();
    if (year >= 1905 && year <= 1912) return L.trGapEarly;
    if (year >= 1924 && year <= 1961) {
      const a = Object.keys(TRAM_KM).map(Number).reduce((best, k) => (Math.abs(k - year) < Math.abs(best - year) ? k : best));
      return L.trGapMid(TRAM_KM[a], a);
    }
    return "";
  }
  function updateTransport() {
    const on = $("showTransport").checked;
    const AER = ["match", ["get", "kind"], ["funicular", "cablecar"], true, false];
    for (const id of ["tr-line", "tr-pt", "tr-aerial"]) {
      if (!map.getLayer(id)) continue;
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      const base = id === "tr-pt" ? ["==", ["geometry-type"], "Point"] : id === "tr-aerial" ? ["all", ["!=", ["geometry-type"], "Point"], AER] : ["all", ["!=", ["geometry-type"], "Point"], ["!", AER]];
      map.setFilter(id, ["all", base, trFilter()]);
    }
    const box = $("trevents");
    if (!box) return;
    const list = on ? trEvents.filter((x) => x.year <= year && x.year > year - 12).slice(-4).reverse() : [];
    box.textContent = "";
    const gap = on ? trGapNote() : "";
    box.hidden = !list.length && !gap;
    if (box.hidden) return;
    const h = document.createElement("div");
    h.textContent = t().trEvents;
    box.appendChild(h);
    if (gap) { const g = document.createElement("div"); g.className = "small"; g.textContent = gap; box.appendChild(g); }
    for (const x of list) {
      const d = document.createElement("div");
      const b = document.createElement("b");
      b.textContent = x.date + " · ";
      d.appendChild(b);
      d.appendChild(document.createTextNode(x[lang] || x.en || x.ru));
      box.appendChild(d);
    }
  }

  function transportPopup(p, lngLat) {
    reopenPopup = () => transportPopup(p, lngLat);
    const L = t();
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = p["name_" + lang] || p.name_en || p.name_ru || "—";
    el.appendChild(h3);
    const add = (txt, cls) => { const d = document.createElement("div"); if (cls) d.className = cls; d.textContent = txt; el.appendChild(d); };
    add((L.trKinds[p.kind] || p.kind) + " · " + L.trPeriod(+p.y0, +p.y1, +p.y2, +p.y3));
    if (p.r62) add(L.trRoutes62 + ": " + p.r62);                       // the numbers of the routes that name the street in the list of 1962 / 1986
    if (p.r86) add(L.trRoutes86 + ": " + p.r86);
    let srcs = [];
    try { srcs = JSON.parse(p.src || "[]"); } catch (e) {}
    actions(el, () => openInfo((body) => {
      if (p.note) infoLine(body, p.note);
      infoLine(body, "Wikipedia:");
      srcs.forEach((u) => { const d = document.createElement("div"); d.className = "small"; const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURIComponent(u); d.appendChild(a); body.appendChild(d); });
      infoLine(body, "OpenStreetMap contributors (ODbL): geometry");
    }), { id: p.id, name: p.name_en, reg: "-" });
    showPopup("300px", lngLat, el);
  }

  let streetsLoaded = false;
  async function updateStreets() {
    const on = $("showStreets").checked && year >= 1913 && year < 1954;
    if (on && !streetsLoaded && map.isStyleLoaded()) {
      streetsLoaded = true;
      try {
        const d = await getJSON("data/streets_1913.json", 2);
        if (!map.getSource("streets1913")) {
          map.addSource("streets1913", { type: "geojson", data: d });
          map.addLayer({ id: "streets1913-line", type: "line", source: "streets1913", layout: { visibility: "none" }, paint: { "line-color": "#a0522d", "line-width": 1.4, "line-opacity": 0.85 } });
        }
      } catch (e) { streetsLoaded = false; }
    }
    if (map.getLayer("streets1913-line")) map.setLayoutProperty("streets1913-line", "visibility", on ? "visible" : "none");
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
  // two panels (history info, filters), each can be hidden; the choice is remembered on wide screens; on a phone only one is open at a time
  {
    const mq = window.matchMedia("(max-width:640px)");
    const KEYS = ["info", "filters", "views"];
    const els = { info: $("side"), filters: $("filters"), views: $("views") }, btns = { info: $("btnInfo"), filters: $("btnFilters"), views: $("btnViews") };
    let st = { info: !mq.matches, filters: !mq.matches, views: false };
    try { const s = JSON.parse(localStorage.getItem("panels") || "null"); if (s && !mq.matches) st = { info: s.info !== false, filters: s.filters !== false, views: s.views === true }; } catch (e) {}
    const apply = () => {
      for (const k of KEYS) { els[k].hidden = !st[k]; btns[k].setAttribute("aria-pressed", st[k] ? "true" : "false"); }
      document.body.classList.toggle("nofilters", !st.filters);
      if (!mq.matches) { try { localStorage.setItem("panels", JSON.stringify(st)); } catch (e) {} }
      updateViews();
    };
    const toggle = (k, on) => {
      st[k] = on === undefined ? !st[k] : on;
      if (mq.matches && st[k]) for (const o of KEYS) if (o !== k) st[o] = false;
      apply();
    };
    btns.info.addEventListener("click", () => toggle("info"));
    btns.filters.addEventListener("click", () => toggle("filters"));
    btns.views.addEventListener("click", () => toggle("views"));
    for (const b of document.querySelectorAll(".pclose")) b.addEventListener("click", () => toggle(b.dataset.panel, false));
    apply();
  }

  // A card must lie inside the free part of the screen: not under the top bar, the slider, or an open side panel. The map is moved a little if needed,
  // and a tall card gets its own scrollbar.
  function freeRect() {
    const W = window.innerWidth, H = window.innerHeight, m = 8;
    const bb = $("bottom").getBoundingClientRect();
    const r = { left: m, right: W - m, top: $("timebar").getBoundingClientRect().bottom + 4, bottom: (bb.height ? bb.top : H - 30) - m };
    const mobile = window.matchMedia("(max-width:640px)").matches;
    for (const id of ["side", "filters", "views"]) {
      const el = $(id);
      if (!el || el.hidden) continue;
      const b = el.getBoundingClientRect();
      if (mobile) r.top = Math.max(r.top, b.bottom + m);
      else if (b.left < W / 2) r.left = Math.max(r.left, b.right + m);
      else r.right = Math.min(r.right, b.left - m);
    }
    return r;
  }
  function showPopup(maxWidth, lngLat, el) {
    const pop = new maplibregl.Popup({ maxWidth, focusAfterOpen: false }).setLngLat(lngLat).setDOMContent(el).addTo(map);
    openPop = pop;
    pop.on("close", () => { if (openPop === pop) { openPop = null; reopenPopup = null; } });
    const fit = () => {
      const node = pop.getElement();
      if (!node) return;
      const f = freeRect(), content = node.querySelector(".maplibregl-popup-content");
      if (content) { content.style.maxHeight = Math.max(160, f.bottom - f.top - 24) + "px"; content.style.overflowY = "auto"; }
      const r = node.getBoundingClientRect();
      let dx = 0, dy = 0;
      if (r.left < f.left) dx = r.left - f.left; else if (r.right > f.right) dx = r.right - f.right;
      if (r.top < f.top) dy = r.top - f.top; else if (r.bottom > f.bottom) dy = r.bottom - f.bottom;
      if (dx || dy) map.panBy([dx, dy], { duration: 250 });
    };
    requestAnimationFrame(() => requestAnimationFrame(fit));
    if (window.ResizeObserver) {                      // photos load later and make the card taller: fit again
      const content = pop.getElement().querySelector(".maplibregl-popup-content");
      let t = null;
      const ro = new ResizeObserver(() => { clearTimeout(t); t = setTimeout(fit, 60); });
      if (content) ro.observe(content);
      pop.on("close", () => ro.disconnect());
    }
    return pop;
  }

  // the address bar follows the open object card (?o=<register id>): the link can be sent, and opens the same card
  function setObjParam(id, pop) {
    try {
      const u = new URL(location.href);
      u.searchParams.set("o", id);
      history.replaceState(null, "", u.pathname + u.search + u.hash);
      pop.on("close", () => {
        const v = new URL(location.href);
        if (v.searchParams.get("o") === String(id)) { v.searchParams.delete("o"); history.replaceState(null, "", v.pathname + v.search + v.hash); }
      });
    } catch (e) {}
  }

  function popup(p, lngLat) {
    reopenPopup = () => popup(p, lngLat);
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
    addPhotoLink(el, "mon:" + p.id, !p.ph);
    setObjParam(p.id, showPopup("300px", lngLat, el));
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

  function goOffline() {
    if (baseOffline) return;
    baseOffline = true;
    baseStyle = offlineStyle();
    map.setStyle(baseStyle);
    const n = document.createElement("div");
    n.id = "basenote";
    n.textContent = t().baseOff;
    document.getElementById("map").parentNode.appendChild(n);
  }
  setTimeout(() => { if (!mapLoaded && typeof baseStyle !== "object") goOffline(); }, 8000);
  map.on("error", (e) => { if (!mapLoaded && !e.sourceId && typeof baseStyle !== "object") goOffline(); });
  // loading plank: until the data and the first plan are drawn the screen says "loading"; a small one shows while a heavy plan comes in later
  let dataReady = false, loadKey = "loadMap", loadTimer = 0;
  function setLoading(key, mini) {
    const el = $("loading");
    if (!el) return;
    loadKey = key;
    el.className = mini ? "mini" : "";
    $("loadingTxt").textContent = t()[key];
    el.hidden = false;
    clearTimeout(loadTimer);
    loadTimer = setTimeout(() => {                    // safety: a small plank just goes away; the big one turns into a hint to reload
      if (mini) hideLoading();
      else { loadKey = "loadFail"; $("loadingTxt").textContent = t().loadFail; }
    }, 45000);
  }
  function hideLoading() {
    const el = $("loading");
    if (el) el.hidden = true;
    clearTimeout(loadTimer);
  }
  // version and the log of changes (data/changelog.json: the first entry is the current version); the button in the header opens it in the modal window
  let changelog = null;
  async function loadChangelog() {
    try { changelog = await getJSON("data/changelog.json", 1); } catch (e) { changelog = null; }
    updateVersionBtn();
  }
  function updateVersionBtn() {
    const b = $("btnVersion");
    if (!b) return;
    b.textContent = changelog && changelog.length ? "v" + changelog[0].version.replace(/\.0$/, "") : "v?";
    b.title = t().chgTitle;
    b.setAttribute("aria-label", t().chgTitle);
  }
  function showChangelog() {
    reopenInfo = () => showChangelog();
    const L = t();
    openInfo((body) => {
      $("imTitle").textContent = L.chgTitle;
      if (!changelog || !changelog.length) { infoLine(body, L.chgFail); return; }
      for (const r of changelog) {
        infoLine(body, "v" + r.version + " \u00B7 " + r.date.split("-").reverse().join("."), "chg-h");
        if (r.note) infoLine(body, r.note[lang] || r.note.en);
        for (const [kind, label] of [["new", L.chgNew], ["fix", L.chgFix]]) {
          const its = r.items.filter((x) => x.t === kind);
          if (!its.length) continue;
          infoLine(body, label + ":", "small");
          for (const x of its) infoLine(body, "\u2022 " + (x[lang] || x.en), "small chg-i");
        }
      }
    });
  }
  $("btnVersion").addEventListener("click", showChangelog);

  // the labels of the page at once, before the data are there (applyLang does the whole job later)
  try {
    document.title = t().title;
    $("title").textContent = t().title;
    $("lang").value = lang;
    document.querySelectorAll("[data-i]").forEach((el) => { if (typeof t()[el.dataset.i] === "string") el.textContent = t()[el.dataset.i]; });
  } catch (e) { /* applyLang will do it */ }
  setLoading("loadMap");

  map.on("load", async () => {
    mapLoaded = true;
    if (baseOffline && !document.getElementById("basenote")) {
      const n = document.createElement("div");
      n.id = "basenote";
      n.textContent = t().baseOff;
      document.getElementById("map").parentNode.appendChild(n);
    }
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
      map.addLayer({ id: "density-img", type: "raster", source: "density", layout: { visibility: "none" }, paint: { "raster-opacity": 0.45, "raster-fade-duration": 0 } });
    } catch (e) { /* no density layer */ }
    try {                                            // transport: metro, railway, funicular, avenues, bridges (dates from Wikipedia, see sources)
      const tr = await getJSON("data/transport.json", 2);
      map.addSource("transport", { type: "geojson", data: tr });
      const metroColor = ["match", ["get", "line"], "2", "#2f9e44", "#e03131"];     // line 1 (Akhmeteli-Varketili) red, line 2 (Saburtalo) green
      const kindColor = ["match", ["get", "kind"], "metro_line", metroColor, "railway", "#868e96", "avenue", "#f08c00", "bridge", "#1c7ed6", "tram", "#5a2d0c", "#495057"];
      map.addLayer({ id: "tr-line", type: "line", source: "transport", filter: ["!=", ["geometry-type"], "Point"], layout: { visibility: "none", "line-cap": "round" },
                     paint: { "line-color": kindColor, "line-width": ["match", ["get", "kind"], "railway", 2, "avenue", 3, 3.5], "line-offset": ["match", ["get", "kind"], "tram", 4, 0], "line-opacity": 0.9 } });
      map.addLayer({ id: "tr-pt", type: "circle", source: "transport", filter: ["==", ["geometry-type"], "Point"], layout: { visibility: "none" },
                     paint: { "circle-radius": 5, "circle-color": "#fff", "circle-stroke-color": metroColor, "circle-stroke-width": 2.5 } });
      map.addLayer({ id: "tr-aerial", type: "line", source: "transport", filter: ["!=", ["geometry-type"], "Point"], layout: { visibility: "none", "line-cap": "butt" },     // funicular and cable car: violet dashed (not confused with the green metro line)
                     paint: { "line-color": "#7048e8", "line-width": 3.5, "line-dasharray": [1.6, 1.2] } });
      for (const id of ["tr-line", "tr-pt", "tr-aerial"]) {
        map.on("mouseenter", id, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", id, () => { map.getCanvas().style.cursor = ""; });
      }
      // one click handler for all transport: the lines lie on one another (the tram is drawn 4 px beside the street, an avenue, a bridge and a railway can run along it), so
      // the object of the highest rank within a few pixels is taken: a tram before a metro line, a bridge before an avenue (found out 2026-11-19: on Chavchavadze Avenue the avenue took the click)
      const TR_PRIO = ["tram", "metro_station", "metro_line", "funicular", "cablecar", "railway", "bridge", "avenue"];
      const POINT_LAYERS = ["mon", "rel-pt", "sci-pt", "run-pt", "lost-dot", "settle-dot"];
      map.on("click", (e) => {
        const near = (r) => [[e.point.x - r, e.point.y - r], [e.point.x + r, e.point.y + r]];
        const hits = map.queryRenderedFeatures(near(5), { layers: ["tr-line", "tr-pt", "tr-aerial"].filter((id) => map.getLayer(id)) });
        if (!hits.length) return;
        const exact = POINT_LAYERS.filter((id) => map.getLayer(id));
        if (exact.length && map.queryRenderedFeatures(e.point, { layers: exact }).length) return;      // a point object right under the click has its own card
        const rank = (f) => { const i = TR_PRIO.indexOf(f.properties.kind); return i < 0 ? 99 : i; };
        hits.sort((x, y) => rank(x) - rank(y));
        e.originalEvent.__trHit = true;
        transportPopup(hits[0].properties, e.lngLat);
      });
    } catch (e) { /* no transport layer */ }
    try { trEvents = (await getJSON("data/transport_events.json", 2)).events; } catch (e) { trEvents = []; }
    try { histEvents = (await getJSON("data/history_events.json", 2)).events; buildEvMarks(); } catch (e) { histEvents = []; }
    try { popData = await getJSON("data/population.json", 2); updatePop(); } catch (e) { popData = null; }
    try { runData = await getJSON("data/run_trc2026.json", 1); addRun(); } catch (e) { console.error("run", e && e.message); runData = null; }
    try { rulersMedia = await getJSON("data/rulers_media.json", 1); } catch (e) { rulersMedia = null; }
    try { rulersData = await getJSON("data/rulers.json", 1); buildRulersBand(); updateRuleLine(); } catch (e) { console.error("rulers", e && e.message); rulersData = null; }
    try { science = await getJSON("data/science.json", 1); addScience(); } catch (e) { console.error("science", e && e.message); science = []; }
    try { religious = await getJSON("data/religious.json", 1); addReligious(); } catch (e) { console.error("religious", e && e.message); religious = []; }
    try { c94 = await getJSON("data/city1894.json", 2); addC94(); } catch (e) { console.error("c94", e && e.message); c94 = null; }
    try { stNames = (await getJSON("data/street_names.json", 2)).streets; stGeom = await getJSON("data/street_geom.json", 2); addStLabelsLayer(); updateStNames(); } catch (e) { stNames = []; }
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
    map.addLayer({                                               // "photo hunt": a ring around every register object that has no photo (only where the photo form is on)
      id: "nophoto", type: "circle", source: "mon", layout: { visibility: "none" }, filter: ["!", ["has", "ph"]],
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 6, 15, 12, 18, 17], "circle-color": "rgba(0,0,0,0)", "circle-stroke-width": 2.5, "circle-stroke-color": "#f76707", "circle-stroke-opacity": 0.95 },
    }, "mon-ruin");
    map.on("click", "mon", (e) => {
      if (!e.features || !e.features[0]) return;
      if (picker) {                                                              // "tap the object" after a photo was shared from the phone (pwa.js)
        const p = e.features[0].properties, g = e.features[0].geometry.coordinates;
        let nm = p.name || "";
        try { if (window.GeoTr) nm = window.GeoTr.nameInfo(p.name, lang, p.wp).text || nm; } catch (er) {}
        const cb = picker; picker = null; cb({ obj: "mon:" + p.id, name: nm, lang, lat: g[1], lon: g[0] });
        return;
      }
      popup(e.features[0].properties, e.lngLat);
    });
    map.on("mouseenter", "mon", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "mon", () => { map.getCanvas().style.cursor = ""; });

    for (const id of ["stl-line", "stl-pt", "c94-pt", "c94-lb"]) if (map.getLayer(id)) map.moveLayer(id);   // overlays (old street names, 1894 objects) above the old plans
    buildTicks();
    applyLang();
    try {                                              // a link with ?o=<id> opens that object card
      const oid = new URL(location.href).searchParams.get("o");
      const f = oid && monuments.features.find((x) => String(x.properties.id) === oid);
      if (f) {
        year = Math.max(year, f.properties.ye);
        update();
        map.jumpTo({ center: f.geometry.coordinates, zoom: 17 });
        popup(f.properties, { lng: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] });
      }
    } catch (e) {}
    dataReady = true;
    loadChangelog();
    if (map.loaded()) hideLoading(); else map.once("idle", hideLoading);
  });

  window.addEventListener("hashchange", () => {
    const hy = parseInt((location.hash || "").slice(1), 10);
    if (hy >= MIN && hy <= MAX && hy !== year) { year = hy; update(); }
  });
  $("slider").addEventListener("input", (e) => { const y = v2y(+e.target.value); if (y !== year) { year = y; update(); } });
  for (const id of ["showPlan", "autoTopo", "showStLabels", "roadLabels", "show94", "showRel", "showSci", "showRulers", "showRun", "showBnd", "showAdmin", "showDistricts", "showSettle", "showWater", "showDensity", "showTransport", "showStreets", "showSwipe", "showHere", "showLost", "showGhost", "showNat", "showMon", "showObj", "showNoPhoto"]) $(id).addEventListener("change", update);
  $("op").addEventListener("input", (e) => {
    $("opv").textContent = e.target.value + "%";
    for (const p of plans) if (map.getLayer("plan-" + p.id)) map.setPaintProperty("plan-" + p.id, "raster-opacity", planOpacity());
  });
  function refreshCard() {
    try {
      if (!$("infoModal").hidden && reopenInfo) { reopenInfo(); return; }
      if (openPop && reopenPopup) { const rp = reopenPopup; openPop.remove(); rp(); }
    } catch (e) { console.error("card", e && e.message); }
  }
  $("lang").addEventListener("change", (e) => {
    lang = e.target.value;
    try { localStorage.setItem("lang", lang); } catch (e) {}
    applyLang();
    buildEvMarks();
    layoutSwipe();
    refreshCard();
  });

  let timer = null;
  const SPEEDS = [[1, 240], [2, 120], [3, 80]];          // playback speed: x1 (4 years/s after 1700), x2 (8), x3 (12, the original speed)
  let speedIx = 1;
  try { const k = parseInt(localStorage.getItem("speed"), 10); if (k >= 0 && k < SPEEDS.length) speedIx = k; } catch (e) {}
  $("speed").textContent = "×" + SPEEDS[speedIx][0];
  function stopPlay() { clearInterval(timer); timer = null; $("play").textContent = "▶"; }
  function startPlay() {
    clearInterval(timer);
    timer = setInterval(() => {
      year = Math.min(MAX, year + (year < 1000 ? 25 : year < 1700 ? 10 : 1));
      update();
      if (year >= MAX) stopPlay();
    }, SPEEDS[speedIx][1]);
  }
  $("play").addEventListener("click", () => {
    if (timer) { stopPlay(); return; }
    if (year >= MAX) year = MIN;
    $("play").textContent = "❚❚";
    startPlay();
  });
  $("speed").addEventListener("click", () => {
    speedIx = (speedIx + 1) % SPEEDS.length;
    $("speed").textContent = "×" + SPEEDS[speedIx][0];
    try { localStorage.setItem("speed", String(speedIx)); } catch (e) {}
    if (timer) startPlay();
  });

  // zoom of the time scale: the slider shows a window of years (ZOOM_W[zoomIx] wide) around the chosen year, so that a decade can be set exactly;
  // the window is moved with the arrow buttons or Shift+wheel, and follows the year when it leaves the window (playback, search, a click on an event)
  function applyWindow(lo) {
    if (zoomIx === 0) { KNOTS = FULL_KNOTS; zoomLo = MIN; zoomHi = MAX; }
    else {
      const w = ZOOM_W[zoomIx];
      lo = Math.round(lo);
      if (lo < MIN) lo = MIN;
      if (lo + w > MAX) lo = MAX - w;
      zoomLo = lo; zoomHi = lo + w; KNOTS = [[zoomLo, 0], [zoomHi, 1000]];
    }
    $("slider").value = Math.round(y2v(year));
    buildTicks(); buildEvMarks(); buildRulersBand(); updateZoomUi();
  }
  function ensureInWindow() {
    if (zoomIx === 0 || (year >= zoomLo && year <= zoomHi)) return;
    applyWindow(year - ZOOM_W[zoomIx] / 2);
  }
  function updateZoomUi() {
    $("zoomLbl").textContent = zoomIx === 0 ? t().zoomAll : zoomLo + "\u2013" + zoomHi;
    $("zoomIn").setAttribute("aria-label", t().zoomIn); $("zoomIn").title = t().zoomIn;
    $("zoomOut").setAttribute("aria-label", t().zoomOut); $("zoomOut").title = t().zoomOut;
    $("zoomL").setAttribute("aria-label", t().zoomL); $("zoomL").title = t().zoomL;
    $("zoomR").setAttribute("aria-label", t().zoomR); $("zoomR").title = t().zoomR;
    $("zoomOut").disabled = zoomIx === 0;
    $("zoomIn").disabled = zoomIx === ZOOM_W.length - 1;
    $("zoomL").disabled = zoomIx === 0 || zoomLo <= MIN;
    $("zoomR").disabled = zoomIx === 0 || zoomHi >= MAX;
  }
  function setZoom(ix) {
    zoomIx = ix;
    applyWindow(year - (ZOOM_W[ix] || 0) / 2);
    update();
  }
  function zoomBy(d) {
    const ix = zoomIx + d;
    if (ix < 0 || ix >= ZOOM_W.length) return;
    setZoom(ix);
  }
  function panWindow(dir) {
    if (zoomIx === 0) return;
    applyWindow(zoomLo + dir * ZOOM_W[zoomIx] / 2);
    if (year < zoomLo) year = zoomLo; else if (year > zoomHi) year = zoomHi;
    update();
  }
  $("zoomIn").addEventListener("click", () => zoomBy(1));
  $("zoomOut").addEventListener("click", () => zoomBy(-1));
  $("zoomL").addEventListener("click", () => panWindow(-1));
  $("zoomR").addEventListener("click", () => panWindow(1));
  $("sliderwrap").addEventListener("wheel", (e) => {
    e.preventDefault();
    if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) panWindow((e.deltaX || e.deltaY) > 0 ? 1 : -1);
    else zoomBy(e.deltaY < 0 ? 1 : -1);
  }, { passive: false });
  updateZoomUi();

  // the route of a run (TRC City Run 2026) and the architectural sights near it: a separate layer, independent of the year (the city of today)
  const RUN_COLOR = "#d9480f";
  function runGeo() {
    const feats = [{ type: "Feature", geometry: { type: "LineString", coordinates: runData.route.coords }, properties: { k: "line" } }];
    for (const s of runData.sights) feats.push({ type: "Feature", geometry: { type: "Point", coordinates: [s.lon, s.lat] }, properties: { k: "sight", n: s.n, label: s.name[lang] || s.name.en } });
    feats.push({ type: "Feature", geometry: { type: "Point", coordinates: runData.route.coords[0] }, properties: { k: "start" } });
    return { type: "FeatureCollection", features: feats };
  }
  function addRun() {
    if (!runData || map.getSource("run")) return;
    map.addSource("run", { type: "geojson", data: runGeo() });
    const only = (k) => ["==", ["get", "k"], k];
    map.addLayer({ id: "run-casing", type: "line", source: "run", filter: only("line"), layout: { visibility: "none", "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#ffffff", "line-width": 8, "line-opacity": 0.85 } });
    map.addLayer({ id: "run-line", type: "line", source: "run", filter: only("line"), layout: { visibility: "none", "line-join": "round", "line-cap": "round" }, paint: { "line-color": RUN_COLOR, "line-width": 4.5 } });
    map.addLayer({ id: "run-start", type: "circle", source: "run", filter: only("start"), layout: { visibility: "none" }, paint: { "circle-radius": 9, "circle-color": "#2b8a3e", "circle-stroke-color": "#ffffff", "circle-stroke-width": 2.5 } });
    map.addLayer({ id: "run-pt", type: "circle", source: "run", filter: only("sight"), layout: { visibility: "none" }, paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 9, 15, 11, 17, 14], "circle-color": RUN_COLOR, "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });
    map.addLayer({ id: "run-num", type: "symbol", source: "run", filter: only("sight"), layout: { visibility: "none", "text-field": ["to-string", ["get", "n"]], "text-font": ["Noto Sans Bold"], "text-size": ["interpolate", ["linear"], ["zoom"], 12, 11, 17, 14], "text-allow-overlap": true, "text-ignore-placement": true }, paint: { "text-color": "#ffffff" } });
    map.addLayer({ id: "run-lb", type: "symbol", source: "run", minzoom: 15.2, filter: only("sight"), layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 11.5, "text-offset": [0, 1.4], "text-anchor": "top", "text-optional": true }, paint: { "text-color": "#7a2e08", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "run-pt", (e) => {
      const f = e.features && e.features[0], s = f && runData.sights.find((x) => x.n === f.properties.n);
      if (s) popupRunSight(s, e.lngLat);
    });
    map.on("click", "run-line", (e) => { if (!map.queryRenderedFeatures(e.point, { layers: ["run-pt"] }).length) showRunCard(); });
    for (const id of ["run-pt", "run-line"]) {
      map.on("mouseenter", id, () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", id, () => { map.getCanvas().style.cursor = ""; });
    }
    updateRun(false);
  }
  function updateRun(fit) {
    if (!map.getLayer("run-line")) return;
    const on = $("showRun").checked;
    for (const id of ["run-casing", "run-line", "run-start", "run-pt", "run-num", "run-lb"]) map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
    if (on) {                                        // above the dots of the register objects, but not above the other layers
      const ids = ["run-casing", "run-line", "run-start", "run-pt", "run-num", "run-lb"], order = map.getStyle().layers.map((l) => l.id).filter((id) => !ids.includes(id));
      const at = order.indexOf("mon"), before = at >= 0 ? order[at + 1] : undefined;
      for (const id of ids) map.moveLayer(id, before);
    }
    if (on && fit) {
      const c = runData.route.coords, b = new maplibregl.LngLatBounds(c[0], c[0]);
      for (const p of c) b.extend(p);
      map.fitBounds(b, { padding: { top: Math.round($("timebar").getBoundingClientRect().bottom) + 30, bottom: document.body.classList.contains("rulers-on") ? 150 : 70, left: 330, right: 300 }, maxZoom: 15.6, duration: 900 });
    }
  }
  function updateRunUi() {
    const box = $("runLegend");
    if (box) box.textContent = runData ? t().runStats(runData.route, runData.sights.length) : "";
    const src = map && map.getSource && map.getSource("run");
    if (src && runData) src.setData(runGeo());
  }
  function runWikiLink(s) {
    const l = s.wp[lang] ? lang : s.wp.en ? "en" : s.wp.ru ? "ru" : s.wp.ka ? "ka" : null;
    return l ? "https://" + l + ".wikipedia.org/wiki/" + encodeURIComponent(s.wp[l].replace(/ /g, "_")) : null;
  }
  function popupRunSight(s, lngLat) {
    reopenPopup = () => popupRunSight(s, lngLat);
    const L = t(), el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = s.n + ". " + (s.name[lang] || s.name.en);
    el.appendChild(h3);
    const row = (k, v) => { if (v === null || v === undefined || v === "") return; const d = document.createElement("div"), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; d.appendChild(kk); d.appendChild(document.createTextNode(v)); el.appendChild(d); };
    row(L.runKm, String(s.km).replace(".", ","));
    row(L.runDist, s.d + " " + (lang === "ru" ? "м" : lang === "ka" ? "მ" : "m"));
    row(L.runYear, s.year ? "\u2248 " + s.year : "");
    const u = runWikiLink(s);
    if (u) { const d = document.createElement("div"), a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = L.runWiki; d.appendChild(a); el.appendChild(d); }
    showPopup("300px", lngLat, el);
  }
  function showRunCard() {
    reopenInfo = () => showRunCard();
    const L = t(), r = runData.route;
    openInfo((body) => {
      infoLine(body, "Tbilisi Running Club · TRC City Run 2026 \u00B7 " + L.runStats(r, runData.sights.length), "small");
      const pg = document.createElement("div");                         // the separate page of the route: its own link, a small map and the sights with descriptions and photos
      pg.className = "small";
      const pa = document.createElement("a");
      pa.href = "run/?lang=" + lang; pa.target = "_blank"; pa.rel = "noopener"; pa.textContent = L.runPage;
      const cp = document.createElement("button");
      cp.type = "button"; cp.className = "chip"; cp.style.marginLeft = "10px"; cp.textContent = L.runCopy;
      cp.addEventListener("click", async () => {
        const url = new URL("run/", location.href).href;                 // the common address (English by default), not the language of this window
        try { await navigator.clipboard.writeText(url); cp.textContent = L.runCopied; setTimeout(() => { cp.textContent = L.runCopy; }, 1800); } catch (e) { window.prompt(L.runCopy, url); }
      });
      pg.appendChild(pa); pg.appendChild(cp); body.appendChild(pg);
      infoLine(body, L.runList + ":", "");
      for (const s of runData.sights) infoLine(body, s.n + ". " + String(s.km).replace(".", ",") + " " + (lang === "ru" ? "км" : lang === "ka" ? "კმ" : "km") + " \u00B7 " + (s.name[lang] || s.name.en) + " \u00B7 " + s.d + " " + (lang === "ru" ? "м" : lang === "ka" ? "მ" : "m"), "small");
      infoLine(body, L.runNote);
      infoLine(body, L.runSrc + ":");
      const d = document.createElement("div"), a = document.createElement("a");
      d.className = "small"; a.href = r.src; a.target = "_blank"; a.rel = "noopener"; a.textContent = r.src.replace("https://", "");
      d.appendChild(a); body.appendChild(d);
    });
  }
  $("showRun").addEventListener("change", () => updateRun($("showRun").checked));

  // forms of state and rulers over Tbilisi: a band under the time scale (two rows with up to two lanes each), a line "who ruled" in the side panel, a card on a click
  const RULE_MAIN_H = 22, RULE_SUB_H = 14, RULE_GAP = 2;               // the main row of the band (lane 0) and the thin row (lane 1: overlords, second rulers)
  const dispYear = (v) => Math.floor(v + 0.0001);
  const rText = (o) => (o && (o[lang] || o.en)) || "";
  // the heights of the time bar (top) and of the bar of rulers (bottom) go to CSS: the panels lie between them; the band of rulers is aligned with the track of the slider
  function syncBars() {
    alignRulers();
    const tb = $("timebar"), bb = $("bottom"), root = document.documentElement.style;
    root.setProperty("--tb", Math.round(tb.getBoundingClientRect().height) + "px");
    const bh = bb.getBoundingClientRect().height;
    root.setProperty("--bb", (bh ? Math.round(bh) + 30 : 0) + "px");
    updateToken();
    updateRuleSummary();
    markRulers();
  }
  window.addEventListener("load", () => syncBars());
  function alignRulers() {                     // the summary "who rules now" stands left of the slider track, the axis (rulers) has the extent of the slider
    const ax = $("axis"), rn = $("ruleNow"), bar = $("bottom"), sw = $("sliderwrap").getBoundingClientRect(), b = bar.getBoundingClientRect(), cs = getComputedStyle(bar);
    if (!ax || !b.width || !sw.width) return;
    const L = Math.max(0, Math.round(sw.left - b.left - parseFloat(cs.paddingLeft)));
    rn.style.width = L + "px";
    ax.style.marginLeft = "0px";
    ax.style.marginRight = Math.max(0, Math.round(b.right - sw.right - parseFloat(cs.paddingRight))) + "px";
  }
  function buildRulersBand() {
    const box = $("rulers");
    if (!box) return;
    const on = $("showRulers") && $("showRulers").checked && rulersData;
    box.hidden = !on;
    document.body.classList.toggle("rulers-on", !!on);
    if (!on) { syncBars(); return; }
    alignRulers();
    const lo = zoomLo, hi = zoomHi, W = Math.max(0, $("rStates").clientWidth - 16);
    const fill = (row, items, kindOf, nameOf) => {
      row.textContent = "";
      let lanes = 0;
      for (const it of items) {
        if (it.to <= lo || it.from >= hi) continue;
        const a = Math.max(it.from, lo), b = Math.min(it.to, hi), x1 = y2v(a) / 1000, x2 = y2v(b) / 1000;
        const px = (x2 - x1) * W;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "rseg " + kindOf(it) + (it.approx ? " approx" : "") + (it.lane ? " sub" : "");
        btn.dataset.from = it.from; btn.dataset.to = it.to;
        const MIN = 6, grow = px < MIN ? (MIN - px) / 2 : 0;           // a term shorter than 6 px is widened to 6 px around its place
        btn.style.left = "calc(8px + (100% - 16px) * " + x1 + " - " + grow.toFixed(1) + "px)";
        btn.style.width = px < MIN ? MIN + "px" : "calc((100% - 16px) * " + (x2 - x1) + ")";
        if (px < MIN) btn.classList.add("short");
        const lane = it.lane || 0;
        btn.style.top = (lane ? RULE_MAIN_H + RULE_GAP : 0) + "px";
        lanes = Math.max(lanes, lane + 1);
        if (px >= (lane ? 56 : 46)) btn.textContent = nameOf(it); else btn.classList.add("nolabel");       // no text: no padding, so the width is the real length of the term
        btn.title = nameOf(it) + " \u00B7 " + dispYear(it.from) + "\u2013" + dispYear(it.to);
        btn.addEventListener("click", () => showRulerCard(it));
        row.appendChild(btn);
      }
      row.style.height = (lanes > 1 ? RULE_MAIN_H + RULE_GAP + RULE_SUB_H : RULE_MAIN_H) + "px";
    };
    fill($("rStates"), rulersData.states, (it) => "rk-" + it.kind, (it) => rText(it.name));
    fill($("rRulers"), rulersData.rulers, (it) => "rg-" + it.grp, (it) => rText(it.name));
    markRulers();
    syncBars();
  }
  function showRulerCard(it) {
    reopenInfo = () => showRulerCard(it);
    const L = t(), isState = it.kind !== undefined, g = rulersData.groups[isState ? it.kind : it.grp];
    openInfo((body) => {
      infoLine(body, (rText(g) || "") + " \u00B7 " + dispYear(it.from) + "\u2013" + dispYear(it.to), "small");
      infoLine(body, rText(it.name), "");
      const pm = !isState && rulersMedia && rulersMedia.rulers && rulersMedia.rulers[it.id];
      if (pm) { const bi = mediaImg(pm.b || pm.i, 0, 0, rText(it.name)); bi.className = "rbig"; body.appendChild(bi); credit(body, pm, it.from < 1700); }
      if (isState && rulersMedia && rulersMedia.flags && rulersMedia.flags[it.id]) {
        for (const f of rulersMedia.flags[it.id].slice().sort((a, b) => a.from - b.from)) {
          const row = document.createElement("div"); row.className = "small";
          { const fi = mediaImg(f.b || f.i, 0, 0, (RN[lang] || RN.en).flag); fi.className = "rflag"; row.appendChild(fi); } row.appendChild(document.createTextNode(" " + dispYear(f.from) + "–" + dispYear(f.to) + (f.k === "recon" ? " · " + (RN[lang] || RN.en).recon : f.k === "civil" ? " · " + (RN[lang] || RN.en).civil : "")));
          body.appendChild(row); credit(body, f, false);
        }
      }
      if (isState && it.form) infoLine(body, L.ruleForm + ": " + rText(it.form));
      if (!isState && it.title) infoLine(body, rText(it.title));
      if (it.note && rText(it.note)) infoLine(body, rText(it.note));
      if (it.approx) infoLine(body, "\u2248");
      infoLine(body, L.evSrc + ":");
      for (const u of it.src) {
        const d = document.createElement("div"), a = document.createElement("a");
        d.className = "small";
        a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURI(u).replace("https://", "");
        d.appendChild(a);
        body.appendChild(d);
      }
    });
  }
  // the plate under the band: the flag of the period and up to two rulers with their portraits (Wikimedia Commons; the author and the licence are in the card)
  const RN = {
    ru: { civil: "гражданский флаг, государственного флага не было", recon: "реконструкция", img: "Изображение", cond: "До XVIII века это условное изображение (роспись, миниатюра или памятник), а не прижизненный портрет.", flag: "Флаг", open: "Карточка", src: "файл на Commons" },
    en: { civil: "civil ensign; there was no national flag", recon: "reconstruction", img: "Image", cond: "Before the 18th century this is a conventional image (a fresco, a miniature or a monument), not a portrait from life.", flag: "Flag", open: "Card", src: "file on Commons" },
    ka: { civil: "სამოქალაქო დროშა; სახელმწიფო დროშა არ იყო", recon: "რეკონსტრუქცია", img: "გამოსახულება", cond: "XVIII საუკუნემდე ეს პირობითი გამოსახულებაა (ფრესკა, მინიატურა ან ძეგლი), და არა ცოცხალი პორტრეტი.", flag: "დროშა", open: "ბარათი", src: "ფაილი Commons-ზე" },
  };
  const RGROUP_ORDER = ["king", "emperor", "president", "secretary", "head", "viceroy", "wali", "emir"];
  function mediaImg(rel, w, h, alt) {
    const i = document.createElement("img");
    i.src = "data/rulers/" + rel; i.alt = alt || ""; i.loading = "lazy"; i.decoding = "async";
    if (w) i.width = w;
    if (h) i.height = h;
    return i;
  }
  const flagFor = (stateId, yr) => { const l = rulersMedia && rulersMedia.flags && rulersMedia.flags[stateId]; return l ? l.find((f) => f.from <= yr && yr < f.to) : null; };
  function credit(body, m, withCond) {
    const d = document.createElement("div"), a = document.createElement("a"), R = RN[lang] || RN.en;
    d.className = "small";
    d.appendChild(document.createTextNode(R.img + ": " + (m.a ? m.a + ", " : "") + (m.l || "") + " · "));
    a.href = m.u; a.target = "_blank"; a.rel = "noopener noreferrer"; a.textContent = R.src;
    d.appendChild(a); body.appendChild(d);
    if (withCond) { const c = document.createElement("div"); c.className = "small"; c.textContent = R.cond; body.appendChild(c); }
  }
  // the token on the slider: the flag of the year and up to two rulers; it rides with the thumb and changes only when the state or a ruler changes (no flicker while playing)
  function updateToken() {
    const tk = $("ruleToken");
    if (!tk) return;
    if (!rulersData || !$("showRulers").checked) { tk.hidden = true; tk.dataset.key = ""; return; }
    const R = RN[lang] || RN.en, within = (it) => it.from < year + 1 && it.to > year;
    const st = rulersData.states.find((s) => within(s) && !s.lane);
    const rl = rulersData.rulers.filter(within).sort((a, b) => RGROUP_ORDER.indexOf(a.grp) - RGROUP_ORDER.indexOf(b.grp)).filter((r, i, a) => a.findIndex((x) => x.name.en === r.name.en) === i).slice(0, 2);
    const fl = st ? flagFor(st.id, year + 0.5) : null;
    const key = (st ? st.id : "") + "|" + rl.map((r) => r.id).join(",") + "|" + (fl ? fl.i : "") + "|" + lang;
    if (tk.dataset.key !== key) {
      tk.dataset.key = key; tk.textContent = "";
      for (const r of rl) {
        const m = rulersMedia && rulersMedia.rulers && rulersMedia.rulers[r.id];
        if (m) { const i = mediaImg(m.i, 32, 40, rText(r.name)); i.className = "tkp"; i.title = rText(r.name) + " · " + dispYear(r.from) + "–" + dispYear(r.to); tk.appendChild(i); }
      }
      if (rl.length && !tk.querySelector(".tkp")) {          // no portrait: a crown for the rulers of the monarchies, a star for the others
        const g = document.createElement("span"); g.className = "tkph"; g.textContent = ["king", "emperor", "wali", "emir"].includes(rl[0].grp) ? "♛" : "★";
        g.title = rText(rl[0].name) + " · " + dispYear(rl[0].from) + "–" + dispYear(rl[0].to); tk.appendChild(g);
      }
      if (fl) { const i = mediaImg(fl.i, 0, 22, R.flag); i.className = "tkf"; i.title = R.flag + ": " + rText(st.name) + (fl.k === "recon" ? " (" + R.recon + ")" : fl.k === "civil" ? " (" + R.civil + ")" : ""); tk.appendChild(i); }
      if (tk.children.length) {
        const b = document.createElement("button");
        b.type = "button"; b.className = "tki"; b.textContent = "i"; b.setAttribute("aria-label", R.open);
        b.addEventListener("click", (e) => { e.stopPropagation(); showRulerCard(rl[0] || st); });
        tk.appendChild(b);
      }
      tk.setAttribute("aria-label", (st ? rText(st.name) : "") + (rl.length ? ": " + rl.map((r) => rText(r.name)).join(", ") : ""));
    }
    tk.hidden = !tk.children.length;
    if (tk.hidden) return;
    const sw = $("sliderwrap"), W = sw.clientWidth, half = tk.offsetWidth / 2;
    tk.style.left = Math.min(Math.max(8 + (W - 16) * (+$("slider").value / 1000), half), W - half) + "px";
  }
  // the highlight of the periods that contain the year (the others are dimmed) and the line at the position of the thumb
  function markRulers() {
    const y = year + 0.5;
    for (const el of document.querySelectorAll("#rulers .rseg")) el.classList.toggle("on", +el.dataset.from <= y && +el.dataset.to > y);
    const h = $("rhead");
    if (h) h.style.left = "calc(8px + (100% - 16px) * " + (+$("slider").value / 1000) + " - 1px)";
  }
  // the summary at the left of the band: the form of government, the state, the rulers of the year, in a readable size
  function updateRuleSummary() {
    const box = $("ruleNow");
    if (!box) return;
    box.textContent = "";
    if (!rulersData || !$("showRulers").checked) return;
    const L = t(), within = (it) => it.from < year + 1 && it.to > year;
    const st = rulersData.states.find((s) => within(s) && !s.lane), ov = rulersData.states.filter((s) => within(s) && s.lane);
    const rl = rulersData.rulers.filter(within).filter((r, i, a) => a.findIndex((x) => x.name.en === r.name.en && x.grp === r.grp) === i);
    const line = (cls, txt) => { const d = document.createElement("div"); d.className = cls; d.textContent = txt; box.appendChild(d); return d; };
    if (st) {
      line("rs1", rText(st.name));
      if (st.form && rText(st.form)) line("rs2", rText(st.form));
    } else line("rs2", L.ruleNoData);
    for (const s of ov) line("rs3", (s.kind === "overlord" ? L.ruleOver : L.ruleAdmin) + ": " + rText(s.name));
    for (const r of rl.slice(0, 3)) line("rs3", (rText(r.title) || rText(rulersData.groups[r.grp])) + ": " + rText(r.name));
  }
  function updateRuleLine() {
    updateToken();
    updateRuleSummary();
    markRulers();
    const box = $("ruleline");
    if (!box) return;
    box.textContent = "";
    if (!rulersData || !$("showRulers").checked) return;
    const L = t(), within = (it) => it.from < year + 1 && it.to > year;
    const add = (k, v) => { const d = document.createElement("div"); const kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; d.appendChild(kk); d.appendChild(document.createTextNode(v)); box.appendChild(d); };
    const st = rulersData.states.filter((s) => within(s) && !s.lane), ov = rulersData.states.filter((s) => within(s) && s.lane);
    const rl = rulersData.rulers.filter(within);
    const head = document.createElement("div");
    head.className = "small";
    head.textContent = L.ruleNow + " (" + year + ")";
    box.appendChild(head);
    add(L.ruleState, st.length ? st.map((s) => rText(s.name)).join("; ") : L.ruleNoData);
    for (const s of ov) add(s.kind === "overlord" ? L.ruleOver : L.ruleAdmin, rText(s.name));
    for (const r of rl) add(rText(r.title) || rText(rulersData.groups[r.grp]), rText(r.name));
  }
  $("showRulers").addEventListener("change", () => { buildRulersBand(); updateRuleLine(); });
  if (window.innerWidth > 900) $("showRulers").checked = true;      // on a narrow screen the band stays off until it is asked for

  // science and culture: universities, institutes, libraries, museums, theatres; points that appear in the year (data/science.json); science is drawn larger and above culture
  const SCI_COLOR = { science: "#1c7ed6", culture: "#868e96" };
  const sciFeats = () => science.map((c) => ({ type: "Feature", geometry: { type: "Point", coordinates: [c.lon, c.lat] },
    properties: { id: c.id, kind: c.kind, from: c.from, sf: c.sf || 0, label: c.name[lang] || c.name.en } }));
  function addScience() {
    if (!science.length || map.getSource("sci")) return;
    map.addSource("sci", { type: "geojson", data: { type: "FeatureCollection", features: sciFeats() } });
    const sci = ["==", ["get", "kind"], "science"];
    map.addLayer({ id: "sci-pt", type: "circle", source: "sci", layout: { visibility: "none", "circle-sort-key": ["case", sci, 2, 1] },
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, ["case", sci, 6.5, 4.5], 17, ["case", sci, 12.5, 9]], "circle-color": ["case", sci, SCI_COLOR.science, SCI_COLOR.culture],
               "circle-stroke-color": ["case", sci, "#0b3d91", "#343a40"], "circle-stroke-width": 2, "circle-opacity": 1, "circle-stroke-opacity": 1 } });
    map.addLayer({ id: "sci-lb", type: "symbol", source: "sci", minzoom: 14.5, layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.3], "text-anchor": "top", "text-optional": true },
      paint: { "text-color": ["case", sci, "#0b3d91", "#495057"], "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "sci-pt", (e) => {
      const f = e.features && e.features[0], c = f && science.find((x) => x.id === f.properties.id);
      if (c) popupSci(c, e.lngLat);
    });
    map.on("mouseenter", "sci-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "sci-pt", () => { map.getCanvas().style.cursor = ""; });
    updateScience();
  }
  function updateScience() {
    if (!map.getLayer("sci-pt")) return;
    const on = $("showSci").checked;
    for (const id of ["sci-pt", "sci-lb"]) {
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["<=", ["get", "from"], year]);
    }
    for (const id of ["sci-pt", "sci-lb"]) map.moveLayer(id);          // to the top: above the topographic map and the points of the register, which other code also moves
    const faint = ["case", ["<", year, ["get", "sf"]], 0.35, 1];       // before the present building stands (or the institution is in another place) the point is faint
    map.setPaintProperty("sci-pt", "circle-opacity", faint);
    map.setPaintProperty("sci-pt", "circle-stroke-opacity", faint);
  }
  function updateSciUi() {
    const box = $("sciLegend");
    if (box) {
      box.textContent = "";
      for (const k of Object.keys(SCI_COLOR)) { const s = document.createElement("span"); s.textContent = t().sciKinds[k]; s.style.setProperty("--c", SCI_COLOR[k]); box.appendChild(s); }
    }
    const src = map && map.getSource && map.getSource("sci");
    if (src) src.setData({ type: "FeatureCollection", features: sciFeats() });
  }
  function popupSci(c, lngLat) {
    reopenPopup = () => popupSci(c, lngLat);
    const L = t(), el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = c.name[lang] || c.name.en;
    el.appendChild(h3);
    const row = (k, v) => { if (!v) return; const d = document.createElement("div"), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; d.appendChild(kk); d.appendChild(document.createTextNode(v)); el.appendChild(d); };
    const rr = document.createElement("div");
    rr.className = "k";
    rr.textContent = L.sciKinds[c.kind] || c.kind;
    el.appendChild(rr);
    row(L.sciFounded, c.founded);
    row(L.sciBuilt, c.built);
    if (!String(c.founded || "").includes(String(c.from))) row(L.sciFrom, String(c.from));
    if (c.approx) row(L.relApprox, "\u2248");
    if (c.sf && year < c.sf) row("\u25CB", L.sciFaint);
    const n = document.createElement("div");
    n.className = "small";
    n.textContent = c.note[lang] || c.note.en;
    el.appendChild(n);
    const s = document.createElement("div");
    s.className = "src";
    s.appendChild(document.createTextNode(L.sciSrc + ": "));
    c.src.forEach((u, i) => { const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURIComponent(u.replace("https://", "")).slice(0, 60); if (i) s.appendChild(document.createTextNode(" \u00B7 ")); s.appendChild(a); });
    el.appendChild(s);
    showPopup("340px", lngLat, el);
  }
  $("showSci").addEventListener("change", updateScience);

  // religious buildings of different religions: points that appear in the year of the building and disappear when it was destroyed
  const REL_COLOR = { orthodox: "#b8860b", russian: "#6741d9", lutheran: "#868e96", yazidi: "#74b816", armenian: "#c2255c", catholic: "#1971c2", jewish: "#2f9e44", muslim: "#087f5b", zoroastrian: "#e8590c" };
  function addReligious() {
    if (!religious.length || map.getSource("rel")) return;
    const feats = religious.map((r) => ({ type: "Feature", geometry: { type: "Point", coordinates: [r.lon, r.lat] },
      properties: { id: r.id, from: r.from, to: r.to === undefined ? 99999 : r.to, color: REL_COLOR[r.rel] || "#555", label: r.name[lang] || r.name.en } }));
    map.addSource("rel", { type: "geojson", data: { type: "FeatureCollection", features: feats } });
    map.addLayer({ id: "rel-pt", type: "circle", source: "rel", layout: { visibility: "none" }, paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 5, 17, 10], "circle-color": ["get", "color"], "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });
    map.addLayer({ id: "rel-lb", type: "symbol", source: "rel", minzoom: 14.5, layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.2], "text-anchor": "top", "text-optional": true }, paint: { "text-color": "#222222", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "rel-pt", (e) => {
      const f = e.features && e.features[0], r = f && religious.find((x) => x.id === f.properties.id);
      if (r) popupRel(r, e.lngLat);
    });
    map.on("mouseenter", "rel-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "rel-pt", () => { map.getCanvas().style.cursor = ""; });
    updateReligious();
  }
  function updateReligious() {
    if (!map.getLayer("rel-pt")) return;
    const on = $("showRel").checked;
    for (const id of ["rel-pt", "rel-lb"]) {
      map.moveLayer(id);                                              // to the top: above the topographic map and the points of the register (the layer of science and culture goes above this one)
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["all", ["<=", ["get", "from"], year], [">", ["get", "to"], year]]);
    }
  }
  function updateRelUi() {
    const box = $("relLegend");
    if (box) {
      box.textContent = "";
      for (const k of Object.keys(REL_COLOR)) { const s = document.createElement("span"); s.textContent = t().relNames[k]; s.style.setProperty("--c", REL_COLOR[k]); box.appendChild(s); }
    }
    const src = map && map.getSource && map.getSource("rel");
    if (src) src.setData({ type: "FeatureCollection", features: religious.map((r) => ({ type: "Feature", geometry: { type: "Point", coordinates: [r.lon, r.lat] },
      properties: { id: r.id, from: r.from, to: r.to === undefined ? 99999 : r.to, color: REL_COLOR[r.rel] || "#555", label: r.name[lang] || r.name.en } })) });
  }
  function popupRel(r, lngLat) {
    reopenPopup = () => popupRel(r, lngLat);
    const L = t(), el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = r.name[lang] || r.name.en;
    el.appendChild(h3);
    const row = (k, v) => { if (!v) return; const d = document.createElement("div"), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; d.appendChild(kk); d.appendChild(document.createTextNode(v)); el.appendChild(d); };
    const rr = document.createElement("div");
    rr.className = "k";
    rr.textContent = L.relNames[r.rel] || r.rel;
    el.appendChild(rr);
    row(L.relBuilt, r.date);
    if (r.approx) row(L.relApprox, "≈");
    if (r.to !== undefined) row(L.relGone, String(r.to));
    row(L.relStatus, r.status[lang] || r.status.en);
    const n = document.createElement("div");
    n.className = "small";
    n.textContent = r.note[lang] || r.note.en;
    el.appendChild(n);
    const s = document.createElement("div");
    s.className = "src";
    s.appendChild(document.createTextNode(L.relSrc + ": "));
    r.src.forEach((u, i) => { const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURIComponent(u.replace("https://", "")).slice(0, 60); if (i) s.appendChild(document.createTextNode(" \u00B7 ")); s.appendChild(a); });
    el.appendChild(s);
    showPopup("320px", lngLat, el);
  }

  // search: objects of the register (name and address in three languages), historical events and years
  const normQ = (s) => String(s || "").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^\p{L}\p{N}]+/gu, " ").trim();
  function buildSearchIndex() {
    const idx = [], tr = window.GeoTr;
    for (const f of (monuments ? monuments.features : [])) {
      const p = f.properties, parts = [p.name || "", p.address || ""];
      for (const l of ["ru", "en"]) {
        try { if (tr) { parts.push(tr.nameInfo(p.name, l, p.wp).text, tr.address(p.address, l)); } } catch (e) {}
      }
      idx.push({ kind: "o", f, key: normQ(parts.join(" ")) });
    }
    for (const ev of histEvents) idx.push({ kind: "e", ev, key: normQ([ev.ru, ev.en, ev.ka, ev.date, ev.year].join(" ")) });
    if (rulersData) for (const u of rulersData.rulers.concat(rulersData.states)) idx.push({ kind: "u", u, key: normQ([u.name.ru, u.name.en, u.name.ka, u.title ? u.title.ru + " " + u.title.en : "", Math.floor(u.from), Math.floor(u.to)].join(" ")) });
    for (const c of science) idx.push({ kind: "s", c, key: normQ([c.name.ru, c.name.en, c.name.ka, c.founded, c.built, c.from, T.ru.sciKinds[c.kind], T.en.sciKinds[c.kind]].join(" ")) });
    for (const r of religious) idx.push({ kind: "r", r, key: normQ([r.name.ru, r.name.en, r.name.ka, r.date, t().relNames[r.rel], T.en.relNames[r.rel]].join(" ")) });
    return idx;
  }
  function updateSearchUi() {
    $("searchQ").placeholder = t().searchPh;
    $("searchQ").setAttribute("aria-label", t().searchPh);
    $("btnSearch").title = t().searchBtn;
    $("btnSearch").setAttribute("aria-label", t().searchBtn);
    if (!$("search").hidden) renderSearch();
  }
  // does the word w, or its beginning of the length of the query, differ from the query tk by at most one letter (changed, lost or added)?
  function within1(tk, w) {
    for (const v of [w, w.slice(0, tk.length), w.slice(0, tk.length + 1), w.slice(0, tk.length - 1)]) {
      if (Math.abs(v.length - tk.length) > 1) continue;
      let i = 0;
      while (i < v.length && i < tk.length && v[i] === tk[i]) i++;
      if (v.length === tk.length && v.slice(i + 1) === tk.slice(i + 1)) return true;
      if (v.length === tk.length + 1 && v.slice(i + 1) === tk.slice(i)) return true;
      if (v.length + 1 === tk.length && v.slice(i) === tk.slice(i + 1)) return true;
    }
    return false;
  }
  function runSearch(q) {
    const toks = normQ(q).split(" ").filter(Boolean);
    const rows = [];
    if (!toks.length) return rows;
    if (/^\d{3,4}$/.test(toks[0]) && toks.length === 1 && +toks[0] >= MIN && +toks[0] <= MAX) rows.push({ kind: "y", year: +toks[0] });
    if (!searchIndex || (searchIndex.length === 0 && monuments)) searchIndex = buildSearchIndex();
    const scored = [];
    for (const it of searchIndex) {
      let s = 0;
      for (const tk of toks) {
        const k = it.key;
        if (!k.includes(tk)) { s = -1; break; }
        s += k.startsWith(tk) ? 3 : k.includes(" " + tk) ? 2 : 1;
      }
      if (s >= 0) scored.push({ it, s: s + (it.kind === "e" ? 0.5 : 0) });
    }
    if (!scored.length && toks.some((tk) => tk.length >= 5)) {      // nothing found: one typo (a letter changed, lost or added) is allowed in the words of 5+ letters
      for (const it of searchIndex) {
        const words = it.key.split(" ");
        let s = 0;
        for (const tk of toks) {
          if (it.key.includes(tk)) { s += 2; continue; }
          if (tk.length < 5 || !words.some((w) => within1(tk, w))) { s = -1; break; }
          s += 1;
        }
        if (s >= 0) scored.push({ it, s });
      }
    }
    scored.sort((a, b) => b.s - a.s);
    for (const x of scored.slice(0, 40)) rows.push(x.it);
    rows.more = scored.length > 40;
    return rows;
  }
  function renderSearch() {
    const L = t(), ul = $("searchRes");
    ul.textContent = "";
    const q = $("searchQ").value;
    searchRows = runSearch(q);
    searchSel = searchRows.length ? 0 : -1;
    if (!normQ(q)) return;
    if (!searchRows.length) { const li = document.createElement("li"); li.className = "sn"; li.textContent = L.searchNone; ul.appendChild(li); return; }
    searchRows.forEach((r, i) => {
      const li = document.createElement("li"), a = document.createElement("div"), b = document.createElement("div");
      b.className = "st";
      if (r.kind === "y") { a.textContent = "\u23F1 " + L.searchYear + " " + r.year; }
      else if (r.kind === "u") { a.textContent = "\uD83D\uDC51 " + rText(r.u.name); b.textContent = [rText(r.u.title) || rText(rulersData.groups[r.u.grp || r.u.kind]), Math.floor(r.u.from) + "–" + Math.floor(r.u.to)].filter(Boolean).join(" · "); }
      else if (r.kind === "s") { a.textContent = (r.c.kind === "science" ? "\uD83D\uDD2C " : "\uD83C\uDFAD ") + (r.c.name[lang] || r.c.name.en); b.textContent = [L.sciKinds[r.c.kind], r.c.founded ? L.sciFounded + " " + r.c.founded : r.c.from].filter(Boolean).join(" \u00B7 "); }
      else if (r.kind === "r") { a.textContent = "\u26EA " + (r.r.name[lang] || r.r.name.en); b.textContent = [L.relNames[r.r.rel], r.r.date, r.r.to ? L.relGone + " " + r.r.to : ""].filter(Boolean).join(" \u00B7 "); }
      else if (r.kind === "e") { a.textContent = (EV_ICON[r.ev.cat] || EV_ICON.other) + " " + (r.ev[lang] || r.ev.en); b.textContent = r.ev.date + " \u00B7 " + (L.evCats[r.ev.cat] || ""); }
      else {
        const p = r.f.properties, tr = window.GeoTr;
        let nm = p.name, ad = p.address;
        try { if (tr) { nm = tr.nameInfo(p.name, lang, p.wp).text || p.name; ad = tr.address(p.address, lang); } } catch (e) {}
        a.textContent = (p.fn === "religious" ? "\u26EA " : "\uD83C\uDFDB\uFE0F ") + (nm || "\u2014");
        b.textContent = [ad, (L.classes[p.cls] || p.cls), p.ye].filter(Boolean).join(" \u00B7 ");
      }
      li.appendChild(a); if (b.textContent) li.appendChild(b);
      li.addEventListener("mousedown", (e) => e.preventDefault());
      li.addEventListener("click", () => pickSearch(r));
      li.dataset.i = i;
      ul.appendChild(li);
    });
    if (searchRows.more) { const li = document.createElement("li"); li.className = "sn"; li.textContent = L.searchMore; ul.appendChild(li); }
    markSearchSel();
  }
  function markSearchSel() {
    [...$("searchRes").querySelectorAll("li[data-i]")].forEach((li) => {
      const on = +li.dataset.i === searchSel;
      li.classList.toggle("sel", on);
      if (on) li.scrollIntoView({ block: "nearest" });
    });
  }
  function closeSearch() { $("search").hidden = true; $("btnSearch").setAttribute("aria-expanded", "false"); }
  function openSearch() {
    $("search").hidden = false; $("btnSearch").setAttribute("aria-expanded", "true");
    $("searchQ").focus(); $("searchQ").select();
    if ($("searchQ").value) renderSearch();
  }
  function pickSearch(r) {
    closeSearch();
    let target = year;
    if (r.kind === "y") target = r.year;
    else if (r.kind === "e") target = r.ev.year;
    else if (r.kind === "u") target = (year >= r.u.from && year < r.u.to) ? year : Math.floor(r.u.from);
    else if (r.kind === "s") target = Math.max(year, r.c.from);
    else if (r.kind === "r") target = (year >= r.r.from && (r.r.to === undefined || year < r.r.to)) ? year : r.r.from;
    else target = Math.max(year, r.f.properties.ye);
    year = target;
    update();
    if (r.kind === "e") { showHistEvent(r.ev); return; }
    if (r.kind === "u") {
      $("showRulers").checked = true; buildRulersBand(); updateRuleLine();
      showRulerCard(r.u);
      return;
    }
    if (r.kind === "s") {
      $("showSci").checked = true; updateScience();
      map.flyTo({ center: [r.c.lon, r.c.lat], zoom: Math.max(map.getZoom(), 16.5), duration: 1200 });
      popupSci(r.c, { lng: r.c.lon, lat: r.c.lat });
      return;
    }
    if (r.kind === "r") {
      $("showRel").checked = true; updateReligious();
      map.flyTo({ center: [r.r.lon, r.r.lat], zoom: Math.max(map.getZoom(), 16.5), duration: 1200 });
      popupRel(r.r, { lng: r.r.lon, lat: r.r.lat });
      return;
    }
    if (r.kind === "o") {
      const [lng, lat] = r.f.geometry.coordinates;
      map.flyTo({ center: [lng, lat], zoom: Math.max(map.getZoom(), 17), duration: 1200 });
      popup(r.f.properties, { lng, lat });
    }
  }
  $("btnSearch").addEventListener("click", () => { if ($("search").hidden) openSearch(); else closeSearch(); });
  $("searchQ").addEventListener("input", renderSearch);
  $("searchQ").addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); if (searchRows.length) { searchSel = (searchSel + 1) % searchRows.length; markSearchSel(); } }
    else if (e.key === "ArrowUp") { e.preventDefault(); if (searchRows.length) { searchSel = (searchSel - 1 + searchRows.length) % searchRows.length; markSearchSel(); } }
    else if (e.key === "Enter") { e.preventDefault(); if (searchRows[searchSel]) pickSearch(searchRows[searchSel]); }
    else if (e.key === "Escape") { e.preventDefault(); closeSearch(); $("btnSearch").focus(); }
  });
  updateSearchUi();

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", update);
  window.addEventListener("resize", () => { if (urbanSnaps.length || plans.length) buildTicks(); buildRulersBand(); });
  $("slider").value = Math.round(y2v(year));
  $("year").textContent = year;
})();
