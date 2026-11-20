// The page "Entrance Halls of Tbilisi": a walking route through Sololaki past old residential houses with painted entrance halls.
// Data: ../data/entrances.json (stops, route and walking times, see tools/build_entrances.py). The order of the stops is the one with the least walking time
// (computed once, not in the browser). The position of the visitor ("where am I") is used only in the browser and is sent nowhere. No codes of door locks.
(function () {
  "use strict";
  const LANGS = ["ru", "en", "ka"];
  let lang = "en";
  try { const s = localStorage.getItem("entrLang"); if (LANGS.includes(s)) lang = s; } catch (e) {}
  const q = new URLSearchParams(location.search).get("lang");
  if (LANGS.includes(q)) lang = q;
  const $ = (id) => document.getElementById(id);
  const num = (v) => String(v).replace(".", lang === "en" ? "." : ",");

  const T = {
    ru: {
      title: "Парадные Тбилиси: пешеходный маршрут", home: "К карте с таймлайном", share: "Скопировать ссылку", copied: "Ссылка скопирована", loading: "Загрузка карты…",
      intro: (p) => `Пешеходный маршрут «${p.title.ru}» мимо старых жилых домов с парадными конца XIX — начала XX века: <b>${p.stops.length} ${p.stops.length === 1 ? "дом" : p.stops.length < 5 ? "дома" : "домов"}</b>, <b>${num(p.route.length_km)} км</b>, около <b>${p.route.walk_min} мин</b> ходьбы без остановок. Старт и финиш у станции метро «Площадь Свободы». Порядок домов подобран так, чтобы идти как можно меньше: время считалось по уличным путям OpenStreetMap с учётом подъёмов, перебором всех порядков. Годы и авторы взяты из таблицы зданий в диссертации Т. Кутателадзе (2015) и из реестра культурного наследия; где они расходятся, это сказано в карточке.`,
      tab: (t, n) => `${t} (${n})`, imgAlt: (n) => `Фото: ${n}`, locate: "Где я: ближайший дом", gpx: "Скачать GPX", busy: "Определяю положение…", denied: "Не удалось определить положение (разрешите доступ к геолокации в браузере).", nogeo: "Браузер не умеет определять положение.",
      nearest: (n, addr, d) => `Ближайший не отмеченный дом: № ${n}, ${addr}, примерно ${d} м по прямой. Положение остаётся в вашем браузере и никуда не отправляется.`, alldone: "Все дома отмечены. Ваше положение остаётся в браузере и никуда не отправляется.",
      legFirst: (m, d) => `${m} мин пешком от метро (${d} м)`, leg: (m, d) => `${m} мин пешком от предыдущего дома (${d} м)`, back: (m, d) => `Возвращение к метро «Площадь Свободы» от последнего дома: ${m} мин (${d} м).`,
      year: "Время", arch: "Архитектор", addr: "Адрес", lock: "Жилой дом: доступ зависит от жильцов, коды замков не публикуются.", done: "Пройдено", onMap: "Показать на карте", dir: "Путь сюда (Google Карты)", sources: "Источники",
      start: "Старт и финиш: метро «Площадь Свободы»",
      credits: ["Карта: © участники OpenStreetMap, данные OpenFreeMap и OpenMapTiles. Линия маршрута и время ходьбы: пешеходный маршрутизатор Valhalla на данных OpenStreetMap, рассчитано один раз при подготовке страницы.", "Факты (адрес, год, архитектор) взяты из таблицы зданий в диссертации Т. Кутателадзе (2015; текст и фотографии диссертации принадлежат автору и здесь не воспроизводятся), из реестра культурного наследия Грузии и из указанных в карточках публикаций. Координаты домов — по реестру. Фото: Wikimedia Commons, автор и лицензия (CC BY или CC BY-SA) указаны под каждым снимком, ссылка ведёт на страницу файла; показаны уменьшенные копии. Сайт любительский, некоммерческий и не является официальным."],
    },
    en: {
      title: "Entrance Halls of Tbilisi: a walking route", home: "To the timeline map", share: "Copy link", copied: "Link copied", loading: "Loading the map…",
      intro: (p) => `A walking route "${p.title.en}" past old residential houses with entrance halls of the late 19th - early 20th century: <b>${p.stops.length} houses</b>, <b>${num(p.route.length_km)} km</b>, about <b>${p.route.walk_min} min</b> of walking without stops. The start and the finish are at the metro station Freedom Square. The order of the houses is chosen so that you walk as little as possible: the time was calculated along the streets of OpenStreetMap with the climbs taken into account, by trying all the orders. The years and the architects are taken from the table of buildings in the dissertation of T. Kutateladze (2015) and from the heritage register; where they differ, the card says so.`,
      tab: (t, n) => `${t} (${n})`, imgAlt: (n) => `Photo: ${n}`, locate: "Where am I: the nearest house", gpx: "Download GPX", busy: "Finding the position…", denied: "The position could not be found (allow the access to the location in the browser).", nogeo: "The browser cannot find the position.",
      nearest: (n, addr, d) => `The nearest house not marked yet: no. ${n}, ${addr}, about ${d} m in a straight line. Your position stays in your browser and is sent nowhere.`, alldone: "All the houses are marked. Your position stays in your browser and is sent nowhere.",
      legFirst: (m, d) => `${m} min on foot from the metro (${d} m)`, leg: (m, d) => `${m} min on foot from the previous house (${d} m)`, back: (m, d) => `The way back to the metro station Freedom Square from the last house: ${m} min (${d} m).`,
      year: "Time", arch: "Architect", addr: "Address", lock: "A residential building: access depends on the residents, door codes are not published.", done: "Visited", onMap: "Show on the map", dir: "Directions (Google Maps)", sources: "Sources",
      start: "Start and finish: the metro station Freedom Square",
      credits: ["Map: © OpenStreetMap contributors, data of OpenFreeMap and OpenMapTiles. The line of the route and the walking times: the pedestrian router Valhalla on OpenStreetMap data, calculated once when the page was prepared.", "The facts (address, year, architect) are taken from the table of buildings in the dissertation of T. Kutateladze (2015; the text and the photographs of the dissertation belong to the author and are not reproduced here), from the heritage register of Georgia and from the publications named in the cards. The coordinates of the houses are those of the register. Photos: Wikimedia Commons, the author and the licence (CC BY or CC BY-SA) are given under each photo, the link leads to the page of the file; the pictures are reduced copies. This is a hobby, non-commercial site and it is not official."],
    },
    ka: {
      title: "თბილისური სადარბაზოები: ფეხით მარშრუტი", home: "ისტორიულ რუკაზე", share: "ბმულის კოპირება", copied: "ბმული დაკოპირდა", loading: "რუკა იტვირთება…",
      intro: (p) => `ფეხით მარშრუტი „${p.title.ka}“ XIX საუკუნის ბოლოსა და XX საუკუნის დასაწყისის ძველი საცხოვრებელი სახლების გვერდით: <b>${p.stops.length} სახლი</b>, <b>${num(p.route.length_km)} კმ</b>, გაჩერებების გარეშე დაახლოებით <b>${p.route.walk_min} წუთი</b>. დასაწყისი და დასასრული მეტროსადგურ „თავისუფლების მოედანთან“. სახლების თანმიმდევრობა ისეა შერჩეული, რომ რაც შეიძლება ნაკლები გავიაროთ: დრო OpenStreetMap-ის ქუჩების გასწვრივ, აღმართების გათვალისწინებით, ყველა თანმიმდევრობის გადარჩევით გამოითვალა. წლები და არქიტექტორები აღებულია თ. ქუთათელაძის დისერტაციის (2015) შენობათა ცხრილიდან და კულტურული მემკვიდრეობის რეესტრიდან; სადაც ისინი განსხვავდება, ეს ბარათშია აღნიშნული.`,
      tab: (t, n) => `${t} (${n})`, imgAlt: (n) => `ფოტო: ${n}`, locate: "სად ვარ: უახლოესი სახლი", gpx: "GPX-ის ჩამოტვირთვა", busy: "მდებარეობა დგინდება…", denied: "მდებარეობის დადგენა ვერ მოხერხდა (ბრაუზერში მდებარეობაზე წვდომა დაუშვით).", nogeo: "ბრაუზერს მდებარეობის დადგენა არ შეუძლია.",
      nearest: (n, addr, d) => `უახლოესი ჯერ მოუნიშნავი სახლი: № ${n}, ${addr}, სწორი ხაზით დაახლოებით ${d} მ. თქვენი მდებარეობა თქვენს ბრაუზერში რჩება და არსად იგზავნება.`, alldone: "ყველა სახლი აღნიშნულია. თქვენი მდებარეობა ბრაუზერში რჩება და არსად იგზავნება.",
      legFirst: (m, d) => `${m} წთ ფეხით მეტროდან (${d} მ)`, leg: (m, d) => `${m} წთ ფეხით წინა სახლიდან (${d} მ)`, back: (m, d) => `დაბრუნება მეტროსადგურ „თავისუფლების მოედანზე“ ბოლო სახლიდან: ${m} წთ (${d} მ).`,
      year: "დრო", arch: "არქიტექტორი", addr: "მისამართი", lock: "საცხოვრებელი სახლი: შესვლა მობინადრეებზეა დამოკიდებული, კოდური საკეტების კოდები არ ქვეყნდება.", done: "გავლილია", onMap: "რუკაზე ჩვენება", dir: "გზა აქეთკენ (Google Maps)", sources: "წყაროები",
      start: "დასაწყისი და დასასრული: მეტროსადგური „თავისუფლების მოედანი“",
      credits: ["რუკა: © OpenStreetMap-ის მონაწილეები, OpenFreeMap-ისა და OpenMapTiles-ის მონაცემები. მარშრუტის ხაზი და სიარულის დრო: OpenStreetMap-ის მონაცემებზე დაფუძნებული ფეხით მოსიარულეთა მარშრუტიზატორი Valhalla, გვერდის მომზადებისას ერთხელ გამოითვალა.", "ფაქტები (მისამართი, წელი, არქიტექტორი) აღებულია თ. ქუთათელაძის დისერტაციის (2015) შენობათა ცხრილიდან (დისერტაციის ტექსტი და ფოტოები ავტორს ეკუთვნის და აქ არ მეორდება), საქართველოს კულტურული მემკვიდრეობის რეესტრიდან და ბარათებში დასახელებული პუბლიკაციებიდან. სახლების კოორდინატები რეესტრისაა. ფოტოები: Wikimedia Commons, ავტორი და ლიცენზია (CC BY ან CC BY-SA) მითითებულია თითოეული ფოტოს ქვეშ, ბმული ფაილის გვერდზე მიგიყვანთ; ნაჩვენებია შემცირებული ასლები. საიტი სამოყვარულო, არაკომერციულია და ოფიციალური არ არის."],
    },
  };
  const t = () => T[lang];

  let data = null, part = null, partIdx = 0, markers = {}, active = 0, map = null, meMarker = null;
  let done = new Set();
  try { JSON.parse(localStorage.getItem("entrDone") || "[]").forEach((n) => done.add(n)); } catch (e) {}
  const saveDone = () => { try { localStorage.setItem("entrDone", JSON.stringify([...done])); } catch (e) {} };
  const BASE = "https://tiles.openfreemap.org/styles/liberty";
  const BG_STYLE = { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": "#ece9df" } }] };

  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function link(href, text) { const a = el("a", "", text); a.href = href; a.target = "_blank"; a.rel = "noopener"; return a; }
  const L3 = (o) => (o && (o[lang] || o.en || o.ru || o.ka)) || "";

  function renderCards() {
    const L = t(), ol = $("cards");
    ol.textContent = "";
    for (const s of part.stops) {
      const li = el("li", "card" + (s.n === active ? " active" : "") + (done.has(s.n) ? " done" : ""));
      li.id = "s" + s.n;
      if (s.photos && s.photos.length) {                              // the photos of Wikimedia Commons: the author and the licence are under each of them
        const ph = el("div", "ph");
        for (const p of s.photos) {
          const fig = el("figure"), img = el("img");
          img.src = p.thumb; img.alt = L.imgAlt(L3(s.name) + ", " + L3(s.address)); img.loading = "lazy"; img.decoding = "async";
          img.width = p.w; img.height = p.h;
          const cap = el("figcaption");
          cap.appendChild(link(p.page, "© " + p.author + " · " + p.license));
          fig.appendChild(img); fig.appendChild(cap); ph.appendChild(fig);
        }
        li.appendChild(ph);
      }
      const body = el("div", "body");
      const h2 = el("h2");
      h2.appendChild(el("span", "badge", String(s.n)));
      h2.appendChild(el("span", "", L3(s.name)));
      body.appendChild(h2);
      body.appendChild(el("p", "addr", L3(s.address)));
      const meta = el("div", "meta");
      meta.appendChild(el("span", "", (s.n === 1 ? L.legFirst : L.leg)(num(s.leg_min), s.leg_m)));
      meta.appendChild(el("span", "", L.year + ": " + L3(s.year)));
      if (s.architect) meta.appendChild(el("span", "", L.arch + ": " + L3(s.architect)));
      body.appendChild(meta);
      body.appendChild(el("p", "", L3(s.desc)));
      body.appendChild(el("div", "lock", L.lock));
      const links = el("div", "links");
      const b = el("button", "", L.onMap); b.type = "button"; b.addEventListener("click", () => select(s.n, { fly: true }));
      links.appendChild(b);
      links.appendChild(link("https://www.google.com/maps/dir/?api=1&destination=" + s.lat + "," + s.lon + "&travelmode=walking", L.dir));
      const lab = el("label"), cb = el("input"); cb.type = "checkbox"; cb.checked = done.has(s.n);
      cb.addEventListener("change", () => { if (cb.checked) done.add(s.n); else done.delete(s.n); saveDone(); li.classList.toggle("done", cb.checked); if (markers[s.n]) markers[s.n].getElement().classList.toggle("done", cb.checked); });
      lab.appendChild(cb); lab.appendChild(document.createTextNode(L.done));
      links.appendChild(lab);
      body.appendChild(links);
      if (s.src && s.src.length) {
        const src = el("div", "notes");
        src.appendChild(document.createTextNode(L.sources + ": "));
        s.src.forEach((u, i) => { if (i) src.appendChild(document.createTextNode(" · ")); src.appendChild(u.url ? link(u.url, u.url.replace(/^https?:\/\//, "").split("/")[0]) : document.createTextNode(lang === "ru" ? "реестр культурного наследия" : lang === "ka" ? "კულტურული მემკვიდრეობის რეესტრი" : "heritage register")); });
        body.appendChild(src);
      }
      li.appendChild(body);
      ol.appendChild(li);
    }
    const back = el("li", "card"); back.appendChild(el("div", "body", ""));
    back.firstChild.appendChild(el("p", "", L.back(num(part.route.back_min), part.route.back_m)));
    ol.appendChild(back);
  }

  function renderText() {
    const L = t();
    document.documentElement.lang = lang;
    document.title = (part ? L3(part.title) + " · " : "") + L.title + " · Tbilisi through time";
    $("title").textContent = L.title;
    $("homeTxt").textContent = L.home;
    $("share").textContent = L.share;
    $("lang").value = lang;
    $("loadingTxt").textContent = L.loading;
    $("locate").textContent = "\u{1F4CD} " + L.locate;
    $("gpx").textContent = "⬇ " + L.gpx;
    if (data) {
      const tb = $("tabs"); tb.textContent = "";
      data.parts.forEach((p, i) => {
        const b = el("button", "", L.tab(L3(p.title), p.stops.length)); b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-selected", String(i === partIdx));
        b.addEventListener("click", () => showPart(i, { fit: true }));
        tb.appendChild(b);
      });
    }
    if (part) {
      const box = $("intro"); box.textContent = "";
      box.appendChild(el("h2", "it", L.title));
      const p = el("p"); p.innerHTML = L.intro(part); box.appendChild(p);       // our own text with <b> only
      box.appendChild(el("div", "rules", data.door_note[lang]));
    }
    const cr = $("credits"); cr.textContent = "";
    for (const p of L.credits) cr.appendChild(el("p", "", p));
    if (part) renderCards();
  }

  function select(n, opt) {
    opt = opt || {};
    active = n;
    for (const k of Object.keys(markers)) markers[k].getElement().classList.toggle("active", +k === n);
    document.querySelectorAll(".card").forEach((c) => c.classList.toggle("active", c.id === "s" + n));
    const s = part.stops.find((x) => x.n === n);
    if (!s) return;
    if (opt.fly && map) map.flyTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 17), duration: 900 });
    if (opt.scroll) { const c = $("s" + n); if (c) c.scrollIntoView({ behavior: "smooth", block: "start" }); }
    try { history.replaceState(null, "", "#" + n); } catch (e) {}
  }

  const routeFeature = () => ({ type: "Feature", geometry: { type: "LineString", coordinates: part.route.coords } });
  function addRoute() {
    if (!part) return;
    if (map.getSource("route")) { map.getSource("route").setData(routeFeature()); return; }
    map.addSource("route", { type: "geojson", data: routeFeature() });
    map.addLayer({ id: "route-casing", type: "line", source: "route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#ffffff", "line-width": 8, "line-opacity": 0.85 } });
    map.addLayer({ id: "route-line", type: "line", source: "route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#a4392a", "line-width": 4.5 } });
  }

  function addMarkers() {
    for (const k of Object.keys(markers)) markers[k].remove();
    markers = {};
    for (const s of part.stops) {
      const m = el("button", "mk" + (done.has(s.n) ? " done" : ""), String(s.n));
      m.type = "button"; m.title = L3(s.name) + ", " + L3(s.address);
      m.addEventListener("click", (ev) => { ev.stopPropagation(); select(s.n, { scroll: true }); });
      markers[s.n] = new maplibregl.Marker({ element: m }).setLngLat([s.lon, s.lat]).addTo(map);
      m.setAttribute("aria-label", s.n + ". " + L3(s.name) + ", " + L3(s.address));    // after the Marker: it sets its own label "Map marker"
    }
  }
  const partBounds = () => { const c = part.route.coords, b = new maplibregl.LngLatBounds(c[0], c[0]); for (const p of c) b.extend(p); return b; };
  function showPart(i, opt) {                                  // the page shows one part at a time: its route, its markers, its cards
    opt = opt || {};
    partIdx = i; part = data.parts[i]; active = 0;
    renderText();
    if (map) {
      if (map.isStyleLoaded() || map.getSource("route")) addRoute();
      addMarkers();
      if (opt.fit) map.fitBounds(partBounds(), { padding: 50, duration: 700 });
    }
    try { const u = new URL(location.href); if (i) u.searchParams.set("part", part.id); else u.searchParams.delete("part"); history.replaceState(null, "", u.pathname + u.search); } catch (e) {}
    $("list").scrollTop = 0;
  }

  function initMap() {
    map = new maplibregl.Map({ container: "map", style: BASE, bounds: partBounds(), fitBoundsOptions: { padding: 50 }, minZoom: 10, maxZoom: 19, attributionControl: true });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    let fell = false;
    map.on("error", (e) => {                                    // the basemap cannot be loaded: a plain background, the route and the markers still work
      if (fell || map.isStyleLoaded() || (e && e.sourceId)) return;
      fell = true; map.setStyle(BG_STYLE);
    });
    map.on("style.load", addRoute);
    map.on("load", () => { addRoute(); $("loading").hidden = true; });
    const st = el("div", "mk start", "S"); st.title = t().start;
    new maplibregl.Marker({ element: st }).setLngLat([part.start.lon, part.start.lat]).addTo(map);
    addMarkers();
  }

  // "where am I": the browser position (it stays in the browser) and the nearest house that is not marked yet
  function metersBetween(la1, lo1, la2, lo2) { return Math.hypot((la1 - la2) * 111320, (lo1 - lo2) * 111320 * Math.cos(la1 * Math.PI / 180)); }
  $("locate").addEventListener("click", () => {
    const w = $("where"), L = t();
    w.hidden = false;
    if (!navigator.geolocation) { w.textContent = L.nogeo; return; }
    w.textContent = L.busy;
    navigator.geolocation.getCurrentPosition((g) => {
      const la = g.coords.latitude, lo = g.coords.longitude;
      if (map) {
        if (!meMarker) meMarker = new maplibregl.Marker({ element: el("div", "mk me") });
        meMarker.setLngLat([lo, la]).addTo(map);
      }
      const rest = data.parts.flatMap((p) => p.stops).filter((s) => !done.has(s.n));
      if (!rest.length) { w.textContent = L.alldone; return; }
      let best = null;
      for (const s of rest) { const d = metersBetween(la, lo, s.lat, s.lon); if (!best || d < best.d) best = { s, d }; }
      const pi = data.parts.findIndex((p) => p.stops.some((x) => x.n === best.s.n));
      if (pi !== partIdx) showPart(pi);                          // the nearest house is in another part
      w.hidden = false;
      w.textContent = L.nearest(best.s.n, L3(best.s.address), Math.round(best.d / 10) * 10);
      select(best.s.n, { scroll: true });
      if (map) map.fitBounds(new maplibregl.LngLatBounds([lo, la], [best.s.lon, best.s.lat]), { padding: 90, maxZoom: 17, duration: 800 });
    }, () => { w.textContent = L.denied; }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 });
  });

  // GPX of the route and the stops, made in the browser (for an offline navigator)
  function xmlEsc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  $("gpx").addEventListener("click", () => {
    const rows = ['<?xml version="1.0" encoding="UTF-8"?>', '<gpx version="1.1" creator="Tbilisi through time" xmlns="http://www.topografix.com/GPX/1/1">',
      "<metadata><name>" + xmlEsc(t().title) + "</name></metadata>",
      '<wpt lat="' + part.start.lat + '" lon="' + part.start.lon + '"><name>' + xmlEsc(L3(part.start.name)) + "</name></wpt>"];
    for (const s of part.stops) rows.push('<wpt lat="' + s.lat + '" lon="' + s.lon + '"><name>' + s.n + ". " + xmlEsc(L3(s.address)) + "</name><desc>" + xmlEsc(L3(s.name)) + "</desc></wpt>");
    rows.push("<trk><name>" + xmlEsc(t().title) + "</name><trkseg>");
    for (const c of part.route.coords) rows.push('<trkpt lat="' + c[1] + '" lon="' + c[0] + '"/>');
    rows.push("</trkseg></trk></gpx>");
    const url = URL.createObjectURL(new Blob([rows.join("\n")], { type: "application/gpx+xml" }));
    const a = document.createElement("a"); a.href = url; a.download = "entrances-" + part.id + ".gpx"; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  });

  $("lang").addEventListener("change", (e) => {
    lang = e.target.value;
    try { localStorage.setItem("entrLang", lang); } catch (x) {}
    $("where").hidden = true;                      // its text was made in the old language
    renderText();
    if (part) for (const s of part.stops) if (markers[s.n]) markers[s.n].getElement().title = L3(s.name) + ", " + L3(s.address);
  });
  $("share").addEventListener("click", async () => {
    const url = location.href;
    try { await navigator.clipboard.writeText(url); $("share").textContent = t().copied; setTimeout(() => { $("share").textContent = t().share; }, 1800); }
    catch (e) { window.prompt(t().share, url); }
  });

  async function getJSON(u) { const r = await fetch(u); if (!r.ok) throw new Error(u + " " + r.status); return r.json(); }
  (async function main() {
    renderText();
    try { data = await getJSON("../data/entrances.json"); }
    catch (e) { $("loadingTxt").textContent = "Error: " + (e && e.message); return; }
    const h = parseInt((location.hash || "").slice(1), 10), pq = new URLSearchParams(location.search).get("part");
    let pi = data.parts.findIndex((p) => p.id === pq);
    if (h) { const hi = data.parts.findIndex((p) => p.stops.some((x) => x.n === h)); if (hi >= 0) pi = hi; }
    partIdx = pi >= 0 ? pi : 0; part = data.parts[partIdx];
    renderText();
    initMap();
    if (h && part.stops.some((x) => x.n === h)) setTimeout(() => select(h, { scroll: true, fly: true }), 400);
  })();
})();
