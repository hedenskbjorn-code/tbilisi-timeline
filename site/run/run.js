// The page of the route "TRC City Run 2026": the route on a small map and the sights along it, with descriptions and photos.
// Data: ../data/run_trc2026.json (route and sights, see tools/build_run_route.py) and ../data/run_details.json (descriptions, photos, sources, see tools/build_run_details.py).
(function () {
  "use strict";
  const LANGS = ["ru", "en", "ka"];
  let lang = "en";
  const nav = (navigator.language || "en").slice(0, 2);
  if (LANGS.includes(nav)) lang = nav;
  try { const s = localStorage.getItem("lang"); if (LANGS.includes(s)) lang = s; } catch (e) {}
  const q = new URLSearchParams(location.search).get("lang");
  if (LANGS.includes(q)) lang = q;
  const $ = (id) => document.getElementById(id);
  const OG = new URLSearchParams(location.search).get("og") === "1";          // ?og=1: only the map and a banner, for the preview picture of the page (img/og-run.jpg)
  if (OG) document.body.classList.add("og");
  const num = (v) => String(v).replace(".", lang === "en" ? "." : ",");

  const T = {
    ru: {
      title: "TRC City Run 2026: что увидеть по пути", home: "К карте с таймлайном", share: "Скопировать ссылку", copied: "Ссылка скопирована", loading: "Загрузка карты…",
      intro: (r, n) => `Маршрут пробежки Tbilisi Running Club: <b>${num(r.length_km)} км</b>, высоты ${r.ele_min}–${r.ele_max} м, <b>${n}</b> достопримечательностей по порядку вдоль трассы. В список входят объекты не дальше 150 м от трассы; расстояние считается от точки объекта до линии трассы и не означает, что объект виден с неё. Описания взяты из вводных абзацев статей Википедии (ссылка и лицензия под каждым описанием); у объектов без статьи описания нет.`,
      km: (v) => `${num(v)} км от старта`, dist: (d) => `${d} м от трассы`, reg: (y) => `дата по реестру ≈ ${y}`, noDesc: "Описание пока не добавлено.", textFrom: "Текст:", wiki: "Википедия", onMap: "Показать на карте", sources: "Источники",
      factYear: "Время", factArch: "Автор проекта", factType: "Тип и стиль", factAddr: "Адрес", notes: "Примечание", start: "Старт и финиш",
      credits: ["Карта: © участники OpenStreetMap, данные OpenFreeMap и OpenMapTiles. Геометрия трассы: Strava-маршрут «TRC City Run 2026» (сохранена только линия).", "Фото: Wikimedia Commons, автор и лицензия указаны на каждом снимке (ссылка ведёт на страницу файла). Тексты описаний: вводные абзацы статей Википедии (CC BY-SA 4.0), ссылка на статью под каждым описанием. Логотип: Tbilisi Running Club. Сайт любительский, некоммерческий и не является официальным."],
      imgAlt: (n) => `Фото: ${n}`, license: "лицензия", ogLine: (r, n) => `что увидеть по пути · ${num(r.length_km)} км · ${n} объектов`,
    },
    en: {
      title: "TRC City Run 2026: what to see on the way", home: "To the timeline map", share: "Copy link", copied: "Link copied", loading: "Loading the map…",
      intro: (r, n) => `The route of a run of the Tbilisi Running Club: <b>${num(r.length_km)} km</b>, elevation ${r.ele_min}-${r.ele_max} m, <b>${n}</b> sights in order along the track. The list holds the objects within 150 m of the track; the distance is from the point of the object to the line of the track and does not mean that the object can be seen from it. The descriptions are taken from the introductions of the Wikipedia articles (the link and the licence are under each description); an object without an article has no description.`,
      km: (v) => `${num(v)} km from the start`, dist: (d) => `${d} m from the track`, reg: (y) => `date in the register ≈ ${y}`, noDesc: "No description yet.", textFrom: "Text:", wiki: "Wikipedia", onMap: "Show on the map", sources: "Sources",
      factYear: "Time", factArch: "Architect / author", factType: "Type and style", factAddr: "Address", notes: "Note", start: "Start and finish",
      credits: ["Map: © OpenStreetMap contributors, data of OpenFreeMap and OpenMapTiles. Geometry of the track: the Strava route \"TRC City Run 2026\" (only the line is kept).", "Photos: Wikimedia Commons, the author and the licence are given on each photo (the link leads to the page of the file). Texts of the descriptions: the introductions of the Wikipedia articles (CC BY-SA 4.0), the link to the article is under each description. Logo: Tbilisi Running Club. This is a hobby, non-commercial site and it is not official."],
      imgAlt: (n) => `Photo: ${n}`, license: "licence", ogLine: (r, n) => `what to see on the way · ${num(r.length_km)} km · ${n} sights`,
    },
    ka: {
      title: "TRC City Run 2026: რა ჩანს გზაზე", home: "ისტორიულ რუკაზე", share: "ბმულის კოპირება", copied: "ბმული დაკოპირდა", loading: "რუკა იტვირთება…",
      intro: (r, n) => `Tbilisi Running Club-ის სირბილის მარშრუტი: <b>${num(r.length_km)} კმ</b>, სიმაღლე ${r.ele_min}–${r.ele_max} მ, <b>${n}</b> ღირსშესანიშნაობა ტრასის გასწვრივ თანმიმდევრობით. სიაში შედის ობიექტები ტრასიდან 150 მ-ის ფარგლებში; მანძილი ობიექტის წერტილიდან ტრასის ხაზამდეა და არ ნიშნავს, რომ ობიექტი ტრასიდან ჩანს. აღწერები აღებულია ვიკიპედიის სტატიების შესავლიდან (ბმული და ლიცენზია თითოეული აღწერის ქვეშაა); ობიექტს, რომელსაც სტატია არა აქვს, აღწერა არ აქვს.`,
      km: (v) => `${num(v)} კმ სტარტიდან`, dist: (d) => `${d} მ ტრასიდან`, reg: (y) => `თარიღი რეესტრში ≈ ${y}`, noDesc: "აღწერა ჯერ არ არის დამატებული.", textFrom: "ტექსტი:", wiki: "ვიკიპედია", onMap: "რუკაზე ჩვენება", sources: "წყაროები",
      factYear: "დრო", factArch: "პროექტის ავტორი", factType: "ტიპი და სტილი", factAddr: "მისამართი", notes: "შენიშვნა", start: "სტარტი და ფინიში",
      credits: ["რუკა: © OpenStreetMap-ის მონაწილეები, OpenFreeMap-ისა და OpenMapTiles-ის მონაცემები. ტრასის გეომეტრია: Strava-ს მარშრუტი „TRC City Run 2026“ (შენახულია მხოლოდ ხაზი).", "ფოტოები: Wikimedia Commons, ავტორი და ლიცენზია მითითებულია თითოეულ ფოტოზე (ბმული ფაილის გვერდზე მიგიყვანთ). აღწერების ტექსტები: ვიკიპედიის სტატიების შესავალი (CC BY-SA 4.0), სტატიის ბმული თითოეული აღწერის ქვეშაა. ლოგო: Tbilisi Running Club. საიტი სამოყვარულო, არაკომერციულია და ოფიციალური არ არის."],
      imgAlt: (n) => `ფოტო: ${n}`, license: "ლიცენზია", ogLine: (r, n) => `რა ჩანს გზაზე · ${num(r.length_km)} კმ · ${n} ღირსშესანიშნაობა`,
    },
  };
  const t = () => T[lang];

  let route = null, sights = [], details = {}, markers = {}, active = 0, map = null;
  const BASE = "https://tiles.openfreemap.org/styles/liberty";
  const BG_STYLE = { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": "#ece9df" } }] };

  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function link(href, text) { const a = el("a", "", text); a.href = href; a.target = "_blank"; a.rel = "noopener"; return a; }
  function wikiHref(s, d) {
    const w = Object.assign({}, s.wp, (d && d.wp) || {});
    const l = w[lang] ? lang : w.en ? "en" : w.ru ? "ru" : w.ka ? "ka" : null;
    return l ? "https://" + l + ".wikipedia.org/wiki/" + encodeURIComponent(String(w[l]).replace(/ /g, "_")) : null;
  }
  const clean = (s) => String(s || "").replace(/<[^>]+>/g, "").trim();

  function renderCards() {
    const L = t(), ol = $("cards");
    ol.textContent = "";
    for (const s of sights) {
      const d = details[s.n] || {};
      const li = el("li", "card" + (s.n === active ? " active" : ""));
      li.id = "s" + s.n;
      const photos = (d.photos || []).slice(0, 2);
      if (photos.length) {
        const ph = el("div", "ph");
        for (const p of photos) {
          const fig = el("figure"), img = el("img");
          img.src = p.thumb; img.alt = L.imgAlt(s.name[lang] || s.name.en); img.loading = "lazy"; img.decoding = "async";
          if (p.w && p.h) { img.width = p.w; img.height = p.h; }
          const cap = el("figcaption");
          cap.appendChild(link(p.page, "© " + clean(p.author || "Wikimedia Commons") + " · " + (p.license || "")));
          fig.appendChild(img); fig.appendChild(cap); ph.appendChild(fig);
        }
        li.appendChild(ph);
      }
      const body = el("div", "body");
      const h2 = el("h2");
      h2.appendChild(el("span", "badge", String(s.n)));
      h2.appendChild(el("span", "", s.name[lang] || s.name.en));
      body.appendChild(h2);
      const meta = el("div", "meta");
      meta.appendChild(el("span", "", L.km(s.km)));
      meta.appendChild(el("span", "", L.dist(s.d)));
      if (s.year) meta.appendChild(el("span", "", L.reg(s.year)));
      body.appendChild(meta);
      const text = d.desc && (d.desc[lang] || d.desc.en || d.desc.ru || d.desc.ka);
      body.appendChild(text ? el("p", "", text) : el("p", "nodesc", L.noDesc));
      if (text) {                                                    // the text is that of Wikipedia (CC BY-SA 4.0): the article and the licence are named
        const ul = d.desc[lang] ? lang : d.desc.en ? "en" : d.desc.ru ? "ru" : "ka";
        const su = d.src_by_lang && d.src_by_lang[ul];
        const cr = el("div", "notes");
        cr.appendChild(document.createTextNode(L.textFrom + " "));
        cr.appendChild(su ? link(su, L.wiki + " (" + ul.toUpperCase() + ")") : document.createTextNode(L.wiki + " (" + ul.toUpperCase() + ")"));
        cr.appendChild(document.createTextNode(", CC BY-SA 4.0"));
        body.appendChild(cr);
      }
      const f = d.facts || {};
      const facts = [[L.factYear, f.year], [L.factArch, f.architect], [L.factType, f.style_or_type], [L.factAddr, f.address]].filter((x) => x[1] && x[1] !== "null");
      if (facts.length) body.appendChild(el("div", "facts", facts.map((x) => x[0] + ": " + x[1]).join(" · ")));
      const links = el("div", "links");
      const wh = wikiHref(s, d);
      if (wh) links.appendChild(link(wh, L.wiki));
      const b = el("button", "", L.onMap);
      b.type = "button";
      b.addEventListener("click", () => select(s.n, { fly: true }));
      links.appendChild(b);
      body.appendChild(links);
      if (d.notes_public && d.notes_public[lang]) body.appendChild(el("div", "notes", L.notes + ": " + d.notes_public[lang]));
      if (d.sources && d.sources.length) {
        const src = el("div", "notes");
        src.appendChild(document.createTextNode(L.sources + ": "));
        d.sources.slice(0, 4).forEach((u, i) => { if (i) src.appendChild(document.createTextNode(" · ")); src.appendChild(link(u, u.replace(/^https?:\/\//, "").split("/")[0])); });
        body.appendChild(src);
      }
      li.appendChild(body);
      ol.appendChild(li);
    }
  }

  function renderText() {
    const L = t();
    document.documentElement.lang = lang;
    document.title = L.title + " · Tbilisi through time";
    $("title").textContent = L.title;
    $("homeTxt").textContent = L.home;
    $("share").textContent = L.share;
    $("lang").value = lang;
    $("loadingTxt").textContent = L.loading;
    if (route) $("intro").innerHTML = '<h2 class="it">' + L.title + "</h2>" + L.intro(route, sights.length);
    const cr = $("credits");
    cr.textContent = "";
    for (const p of L.credits) cr.appendChild(el("p", "", p));
    renderCards();
  }

  function select(n, opt) {
    opt = opt || {};
    active = n;
    for (const k of Object.keys(markers)) markers[k].getElement().classList.toggle("active", +k === n);
    document.querySelectorAll(".card").forEach((c) => c.classList.toggle("active", c.id === "s" + n));
    const s = sights.find((x) => x.n === n);
    if (!s) return;
    if (opt.fly && map) map.flyTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 16), duration: 900 });
    if (opt.scroll) { const c = $("s" + n); if (c) c.scrollIntoView({ behavior: "smooth", block: "start" }); }
    try { history.replaceState(null, "", "#" + n); } catch (e) {}
  }

  function addRoute() {
    if (!route || map.getSource("route")) return;
    map.addSource("route", { type: "geojson", data: { type: "Feature", geometry: { type: "LineString", coordinates: route.coords } } });
    map.addLayer({ id: "route-casing", type: "line", source: "route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#ffffff", "line-width": 8, "line-opacity": 0.85 } });
    map.addLayer({ id: "route-line", type: "line", source: "route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#d9480f", "line-width": 4.5 } });
  }

  function initMap() {
    const c = route.coords;
    const b = new maplibregl.LngLatBounds(c[0], c[0]);
    for (const p of c) b.extend(p);
    map = new maplibregl.Map({ container: "map", style: BASE, bounds: b, fitBoundsOptions: { padding: OG ? { top: 30, left: 30, right: 30, bottom: 150 } : 40 }, minZoom: 10, maxZoom: 19, attributionControl: true });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    let fell = false;
    map.on("error", (e) => {                           // the basemap cannot be loaded: a plain background, the route and the markers still work
      if (fell || map.isStyleLoaded() || (e && e.sourceId)) return;
      fell = true;
      map.setStyle(BG_STYLE);
    });
    map.on("style.load", addRoute);
    map.on("load", () => { addRoute(); $("loading").hidden = true; });
    const start = el("div", "mk start", "S");
    start.title = t().start;
    new maplibregl.Marker({ element: start }).setLngLat(c[0]).addTo(map);
    for (const s of sights) {
      const m = el("div", "mk", String(s.n));
      m.title = s.name[lang] || s.name.en;
      m.addEventListener("click", (ev) => { ev.stopPropagation(); select(s.n, { scroll: true }); });
      markers[s.n] = new maplibregl.Marker({ element: m }).setLngLat([s.lon, s.lat]).addTo(map);
    }
  }

  $("lang").addEventListener("change", (e) => {
    lang = e.target.value;
    try { localStorage.setItem("lang", lang); } catch (x) {}
    renderText();
    for (const s of sights) if (markers[s.n]) markers[s.n].getElement().title = s.name[lang] || s.name.en;
  });
  $("share").addEventListener("click", async () => {
    const url = location.href;
    try { await navigator.clipboard.writeText(url); $("share").textContent = t().copied; setTimeout(() => { $("share").textContent = t().share; }, 1800); }
    catch (e) { window.prompt(t().share, url); }
  });

  async function getJSON(u) { const r = await fetch(u); if (!r.ok) throw new Error(u + " " + r.status); return r.json(); }
  (async function main() {
    renderText();
    try {
      const [rd, dd] = await Promise.all([getJSON("../data/run_trc2026.json"), getJSON("../data/run_details.json").catch(() => ({ sights: {} }))]);
      route = rd.route; sights = rd.sights; details = dd.sights || {};
    } catch (e) { $("loadingTxt").textContent = "Error: " + (e && e.message); return; }
    renderText();
    initMap();
    if (OG) {
      const bn = el("div"); bn.id = "ogbanner";
      const img = el("img"); img.src = "../img/trc-logo.png"; img.alt = ""; img.width = 84; img.height = 84;
      const tx = el("div");
      tx.appendChild(el("b", "", "TRC City Run 2026"));
      tx.appendChild(el("span", "", t().ogLine(route, sights.length)));
      bn.appendChild(img); bn.appendChild(tx); $("map").parentNode.appendChild(bn);
    }
    const h = parseInt((location.hash || "").slice(1), 10);
    if (h && sights.some((x) => x.n === h)) setTimeout(() => select(h, { scroll: true, fly: true }), 400);
  })();
})();
