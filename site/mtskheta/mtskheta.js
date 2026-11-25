// The page "Mtskheta & Svetitskhoveli": walking excursion past unique monuments, including objects on the cathedral grounds.
// Data: ../data/mtskheta_tour.json. The position of the visitor ("where am I") is used only in the browser and is sent nowhere.
(function () {
  "use strict";
  const LANGS = ["ru", "en", "ka"];
  let lang = "en";
  try { const s = localStorage.getItem("mtsLang"); if (LANGS.includes(s)) lang = s; } catch (e) {}
  const q = new URLSearchParams(location.search).get("lang");
  if (LANGS.includes(q)) lang = q;
  const $ = (id) => document.getElementById(id);
  const num = (v) => String(v).replace(".", lang === "en" ? "." : ",");

  const T = {
    ru: {
      report: "Сообщить об ошибке",
      title: "Мцхета и Светицховели: экскурсия", home: "К карте с таймлайном", ariaPages: "Разделы сайта",
      navMap: "Карта во времени", navEntr: "Парадные Тбилиси", navRun: "Маршрут TRC City Run", navMus: "Музеи Тбилиси", navMtskheta: "Экскурсия по Мцхете", navLost: "Утраченный Тбилиси",
      share: "Скопировать ссылку", copied: "Ссылка скопирована", loading: "Загрузка карты…",
      intro: (p) => `Экскурсионный маршрут «${p.title.ru}»: <b>${p.stops.length} объектов</b>, около <b>${num(p.route.length_km)} км</b>, примерно <b>${p.route.walk_min} мин</b> ходьбы без учёта осмотра. Старт: ${p.start.name.ru}.`,
      tab: (t, n) => `${t} (${n})`, imgAlt: (n) => `Фото: ${n}`, locate: "Где я: ближайший объект", gpx: "Скачать GPX",
      busy: "Определяю положение…", denied: "Не удалось определить положение (разрешите доступ к геолокации в браузере).", nogeo: "Браузер не умеет определять положение.",
      nearest: (n, addr, d) => `Ближайший не отмеченный объект: № ${n}, ${addr}, примерно ${d} м по прямой. Положение остаётся в вашем браузере и никуда не отправляется.`,
      alldone: "Все объекты отмечены. Ваше положение остаётся в браузере и никуда не отправляется.",
      legFirst: (m, d) => `${m} мин пешком от старта (${d} м)`, leg: (m, d) => `${m} мин пешком от предыдущего объекта (${d} м)`,
      year: "Дата / эпоха", addr: "Место",
      kinds: {
        cathedral: "Собор", monastery: "Монастырь", church: "Церковь", shrine: "Святыня",
        necropolis: "Некрополь / усыпальница", chapel: "Часовня", palace: "Дворец",
        fortress: "Крепость", bridge: "Мост", bath: "Античная баня", temple: "Храм", cellar: "Винный погреб (марани)"
      },
      done: "Осмотрено", onMap: "Показать на карте", dir: "Путь сюда (Google Карты)", sources: "Источники",
      regSrc: "Реестр культурного наследия Грузии", start: (p) => `Старт: ${p.start.name.ru}`,
      credits: [
        "Карта: © участники OpenStreetMap, данные OpenFreeMap и OpenMapTiles.",
        "Факты, даты и источники основаны на реестре культурного наследия Грузии, Православной энциклопедии и материалах Википедии. Сайт любительский, некоммерческий и не является официальным."
      ]
    },
    en: {
      report: "Report a problem",
      title: "Mtskheta & Svetitskhoveli: excursion", home: "To the timeline map", ariaPages: "Site sections",
      navMap: "Timeline map", navEntr: "Entrance Halls of Tbilisi", navRun: "TRC City Run route", navMus: "Museums of Tbilisi", navMtskheta: "Mtskheta Excursion", navLost: "Lost Tbilisi",
      share: "Copy link", copied: "Link copied", loading: "Loading the map…",
      intro: (p) => `Excursion route "${p.title.en}": <b>${p.stops.length} landmarks</b>, about <b>${num(p.route.length_km)} km</b>, roughly <b>${p.route.walk_min} min</b> of walking excluding visits. Starts at ${p.start.name.en}.`,
      tab: (t, n) => `${t} (${n})`, imgAlt: (n) => `Photo: ${n}`, locate: "Where am I: nearest site", gpx: "Download GPX",
      busy: "Finding the position…", denied: "The position could not be found (allow location access in the browser).", nogeo: "The browser cannot find the position.",
      nearest: (n, addr, d) => `The nearest unvisited site: no. ${n}, ${addr}, about ${d} m in a straight line. Your position stays in your browser and is sent nowhere.`,
      alldone: "All sites are marked. Your position stays in your browser and is sent nowhere.",
      legFirst: (m, d) => `${m} min on foot from start (${d} m)`, leg: (m, d) => `${m} min on foot from previous site (${d} m)`,
      year: "Date / era", addr: "Location",
      kinds: {
        cathedral: "Cathedral", monastery: "Monastery", church: "Church", shrine: "Shrine",
        necropolis: "Necropolis / royal tombs", chapel: "Chapel", palace: "Palace",
        fortress: "Fortress", bridge: "Bridge", bath: "Roman bathhouse", temple: "Temple", cellar: "Wine cellar (marani)"
      },
      done: "Visited", onMap: "Show on the map", dir: "Directions (Google Maps)", sources: "Sources",
      regSrc: "Heritage register of Georgia", start: (p) => `Start: ${p.start.name.en}`,
      credits: [
        "Map: © OpenStreetMap contributors, data of OpenFreeMap and OpenMapTiles.",
        "Facts, dates and sources are based on the Georgian heritage register, Orthodox Encyclopedia and Wikipedia. This is a hobby, non-commercial site and it is not official."
      ]
    },
    ka: {
      report: "შეცდომის შეტყობინება",
      title: "მცხეთა და სვეტიცხოველი: ექსკურსია", home: "ისტორიულ რუკაზე", ariaPages: "საიტის განყოფილებები",
      navMap: "რუკა დროში", navEntr: "თბილისური სადარბაზოები", navRun: "TRC City Run-ის მარშრუტი", navMus: "თბილისის მუზეუმები", navMtskheta: "მცხეთის ექსკურსია", navLost: "დაკარგული თბილისი",
      share: "ბმულის კოპირება", copied: "ბმული დაკოპირდა", loading: "რუკა იტვირთება…",
      intro: (p) => `საექსკურსიო მარშრუტი „${p.title.ka}“: <b>${p.stops.length} ძეგლი</b>, დაახლოებით <b>${num(p.route.length_km)} კმ</b>, სიარულით <b>${p.route.walk_min} წთ</b>. სტარტი: ${p.start.name.ka}.`,
      tab: (t, n) => `${t} (${n})`, imgAlt: (n) => `ფოტო: ${n}`, locate: "სად ვარ: უახლოესი ძეგლი", gpx: "GPX-ის ჩამოტვირთვა",
      busy: "მდებარეობა დგინდება…", denied: "მდებარეობის დადგენა ვერ მოხერხდა (ბრაუზერში მდებარეობაზე წვდომა დაუშვით).", nogeo: "ბრაუზერს მდებარეობის დადგენა არ შეუძლია.",
      nearest: (n, addr, d) => `უახლოესი მოუნიშნავი ძეგლი: № ${n}, ${addr}, სწორი ხაზით დაახლოებით ${d} მ. თქვენი მდებარეობა ბრაუზერში რჩება და არსად იგზავნება.`,
      alldone: "ყველა ძეგლი აღნიშნულია. თქვენი მდებარეობა ბრაუზერში რჩება და არსად იგზავნება.",
      legFirst: (m, d) => `${m} წთ ფეხით სტარტიდან (${d} მ)`, leg: (m, d) => `${m} წთ ფეხით წინა ძეგლიდან (${d} მ)`,
      year: "თარიღი / ეპოქა", addr: "მდებარეობა",
      kinds: {
        cathedral: "ტაძარი", monastery: "მონასტერი", church: "ეკლესია", shrine: "სიწმინდე",
        necropolis: "სამაროვანი / საძვალე", chapel: "სამლოცველო", palace: "სასახლე",
        fortress: "ციხესიმაგრე", bridge: "ხიდი", bath: "ანტიკური აბანო", temple: "ტაძარი", cellar: "მარანი"
      },
      done: "ნანახია", onMap: "რუკაზე ჩვენება", dir: "გზა აქეთკენ (Google Maps)", sources: "წყაროები",
      regSrc: "საქართველოს კულტურული მემკვიდრეობის რეესტრი", start: (p) => `სტარტი: ${p.start.name.ka}`,
      credits: [
        "რუკა: © OpenStreetMap-ის მონაწილეები, OpenFreeMap-ისა და OpenMapTiles-ის მონაცემები.",
        "ფაქტები, თარიღები და წყაროები ეფუძნება საქართველოს კულტურული მემკვიდრეობის რეესტრს, მართლმადიდებლურ ენციკლოპედიასა და ვიკიპედიას. საიტი სამოყვარულო და არაკომერციულია."
      ]
    }
  };
  const t = () => T[lang];

  let data = null, photosDb = {}, part = null, partIdx = 0, markers = {}, startMarker = null, active = 0, map = null, meMarker = null;
  let done = new Set();
  try { JSON.parse(localStorage.getItem("mtsDone") || "[]").forEach((id) => done.add(id)); } catch (e) {}
  const saveDone = () => { try { localStorage.setItem("mtsDone", JSON.stringify([...done])); } catch (e) {} };
  const BASE = "https://tiles.openfreemap.org/styles/liberty";
  const BG_STYLE = { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": "#ece9df" } }] };

  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function link(href, text) { const a = el("a", "", text); a.href = href; a.target = "_blank"; a.rel = "noopener"; return a; }
  const L3 = (o) => (o && (o[lang] || o.en || o.ru || o.ka)) || "";

  function renderCards() {
    const L = t(), ol = $("cards");
    ol.textContent = "";
    for (const s of part.stops) {
      const li = el("li", "card" + (s.n === active ? " active" : "") + (done.has(s.id) ? " done" : ""));
      li.id = "s" + s.n;
      if (s.ph) {
        const files = s.ph.split("|").map((x) => x.trim()).filter(Boolean).slice(0, 2);
        if (files.length) {
          const ph = el("div", "ph");
          for (const raw of files) {
            const p = photosDb[raw];
            const fig = el("figure"), img = el("img");
            const clean = raw.replace(/^File:/i, "");
            img.src = (p && p.thumb) ? p.thumb : "https://commons.wikimedia.org/wiki/Special:FilePath/" + encodeURIComponent(clean) + "?width=640";
            img.alt = L.imgAlt(L3(s.name)); img.loading = "lazy"; img.decoding = "async";
            if (p && p.w && p.h) { img.width = p.w; img.height = p.h; }
            fig.appendChild(img);
            if (p && p.page) {
              const cap = el("figcaption");
              cap.appendChild(link(p.page, (p.author ? "© " + p.author + " · " : "") + (p.license || "Wikimedia Commons")));
              fig.appendChild(cap);
            }
            ph.appendChild(fig);
          }
          li.appendChild(ph);
        }
      }
      const body = el("div", "body");
      const h2 = el("h2");
      h2.appendChild(el("span", "badge", String(s.n)));
      h2.appendChild(el("span", "", L3(s.name)));
      body.appendChild(h2);
      body.appendChild(el("p", "addr", L3(s.address)));
      const meta = el("div", "meta");
      meta.appendChild(el("span", "", L.kinds[s.kind] || s.kind));
      meta.appendChild(el("span", "", (s.n === 1 ? L.legFirst : L.leg)(num(s.leg_min), s.leg_m)));
      meta.appendChild(el("span", "", L.year + ": " + L3(s.year)));
      body.appendChild(meta);
      body.appendChild(el("p", "", L3(s.desc)));
      const links = el("div", "links");
      const b = el("button", "", L.onMap); b.type = "button"; b.addEventListener("click", () => select(s.n, { fly: true }));
      links.appendChild(b);
      links.appendChild(link("https://www.google.com/maps/dir/?api=1&destination=" + s.lat + "," + s.lon + "&travelmode=walking", L.dir));
      const lab = el("label"), cb = el("input"); cb.type = "checkbox"; cb.checked = done.has(s.id);
      cb.addEventListener("change", () => {
        if (cb.checked) done.add(s.id); else done.delete(s.id);
        saveDone();
        li.classList.toggle("done", cb.checked);
        if (markers[s.n]) markers[s.n].getElement().classList.toggle("done", cb.checked);
      });
      lab.appendChild(cb); lab.appendChild(document.createTextNode(L.done));
      links.appendChild(lab);
      body.appendChild(links);
      const src = el("div", "src", L.sources + ": ");
      if (s.src && s.src.length) {
        s.src.forEach((u, i) => {
          if (i) src.appendChild(document.createTextNode(" · "));
          src.appendChild(link(u, decodeURIComponent(u.replace("https://", "")).slice(0, 55)));
        });
      } else {
        src.appendChild(document.createTextNode(L.regSrc + (s.rid ? " #" + s.rid : "")));
      }
      body.appendChild(src);
      li.appendChild(body);
      ol.appendChild(li);
    }
  }

  function renderTabs() {
    const box = $("tabs");
    box.textContent = "";
    data.parts.forEach((p, i) => {
      const b = el("button", "", t().tab(L3(p.title), p.stops.length));
      b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-selected", i === partIdx ? "true" : "false");
      b.addEventListener("click", () => showPart(i, { fit: true }));
      box.appendChild(b);
    });
  }

  function renderText() {
    const L = t();
    document.documentElement.lang = lang;
    document.title = L.title;
    $("homeTxt").textContent = L.home;
    $("home").href = "../?lang=" + lang;
    $("title").textContent = L.title;
    const sel = $("pagesSel");
    if (sel) {
      sel.setAttribute("aria-label", L.ariaPages);
      sel.textContent = "";
      for (const [v, k] of [["../", "navMap"], ["../entrances/", "navEntr"], ["../run/", "navRun"], ["../museums/", "navMus"], ["../mtskheta/", "navMtskheta"], ["../lost/", "navLost"]]) {
        const o = document.createElement("option"); o.value = v; o.textContent = L[k]; sel.appendChild(o);
      }
      sel.value = "../mtskheta/";
    }
    $("share").textContent = L.share;
    $("report").textContent = L.report;
    $("report").href = "../?report=mtskheta&lang=" + lang;
    $("loadingTxt").textContent = L.loading;
    $("locate").textContent = L.locate;
    $("gpx").textContent = L.gpx;
    $("lang").value = lang;
    if (part) {
      renderTabs();
      $("intro").innerHTML = L.intro(part);
      renderCards();
    }
    const cr = $("credits"); cr.textContent = "";
    for (const p of L.credits) cr.appendChild(el("p", "", p));
  }

  function select(n, opt) {
    opt = opt || {};
    active = n;
    for (const k of Object.keys(markers)) markers[k].getElement().classList.toggle("active", +k === n);
    document.querySelectorAll(".card").forEach((c) => c.classList.toggle("active", c.id === "s" + n));
    const s = part.stops.find((x) => x.n === n);
    if (!s) return;
    if (opt.fly && map) map.flyTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 16.5), duration: 800 });
    if (opt.scroll) { const c = $("s" + n); if (c) c.scrollIntoView({ behavior: "smooth", block: "start" }); }
    try { history.replaceState(null, "", "#" + n); } catch (e) {}
  }

  const routeFeature = () => ({ type: "Feature", geometry: { type: "LineString", coordinates: part.route.coords } });
  function addRoute() {
    if (!part) return;
    if (map.getSource("route")) { map.getSource("route").setData(routeFeature()); return; }
    map.addSource("route", { type: "geojson", data: routeFeature() });
    map.addLayer({ id: "route-casing", type: "line", source: "route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#ffffff", "line-width": 7, "line-opacity": 0.85 } });
    map.addLayer({ id: "route-line", type: "line", source: "route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#0b7285", "line-width": 4, "line-dasharray": [2, 1.5] } });
  }

  function addMarkers() {
    for (const k of Object.keys(markers)) markers[k].remove();
    markers = {};
    if (startMarker) startMarker.remove();
    const st = el("div", "mk start", "S"); st.title = t().start(part);
    startMarker = new maplibregl.Marker({ element: st }).setLngLat([part.start.lon, part.start.lat]).addTo(map);
    for (const s of part.stops) {
      const m = el("button", "mk" + (done.has(s.id) ? " done" : ""), String(s.n));
      m.type = "button"; m.title = L3(s.name) + ", " + L3(s.address);
      m.addEventListener("click", (ev) => { ev.stopPropagation(); select(s.n, { scroll: true }); });
      markers[s.n] = new maplibregl.Marker({ element: m }).setLngLat([s.lon, s.lat]).addTo(map);
      m.setAttribute("aria-label", s.n + ". " + L3(s.name));
    }
  }

  const partBounds = () => { const c = part.route.coords, b = new maplibregl.LngLatBounds(c[0], c[0]); for (const p of c) b.extend(p); return b; };
  function showPart(i, opt) {
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
    map.on("error", (e) => { if (fell || map.isStyleLoaded() || (e && e.sourceId)) return; fell = true; map.setStyle(BG_STYLE); });
    map.on("style.load", addRoute);
    map.on("load", () => { addRoute(); $("loading").hidden = true; });
    addMarkers();
  }

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
      const rest = data.parts.flatMap((p) => p.stops).filter((s) => !done.has(s.id));
      if (!rest.length) { w.textContent = L.alldone; return; }
      let best = null;
      for (const s of rest) { const d = metersBetween(la, lo, s.lat, s.lon); if (!best || d < best.d) best = { s, d }; }
      const pi = data.parts.findIndex((p) => p.stops.some((x) => x.id === best.s.id));
      if (pi !== partIdx) showPart(pi);
      w.hidden = false;
      w.textContent = L.nearest(best.s.n, L3(best.s.address), Math.round(best.d / 10) * 10);
      select(best.s.n, { scroll: true });
      if (map) map.fitBounds(new maplibregl.LngLatBounds([lo, la], [best.s.lon, best.s.lat]), { padding: 90, maxZoom: 17, duration: 800 });
    }, () => { w.textContent = L.denied; }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 });
  });

  function xmlEsc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  $("gpx").addEventListener("click", () => {
    const rows = ['<?xml version="1.0" encoding="UTF-8"?>', '<gpx version="1.1" creator="Tbilisi through time" xmlns="http://www.topografix.com/GPX/1/1">',
      "<metadata><name>" + xmlEsc(t().title) + "</name></metadata>",
      '<wpt lat="' + part.start.lat + '" lon="' + part.start.lon + '"><name>' + xmlEsc(L3(part.start.name)) + "</name></wpt>"];
    for (const s of part.stops) rows.push('<wpt lat="' + s.lat + '" lon="' + s.lon + '"><name>' + s.n + ". " + xmlEsc(L3(s.name)) + "</name><desc>" + xmlEsc(L3(s.address)) + "</desc></wpt>");
    rows.push("<trk><name>" + xmlEsc(t().title) + "</name><trkseg>");
    for (const c of part.route.coords) rows.push('<trkpt lat="' + c[1] + '" lon="' + c[0] + '"/>');
    rows.push("</trkseg></trk></gpx>");
    const url = URL.createObjectURL(new Blob([rows.join("\n")], { type: "application/gpx+xml" }));
    const a = document.createElement("a"); a.href = url; a.download = "mtskheta-" + part.id + ".gpx"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  $("lang").addEventListener("change", (e) => {
    lang = e.target.value;
    try { localStorage.setItem("mtsLang", lang); } catch (err) {}
    try { const u = new URL(location.href); u.searchParams.set("lang", lang); history.replaceState(null, "", u.pathname + u.search); } catch (err) {}
    renderText();
    addMarkers();
  });
  if ($("pagesSel")) $("pagesSel").addEventListener("change", (e) => {
    if (e.target.value && e.target.value !== "../mtskheta/") location.href = e.target.value + "?lang=" + lang;
  });
  $("share").addEventListener("click", async () => {
    const b = $("share"), u = new URL(location.href); u.searchParams.set("lang", lang);
    try { await navigator.clipboard.writeText(u.toString()); } catch (e) {}
    b.textContent = t().copied; setTimeout(() => { b.textContent = t().share; }, 1800);
  });

  renderText();
  Promise.all([
    fetch("../data/mtskheta_tour.json").then((r) => r.json()),
    fetch("../data/photos.json").then((r) => r.json()).catch(() => ({}))
  ]).then(([d, ph]) => {
    data = d; photosDb = ph || {};
    const pq = new URLSearchParams(location.search).get("part");
    const pi = pq ? data.parts.findIndex((p) => p.id === pq) : 0;
    showPart(pi >= 0 ? pi : 0);
    initMap();
    const h = +location.hash.slice(1);
    if (h) setTimeout(() => select(h, { fly: true, scroll: true }), 400);
  });
})();
