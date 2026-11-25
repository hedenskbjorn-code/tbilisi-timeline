import { getJSON, prefetchJSON, verUrl } from "./js/net.js";
(() => {
  "use strict";
  // The timeline starts in the 2nd century CE (Armaziskhevi / Mtskheta antiquities; Tbilisi fortress ~364); the long early period is
  // compressed: slider units 0..1000 map piecewise-linearly to years (100-1000 -> 0-150, 1000-1700 -> 150-350, 1700-2026 -> 350-1000); the early centuries have 71 events in 1336 years, the last 326 years 199, so they keep the larger part
  const MIN = 100, MAX = 2026, NEW_YEARS = 25;
  const FULL_KNOTS = [[100, 0], [1000, 150], [1700, 350], [2026, 1000]];
  const ZOOM_W = [0, 1000, 600, 330, 230, 150, 90, 50, 26];   // width in years of the window of the zoomed time scale (0 = the whole scale)
  let zoomIx = 0, zoomLo = 100, zoomHi = 2026;
  let rulersMedia = null;                                              // portraits of the rulers and flags of the states (data/rulers_media.json, made by tools/fetch_rulers_media.py)
  let rulersData = null;                                               // forms of state and rulers (data/rulers.json), see buildRulersBand
  let reopenPopup = null, reopenInfo = null, openPop = null;          // the open card (a popup or the modal) and how to build it again, when the language is switched
  let placesLoading = null, placesFailedAt = 0, placesTimer = null;
  let places = null;                                                   // local names (data/places.json, loaded when the layer is switched on or the search is opened), see ensurePlaces
  let education = [];                                                  // schools and kindergartens of the register (data/education.json), see addEducation
  let museums = [];                                                    // museums and house-museums (data/museums.json), see addMuseums
  let science = [];                                                    // science and culture buildings (data/science.json), see addScience
  let religious = [];                                                  // religious buildings (data/religious.json), see addReligious
  let searchIndex = null, searchRows = [], searchSel = -1;      // search (see the block "search" below)
  let KNOTS = FULL_KNOTS;                         // zoomed scale: one linear piece over the window zoomLo..zoomHi (see applyWindow)
  const y2v = (y) => { for (let i = 1; i < KNOTS.length; i++) if (y <= KNOTS[i][0]) { const [y0, v0] = KNOTS[i - 1], [y1, v1] = KNOTS[i]; return v0 + ((y - y0) / (y1 - y0)) * (v1 - v0); } return 1000; };
  const v2y = (v) => { for (let i = 1; i < KNOTS.length; i++) if (v <= KNOTS[i][1]) { const [y0, v0] = KNOTS[i - 1], [y1, v1] = KNOTS[i]; return Math.round(y0 + ((v - v0) / (v1 - v0)) * (y1 - y0)); } return MAX; };
  const PLAN_AFTER = 10; // the last plan is shown at most this many years after its date
  const COARSE = new Set(["century", "half", "mixed"]);

  const T = window.TT_I18N;


  const LANGS = ["ka", "en", "ru"];
  let lang = "en";
  const nav = (navigator.language || "en").slice(0, 2);
  if (LANGS.includes(nav)) lang = nav;
  try { const s = localStorage.getItem("lang"); if (LANGS.includes(s)) lang = s; } catch (e) {}
  const q = new URLSearchParams(location.search).get("lang");
  if (LANGS.includes(q)) lang = q;
  const $ = (id) => document.getElementById(id);
  const t = () => T[lang];

  // The objects of the register are drawn by the layers of the panel (no list of the register): a check box of a layer switches the register objects with its purpose (fn)
  // on or off. The objects that a thematic layer already shows carry "dup" and are not drawn (tools/mark_register_dups.py).
  const FN_BOXES = { showResid: ["residential"], showPublic: ["public"], showRel: ["religious"], showSci: ["culture"], showEdu: ["culture"], showDef: ["defense"], showOtherB: ["memorial", "rural", "transport", "other"] };
  const activeFns = () => { const s = new Set(); for (const [id, fns] of Object.entries(FN_BOXES)) if ($(id).checked) for (const k of fns) s.add(k); return s; };
  const regVisible = (p, fns) => !(p.ye > year) && !p.dup && fns.has(p.fn);
  let plans = [], monuments = null, monAllById = new Map(), undated = 0, areas = [];
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
  // WebGL guard: when the graphics of the browser cannot start (a driver update, a lost context) the map would stay black without a word; the page says what to do instead.
  function glNote(key, blocking) {
    if (document.getElementById("glnote")) return;
    const n = document.createElement("div");
    n.id = "glnote"; n.className = blocking ? "block" : "";
    const p = document.createElement("p"); p.textContent = t()[key];
    n.append(p);
    if (!blocking) { const b = document.createElement("button"); b.type = "button"; b.textContent = t().glReload; b.onclick = () => location.reload(); n.append(b); }   // a reload does not cure a failed graphics driver: the blocking text asks for a restart of the browser instead
    document.body.appendChild(n);
  }
  (function () {
    let ok = false;
    try { const c = document.createElement("canvas"); ok = !!(c.getContext("webgl2") || c.getContext("webgl")); } catch (e) {}
    if (!ok) { glNote("glFail", true); window.__noGL = true; }
  })();
  if (window.__noGL) return;
  const map = new maplibregl.Map({
    container: "map",
    // OpenFreeMap vector tiles (free, no key; data © OpenStreetMap contributors, © OpenMapTiles; attribution added by MapLibre)
    // OpenFreeMap "liberty" style, same in light and dark system themes (free, no key; attribution is added by MapLibre)
    style: baseStyle,
    center: (() => { const c = (new URLSearchParams(location.search).get("c") || "").split(",").map(Number); return c.length >= 2 && c.every(isFinite) ? [c[0], c[1]] : [44.8085, 41.6955]; })(),
    zoom: (() => { const c = (new URLSearchParams(location.search).get("c") || "").split(",").map(Number); return c.length >= 3 && isFinite(c[2]) ? c[2] : 13.2; })(), minZoom: 9, maxZoom: 19, hash: false,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  // a read-only handle for the browser tests (tests/e2e): only with ?e2e=1 in the address
  if (new URLSearchParams(location.search).has("e2e")) window.TT_E2E = { map, get year() { return year; }, get lang() { return lang; }, nearCandidates: (pt) => nearCandidates(pt).map((c) => c.key + "|" + c.label), get lastClick() { return lastClick; } };
  map.once("load", () => { const n = document.getElementById("glnote"); if (n) n.remove(); });
  map.getCanvas().addEventListener("webglcontextlost", () => glNote("glFail", false));
  setTimeout(() => { if (!mapLoaded) glNote("glSlow", false); }, 25000);
  function syncUrl() {                           // permalink: ?c=lng,lat,zoom (the year stays in the hash), ?sw=the bar of the comparison
    try {
      const u = new URL(location.href), c = map.getCenter();
      u.searchParams.set("c", c.lng.toFixed(5) + "," + c.lat.toFixed(5) + "," + map.getZoom().toFixed(1));
      if ($("showSwipe") && $("showSwipe").checked) u.searchParams.set("sw", swipeFrac.toFixed(2)); else u.searchParams.delete("sw");
      history.replaceState(null, "", u.pathname + u.search + u.hash);
    } catch (e) {}
  }
  map.on("moveend", syncUrl);

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
    const f = ["all", ["<=", ["get", "ye"], year], ["!=", ["get", "dup"], 1], ["in", ["get", "fn"], ["literal", [...activeFns()]]]];
    return f;
  }

  function countVisible() {
    const fns = activeFns();
    let n = 0;
    for (const f of monuments.features) if (regVisible(f.properties, fns)) n++;
    return n;
  }

  let bndText = "";
  function updateUrban() {
    if (!map.getLayer("urban-fill")) return;
    let snap = null;
    for (const s of urbanSnaps) if (s <= year) snap = s;
    const on = $("showBnd").checked && snap !== null;
    const traced = ["in", ["get", "src"], ["literal", ["traced", "khar"]]];                // hand-traced and digitised outlines are approximate: dashed
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
  // ONE basemap "the old map of the chosen year": the source is picked by the year (the old plan of the year; from 1953 to 2005, where there is no plan, the topographic map 1:25 000), or by the choice
  // in the list "map source": only the plans, or one scale of the topographic map for every year. The map and the plan share one opacity slider.
  const topoMode = () => $("topoSel").value;                     // auto | plan | t2 | t10 | t25 | t50 | t100
  const explicitTopo = () => !!TOPO[topoMode()];
  const autoTopoOn = () => topoMode() === "auto" && year >= TOPO_FROM && year <= TOPO_TO && !currentPlan(year);
  const topoWanted = () => $("showPlan").checked && (explicitTopo() || autoTopoOn());
  const topoKey = () => (explicitTopo() ? topoMode() : "t25");
  const topoOpacity = () => ($("showSwipe").checked ? 1 : $("op").value / 100);
  function updateTopo() {
    const on = topoWanted(), key = topoKey();
    $("topobox").hidden = !$("showPlan").checked;
    $("topoNoteRow").hidden = !on;                                // the note about the editions of the topographic maps is shown while one is on the map
    if (topoShown && (!on || topoShown !== key)) {
      if (map.getLayer("topo")) map.removeLayer("topo");
      if (map.getSource("topo")) map.removeSource("topo");
      topoShown = null;
    }
    if (!on) return;
    if (!topoShown) {
      const c = TOPO[key], base = new URL("topo/" + key + "/", document.baseURI).href;
      map.addSource("topo", { type: "raster", tiles: [base + "{z}/{x}/{y}.webp"], tileSize: 256, minzoom: 11, maxzoom: c.max, bounds: TOPO_BOUNDS, attribution: "© NAPR (maps.gov.ge)" });
      map.addLayer({ id: "topo", type: "raster", source: "topo", paint: { "raster-opacity": topoOpacity(), "raster-fade-duration": 0 } }, "admin-line");
      liftTransport();
      topoShown = key;
    }
    map.setPaintProperty("topo", "raster-opacity", topoOpacity());
  }
  $("topoSel").addEventListener("input", () => { update(); });

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
    const pl = currentPlan(year);
    $("swlTxt").textContent = "← " + t().swPlanWord;
    const sel = $("swPlan");
    if (sel.options.length !== plans.length) { sel.textContent = ""; for (const p of plans) { const o = document.createElement("option"); o.value = String(p.year); o.textContent = String(p.year); sel.appendChild(o); } }
    sel.setAttribute("aria-label", t().swPlanSel);
    if (pl) sel.value = String(pl.year);
    $("swAcc").textContent = pl && pl.accuracy_m ? "\u00B1" + Math.round(pl.accuracy_m) + " " + t().swM : "";
    $("swr").textContent = t().swRight + " \u2192";
    $("swipebar").setAttribute("aria-label", t().swBar); $("swipebar").setAttribute("aria-valuenow", String(Math.round(swipeFrac * 100)));
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
    bar.addEventListener("pointerup", () => syncUrl());                 // the position of the bar goes to the address
    bar.addEventListener("keydown", (ev) => {
      const step = ev.shiftKey ? 0.1 : 0.02;
      let f = null;
      if (ev.key === "ArrowLeft") f = swipeFrac - step; else if (ev.key === "ArrowRight") f = swipeFrac + step;
      else if (ev.key === "Home") f = 0.03; else if (ev.key === "End") f = 0.97;
      if (f === null) return;
      ev.preventDefault();
      swipeFrac = Math.min(0.97, Math.max(0.03, f)); layoutSwipe(); syncUrl();
    });
    $("swPlan").addEventListener("change", (e) => { year = +e.target.value; update(); });
    // the shared link: ?sw=0.5 opens the page with the bar on
    const sw = parseFloat(new URLSearchParams(location.search).get("sw"));
    if (isFinite(sw) && sw >= 0.03 && sw <= 0.97) { swipeFrac = sw; $("showSwipe").checked = true; }
  }
  // the buttons of the map: "then and now" (the bar on/off; a year without a plan jumps to the nearest plan) and "copy the link to this view"
  map.addControl({
    onAdd() {
      const box = document.createElement("div"); box.className = "maplibregl-ctrl maplibregl-ctrl-group";
      const b1 = document.createElement("button"); b1.type = "button"; b1.className = "thenctl"; b1.id = "thenBtn"; b1.textContent = "\u21C4";
      b1.addEventListener("click", () => {
        const cb = $("showSwipe"), turnOn = !cb.checked;
        if (turnOn) {
          if (!$("showPlan").checked) $("showPlan").checked = true;
          if (!currentPlan(year) && plans.length) year = year < plans[0].year ? plans[0].year : plans[plans.length - 1].year;   // the nearest plan
        }
        cb.checked = turnOn; update(); syncUrl();
      });
      const b2 = document.createElement("button"); b2.type = "button"; b2.className = "linkctl"; b2.id = "linkBtn"; b2.textContent = "\uD83D\uDD17";
      b2.addEventListener("click", async () => {
        syncUrl();
        const url = location.href;
        try { await navigator.clipboard.writeText(url); b2.textContent = "\u2713"; setTimeout(() => { b2.textContent = "\uD83D\uDD17"; }, 1600); }
        catch (e) { window.prompt(t().linkTitle, url); }
      });
      const b3 = document.createElement("button"); b3.type = "button"; b3.className = "thenctl"; b3.id = "hereBtn"; b3.textContent = "\uD83D\uDCCD";
      b3.addEventListener("click", () => { const cb = $("showHere"); cb.checked = !cb.checked; cb.dispatchEvent(new Event("change", { bubbles: true })); });
      box.appendChild(b1); box.appendChild(b3); box.appendChild(b2); return box;
    },
    onRemove() {},
  }, "top-right");
  function updateThenTitles() {
    const b1 = $("thenBtn"), b2 = $("linkBtn"), b3 = $("hereBtn");
    if (b3) { b3.title = t().showHere; b3.setAttribute("aria-label", t().showHere); b3.setAttribute("aria-pressed", String($("showHere").checked)); }
    if (b1) { b1.title = t().thenTitle; b1.setAttribute("aria-label", t().thenTitle); b1.setAttribute("aria-pressed", String($("showSwipe").checked)); }
    if (b2) { b2.title = t().linkTitle; b2.setAttribute("aria-label", t().linkTitle); }
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
  let lastClick = null;                                              // the last click on the map (where and when): a card that opens right after it knows what else lies under the click, see nearCandidates
  map.getContainer().addEventListener("click", (ev) => {          // in the capture phase: before MapLibre sends its own click to the layers whose handlers open the card
    const r = map.getCanvas().getBoundingClientRect();
    lastClick = { t: Date.now(), point: { x: ev.clientX - r.left, y: ev.clientY - r.top } };
  }, true);
  map.on("click", (e) => { if ($("showHere").checked) showHere(e.lngLat); });
  $("showHere").addEventListener("change", () => { $("map").classList.toggle("here", $("showHere").checked); });

  // plan rasters are added to the map only when a plan is first needed (keeps the first page load light)
  // transport (tram, metro, railway, bridges, avenues) lies above the old plans and the topographic map: layers added later go in just under "admin-line", i.e. above the transport
  // that was added earlier, so the transport is lifted again after every plan or topographic map is added (found out 2026-11-19: the tram was hidden under the topographic map)
  // the layers of the transport, from the bottom: the casing of the avenues, the lines, the cross ticks of the tram, the metro stations (circle, letter), the funicular, the cable car
  const TR_IDS = ["tr-casing", "tr-line", "tr-ticks", "tr-pt", "tr-pt-m", "tr-funic", "tr-cable"];
  function liftTransport() {
    for (const id of TR_IDS) if (map.getLayer(id) && map.getLayer("admin-line")) map.moveLayer(id, "admin-line");
  }
  function ensurePlan(p) {
    if (map.getLayer("plan-" + p.id)) return;
    map.addSource("plan-" + p.id, { type: "image", url: p.overview || p.image, coordinates: p.corners });      // the light copy first (see upgradePlans)
    p._full = !p.overview;
    map.addLayer({ id: "plan-" + p.id, type: "raster", source: "plan-" + p.id, layout: { visibility: "none" },
                   paint: { "raster-opacity": planOpacity(), "raster-fade-duration": 0 } }, "admin-line");
    liftTransport();
    if (dataReady) { setLoading("loadPlan", true); map.once("idle", hideLoading); }
  }
  // The first screen shows the light copy of a plan (p.overview, about 8 m per pixel, made by tools/make_plan_overviews.py): it is as sharp as the screen at the
  // starting scale and 10 times lighter than the full picture. The full picture takes its place when it is needed: when the map is zoomed in until a pixel of the
  // overview is bigger than a pixel of the screen, or at once (in the background, after the first screen) on a screen with a dense pixel grid. No quality is lost.
  function planNeedsFull(p) {
    const zNeed = Math.log2(156543.03 * Math.cos(41.7 * Math.PI / 180) / (p.overview_mpp || 8)) - 0.3;
    return map.getZoom() + Math.log2(window.devicePixelRatio || 1) >= zNeed;
  }
  function upgradePlans() {
    if (!dataReady) return;                                                  // the first screen first
    for (const p of plans) {
      if (p._full || !p.overview) continue;
      const src = map.getSource("plan-" + p.id);
      if (!src || map.getLayoutProperty("plan-" + p.id, "visibility") !== "visible" || !planNeedsFull(p)) continue;
      p._full = true;
      src.updateImage({ url: p.image, coordinates: p.corners });
    }
  }
  map.on("zoomend", upgradePlans);
  map.on("idle", upgradePlans);

  // the periods of the history of Georgia as the sections of the tests for the Georgian citizenship (2024): 4th-10th, 11th-15th, 16th-18th centuries, 19th century - 1921, from 1921.
  // The select shows the period of the year on the slider; a choice jumps to the beginning of the period.
  const EPOCHS = [100, 1001, 1501, 1801, 1921];
  const epochOf = (y) => { let k = 0; for (let i = 0; i < EPOCHS.length; i++) if (y >= EPOCHS[i]) k = i; return k; };
  function buildEpochs() {
    const sel = $("epochSel");
    if (!sel) return;
    sel.textContent = "";
    t().epochs.forEach((name, i) => { const o = document.createElement("option"); o.value = String(i); o.textContent = name; sel.appendChild(o); });
    sel.setAttribute("aria-label", t().ariaEpoch);
    sel.title = t().ariaEpoch;
    sel.value = String(epochOf(year));
    sel.dataset.e = String(epochOf(year));
  }
  $("epochSel").addEventListener("change", (e) => { year = EPOCHS[+e.target.value]; update(); });
  // the band behind the slider: one coloured segment per period, so that it is clear where one period ends and the next begins; labels are numerals only (no translation)
  const EPOCH_SHORT = ["IV\u2013X", "XI\u2013XV", "XVI\u2013XVIII", "XIX\u20131921", "1921\u2013"];
  function buildEpochBand() {
    const box = $("epochBand");
    if (!box) return;
    box.textContent = "";
    const wpx = box.clientWidth || 300;
    EPOCHS.forEach((s0, i) => {
      const v0 = Math.max(0, y2v(s0)), v1 = Math.min(1000, i + 1 < EPOCHS.length ? y2v(EPOCHS[i + 1]) : 1000);
      if (v1 <= v0 + 0.5) return;
      const seg = document.createElement("i");
      seg.style.left = (v0 / 10) + "%";
      seg.style.width = ((v1 - v0) / 10) + "%";
      seg.style.setProperty("--ep", `var(--ep${i})`);
      if (((v1 - v0) / 1000) * wpx >= EPOCH_SHORT[i].length * 6.2 + 8) { const b = document.createElement("b"); b.textContent = EPOCH_SHORT[i]; seg.appendChild(b); }
      box.appendChild(seg);
    });
  }

  function update() {
    ensureInWindow();
    syncFilterUi();
    $("year").textContent = year;
    if ($("epochSel")) { $("epochSel").value = String(epochOf(year)); $("epochSel").dataset.e = String(epochOf(year)); }
    if ($("yearchip")) $("yearchip").textContent = year;
    if ($("tbYear")) $("tbYear").textContent = year;
    $("slider").value = Math.round(y2v(year));
    $("slider").setAttribute("aria-valuetext", String(year));                     // a screen reader says the year, not the position 0-1000
    try { history.replaceState(null, "", "#" + year); } catch (e) {}
    if (!map.getLayer("mon")) return;
    map.setFilter("mon", filterExpr());
    if (map.getLayer("mon-ruin")) map.setFilter("mon-ruin", ["all", filterExpr(), ["==", ["get", "ruin"], true]]);
    map.setPaintProperty("mon", "circle-color", ["case",
      ["==", ["get", "national"], true], getCss("--nat"),
      ["<=", ["-", year, ["get", "ye"]], NEW_YEARS], getCss("--accent"),
      getCss("--old")]);
    const pl = currentPlan(year);
    for (const p of plans) {
      const on = pl && p.id === pl.id && $("showPlan").checked && !explicitTopo();      // a chosen scale of the topographic map takes the place of the plan
      if (on) ensurePlan(p);
      if (map.getLayer("plan-" + p.id)) map.setLayoutProperty("plan-" + p.id, "visibility", on ? "visible" : "none");
    }
    updateUrban();
    updateSettle();
    updateWater();
    updateDensity();
    updateTransport();
    updateTopo();
    updateC94();
    updateReligious();
    updateScience();
    updateEducation();
    updateMuseums();
    updateBattleMap();
    updatePlaces();
    updateMP("mon");
    updateMP("plq");
    updateMP("mod");
    updateNoPhoto();
    updateRuleBar();
    updateStreets();
    updateSwipe();
    updateThenTitles();
    updateLost();
    if (map.getLayer("admin-line")) map.setLayoutProperty("admin-line", "visibility", $("showAdmin").checked ? "visible" : "none");
    const oldOn = $("showAdmin").checked && year >= 1973 && year <= 2005;
    if (map.getLayer("admin-old-line")) map.setLayoutProperty("admin-old-line", "visibility", oldOn ? "visible" : "none");
    const dOn = $("showDistricts").checked ? "visible" : "none";
    for (const id of ["districts-line", "districts-label"]) if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", dOn);
    if (map.getLayer("districts-label")) map.setLayoutProperty("districts-label", "text-field", ["get", "name_" + lang]);
    syncSections();
    schedulePanels();
  }

  // The map, the year and the time scale follow every step; the content panels (the text on the left, the views on the right, the chart) are drawn
  // a moment after the last change (0.3 s) and, while the playback runs, only when it stops: they cannot be read at that speed and they made everything jerk.
  let playing = false, panelTimer = 0, panelsDrawn = false;
  function updatePanels() {
    $("count").textContent = t().count(countVisible(), year);
    updateStNames();
    updatePop();
    updateRuleBox();
    updateViews();
    let ar = null;
    for (const x of areas) if (x.year <= year) ar = x;
    $("arealine").textContent = (ar ? t().area(ar.km2, ar.year, ar.src) : "") + ($("showAdmin").checked && year >= 1973 && year <= 2005 ? " · " + t().oldAdmin : "");
    updateDistInfo();
    updatePlanLine();
    $("bndline").textContent = bndText;
    syncSections();
    document.body.classList.remove("stale");
  }
  let secState = {};
  try { secState = JSON.parse(localStorage.getItem("sec") || "{}") || {}; } catch (e) {}
  function syncSections() {
    for (const sec of document.querySelectorAll("#side details.sec")) {
      const id = sec.dataset.sec;
      if (!sec.dataset.ready) {
        sec.dataset.ready = "1";
        if (id in secState) sec.open = !!secState[id];
        sec.addEventListener("toggle", () => { secState[id] = sec.open; try { localStorage.setItem("sec", JSON.stringify(secState)); } catch (e) {} });
      }
      sec.hidden = ![...sec.querySelectorAll(":scope > div")].some((d) => !d.hidden && (d.children.length || d.textContent.trim()));
    }
  }
  function flushPanels() { clearTimeout(panelTimer); panelTimer = 0; updatePanels(); }
  function schedulePanels() {
    if (!panelsDrawn) { panelsDrawn = true; flushPanels(); return; }          // the first drawing is at once
    if (playing) { document.body.classList.add("stale"); return; }
    document.body.classList.add("stale");
    clearTimeout(panelTimer);
    panelTimer = setTimeout(flushPanels, 300);
  }

  function updatePlanLine() {
    const pl = currentPlan(year), sel = $("topoSel"), opt = sel.querySelector('option[value="' + topoKey() + '"]');
    $("planline").textContent = explicitTopo() ? t().topoLine(opt.textContent) : pl ? t().plan(pl.year, pl.accuracy_m) : topoWanted() ? t().topoLine(opt.textContent) : t().noPlan(plans[0].year, plans[plans.length - 1].year, year);
  }

  function applyLang() {
    document.documentElement.lang = lang;
    document.title = t().title;
    if (typeof feedbackRefreshCtx === "function") feedbackRefreshCtx();
    $("title").textContent = t().title;
    $("lang").value = lang;
    if ($("loading") && !$("loading").hidden) $("loadingTxt").textContent = t()[loadKey];
    $("lang").setAttribute("aria-label", t().ariaLang);
    $("slider").setAttribute("aria-label", t().ariaYear);
    if ($("entrLink")) $("entrLink").href = "entrances/?lang=" + lang;
    { const sel = $("pagesSel");                                               // the sections of the site: the map, the walking route, the running route
      if (sel) {
        sel.textContent = "";
        sel.setAttribute("aria-label", t().ariaPages); sel.title = t().ariaPages;
        for (const [v, k] of [["./", "navMap"], ["entrances/", "navEntr"], ["run/", "navRun"], ["museums/", "navMus"], ["mtskheta/", "navMtskheta"], ["lost/", "navLost"]]) { const o = document.createElement("option"); o.value = v; o.textContent = t()[k]; sel.appendChild(o); }
        sel.value = "./";
      } }
    $("speed").setAttribute("aria-label", t().ariaSpeed);
    buildEpochs();
    $("btnMore").setAttribute("aria-label", t().ariaMore); $("btnMore").title = t().ariaMore;
    $("vmPrev").setAttribute("aria-label", t().ariaPrev);
    $("vmNext").setAttribute("aria-label", t().ariaNext);
    if (typeof updateLocTitles === "function") updateLocTitles();
    if (typeof updateFoldTitles === "function" && $("tbToggle")) updateFoldTitles();
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
    updateSciUi();
    updateEduUi();
    updateMusUi();
    updateBattleMapUi();
    updatePlacesUi();
    updateMPUi();
    $("note").textContent = t().note(undated);
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

  // the window "Literature and sources": the list is made by tools/build_bibliography.py from the data of the events
  let biblioData = null;
  async function showBiblio() {
    try {
      if (!biblioData) {
        const r = await fetch("data/bibliography.json");
        if (!r.ok) throw new Error(r.status);
        biblioData = await r.json();
      }
    } catch (e) {
      openInfo((body) => infoLine(body, t().biblioFail), false, t().biblioTitle);
      return;
    }
    const d = biblioData;
    openInfo((body) => {
      infoLine(body, t().biblioIntro);
      const head = (txt) => { const h = document.createElement("h4"); h.textContent = txt; body.appendChild(h); };
      const links = (box, arr) => {
        for (const l of arr) {
          box.appendChild(document.createTextNode(" "));
          const a = document.createElement("a");
          a.href = l.u; a.target = "_blank"; a.rel = "noopener";
          a.textContent = l.t === "scan" ? t().biblioScan : l.t;
          box.appendChild(a);
        }
      };
      head(t().biblioBooks);
      for (const b of d.books) {
        const row = infoLine(body, b.ref + " (" + t().biblioEvents(b.events) + ")");
        links(row, b.links);
      }
      head(t().biblioConsulted);
      for (const b of d.consulted) {
        const row = infoLine(body, b.ref);
        links(row, b.links);
      }
      head(t().biblioWeb);
      for (const w of d.web) infoLine(body, w.name + ": " + w.pages + " / " + t().biblioEvents(w.events));
      infoLine(body, t().biblioMethod);
    }, false, t().biblioTitle);
  }
  $("btnBiblio").addEventListener("click", showBiblio);

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
    actions(el, null, fbRef("C94", p.id ?? p.num, el));
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
  let stNames = [], stGeom = {}, trStations = [];                 // trStations: the stations of the metro (for the search)
  function updateStLabelsLayer() {
    const src = map.getSource("stlabels");
    if (!src) return;
    const feats = [];
    if ($("showStLabels").checked) {
      for (const st of stNames) {
        const g = stGeom[st.geom || st.now.en], iv = st.iv.find((x) => year >= x[0] && year < x[1] && x[2]);
        if (g && iv) feats.push({ type: "Feature", geometry: g, properties: { t: pickName(iv[2]), k: stNames.indexOf(st) } });
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
    for (const id of ["stl-line", "stl-pt"]) {                    // a click on the name of a street opens the card of the street
      map.on("click", id, (e) => { const f = e.features && e.features[0]; if (f && stNames[f.properties.k]) showStreetCard(stNames[f.properties.k]); });
      map.on("mouseenter", id, () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", id, () => { map.getCanvas().style.cursor = ""; });
    }
  }
  // the namesake (in whose honour or after what the object is named; data/namesakes.json, loaded when a card or a popup is opened): the name, the years, the description of the encyclopedia of 2008 with its
  // page, a link to Wikipedia only where the link is confirmed (tools/verify_namesakes.py)
  let namesakes = null;
  async function loadNamesakes() {
    if (!namesakes) { try { namesakes = await getJSON("data/namesakes.json", 1); } catch (e) { namesakes = { streets: {}, objects: {}, ui: {} }; } }
    return namesakes;
  }
  function addNamesake(parent, it) {
    const U = (k) => ((namesakes.ui || {})[k] && ((namesakes.ui[k][lang]) || namesakes.ui[k].en)) || "";
    const d = document.createElement("div");
    d.className = "small";
    const yrs = it.y ? " (" + (it.y[0] != null ? it.y[0] : "?") + "\u2013" + (it.y[1] != null ? it.y[1] : "") + ")" : "";
    const desc = it.d && (it.d[lang] || it.d.en);
    d.textContent = U("named") + ": " + (it.n[lang] || it.n.en) + yrs + (desc ? " \u2014 " + desc : "") + " ";
    const l = it.w && [lang, "en", "ru", "ka"].find((x) => it.w[x]);
    if (l) { const a = document.createElement("a"); a.href = "https://" + l + ".wikipedia.org/wiki/" + encodeURIComponent(it.w[l].replace(/ /g, "_")); a.target = "_blank"; a.rel = "noopener"; a.textContent = U("wiki") + " (" + l + ")"; d.appendChild(a); }
    parent.appendChild(d);
    if (it.p) { const b = document.createElement("div"); b.className = "small"; b.textContent = U("book") + " " + it.p; parent.appendChild(b); }
  }
  async function addNamesakeTo(parent, id) {                       // for a popup that is already on the screen: the line comes when the file is loaded
    const ns = await loadNamesakes();
    if (ns.objects[id]) addNamesake(parent, ns.objects[id]);
  }
  // the card of a street: the name today, every former name with its years (also the names without a year), the note and the source (a link or a book with the page)
  let stNotes = null;                                             // the notes of the streets: street_notes.json, loaded when the first card is opened
  let stObjects = null;                                           // the objects on the streets (buildings, monuments, ...): street_objects.json, loaded with the first card
  const OBJ_KINDS = ["building", "monument", "church", "memorial", "vanished", "planner"];
  async function showStreetCard(s, fly) {
    if (!stNotes) { try { stNotes = (await getJSON("data/street_notes.json", 2)).notes; } catch (e) { stNotes = {}; } }
    if (!stObjects) { try { stObjects = (await getJSON("data/street_objects.json", 2)).objects; } catch (e) { stObjects = {}; } }
    const nsAll = await loadNamesakes();
    reopenInfo = () => showStreetCard(s);
    try { const u = new URL(location.href); u.searchParams.set("o", "st:" + (s.geom || s.now.en)); history.replaceState(null, "", u.pathname + u.search + u.hash); } catch (e) {}
    const L = t(), now = s.now[lang] || s.now.en, note = stNotes[s.geom || s.now.en];
    openInfo((body) => {
      infoLine(body, now, "");
      for (const iv of s.iv) if (iv[2]) infoLine(body, iv[0] + "–" + (iv[1] >= 9999 ? "" : iv[1]) + " · " + pickName(iv[2]), "small");
      if (s.undated && s.undated.length) infoLine(body, L.stUndated + ": " + s.undated.map((u) => pickName(u)).join("; "), "small");
      if (note) infoLine(body, pickName(note));
      const nsItem = nsAll.streets[s.geom || s.now.en];
      if (nsItem) addNamesake(body, nsItem);
      const objs = stObjects[s.geom || s.now.en];
      if (objs && objs.length) {                                  // "On the street": by kind, each with the person (the role), the years and the house number
        infoLine(body, L.objTitle + ":", "");
        for (const k of OBJ_KINDS) {
          const list = objs.filter((o) => o.k === k);
          if (!list.length) continue;
          infoLine(body, L.objKinds[k], "small");
          for (const o of list) {
            const parts = [k === "planner" ? "" : pickName(o.n)];
            if (o.p) parts.push(pickName(o.p) + (o.r ? " (" + L.objRoles[o.r] + ")" : ""));
            else if (o.r && k !== "planner") parts.push(L.objRoles[o.r]);
            if (o.y) parts.push(o.y.join("–"));
            if (o.a) parts.push("№ " + o.a);
            infoLine(body, "• " + parts.filter(Boolean).join(" · "), "small");
          }
        }
      }
      infoLine(body, L.evSrc + ":");
      if (s.src) { const d = infoLine(body, "", "small"), a = document.createElement("a"); a.href = s.src; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURI(s.src); d.appendChild(a); }
      if (s.book) infoLine(body, s.book, "small");
    }, false, now);
    const g = stGeom[s.geom || s.now.en];
    if (fly && g) {
      const pts = g.type === "Point" ? [g.coordinates] : g.coordinates.flat();
      const b = pts.reduce((a, p) => [Math.min(a[0], p[0]), Math.min(a[1], p[1]), Math.max(a[2], p[0]), Math.max(a[3], p[1])], [180, 90, -180, -90]);
      map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 80, maxZoom: 17, duration: 1200 });
    }
  }
  function updateStNames() {
    updateStLabelsLayer();
    updateRoadLabels();
    const box = $("stnames");
    if (!box) return;
    const L = t(), rows = [];
    for (const s of stNames) {
      const iv = s.iv.find((x) => year >= x[0] && year < x[1] && x[2]);
      if (iv) rows.push([pickName(iv[2]), s.now[lang] || s.now.en, s.src, s.book, s]);
    }
    box.textContent = "";
    box.hidden = !rows.length;
    if (!rows.length) return;
    const h = document.createElement("div");
    h.textContent = L.stTitle;
    box.appendChild(h);
    for (const [old, now, src, book, st] of rows) {
      const d = document.createElement("div");
      d.style.cursor = "pointer";
      d.addEventListener("click", (e) => { if (!e.target.closest("a")) showStreetCard(st, true); });   // the card of the street
      const b = document.createElement("b");
      b.textContent = old;
      d.appendChild(b);
      d.appendChild(document.createTextNode(" \u2192 " + L.stNow + ": " + now + " "));
      if (src) {
        const a = document.createElement("a");
        a.href = src; a.target = "_blank"; a.rel = "noopener"; a.className = "src"; a.textContent = "[src]";
        d.appendChild(a);
      } else if (book) {                                          // a book without a link: the reference with the page, as plain text
        const sp = document.createElement("span");
        sp.className = "src"; sp.textContent = "[" + book + "]";
        d.appendChild(sp);
      }
      box.appendChild(d);
    }
    const m = document.createElement("div");
    m.className = "src";
    m.textContent = L.stMore;
    box.appendChild(m);
  }
  const EV_ICON = { unrest: "\uD83D\uDD6F\uFE0F", oldest: "\uD83C\uDFF0", build: "\uD83C\uDFD7\uFE0F", invasion: "\u2694\uFE0F", battle: "\uD83D\uDDE1\uFE0F", earthquake: "\uD83C\uDFDA\uFE0F", fire: "\uD83D\uDD25", flood: "\uD83C\uDF0A", power: "\uD83C\uDFDB\uFE0F", science: "\uD83D\uDD2C", other: "\uD83D\uDCCC" };
  function buildEvMarks() {
    const box = $("evmarks");
    if (!box) return;
    box.textContent = "";
    // markers that would overlap on the scale are merged into one marker with a count; a click on it lists the events
    const W = Math.max(0, box.clientWidth - 16), GAP = window.matchMedia("(max-width:640px)").matches ? 26 : 19;
    const items = histEvents.filter((ev) => (ev.cat !== "battle" || $("showBattles").checked) && ev.year >= zoomLo && ev.year <= zoomHi).map((ev) => ({ ev, x: 8 + W * (y2v(ev.year) / 1000) })).sort((a, b) => a.x - b.x || a.ev.year - b.ev.year);
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
  // a red pin on the map at the place of the event, the map flies there; the card of the event is a sheet at the bottom (the map stays in sight)
  function pinElement(label) {
    const wrap = document.createElement("div");
    wrap.className = "evpinwrap"; wrap.setAttribute("role", "img"); wrap.setAttribute("aria-label", label);
    const NS = "http://www.w3.org/2000/svg", svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 30 42"); svg.setAttribute("width", "30"); svg.setAttribute("height", "42"); svg.setAttribute("class", "evpin");
    const p = document.createElementNS(NS, "path");
    p.setAttribute("d", "M15 1C7.3 1 1.5 6.9 1.5 14.4c0 9.8 11.3 24.2 12.6 25.8a1.1 1.1 0 0 0 1.8 0c1.3-1.6 12.6-16 12.6-25.8C28.5 6.9 22.7 1 15 1z");
    p.setAttribute("fill", "#e03131"); p.setAttribute("stroke", "#fff"); p.setAttribute("stroke-width", "2");
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("cx", "15"); c.setAttribute("cy", "14.5"); c.setAttribute("r", "5.2"); c.setAttribute("fill", "#fff");
    svg.append(p, c);
    const ring = document.createElement("span"); ring.className = "evring";
    wrap.append(ring, svg);
    return wrap;
  }
  function showEventPlace(ev) {
    if (evMarker) { evMarker.remove(); evMarker = null; }
    if (!ev.place) return;
    const nm = ev.place[lang] || ev.place.en || "";
    evMarker = new maplibregl.Marker({ element: pinElement(nm), anchor: "bottom" }).setLngLat([ev.place.lng, ev.place.lat]).addTo(map);
    evMarker.getElement().setAttribute("aria-label", nm);        // MapLibre sets its own label "Map marker"
    const pad = { top: Math.round($("timebar").getBoundingClientRect().bottom) + 16, bottom: Math.min(Math.round(window.innerHeight * 0.42), 380) + (parseInt(getComputedStyle(document.documentElement).getPropertyValue("--bb"), 10) || 0), left: 16, right: 16 };
    map.flyTo({ center: [ev.place.lng, ev.place.lat], zoom: ev.place.zoom || 16, padding: pad, duration: 1200 });
  }
  function showHistEvent(ev) {
    if (window.TT_closePanels) window.TT_closePanels();          // a phone: the card takes the place of the open panel
    if (ev.cat === "battle" && !$("showBattles").checked) { $("showBattles").checked = true; buildEvMarks(); syncFilterUi(); }          // an opened battle must be visible on the scale
    reopenInfo = () => showHistEvent(ev);
    const L = t();
    showEventPlace(ev);
    openInfo((body) => {
      infoLine(body, ev.date + " \u00B7 " + (L.evCats[ev.cat] || ""), "small");
      infoLine(body, ev[lang] || ev.en, "");
      if (ev.note) infoLine(body, pickName(ev.note));
      if (ev.place) infoLine(body, "\uD83D\uDCCD " + (ev.place[lang] || ev.place.en));
      else infoLine(body, "\uD83D\uDCCD " + L.evNoPlace, "small");
      if (ev.src.some((u) => /wikipedia/i.test(typeof u === "string" ? u : u.url || ""))) infoLine(body, L.evNote);
      infoLine(body, L.evSrc + ":");
      for (const u of ev.src) {
        const d = document.createElement("div");
        d.className = "small";
        if (typeof u !== "string" && !u.url) {                  // a book without a link: the reference with the page, as plain text
          d.textContent = u.label;
          body.appendChild(d);
          continue;
        }
        const a = document.createElement("a");
        const url = typeof u === "string" ? u : u.url;
        a.href = url; a.target = "_blank"; a.rel = "noopener"; a.textContent = typeof u === "string" ? decodeURI(u) : u.label + " \u2014 " + decodeURI(url);
        d.appendChild(a);
        body.appendChild(d);
      }
    }, !!ev.place);
  }

  let photoInfo = null;
  // Details that do not belong on the card (licences, sources, register notes) live in a separate window opened by a button.
  let infoFocus = null, viewFocus = null, fbFocus = null;       // the element that had the focus before a window was opened: the focus goes back to it
  const giveFocusBack = (el, ...fallbacks) => {                 // the element may be gone (the tiles are rebuilt when the year changes): then the first visible element of the list
    const cands = [el, ...fallbacks.map((q) => document.querySelector(q))];
    const target = cands.find((c) => c && c.isConnected && c.offsetParent !== null);
    if (target) { try { target.focus(); } catch (e) {} }
  };
  function openInfo(build, sheet, title) {
    if ($("infoModal").hidden) infoFocus = document.activeElement;
    $("imTitle").textContent = title || t().infoTitle;
    const body = $("imBody");
    body.textContent = "";
    body.className = "";
    build(body);
    $("imReport").textContent = t().fbPopup;
    $("infoModal").classList.toggle("sheet", !!sheet);          // an event with a place: a sheet at the bottom, the map and the pin stay in sight
    $("infoModal").hidden = false;
  }
  function closeInfo() { reopenInfo = null; try { const u = new URL(location.href); if (/^st:/.test(u.searchParams.get("o") || "")) { u.searchParams.delete("o"); history.replaceState(null, "", u.pathname + u.search + u.hash); } } catch (e) {} const was = !$("infoModal").hidden; $("infoModal").hidden = true; if (evMarker) { evMarker.remove(); evMarker = null; } if (was) { giveFocusBack(infoFocus); infoFocus = null; } }
  $("imClose").addEventListener("click", closeInfo);
  $("imReport").addEventListener("click", () => { const name = $("imTitle").textContent; closeInfo(); openFeedback({ id: "info", name: name.slice(0, 80), reg: "-" }); });
  $("infoModal").addEventListener("click", (e) => { if (e.target === $("infoModal")) closeInfo(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("infoModal").hidden) closeInfo(); });
  // Esc closes the open card of the map; an open window (the info, the picture viewer, the form, the search, the menu) takes the key first (the capture phase runs before their own handlers)
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || !openPop) return;
    if (!$("infoModal").hidden || !$("viewModal").hidden || !$("fbModal").hidden || !$("search").hidden || !$("moreMenu").hidden) return;
    openPop.remove();
  }, true);
  // the guided tour (site/tour.js, data/tour.json): loaded when it is asked for, from the welcome window or from the button "?" of the menu
  async function runTour() {
    // on a phone the panel Info (it holds the button of the tour) covers the map: it is closed before the tour, and the step "Map" lights the free part of the map
    if (window.matchMedia("(max-width:640px)").matches && $("btnInfo").getAttribute("aria-pressed") === "true") $("btnInfo").click();
    try { (await import("./js/tour.js")).startTour({ lang, free: freeRect, panel: window.TT_panels }); } catch (e) { console.error("tour", e && e.message); }
  }
  $("btnTour").addEventListener("click", runTour);
  // the welcome window: a short friendly text at the first visit. Not shown: in the tests (only with ?welcome=1), after a link to a year or to an object, after "Do not show again" (localStorage),
  // twice in one session (sessionStorage). "Start" and a closed window do not switch it off for good.
  function maybeWelcome() {
    const sp = new URLSearchParams(location.search), force = sp.get("welcome") === "1";
    let never = false, seen = false;
    try { never = localStorage.getItem("welcome") === "1"; seen = sessionStorage.getItem("welcome") === "1"; } catch (e) {}
    if (!force && (sp.has("e2e") || sp.has("o") || (h >= MIN && h <= MAX) || never || seen)) return;
    try { sessionStorage.setItem("welcome", "1"); } catch (e) {}
    const L = t(), n = (x) => String(x).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    const streets = stNames.filter((x) => x.iv.some((v) => v[2]) || (x.undated && x.undated.length)).length;
    const fill = (txt) => txt.replace("{objects}", n(monuments ? monuments.features.length : 0)).replace("{events}", n(histEvents.length)).replace("{streets}", n(streets));
    openInfo((body) => {
      infoLine(body, L.welIntro, "");
      for (const k of ["welI1", "welI2", "welI3"]) infoLine(body, "• " + fill(L[k]), "small");
      infoLine(body, L.welHonest, "small");
      infoLine(body, L.welReport, "small");
      const row = document.createElement("div");
      row.className = "row";
      row.style.cssText = "display:flex;flex-wrap:wrap;gap:8px";
      const tour = document.createElement("button"), ok = document.createElement("button"), no = document.createElement("button");
      tour.type = ok.type = no.type = "button";
      tour.className = "chip primary";
      ok.className = no.className = "chip";
      tour.textContent = L.tourBtn;
      ok.textContent = L.welOk;
      no.textContent = L.welNever;
      tour.addEventListener("click", () => { closeInfo(); runTour(); });
      ok.addEventListener("click", closeInfo);
      no.addEventListener("click", () => { try { localStorage.setItem("welcome", "1"); } catch (e) {} closeInfo(); });
      row.append(tour, ok, no);
      body.appendChild(row);
    }, false, L.welTitle);
  }
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
  // "Where am I" and "what is near me" (phone, also in the installed PWA): the blue dot of the browser position and a list of the nearest objects and events.
  // The position stays in the browser: nothing is sent anywhere. The list is built from the data that are already on the page.
  let lastGeo = null;
  const geoCtl = new maplibregl.GeolocateControl({ positionOptions: { enableHighAccuracy: true, timeout: 15000 }, trackUserLocation: true, showUserHeading: true, showAccuracyCircle: true });
  map.addControl(geoCtl, "top-right");
  geoCtl.on("geolocate", (e) => { lastGeo = { lat: e.coords.latitude, lng: e.coords.longitude, acc: e.coords.accuracy, t: Date.now() }; });
  let nearBtn = null;
  map.addControl({
    onAdd() {
      const box = document.createElement("div"); box.className = "maplibregl-ctrl maplibregl-ctrl-group";
      nearBtn = document.createElement("button"); nearBtn.type = "button"; nearBtn.className = "nearctl"; nearBtn.textContent = "\uD83D\uDEB6";
      nearBtn.addEventListener("click", askNear); box.appendChild(nearBtn); updateLocTitles(); return box;
    },
    onRemove() {},
  }, "top-right");
  function updateLocTitles() {
    const g = document.querySelector(".maplibregl-ctrl-geolocate");
    if (g) { g.title = t().lcTitle; g.setAttribute("aria-label", t().lcTitle); }
    if (nearBtn) { nearBtn.title = t().nrBtnT; nearBtn.setAttribute("aria-label", t().nrBtnT); }
  }
  updateLocTitles();
  function askNear() {
    if (lastGeo && Date.now() - lastGeo.t < 30000) { showNear(lastGeo); return; }
    const denied = () => openInfo((body) => { $("imTitle").textContent = t().nrTitle; infoLine(body, t().nrDenied); });
    if (!navigator.geolocation) { denied(); return; }
    navigator.geolocation.getCurrentPosition((g) => { lastGeo = { lat: g.coords.latitude, lng: g.coords.longitude, acc: g.coords.accuracy, t: Date.now() }; showNear(lastGeo); }, denied, { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 });
  }
  function showNear(pos) {
    const L = t(), k = Math.cos(pos.lat * Math.PI / 180), list = [];
    reopenInfo = () => showNear(pos);
    const fns = activeFns();
    const dist = (lng, lat) => { const dx = (lng - pos.lng) * k * 111320, dy = (lat - pos.lat) * 111320; return { d: Math.hypot(dx, dy), br: (Math.atan2(dx, dy) * 180 / Math.PI + 360) % 360 }; };
    for (const f of (monuments ? monuments.features : [])) {
      const p = f.properties;
      if (!regVisible(p, fns)) continue;
      const [lng, lat] = f.geometry.coordinates;
      list.push({ p, lng, lat, ...dist(lng, lat) });
    }
    for (const ev of histEvents) if (ev.place) list.push({ ev, lng: ev.place.lng, lat: ev.place.lat, ...dist(ev.place.lng, ev.place.lat) });
    list.sort((a, b) => a.d - b.d);
    const ARROWS = ["\u2191", "\u2197", "\u2192", "\u2198", "\u2193", "\u2199", "\u2190", "\u2196"];
    const fmt = (d) => d < 1000 ? Math.round(d / 10) * 10 + " " + L.unitM : (d / 1000).toFixed(1) + " " + L.unitKm;
    openInfo((body) => {
      $("imTitle").textContent = L.nrTitle;
      infoLine(body, L.nrHint + (pos.acc ? " (" + L.nrAcc + " " + Math.round(pos.acc) + " " + L.unitM + ")" : ""), "small");
      if (!list.length) { infoLine(body, L.nrNone); return; }
      if (list[0].d > 30000) infoLine(body, L.nrFar);
      for (const it of list.slice(0, 15)) {
        const b = document.createElement("button");
        b.type = "button"; b.className = "chip"; b.style.cssText = "display:block;width:100%;text-align:left;margin:4px 0";
        const head = ARROWS[Math.round(it.br / 45) % 8] + " " + fmt(it.d) + " \u00B7 ";
        if (it.ev) {
          const nm = it.ev.place[lang] || it.ev.place.en;
          b.textContent = head + "\uD83D\uDCC5 " + it.ev.date + " \u00B7 " + nm;
          b.addEventListener("click", () => { year = it.ev.year; update(); showHistEvent(it.ev); });
        } else {
          let nm = it.p.name || "", ad = it.p.address || "";
          try { if (window.GeoTr) { nm = window.GeoTr.nameInfo(it.p.name, lang, it.p.wp).text || nm; ad = window.GeoTr.address(it.p.address, lang) || ad; } } catch (e) {}
          b.textContent = head + nm + (ad ? " \u00B7 " + ad : "");
          b.addEventListener("click", () => { closeInfo(); map.flyTo({ center: [it.lng, it.lat], zoom: 17, duration: 1000 }); popup(it.p, { lng: it.lng, lat: it.lat }); });
        }
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
  const fbRef = (kind, id, el) => ({ id: kind + ":" + (id == null ? "-" : id), name: ((el.querySelector("h3") || {}).textContent || "").slice(0, 80), reg: "-", link: OBJ_PREFIX[kind] && id != null ? OBJ_PREFIX[kind] + ":" + id : "" });
  const OBJ_PREFIX = { REL: "rl", SCI: "sc", EDU: "ed" };
  function objLink(id) { const u = new URL(location.href); u.searchParams.set("o", id); return u.toString(); }
  async function shareObject(id, a) {                                         // a phone: the share window; elsewhere: the clipboard
    const url = objLink(id);
    try {
      if (navigator.share && window.matchMedia("(max-width:900px)").matches) await navigator.share({ url });
      else { await navigator.clipboard.writeText(url); a.textContent = "\u2713"; setTimeout(() => { a.textContent = "\uD83D\uDD17"; }, 1600); }
    } catch (e) { if (e && e.name !== "AbortError") window.prompt(t().linkTitle, url); }
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
    if (openDetails) box.appendChild(a1);                          // a card without details has the report link only
    box.appendChild(a2);
    if (fbObj && fbObj.link) {                                                  // the link to THIS object (not to the year and the view of the map)
      const a3 = document.createElement("a");
      a3.href = "#"; a3.className = "fb"; a3.textContent = "\uD83D\uDD17"; a3.title = t().linkObjTitle || t().linkTitle; a3.setAttribute("aria-label", a3.title); a3.id = "objShare";
      a3.addEventListener("click", (ev) => { ev.preventDefault(); shareObject(fbObj.link, a3); });
      box.appendChild(a3);
      el.dataset.obj = fbObj.link;                                              // showPopup puts it into the address bar while the card is open
    }
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
      if (f.w && f.h) { img.width = f.w; img.height = f.h; }                    // the size from the data: the card does not jump when the picture arrives (CLS)
      a.appendChild(img);
      fig.appendChild(a);
      a.title = [f.author || "", f.license || ""].filter(Boolean).join(" · ");
      box.appendChild(fig);
    });
  }
  // the line under the photographs of a card: author, licence and the page of the file on Commons
  async function fillPhotoCredits(box, p) {
    try { if (!photoInfo) photoInfo = await getJSON("data/photos.json"); } catch (e) { return; }
    const titles = String(p.ph).split("|").filter((x) => photoInfo[x] && photoInfo[x].thumb);
    if (!titles.length) return;
    box.appendChild(document.createTextNode(t().infoPhotos + ": "));
    titles.forEach((ti, i) => {
      const f = photoInfo[ti];
      if (i) box.appendChild(document.createTextNode("; "));
      box.appendChild(document.createTextNode([f.author || "?", f.license || ""].filter(Boolean).join(" · ") + " · "));
      const a = document.createElement("a");
      a.href = f.page; a.target = "_blank"; a.rel = "noopener"; a.textContent = "Commons";
      box.appendChild(a);
    });
  }
  // photographs of Wikimedia Commons (data/photos.json) under the title of a card of a layer (religious buildings, science and culture, education), with the author and the licence
  function cardPhotos(el, c) {
    if (!c.ph) return;
    const pp = { ph: c.ph, name: c.name[lang] || c.name.en };
    addPhotos(el, pp);
    const cr = document.createElement("div");
    cr.className = "small phcred";
    el.appendChild(cr);
    fillPhotoCredits(cr, pp);
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
    actions(el, null, fbRef("SET", p.id ?? p.name, el));
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
    actions(el, null, fbRef("WATER", p.id ?? (isRes ? "res" : "lake"), el));
    showPopup("300px", lngLat, el);
  }

  let views = [];
  let viewsSig = "";
  let shownViews = [];                           // the photos offered now (the arrows of the viewer go through them)
  let curView = null;
  const viewTiles = new Map();
  const VIEW_WINDOW = 150;                       // a view is offered for 150 years after its date

  // the tiles of the grid are 130-180 px wide: they load a small copy (site/data/views/thumb/, made by tools/make_view_thumbs.py); the viewer loads the whole picture.
  // Three pictures from Wikimedia have a checked thumbnail address (500 px); the others keep their address.
  const VIEW_THUMB_OK = new Set(["viceroy_palace_1865", "kennan_tiflis_1870s", "ermakov_nevsky"]);
  function viewThumb(v) {
    const u = v.image;
    if (!/^https?:/.test(u)) return u.replace(/^data\/views\/([^/]+?)\.\w+$/, "data/views/thumb/$1.webp");
    if (!VIEW_THUMB_OK.has(v.id)) return u;
    const t = u.replace(/\?.*$/, "");
    let m = t.match(/^(https:\/\/thumb\.wikimedia\.org\/wikipedia\/commons\/thumb\/.+)\/\d+px-([^/]+)$/);
    if (m) return m[1] + "/500px-" + m[2];
    m = t.match(/^https:\/\/upload\.wikimedia\.org\/wikipedia\/commons\/(\w\/\w\w)\/([^/]+)$/);
    return m ? "https://upload.wikimedia.org/wikipedia/commons/thumb/" + m[1] + "/" + m[2] + "/500px-" + m[2] : u;
  }

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
        im.src = viewThumb(v); im.loading = "lazy"; im.alt = "";
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
    if ($("viewModal").hidden) viewFocus = document.activeElement;
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
    $("vmReport").textContent = L.fbPopup;
    $("viewModal").hidden = false;
  }
  function closeView() { const was = !$("viewModal").hidden; $("viewModal").hidden = true; if (was) { giveFocusBack(viewFocus, "#vgrid button", "#btnViews"); viewFocus = null; } }
  $("vmReport").addEventListener("click", () => { const v = curView; closeView(); openFeedback({ id: "view:" + ((v && (v.id || v.image)) || "-"), name: ((v && v.title && (v.title[lang] || v.title.en)) || "").slice(0, 80), reg: "-" }); });
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
    if (year >= 1923 && year <= 1961) {                         // the lines of the plan of 1913 are drawn up to 1922, from 1923 there are none
      const a = Object.keys(TRAM_KM).map(Number).reduce((best, k) => (Math.abs(k - year) < Math.abs(best - year) ? k : best));
      return L.trGapMid(TRAM_KM[a], a);
    }
    return "";
  }
  function updateTransport() {
    const KINDS = { showTrMetro: ["metro_line", "metro_station"], showTrTram: ["tram"], showTrRail: ["railway"], showTrRoad: ["avenue", "road", "bridge"], showTrCable: ["funicular", "cablecar"] };      // the boxes of the group "Transport" and what they switch
    const allowed = Object.keys(KINDS).filter((id) => $(id).checked).flatMap((id) => KINDS[id]);
    const on = allowed.length > 0;
    const LINE = ["!=", ["geometry-type"], "Point"], kind = (...k) => ["match", ["get", "kind"], k, true, false];
    const BASE = { "tr-casing": ["all", LINE, kind("avenue")], "tr-line": ["all", LINE, ["!", kind("funicular", "cablecar")]], "tr-ticks": ["all", LINE, kind("tram")],
      "tr-pt": ["==", ["geometry-type"], "Point"], "tr-pt-m": ["==", ["geometry-type"], "Point"], "tr-funic": ["all", LINE, kind("funicular")], "tr-cable": ["all", LINE, kind("cablecar")] };
    for (const id of TR_IDS) {
      if (!map.getLayer(id)) continue;
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["all", BASE[id], trFilter(), on ? kind(...allowed) : ["==", 1, 0]]);
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

  // the former names of the stations of the metro (data/metro_names.json, loaded when the card of a station is opened)
  let metroNames = null;
  async function loadMetroNames() {
    if (!metroNames) { try { metroNames = await getJSON("data/metro_names.json", 1); } catch (e) { metroNames = { stations: {}, ui: {} }; } }
    return metroNames;
  }
  // the stations of the metro that were planned and not built: no position on the map, a list with the place, the state and the source
  function openPlannedStations() {
    const M = metroNames || { planned: [], ui: {} }, U = (k) => (M.ui[k] && (M.ui[k][lang] || M.ui[k].en)) || "";
    openInfo((body) => {
      infoLine(body, U("planned_intro"));
      let g = "";
      for (const s of M.planned) {
        if (s.g !== g) { g = s.g; infoLine(body, U("g_" + g), "").style.fontWeight = "600"; }
        const st = s.y ? U("s_stopped").replace("{y}", s.y) : U("s_none");
        infoLine(body, "• " + (s.n[lang] || s.n.en) + " · " + st + " · " + U("place") + ": " + (s.pl[lang] || s.pl.en), "small");
        const d = infoLine(body, U("source") + ": ", "small"), a = document.createElement("a");
        a.href = s.src.u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURI(s.src.u).replace(/^https?:\/\//, "").slice(0, 70); d.appendChild(a);
      }
    }, false, U("planned_title"));
  }
  async function transportPopup(p, lngLat) {
    reopenPopup = () => transportPopup(p, lngLat);
    const L = t();
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    const nowName = p["name_" + lang] || p.name_en || p.name_ru || "—";
    h3.textContent = nowName;
    el.appendChild(h3);
    const add = (txt, cls) => { const d = document.createElement("div"); if (cls) d.className = cls; d.textContent = txt; el.appendChild(d); };
    let former = [], MU = {};
    if (p.kind === "metro_station") {                              // the name of the selected year first, the list of the former names below
      const M = await loadMetroNames();
      former = M.stations[p.id] || [];
      MU = M.ui || {};
      const old = former.find((f) => f.to.length && year < Math.min(...f.to) && (f.from == null || year >= f.from));
      if (old) { h3.textContent = old.n[lang] || old.n.en; add((MU.now ? MU.now[lang] || MU.now.en : "now") + ": " + nowName, "small"); }
    }
    add((L.trKinds[p.kind] || p.kind) + " · " + L.trPeriod(+p.y0, +p.y1, +p.y2, +p.y3));
    if (p.r62) add(L.trRoutes62 + ": " + p.r62);                       // the numbers of the routes that name the street in the list of 1962 / 1986
    if (p.r86) add(L.trRoutes86 + ": " + p.r86);
    let srcs = [];
    try { srcs = JSON.parse(p.src || "[]"); } catch (e) {}
    const U = (k) => (MU[k] && (MU[k][lang] || MU[k].en)) || "";
    if (former.length) {
      add(U("former") + ":", "small");
      for (const f of former) {
        const upto = U("until").replace(/:$/, ""), ty = f.to.join(" / ");
        const yrs = f.from != null ? f.from + "–" + ty : lang === "ka" ? ty + " " + upto : upto + " " + ty;      // Georgian: "1992 წლამდე" (the word after the number)
        add("• " + (f.n[lang] || f.n.en) + " · " + yrs + (f.to.length > 1 ? " (" + U("differ") + ")" : ""), "small");
      }
    }
    const projRows = (p.kind === "metro_station" && (metroNames.project || {})[p.id]) || [];     // the names of the station at the design stage / during construction (Wikipedia, quote checked)
    for (const f of projRows) add("• " + U(f.k) + ": " + (f.n[lang] || f.n.en), "small");
    if (p.kind === "metro_station" && (metroNames.planned || []).length) {                  // the list of the stations that were planned and not built
      const d = document.createElement("div"), a = document.createElement("a");
      d.className = "small"; a.href = "#"; a.textContent = U("planned_btn");
      a.addEventListener("click", (ev) => { ev.preventDefault(); openPlannedStations(); });
      d.appendChild(a); el.appendChild(d);
    }
    const linkLine = (body, u) => { const d = infoLine(body, "", "small"), a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURI(u); d.appendChild(a); };
    actions(el, () => openInfo((body) => {
      if (p.note) infoLine(body, p.note);
      for (const f of projRows) { infoLine(body, (f.n[lang] || f.n.en) + ":"); if (f.src.u) linkLine(body, f.src.u); else infoLine(body, U("enc") + " " + f.src.p, "small"); }
      for (const f of former) {                                    // the sources of the former names: the encyclopedia with the page (text) or the page of a site (link)
        infoLine(body, (f.n[lang] || f.n.en) + ":");
        for (const x of f.src) {
          if (x.t === "enc") infoLine(body, U("enc") + " " + x.p, "small");
          else { const d = infoLine(body, "", "small"), a = document.createElement("a"); a.href = x.u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURI(x.u); d.appendChild(a); }
        }
      }
      if (srcs.length) infoLine(body, "Wikipedia:");
      srcs.forEach((u) => { const d = document.createElement("div"); d.className = "small"; const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURIComponent(u); d.appendChild(a); body.appendChild(d); });
      infoLine(body, "OpenStreetMap contributors (ODbL): geometry");
    }), { id: p.id, name: p.name_en, reg: "-", link: p.kind === "metro_station" ? "ms:" + p.id : "" });
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
    if ($("fbModal").hidden) fbFocus = document.activeElement;
    fbObject = obj || null;
    $("fbStatus").textContent = "";
    $("fbMsg").value = "";
    feedbackRefreshCtx();
    fbOpenedAt = Date.now(); $("fbStatus").textContent = ""; fbTsReset();
    $("fbModal").hidden = false;
    $("fbMsg").focus();
  }
  function closeFeedback() { const was = !$("fbModal").hidden; $("fbModal").hidden = true; if (was) { giveFocusBack(fbFocus, "#fbOpen"); fbFocus = null; } }

  // the form sends the message to the private queue of the author (Worker /feedback): Turnstile, the time the form was open and a hidden field protect it; GitHub is the reserve
  let fbToken = "", fbTsId = null, fbOpenedAt = 0;
  function fbTsLoad() {
    return new Promise((res) => {
      if (window.turnstile) return res();
      if (!document.querySelector('script[src^="https://challenges.cloudflare.com/turnstile"]')) {
        const s = document.createElement("script");
        s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"; s.async = true; s.onerror = () => res();
        document.head.appendChild(s);
      }
      let n = 0;
      const w = setInterval(() => { if (window.turnstile || ++n > 50) { clearInterval(w); res(); } }, 100);
    });
  }
  async function fbTsReset() {
    fbToken = "";
    if (!cfg.feedbackEndpoint || !cfg.turnstileSitekey) return;
    await fbTsLoad();
    if (!window.turnstile) return;
    if (fbTsId !== null) { try { window.turnstile.remove(fbTsId); } catch (e) {} fbTsId = null; }
    $("fbTs").textContent = "";
    fbTsId = window.turnstile.render($("fbTs"), { sitekey: cfg.turnstileSitekey, theme: "auto", callback: (tk) => { fbToken = tk; }, "expired-callback": () => { fbToken = ""; }, "error-callback": () => { fbToken = ""; } });
  }
  $("fbOpen").addEventListener("click", () => openFeedback(null));
  {                                                                  // ?report=entrances | run : the other pages of the site have no form of their own, the visitor comes here with the name of the page
    const rp = new URLSearchParams(location.search).get("report");
    if (rp && /^[a-z]{2,12}$/.test(rp)) {
      history.replaceState(null, "", location.pathname + location.search.replace(/([?&])report=[^&]*&?/, "$1").replace(/[?&]$/, "") + location.hash);
      setTimeout(() => { closeInfo(); openFeedback({ id: "page:" + rp, name: "page " + rp, reg: "-" }); }, 700);
    }
  }
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
      if (cfg.turnstileSitekey && !fbToken) { $("fbStatus").textContent = t().fbCaptcha; return; }
      try {
        const r = await fetch(cfg.feedbackEndpoint, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ ...payload, t: fbOpenedAt, hp: $("fbTrap").value, "cf-turnstile-response": fbToken }) });
        const j = await r.json().catch(() => ({}));
        if (r.ok && j.ok) { $("fbStatus").textContent = t().fbSent; fbToken = ""; setTimeout(closeFeedback, 1800); return; }
        // the service answered but refused: say why (the reserve with GitHub is for the case when the service cannot be reached at all)
        $("fbStatus").textContent = j.error === "captcha" ? t().fbCaptcha : (j.error === "limit" || j.error === "busy") ? t().fbLimit : j.error === "time" ? t().fbWait : t().fbFail;
        fbTsReset();
        return;
      } catch (err) { /* the service cannot be reached: fall through to GitHub */ }
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
    const tight = window.matchMedia("(min-width:641px) and (max-width:899px)");     // a tablet: the views panel would lie over the info panel
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
      if (tight.matches && st[k] && (k === "views" || k === "info")) st[k === "views" ? "info" : "views"] = false;
      apply();
    };
    btns.info.addEventListener("click", () => toggle("info"));
    btns.filters.addEventListener("click", () => toggle("filters"));
    btns.views.addEventListener("click", () => toggle("views"));
    if (tight.matches && st.info && st.views) st.views = false;
    tight.addEventListener("change", () => { if (tight.matches && st.info && st.views) { st.views = false; apply(); } });
    for (const b of document.querySelectorAll(".pclose")) b.addEventListener("click", () => toggle(b.dataset.panel, false));
    window.TT_panels = { get: (k) => !!st[k], set: (k, on) => toggle(k, on) };       // the tour opens the panel of the filters for its steps about them and closes it again
    window.TT_closePanels = () => { if (!mq.matches) return; let any = false; for (const k of KEYS) if (st[k]) { st[k] = false; any = true; } if (any) apply(); };
    // on a phone a tap on the map beside an open panel or the search window closes it (the windows of the modal kind close by a tap on their backdrop)
    document.addEventListener("pointerdown", (e) => {
      if (!mq.matches || !e.target.closest || e.target.closest("#side, #filters, #views, #top, #timebar, #search, .modal, .maplibregl-popup, .maplibregl-ctrl, #tour, button, a, input, select, label, summary")) return;      // a tap on an empty place (the map, the band at the bottom), not on a panel, a control or a window
      window.TT_closePanels();
      if (!$("search").hidden) closeSearch();
    }, true);
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
  // a link ?o=<kind>:<id> opens the card of that object (rl religious, sc science and culture, ed education, pl local names, mn monuments, pq plaques, ms metro station, st street)
  async function openLinked(o) {
    const [kind, ...r] = o.split(":"), id = r.join(":");
    const go = (c, pop, y) => { if (y != null && Number.isFinite(y)) year = Math.max(year, y); update(); map.jumpTo({ center: [c.lon, c.lat], zoom: 17 }); pop(c, { lng: c.lon, lat: c.lat }); };
    try {
      if (kind === "o") { const f = monAllById.get(id); if (f) { if (typeof f.properties.ye === "number") year = Math.max(year, f.properties.ye); update(); map.jumpTo({ center: f.geometry.coordinates, zoom: 17 }); popup(f.properties, { lng: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }); } }
      else if (kind === "rl") { if (relOsmLoading) await relOsmLoading; const c = religious.find((x) => x.id === id); if (c) { $("showRel").checked = true; go(c, popupRel, c.undated ? undefined : c.from); } }
      else if (kind === "sc") { const c = science.find((x) => x.id === id); if (c) { $("showSci").checked = true; go(c, popupSci, c.from); } }
      else if (kind === "ed") { const c = education.find((x) => x.id === id); if (c) { $("showEdu").checked = true; go(c, popupEdu, c.from); } }
      else if (kind === "mu") { const c = museums.find((x) => x.id === id); if (c) { $("showMus").checked = true; go(c, popupMus, c.from); } }
      else if (kind === "pl") { await ensurePlaces(); const c = places && places.items.find((x) => x.id === id); if (c) { $("showPlaces").checked = true; updatePlaces(); go(c, popupPlace); } }
      else if (kind === "mn" || kind === "pq" || kind === "md") {
        const key = kind === "mn" ? "mon" : kind === "md" ? "mod" : "plq", m = MP[key];
        await mpLoad(key);
        const c = m.byId && m.byId.get(id);
        if (c) { $(m.chk).checked = true; if (c.y == null && m.sub) $(m.sub).checked = true; updateMP(key); go(c, (cc, ll) => popupMP(key, cc, ll), c.y); }
      } else if (kind === "ms") {
        const f = trStations.find((x) => x.properties.id === id);
        if (f) { year = Math.max(year, f.properties.y0); update(); map.jumpTo({ center: f.geometry.coordinates, zoom: 16 }); transportPopup({ ...f.properties, src: JSON.stringify(f.properties.src || []) }, { lng: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }); }
      } else if (kind === "st") {
        const st = stNames.find((x) => (x.geom || x.now.en) === id);
        if (st) showStreetCard(st, true);
      }
    } catch (e) { console.error("link", o, e && e.message); }
  }
  // The cards under one click: a building of the register, a place, a monument, a plaque, a building of modernism, a religious building ... lie on one point. One card is opened (the others are not), and it gets a row
  // "Also here" with the other objects of the layers that are switched on within 14 px; a tap on a name opens that card in the same place (and the row stays, to come back).
  const NEAR_PX = 14;
  function nearCandidates(pt) {
    const box = [[pt.x - NEAR_PX, pt.y - NEAR_PX], [pt.x + NEAR_PX, pt.y + NEAR_PX]], out = [], seen = new Set();
    const q = (layer) => (map.getLayer(layer) && map.getLayoutProperty(layer, "visibility") !== "none") ? map.queryRenderedFeatures(box, { layers: [layer] }) : [];
    const add = (key, label, open) => { if (key && label && !seen.has(key)) { seen.add(key); out.push({ key, label, open }); } };
    for (const f of q("mon")) { const p = f.properties; let nm = p.name || ""; try { if (window.GeoTr) nm = window.GeoTr.nameInfo(p.name, lang, p.wp).text || nm; } catch (er) {} add(String(p.id), nm, (ll) => popup(p, ll)); }
    for (const f of q("rel-pt")) { const r = religious.find((x) => x.id === f.properties.id); if (r) add("rl:" + r.id, relTitle(r), (ll) => popupRel(r, ll)); }
    for (const f of q("sci-pt")) { const c = science.find((x) => x.id === f.properties.id); if (c) add("sc:" + c.id, c.name[lang] || c.name.en, (ll) => popupSci(c, ll)); }
    for (const f of q("edu-pt")) { const c = education.find((x) => x.id === f.properties.id); if (c) add("ed:" + c.id, c.name[lang] || c.name.en, (ll) => popupEdu(c, ll)); }
    for (const f of q("mus-pt")) { const c = museums.find((x) => x.id === f.properties.id); if (c) add("mu:" + c.id, c.name[lang] || c.name.en, (ll) => popupMus(c, ll)); }
    for (const f of q("places-pt")) { const c = places && places.items.find((x) => x.id === f.properties.id); if (c) add("pl:" + c.id, placeName(c), (ll) => popupPlace(c, ll)); }
    for (const [key, pre] of [["mon", "mn:"], ["plq", "pq:"], ["mod", "md:"]]) for (const f of q(key + "-pt")) { const c = MP[key].byId && MP[key].byId.get(f.properties.id); if (c) add(pre + c.id, mpName(key, c), (ll) => popupMP(key, c, ll)); }
    return out;
  }
  let nearCarry = null;                                              // the list of the objects of the point, kept for the card that a tap on a name opens (the map may have moved: the point of the click no longer says what lies there)
  function addNearby(pop, el, lngLat) {
    const now = Date.now();
    let all;
    if (nearCarry && now - nearCarry.t < 700) all = nearCarry.all;
    else if (lastClick && now - lastClick.t < 700) all = nearCandidates(lastClick.point);
    nearCarry = null;
    if (!all) return;
    const cur = el.dataset && el.dataset.obj, others = all.filter((c) => c.key !== cur).slice(0, 6);
    if (!others.length || !all.some((c) => c.key === cur)) return;     // only a card that is one of the objects found under the click gets the row
    const row = document.createElement("div");
    row.className = "nearby small";
    row.appendChild(document.createTextNode(t().nearHere + ": "));
    others.forEach((c, i) => {
      if (i) row.appendChild(document.createTextNode(" · "));
      const a = document.createElement("a");
      a.href = "#"; a.textContent = c.label;
      a.addEventListener("click", (ev) => { ev.preventDefault(); nearCarry = { t: Date.now(), all }; pop.remove(); c.open(lngLat); });
      row.appendChild(a);
    });
    el.appendChild(row);
  }
  function showPopup(maxWidth, lngLat, el) {
    const pop = new maplibregl.Popup({ maxWidth, focusAfterOpen: false }).setLngLat(lngLat).setDOMContent(el).addTo(map);
    addNearby(pop, el, lngLat);
    openPop = pop;
    if (el.dataset && el.dataset.obj && !/^\d+$/.test(el.dataset.obj)) setObjParam(el.dataset.obj, pop);      // ?o=<kind>:<id> while the card is open (the register sets its own plain number)
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
    // the card is fitted into the free area (between the bars) when the camera is still: during a flight (a card opened from the search) a pan would stop the flight,
    // and a fit made on the way would be wrong at the end of it
    const fitWhenStill = () => {
      if (map.isMoving()) map.once("moveend", () => { if (openPop === pop) setTimeout(fit, 30); });
      else fit();
    };
    requestAnimationFrame(() => requestAnimationFrame(fitWhenStill));
    if (window.ResizeObserver) {                      // photos load later and make the card taller: fit again
      const content = pop.getElement().querySelector(".maplibregl-popup-content");
      let t = null;
      const ro = new ResizeObserver(() => { clearTimeout(t); t = setTimeout(() => { if (!map.isMoving()) fit(); }, 60); });
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
    if (window.TT_closePanels) window.TT_closePanels();          // a phone: the card takes the place of the open panel
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
    }), { id: p.id, name: p.name, reg: p.reg, link: String(p.id) });
    addPhotoLink(el, "mon:" + p.id, !p.ph);
    setObjParam(p.id, showPopup("300px", lngLat, el));
    addNamesakeTo(el, "M" + p.id);
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
  // version and the log of changes: the button shows the version from the small data/version.json (made by tools/build_version.py from the first entry of the log: the log itself is 180 KB and is
  // loaded only when the button is pressed, so it does not weigh on the first screen); the button opens the log in the modal window
  let changelog = null, curVersion = null;
  async function loadChangelog() {
    try { curVersion = (await getJSON("data/version.json", 1)).version; } catch (e) { curVersion = null; }
    updateVersionBtn();
  }
  function updateVersionBtn() {
    const b = $("btnVersion");
    if (!b) return;
    b.textContent = curVersion ? "v" + curVersion.replace(/\.0$/, "") : "v?";
    b.title = t().chgTitle;
    b.setAttribute("aria-label", t().chgTitle);
  }
  async function showChangelog() {
    reopenInfo = () => showChangelog();
    if (!changelog) { try { changelog = await getJSON("data/changelog.json", 1); } catch (e) { changelog = null; } }
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
  $("pagesSel").addEventListener("change", (e) => { if (e.target.value !== "./") location.href = e.target.value + "?lang=" + lang; });

  // the labels of the page at once, before the data are there (applyLang does the whole job later)
  try {
    document.title = t().title;
    $("title").textContent = t().title;
    $("lang").value = lang;
    document.querySelectorAll("[data-i]").forEach((el) => { if (typeof t()[el.dataset.i] === "string") el.textContent = t()[el.dataset.i]; });
  } catch (e) { /* applyLang will do it */ }
  setLoading("loadMap");
  prefetchJSON(["education", "plans", "monuments", "city_area", "views", "names_i18n", "urban", "water", "density", "transport", "transport_events", "history_events", "population", "run_trc2026", "rulers_media", "rulers", "science", "religious", "city1894", "street_names", "street_geom", "admin", "admin_old", "districts", "district_history", "settlements", "lost"].map((n) => "data/" + n + ".json"));

  // the lazy layers (places, monuments, plaques, modernism) are loaded when their box is ticked or the search is opened; here they are loaded quietly when the first screen is drawn and the browser is idle (not on a slow
  // connection or with the data saver), so that the search finds their objects at once. The tests (?e2e) keep them lazy, ?idleload=1 switches this on for the test of this very thing.
  map.once("idle", () => {
    const q = new URLSearchParams(location.search), cn = navigator.connection || {};
    if ((q.has("e2e") && !q.has("idleload")) || q.has("noidle") || cn.saveData || /^(slow-2g|2g|3g)$/.test(cn.effectiveType || "")) return;
    const go = () => { ensurePlaces(); mpLoad("mon"); mpLoad("plq"); mpLoad("mod"); };
    if (window.requestIdleCallback) requestIdleCallback(go, { timeout: 6000 }); else setTimeout(go, 3000);
  });
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
    monAllById = new Map();
    for (const f of mon.features) {
      const p = f.properties;
      monAllById.set(String(p.id), f);
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
      trStations = tr.features.filter((f) => f.properties.kind === "metro_station");
      map.addSource("transport", { type: "geojson", data: tr });
      const metroColor = ["match", ["get", "line"], "2", "#2f9e44", "#e03131"];     // line 1 (Akhmeteli-Varketili) red, line 2 (Saburtalo) green
      const kindColor = ["match", ["get", "kind"], "metro_line", metroColor, "railway", "#343a40", "avenue", "#f08c00", "road", "#e8a33d", "bridge", "#1c7ed6", "tram", "#5a2d0c", "#495057"];
      // the signs follow the topographic maps (conditional signs for the maps 1:25000-1:100000, 1983, tables 14 and 15): the avenue is a road with a dark casing and an orange fill (sign 106),
      // the railway a solid dark line (90), the tram the thinnest line with cross ticks (94), the funicular a thin line of long dashes (95.2), the cable car dashes and dots (95.1),
      // the metro station a circle with the letter M (103). The tram drawn from the route lists (street along its whole length) is paler than the lines read from the plan of 1913 ("prec").
      const trAlpha = ["case", ["all", ["==", ["get", "kind"], "tram"], ["!", ["has", "prec"]]], 0.5, 0.92];
      const LINE = ["!=", ["geometry-type"], "Point"], POINT = ["==", ["geometry-type"], "Point"];
      const add = (id, type, filter, layout, paint) => map.addLayer({ id, type, source: "transport", filter, layout: { visibility: "none", ...layout }, paint });
      add("tr-casing", "line", LINE, { "line-cap": "round" }, { "line-color": "#3d2b10", "line-width": 5.5 });
      add("tr-line", "line", LINE, { "line-cap": "round" }, { "line-color": kindColor, "line-width": ["match", ["get", "kind"], "railway", 2, "avenue", 3, "road", 2.2, "tram", 1.3, 3.5], "line-offset": ["match", ["get", "kind"], "tram", 4, 0], "line-opacity": trAlpha });
      add("tr-ticks", "line", LINE, { "line-cap": "butt" }, { "line-color": "#5a2d0c", "line-width": 5, "line-offset": 4, "line-dasharray": [0.25, 1.1], "line-opacity": trAlpha });
      add("tr-pt", "circle", POINT, {}, { "circle-radius": 7, "circle-color": "#fff", "circle-stroke-color": metroColor, "circle-stroke-width": 2 });
      add("tr-pt-m", "symbol", POINT, { "text-field": "M", "text-font": ["Noto Sans Bold"], "text-size": 10, "text-allow-overlap": true, "text-ignore-placement": true }, { "text-color": metroColor });
      add("tr-funic", "line", LINE, { "line-cap": "butt" }, { "line-color": "#7048e8", "line-width": 2.2, "line-dasharray": [5, 1.2] });
      add("tr-cable", "line", LINE, { "line-cap": "butt" }, { "line-color": "#7048e8", "line-width": 2.4, "line-dasharray": [3, 1.2, 0.5, 1.2] });
      for (const id of TR_IDS.filter((x) => x !== "tr-casing" && x !== "tr-ticks" && x !== "tr-pt-m")) {
        map.on("mouseenter", id, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", id, () => { map.getCanvas().style.cursor = ""; });
      }
      // one click handler for all transport: the lines lie on one another (the tram is drawn 4 px beside the street, an avenue, a bridge and a railway can run along it), so
      // the object of the highest rank within a few pixels is taken: a tram before a metro line, a bridge before an avenue (found out 2026-11-19: on Chavchavadze Avenue the avenue took the click)
      const TR_PRIO = ["tram", "metro_station", "metro_line", "funicular", "cablecar", "railway", "bridge", "avenue", "road"];
      const POINT_LAYERS = ["mon", "rel-pt", "sci-pt", "lost-dot", "settle-dot", "mod-pt", "mon-pt", "plq-pt", "places-pt", "battle-pt"];
      map.on("click", (e) => {
        const near = (r) => [[e.point.x - r, e.point.y - r], [e.point.x + r, e.point.y + r]];
        const hits = map.queryRenderedFeatures(near(5), { layers: ["tr-line", "tr-pt", "tr-funic", "tr-cable"].filter((id) => map.getLayer(id)) });
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
    try { histEvents = (await getJSON("data/history_events.json", 2)).events; buildEvMarks(); addBattleMap(); } catch (e) { histEvents = []; }
    try { popData = await getJSON("data/population.json", 2); updatePop(); } catch (e) { popData = null; }
    try { rulersMedia = await getJSON("data/rulers_media.json", 1); } catch (e) { rulersMedia = null; }
    try { rulersData = await getJSON("data/rulers.json", 1); buildRulersBand(); updateRuleLine(); } catch (e) { console.error("rulers", e && e.message); rulersData = null; }
    try { science = await getJSON("data/science.json", 1); addScience(); } catch (e) { console.error("science", e && e.message); science = []; }
    try { education = await getJSON("data/education.json", 1); addEducation(); } catch (e) { console.error("education", e && e.message); education = []; }
    try { museums = await getJSON("data/museums.json", 1); addMuseums(); } catch (e) { console.error("museums", e && e.message); museums = []; }
    try { religious = await getJSON("data/religious.json", 1); addReligious(); loadReligiousOsm(); } catch (e) { console.error("religious", e && e.message); religious = []; }
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
      const own = ["mod-pt", "places-pt", "mon-pt", "plq-pt"].filter((id) => map.getLayer(id) && map.getLayoutProperty(id, "visibility") === "visible");
      if (own.length && map.queryRenderedFeatures(e.point, { layers: own }).length) return;      // a point of a layer that is switched on (modernism, local names, monuments, plaques) under the click has its own card (two cards at one place are not opened)
      popup(e.features[0].properties, e.lngLat);
    });
    map.on("mouseenter", "mon", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "mon", () => { map.getCanvas().style.cursor = ""; });

    for (const id of ["stl-line", "stl-pt", "c94-pt", "c94-lb"]) if (map.getLayer(id)) map.moveLayer(id);   // overlays (old street names, 1894 objects) above the old plans
    buildTicks(); buildEpochBand();
    applyLang();
    try {                                              // a link with ?o=<id> opens that object card
      const oid = new URL(location.href).searchParams.get("o");
      const f = oid && monuments.features.find((x) => String(x.properties.id) === oid);
      if (f) {
        year = Math.max(year, f.properties.ye);
        update();
        map.jumpTo({ center: f.geometry.coordinates, zoom: 17 });
        popup(f.properties, { lng: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] });
      } else if (oid && /^[a-z]{1,2}:/.test(oid)) openLinked(oid);
    } catch (e) {}
    dataReady = true;
    loadChangelog();
    maybeWelcome();
    if (map.loaded()) hideLoading(); else map.once("idle", hideLoading);
  });

  window.addEventListener("hashchange", () => {
    const hy = parseInt((location.hash || "").slice(1), 10);
    if (hy >= MIN && hy <= MAX && hy !== year) { year = hy; update(); }
  });
  $("slider").addEventListener("input", (e) => { const y = v2y(+e.target.value); if (y !== year) { year = y; sliding = true; try { update(); } finally { sliding = false; } } });
  for (const id of ["showPlan", "showStLabels", "roadLabels", "show94", "showRel", "showSci", "showEdu", "showMus", "showBattleMap", "showRulers", "showBnd", "showAdmin", "showDistricts", "showSettle", "showWater", "showDensity", "showTrMetro", "showTrTram", "showTrRail", "showTrRoad", "showTrCable", "showStreets", "showSwipe", "showHere", "showLost", "showGhost", "showResid", "showPublic", "showDef", "showOtherB", "showNoPhoto"]) $(id).addEventListener("change", update);
  $("op").addEventListener("input", (e) => {
    $("opv").textContent = e.target.value + "%";
    for (const p of plans) if (map.getLayer("plan-" + p.id)) map.setPaintProperty("plan-" + p.id, "raster-opacity", planOpacity());
    if (map.getLayer("topo")) map.setPaintProperty("topo", "raster-opacity", topoOpacity());
  });
  // ---- the panel "Filters and layers": all / none of the types, a hint for an empty choice, "Reset filters"
  // The defaults are those of the markup (checked, value, selected), except the band of rulers: the script turns it on for a wide screen (see below).
  function filterDefaults() {
    const d = {};
    for (const el of document.querySelectorAll("#filters input[type=checkbox][id]")) d[el.id] = el.defaultChecked;
    d.showRulers = window.innerWidth > 900;
    return d;
  }
  function filtersAtDefault() {
    const d = filterDefaults();
    for (const el of document.querySelectorAll("#filters input[type=checkbox][id]")) if (el.checked !== d[el.id]) return false;
    for (const el of document.querySelectorAll("#filters input[type=range]")) if (el.value !== el.defaultValue) return false;
    const sel = $("topoSel");
    if (sel && !sel.options[sel.selectedIndex].defaultSelected) return false;
    return true;
  }
  function syncLegend(chkId, boxId) { const b = $(boxId); if (b) b.hidden = !$(chkId).checked; syncFilterUi(); }
  function syncFilterUi() {
    const rb = $("filtersReset");
    if (rb) rb.disabled = filtersAtDefault();
    for (const sec of document.querySelectorAll("#filters details.fsec")) {      // "switched on / all" of every block (a half-ticked box of the automatic topographic map counts as on)
      const cnt = sec.querySelector(".cnt");
      if (!cnt) continue;
      let on = 0, all = 0;
      for (const cb of sec.querySelectorAll("input[type=checkbox]:not(.gmaster)")) {      // the master box of a group is not counted: its boxes are
        let off = false;                                                    // hidden inside the block (a row that appears on demand); the panel itself may be closed (a phone)
        for (let e = cb; e && e !== sec; e = e.parentElement) if (e.hidden && !e.classList.contains("gmkids")) { off = true; break; }      // a closed group is not "hidden": its boxes count
        if (off) continue;
        all++;
        if (cb.checked || cb.indeterminate) on++;
      }
      cnt.textContent = on + "/" + all;
    }
  }
  function resetFilters() {
    const d = filterDefaults();
    for (const el of document.querySelectorAll("#filters input[type=checkbox][id]")) {
      if (el.id === "showRulers" || el.checked === d[el.id]) continue;
      el.checked = d[el.id];
      el.dispatchEvent(new Event("change", { bubbles: true }));
    }
    if ($("showRulers").checked !== d.showRulers) setRulersOn(d.showRulers);
    for (const el of document.querySelectorAll("#filters input[type=range]")) {
      if (el.value === el.defaultValue) continue;
      el.value = el.defaultValue;
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
    const sel = $("topoSel");
    if (sel) {
      const i = Array.from(sel.options).findIndex((o) => o.defaultSelected);
      if (i >= 0 && sel.selectedIndex !== i) { sel.selectedIndex = i; sel.dispatchEvent(new Event("change", { bubbles: true })); }
    }
  }
  // Groups of boxes in the panel ("Register buildings by use", "Science, culture and education", "Monuments and plaques"): a master box (no id: the reset and the counters do not see it) switches all the
  // boxes of the group, is half-ticked when only some are on and follows them; the arrow opens the list. The boxes keep their ids, so nothing else in the code or in the links changes.
  for (const g of document.querySelectorAll("#filters .gm")) {
    const master = g.querySelector(".gmaster"), kids = [...g.querySelectorAll(".gmkids input[type=checkbox][id]")].filter((k) => !k.closest(".sub2"));
    const sync = () => { const n = kids.filter((k) => k.checked).length; master.checked = n === kids.length; master.indeterminate = n > 0 && n < kids.length; };
    master.addEventListener("change", () => {
      const on = master.checked;                                      // taken once: every box that is switched makes the master half-ticked again (sync), the next box must still get the same state
      for (const k of kids) if (k.checked !== on) { k.checked = on; k.dispatchEvent(new Event("change", { bubbles: true })); }
      sync();
    });
    for (const k of kids) k.addEventListener("change", sync);
    const tg = g.querySelector(".gmtoggle"), box = g.querySelector(".gmkids");
    tg.addEventListener("click", () => { box.hidden = !box.hidden; tg.setAttribute("aria-expanded", String(!box.hidden)); tg.textContent = box.hidden ? "▸" : "▾"; });
    sync();
    if (new URLSearchParams(location.search).has("e2e") && !new URLSearchParams(location.search).has("groups")) tg.click();       // the tests of the layers work with the boxes: the groups are open there (?groups=1 keeps them closed, as for a visitor)
  }
  $("filtersReset").addEventListener("click", resetFilters);
  for (const sec of document.querySelectorAll("#filters details.fsec")) {
    const id = sec.dataset.sec;
    if (id in secState) sec.open = !!secState[id];
    else if (window.innerWidth <= 900) sec.open = id === "f-layers";
    sec.querySelector("summary").addEventListener("click", () => setTimeout(() => {
      // on a phone one block is open at a time (the panel would be a long strip); the counters in the titles still tell what is on inside the closed ones. Only a click of the visitor does it: the tour opens blocks itself
      if (sec.open && window.matchMedia("(max-width:640px)").matches) for (const o of document.querySelectorAll("#filters details.fsec")) if (o !== sec && o.open) { o.open = false; secState[o.dataset.sec] = false; }
      secState[id] = sec.open; try { localStorage.setItem("sec", JSON.stringify(secState)); } catch (e) {}
    }, 0));      // saved on a click of the visitor only
  }
  $("filters").addEventListener("input", syncFilterUi);
  $("filters").addEventListener("change", syncFilterUi);
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
  function stopPlay() { clearInterval(timer); timer = null; $("play").textContent = "▶"; playing = false; document.body.classList.remove("playing"); flushPanels(); }
  function startPlay() {
    clearInterval(timer);
    playing = true; document.body.classList.add("playing");
    timer = setInterval(() => {
      year = Math.min(MAX, year + (year < 1000 ? 15 : year < 1700 ? 8 : 1));   // about the same distance of the thumb per step in each part of the scale
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
    buildTicks(); buildEpochBand(); buildEvMarks(); buildRulersBand(); updateZoomUi();
  }
  // The window of a zoomed scale stays where it is while the year is inside it (a click on the scale, the slider, an event mark change only the year).
  // It moves when the year leaves it (playback, search, a jump: the window is centred on the year at once) and when the scale itself is dragged or the
  // arrows are used (winCenter: the mark stays in the middle and the scale slides under it).
  let winCenter = false;
  function ensureInWindow() {
    if (zoomIx === 0) { winCenter = false; return; }
    if (!winCenter && year >= zoomLo && year <= zoomHi) return;
    winCenter = false;
    const w = ZOOM_W[zoomIx], lo = Math.min(Math.max(Math.round(year - w / 2), MIN), MAX - w);
    if (lo !== zoomLo || zoomHi !== lo + w) applyWindow(lo);
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
    year = Math.min(Math.max(Math.round(year + dir * ZOOM_W[zoomIx] / 2), MIN), MAX);
    winCenter = true;
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

  // A finger on the thumb of the slider (a phone): the marks of the events stop taking touches (body.sliding), and when the thumb is held near either end of the slider the window
  // of years moves by itself (the faster, the nearer to the end), the thumb stays under the finger and the year changes with the window: no stop at the end of the visible span.
  (function edgeScroll() {
    const sl = $("slider"), ZONE = 120, MAXSPEED = 120;          // ZONE: the part of the slider (of 1000) at each end that scrolls; MAXSPEED: years per second at the very end
    let on = false, raf = 0, last = 0, acc = 0, applied = 0;
    function stop() { on = false; cancelAnimationFrame(raf); document.body.classList.remove("sliding"); }
    function step(ts) {
      if (!on) return;
      raf = requestAnimationFrame(step);
      const dt = Math.min(0.1, (ts - last) / 1000); last = ts;
      if (zoomIx === 0) return;                                    // the whole history is on the slider: nothing is hidden
      const v = +sl.value;
      let depth = 0;
      if (v <= ZONE) depth = -(ZONE - v) / ZONE; else if (v >= 1000 - ZONE) depth = (v - (1000 - ZONE)) / ZONE;
      if (!depth) { acc = 0; return; }
      const sp = Math.min(MAXSPEED, zoomHi - zoomLo);
      acc += Math.sign(depth) * Math.pow(Math.abs(depth), 1.5) * sp * dt;
      if (Math.abs(acc) < 1 || ts - applied < 60) return;          // the window is rebuilt at most every 60 ms
      const d = Math.trunc(acc), lo = zoomLo + d;
      if ((d < 0 && zoomLo <= MIN) || (d > 0 && zoomHi >= MAX)) { acc = 0; return; }
      acc -= d; applied = ts;
      applyWindow(lo);
      sl.value = v;                                                // applyWindow puts the thumb to the old year: it must stay under the finger
      const y = Math.min(MAX, Math.max(MIN, v2y(v)));
      if (y !== year) { year = y; update(); }
    }
    sl.addEventListener("pointerdown", (e) => {
      if (e.pointerType !== "touch") return;
      on = true; acc = 0; applied = 0; last = performance.now();
      document.body.classList.add("sliding");
      cancelAnimationFrame(raf); raf = requestAnimationFrame(step);
    });
    window.addEventListener("pointerup", stop);
    window.addEventListener("pointercancel", stop);
  })();

  // forms of state and rulers over Tbilisi: a band under the time scale (two rows with up to two lanes each), a line "who ruled" in the side panel, a card on a click
  let bandW = 0; const BAND_LEVELS = [24, 48, 96, 192, 384, 768, 1536];    // the band is a lens: it shows this many years around the current year
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
    const c = year + 0.5, cnt = (w) => rulersData.rulers.filter((r) => !r.lane && r.to > c - w / 2 && r.from < c + w / 2).length;
    if (!bandW || cnt(bandW) < 3 || cnt(bandW) > 16) bandW = BAND_LEVELS.find((w) => cnt(w) >= 5) || BAND_LEVELS[BAND_LEVELS.length - 1];       // the smallest window with at least 5 rulers; kept while it stays between 3 and 16
    let lo = c - bandW / 2, hi = c + bandW / 2;
    if (zoomIx > 0) { lo = zoomLo; hi = zoomHi; bandW = hi - lo; }       // a zoomed scale: the same window as the scale above
    const W = Math.max(0, $("rStates").clientWidth - 16);
    const shortName = (n) => { const w = n.replace(/\(.*?\)/g, "").trim().split(/\s+/), last = w[w.length - 1]; return /^[IVXLC]+$/.test(last) && w.length > 1 ? w[0] + " " + last : last; };
    const fill = (row, items, kindOf, nameOf, ruler) => {
      row.textContent = "";
      let lanes = 0;
      const phone = window.matchMedia("(max-width:640px)").matches;      // a phone: one row, the main line only
      for (const it of items) {
        if (it.to <= lo || it.from >= hi || (phone && it.lane)) continue;
        const a = Math.max(it.from, lo), b = Math.min(it.to, hi), x1 = (a - lo) / (hi - lo), x2 = (b - lo) / (hi - lo);
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
        const full = nameOf(it), sh = ruler ? shortName(full) : full;
        if (px >= full.length * (lane ? 5.6 : 6.3) + 14) btn.textContent = full;
        else if (ruler && px >= sh.length * (lane ? 5.6 : 6.3) + 10) btn.textContent = sh;
        else btn.classList.add("nolabel");       // no text: no padding, so the width is the real length of the term
        btn.title = nameOf(it) + " \u00B7 " + dispYear(it.from) + "\u2013" + dispYear(it.to);
        btn.addEventListener("click", () => showRulerCard(it));
        row.appendChild(btn);
      }
      row.style.height = (lanes > 1 && !phone ? RULE_MAIN_H + RULE_GAP + RULE_SUB_H : RULE_MAIN_H) + "px";
    };
    fill($("rStates"), rulersData.states, (it) => "rk-" + it.kind, (it) => rText(it.name));
    fill($("rRulers"), rulersData.rulers, (it) => "rg-" + it.grp, (it) => rText(it.name), true);
    const tk = $("rticks");                       // years of the lens
    tk.textContent = "";
    const step = bandW <= 30 ? 5 : bandW <= 60 ? 10 : bandW <= 120 ? 20 : bandW <= 250 ? 50 : bandW <= 500 ? 100 : 200;
    for (let y = Math.ceil(lo / step) * step; y <= hi; y += step) {
      const sp = document.createElement("span");
      sp.textContent = dispYear(y); sp.style.left = "calc(8px + (100% - 16px) * " + ((y - lo) / (hi - lo)) + ")";
      tk.appendChild(sp);
    }
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
          { const fi = mediaImg(f.b || f.i, 0, 0, (RN[lang] || RN.en).flag); fi.className = "rflag"; row.appendChild(fi); } row.appendChild(document.createTextNode(" " + dispYear(f.from) + "–" + dispYear(f.to) + (f.k && (RN[lang] || RN.en)[f.k] ? " \u00B7 " + (RN[lang] || RN.en)[f.k] : "")));
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
    ru: { suz: "флаг сюзерена, реконструкция", civil: "гражданский флаг, государственного флага не было", recon: "реконструкция", img: "Изображение", cond: "До XVIII века это условное изображение (роспись, миниатюра или памятник), а не прижизненный портрет.", flag: "Флаг", open: "Карточка", src: "файл на Commons" },
    en: { suz: "the flag of the suzerain, a reconstruction", civil: "civil ensign; there was no national flag", recon: "reconstruction", img: "Image", cond: "Before the 18th century this is a conventional image (a fresco, a miniature or a monument), not a portrait from life.", flag: "Flag", open: "Card", src: "file on Commons" },
    ka: { suz: "სუზერენის დროშა, რეკონსტრუქცია", civil: "სამოქალაქო დროშა; სახელმწიფო დროშა არ იყო", recon: "რეკონსტრუქცია", img: "გამოსახულება", cond: "XVIII საუკუნემდე ეს პირობითი გამოსახულებაა (ფრესკა, მინიატურა ან ძეგლი), და არა ცოცხალი პორტრეტი.", flag: "დროშა", open: "ბარათი", src: "ფაილი Commons-ზე" },
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
      let np = 0;
      for (const r of rl) {
        const m = rulersMedia && rulersMedia.rulers && rulersMedia.rulers[r.id];
        if (m) { const i = mediaImg(m.i, 32, 40, rText(r.name)); i.className = "tkp" + (np++ ? " tkp2" : ""); i.title = rText(r.name) + " · " + dispYear(r.from) + "–" + dispYear(r.to); tk.appendChild(i); }
      }
      if (rl.length && !tk.querySelector(".tkp")) {          // no portrait: a crown for the rulers of the monarchies, a star for the others
        const g = document.createElement("span"); g.className = "tkph"; const ws = rText(rl[0].name).replace(/\(.*?\)/g, "").trim().split(/\s+/); g.textContent = ((ws[0] || "")[0] || "") + (ws.length > 1 && !/^[IVXLC]+$/.test(ws[ws.length - 1]) ? (ws[ws.length - 1][0] || "") : "");
        g.title = rText(rl[0].name) + " · " + dispYear(rl[0].from) + "–" + dispYear(rl[0].to); tk.appendChild(g);
      }
      if (fl) { const i = mediaImg(fl.i, 0, 22, R.flag); i.className = "tkf"; i.title = R.flag + ": " + rText(st.name) + (fl.k && R[fl.k] ? " (" + R[fl.k] + ")" : ""); tk.appendChild(i); }
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
    if (h) h.style.left = "calc(8px + (100% - 16px) * " + (zoomIx > 0 ? (year + 0.5 - zoomLo) / Math.max(1, zoomHi - zoomLo) : 0.5) + " - 1px)";
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
    const line = (cls, txt, sw) => {
      const d = document.createElement("div"); d.className = cls;
      if (sw) { const i = document.createElement("i"); i.className = "rsw " + sw; i.setAttribute("aria-hidden", "true"); d.appendChild(i); }
      d.appendChild(document.createTextNode(txt)); box.appendChild(d); return d;
    };
    // the small square before a line has the colour of the row of the band that the line is about
    if (st) {
      line("rs1", rText(st.name), "rk-" + st.kind);
      if (st.form && rText(st.form)) line("rs2", rText(st.form));
    } else line("rs2", L.ruleNoData);
    for (const s of ov) line("rs3 ov", (s.kind === "overlord" ? L.ruleOver : L.ruleAdmin) + ": " + rText(s.name), "rk-" + s.kind);
    for (const r of rl.slice(0, 3)) line("rs3 pr", (rText(r.title) || rText(rulersData.groups[r.grp])) + ": " + rText(r.name), "rg-" + r.grp);
  }
  let bandRaf = 0;
  function scheduleBand() { if (bandRaf) return; bandRaf = requestAnimationFrame(() => { bandRaf = 0; if (rulersData && $("showRulers").checked) buildRulersBand(); }); }
  function updateRuleBar() {
    scheduleBand();
    updateToken();
    updateRuleSummary();
    markRulers();
  }
  function updateRuleLine() { updateRuleBar(); updateRuleBox(); }
  function updateRuleBox() {
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

  // Dragging the timeline with the mouse (or a finger). On the scale under the slider (years and events) the thumb follows the pointer; on the band of the rulers the band is grabbed
  // and pulled: dragging to the left brings later years to the line. A drag starts after 4 px, so a plain click on a year, an event or a ruler still works.
  (function dragTimeline() {
    const THRESHOLD = 4;
    function track(el, grabCls, onStart, onMove) {
      let st = null;
      el.addEventListener("pointerdown", (e) => {
        if (e.button !== 0 || (e.target.closest && e.target.closest("input,select,textarea,a"))) return;
        st = { x: e.clientX, drag: false, id: e.pointerId, ctx: null, e0: e };          // the start of a drag is prepared only when the pointer really moves: a plain click (an event mark) must not change the scale
      });
      el.addEventListener("pointermove", (e) => {
        if (!st) return;
        const dx = e.clientX - st.x;
        if (!st.drag) {
          if (Math.abs(dx) < THRESHOLD) return;
          st.drag = true;
          st.ctx = onStart(st.e0);
          try { el.setPointerCapture(st.id); } catch (err) {}
          el.classList.add(grabCls);
        }
        onMove(e, dx, st.ctx);
      });
      const end = () => {
        if (!st) return;
        if (st.drag) {
          el.classList.remove(grabCls);
          const stop = (ev) => { ev.stopPropagation(); ev.preventDefault(); };      // the click that ends a drag must not open a year or an event
          window.addEventListener("click", stop, { capture: true, once: true });
          setTimeout(() => window.removeEventListener("click", stop, true), 0);
        }
        st = null;
      };
      el.addEventListener("pointerup", end);
      el.addEventListener("pointercancel", end);
      el.addEventListener("dragstart", (e) => e.preventDefault());       // no native drag of a selected text or an image
      el.addEventListener("selectstart", (e) => { if (st) e.preventDefault(); });
    }
    const setTo = (y) => { if (y !== year) { year = y; winCenter = true; update(); } };          // dragging the scale: the window follows
    const wrap = $("sliderwrap");
    if (wrap) track(wrap, "grabbing", () => {
      if (zoomIx === 0) setZoom(5);                                  // the whole history cannot be scrolled: zoom in first (the buttons bring it back)
      return { y0: year, span: Math.max(1, zoomHi - zoomLo), w: Math.max(1, wrap.clientWidth - 16) };
    }, (e, dx, c) => {
      setTo(Math.round(Math.min(MAX, Math.max(MIN, c.y0 - dx * c.span / c.w))));          // the scale follows the pointer: to the right = earlier years
    });
    const axis = $("axis");
    if (axis) track(axis, "grabbing", () => ({ y0: year, w: Math.max(1, $("rulers").clientWidth - 16), span: bandW || 100 }), (e, dx, c) => {
      const lo = v2y(0), hi = v2y(1000);
      setTo(Math.round(Math.min(hi, Math.max(lo, c.y0 - dx * c.span / c.w))));
    });
  })();
  if (window.innerWidth > 900) $("showRulers").checked = true;      // on a narrow screen the band stays off until it is asked for
  // a phone or a tablet (up to 1099 px): the less important buttons of the top bar (install, version, feedback, language, sections) live in the menu "...": the bar does not fit otherwise
  {
    const mq = window.matchMedia("(max-width:1099px)"), top = $("top"), menu = $("moreMenu"), group = $("topRight"), more = $("btnMore");     // a phone or a tablet: the bar does not fit otherwise
    const close = () => { menu.hidden = true; more.setAttribute("aria-expanded", "false"); };
    const place = () => {
      if (mq.matches) { if (group.parentNode !== menu) menu.appendChild(group); }
      else { if (group.parentNode !== top) top.insertBefore(group, menu); close(); }
    };
    more.addEventListener("click", (e) => { e.stopPropagation(); menu.hidden = !menu.hidden; more.setAttribute("aria-expanded", String(!menu.hidden)); });
    document.addEventListener("click", (e) => { if (!menu.hidden && !menu.contains(e.target) && e.target !== more) close(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { close(); more.focus(); } });
    menu.addEventListener("click", (e) => { if (e.target.closest("button")) close(); });
    $("lang").addEventListener("change", close);
    if (mq.addEventListener) mq.addEventListener("change", place);
    place();
  }
  // the owner of the screen decides: the time scale folds to a small pill with the year, the line of rulers hides to a pill "Rulers"; the choice is remembered (not part of the filters)
  function uiGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function uiSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function setTbMin(on, save) {
    $("timebar").classList.toggle("min", !!on);
    $("tbToggle").textContent = on ? "▼" : "▲";
    const tx = on ? t().tbShow : t().tbHide; $("tbToggle").title = tx; $("tbToggle").setAttribute("aria-label", tx);
    $("tbYear").textContent = year;
    if (save) uiSet("ui_tb", on ? "min" : "");
    requestAnimationFrame(() => { syncBars(); window.dispatchEvent(new Event("resize")); });
  }
  $("tbToggle").addEventListener("click", () => setTbMin(!$("timebar").classList.contains("min"), true));
  function setRulersOn(on) { $("showRulers").checked = on; $("showRulers").dispatchEvent(new Event("change")); uiSet("ui_rb", on ? "on" : "off"); }
  $("rbToggle").addEventListener("click", () => setRulersOn(false));
  $("rbShow").addEventListener("click", () => setRulersOn(true));
  $("showRulers").addEventListener("change", () => uiSet("ui_rb", $("showRulers").checked ? "on" : "off"));
  function updateFoldTitles() {
    const L = t(); $("rbToggle").title = L.rbHide; $("rbToggle").setAttribute("aria-label", L.rbHide); $("rbShow").textContent = "👑 " + L.rbShow;
    const tx = $("timebar").classList.contains("min") ? L.tbShow : L.tbHide; $("tbToggle").title = tx; $("tbToggle").setAttribute("aria-label", tx);
  }
  { const v = uiGet("ui_rb"); if (v === "on") $("showRulers").checked = true; if (v === "off") $("showRulers").checked = false; }
  // a low screen (a phone lying on its side): the time scale starts folded to a pill with the year until the visitor has chosen
  if (uiGet("ui_tb") === "min" || (uiGet("ui_tb") === null && window.innerHeight < 600)) setTbMin(true, false);
  updateFoldTitles();

  // science and culture: universities, institutes, libraries, museums, theatres; points that appear in the year (data/science.json); science is drawn larger and above culture
  const SCI_COLOR = { science: "#1c7ed6", culture: "#868e96" };
  const sciFeats = () => science.map((c) => ({ type: "Feature", geometry: { type: "Point", coordinates: [c.lon, c.lat] },
    properties: { id: c.id, kind: c.kind, from: c.from, sf: c.sf || 0, undated: !!c.undated, label: c.name[lang] || c.name.en } }));
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
    syncLegend("showSci", "sciLegend");
    if (!map.getLayer("sci-pt")) return;
    const on = $("showSci").checked;
    for (const id of ["sci-pt", "sci-lb"]) {
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["<=", ["get", "from"], year]);
    }
    for (const id of ["sci-pt", "sci-lb"]) map.moveLayer(id);          // to the top: above the topographic map and the points of the register, which other code also moves
    const faint = ["case", ["==", ["get", "undated"], true], 0.45, ["<", year, ["get", "sf"]], 0.35, 1];       // faint before the present building stands (or the institution is in another place), and when the register gives no date
    map.setPaintProperty("sci-pt", "circle-opacity", faint);
    map.setPaintProperty("sci-pt", "circle-stroke-opacity", faint);
  }
  function updateSciUi() {
    const box = $("sciLegend");
    if (box) {
      box.textContent = "";
      for (const k of Object.keys(SCI_COLOR)) { const s = document.createElement("span"); s.textContent = t().sciKinds[k]; s.style.setProperty("--c", SCI_COLOR[k]); box.appendChild(s); }
      syncLegend("showSci", "sciLegend");
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
    if (c.undated) row(L.sciFrom, L.relUndated);
    else if (!String(c.founded || "").includes(String(c.from))) row(L.sciFrom, String(c.from));
    if (c.addr) row(L.relAddr, c.addr[lang] || c.addr.en);
    if (c.approx) row(L.relApprox, "\u2248");
    if (c.sf && year < c.sf) row("\u25CB", L.sciFaint);
    cardPhotos(el, c);
    const n = document.createElement("div");
    n.className = "small";
    n.textContent = c.note[lang] || c.note.en;
    el.appendChild(n);
    const s = document.createElement("div");
    s.className = "src";
    s.appendChild(document.createTextNode(L.sciSrc + ": "));
    if (!c.src.length) s.appendChild(document.createTextNode(L.relRegSrc + " " + (c.regno ? L.relRegNo + " " + c.regno : L.relRegId + " " + c.rid)));
    c.src.forEach((u, i) => { const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURIComponent(u.replace("https://", "")).slice(0, 60); if (i) s.appendChild(document.createTextNode(" \u00B7 ")); s.appendChild(a); });
    el.appendChild(s);
    actions(el, null, fbRef("SCI", c.id, el));
    showPopup("340px", lngLat, el);
    addNamesakeTo(el, "SCI:" + c.id);
  }

  // education: schools and kindergartens of the heritage register (data/education.json); points that appear in the year of the building
  const EDU_COLOR = { school: "#9c36b5", kindergarten: "#f59f00" };
  const eduFeats = () => education.map((c) => ({ type: "Feature", geometry: { type: "Point", coordinates: [c.lon, c.lat] },
    properties: { id: c.id, kind: c.kind, from: c.from, undated: !!c.undated, label: c.name[lang] || c.name.en } }));
  function addEducation() {
    if (!education.length || map.getSource("edu")) return;
    map.addSource("edu", { type: "geojson", data: { type: "FeatureCollection", features: eduFeats() } });
    map.addLayer({ id: "edu-pt", type: "circle", source: "edu", layout: { visibility: "none" },
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 4.5, 17, 9], "circle-color": ["case", ["==", ["get", "kind"], "school"], EDU_COLOR.school, EDU_COLOR.kindergarten],
               "circle-stroke-color": "#ffffff", "circle-stroke-width": 2, "circle-opacity": ["case", ["==", ["get", "undated"], true], 0.5, 1] } });
    map.addLayer({ id: "edu-lb", type: "symbol", source: "edu", minzoom: 15, layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.2], "text-anchor": "top", "text-optional": true },
      paint: { "text-color": "#5f3dc4", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "edu-pt", (e) => {
      const f = e.features && e.features[0], c = f && education.find((x) => x.id === f.properties.id);
      if (c) popupEdu(c, e.lngLat);
    });
    map.on("mouseenter", "edu-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "edu-pt", () => { map.getCanvas().style.cursor = ""; });
    updateEducation();
  }
  function updateEducation() {
    syncLegend("showEdu", "eduLegend");
    if (!map.getLayer("edu-pt")) return;
    const on = $("showEdu").checked;
    for (const id of ["edu-pt", "edu-lb"]) {
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["<=", ["get", "from"], year]);
      map.moveLayer(id);
    }
  }
  function updateEduUi() {
    const box = $("eduLegend");
    if (box) {
      box.textContent = "";
      for (const k of Object.keys(EDU_COLOR)) { const s = document.createElement("span"); s.textContent = t().eduKinds[k]; s.style.setProperty("--c", EDU_COLOR[k]); box.appendChild(s); }
      syncLegend("showEdu", "eduLegend");
    }
    const src = map && map.getSource && map.getSource("edu");
    if (src) src.setData({ type: "FeatureCollection", features: eduFeats() });
  }
  function popupEdu(c, lngLat) {
    reopenPopup = () => popupEdu(c, lngLat);
    const L = t(), el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = c.name[lang] || c.name.en;
    el.appendChild(h3);
    const row = (k, v) => { if (!v) return; const d = document.createElement("div"), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; d.appendChild(kk); d.appendChild(document.createTextNode(v)); el.appendChild(d); };
    const rr = document.createElement("div");
    rr.className = "k";
    rr.textContent = L.eduKinds[c.kind] || c.kind;
    el.appendChild(rr);
    row(L.sciBuilt, c.undated ? L.relUndated : c.built);
    if (c.approx) row(L.relApprox, "\u2248");
    if (!c.undated) row(L.sciFrom, String(c.from));
    if (c.addr) row(L.relAddr, c.addr[lang] || c.addr.en);
    cardPhotos(el, c);
    const n = document.createElement("div");
    n.className = "small";
    n.textContent = c.note[lang] || c.note.en;
    el.appendChild(n);
    const s = document.createElement("div");
    s.className = "src";
    s.appendChild(document.createTextNode(L.sciSrc + ": " + L.relRegSrc + " " + (c.regno ? L.relRegNo + " " + c.regno : L.relRegId + " " + c.rid)));
    el.appendChild(s);
    actions(el, null, fbRef("EDU", c.id, el));
    showPopup("340px", lngLat, el);
    addNamesakeTo(el, "EDU:" + c.id);
  }
  // museums and house-museums (data/museums.json); points that appear in the year of founding or building
  const MUS_COLOR = { museum: "#0b7285", house: "#e67700" };
  const musFeats = () => museums.map((c) => ({ type: "Feature", geometry: { type: "Point", coordinates: [c.lon, c.lat] },
    properties: { id: c.id, kind: c.kind, from: c.from, undated: !!c.undated, label: c.name[lang] || c.name.en } }));
  function addMuseums() {
    if (!museums.length || map.getSource("mus")) return;
    map.addSource("mus", { type: "geojson", data: { type: "FeatureCollection", features: musFeats() } });
    map.addLayer({ id: "mus-pt", type: "circle", source: "mus", layout: { visibility: "none" },
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 5, 17, 10], "circle-color": ["case", ["==", ["get", "kind"], "museum"], MUS_COLOR.museum, MUS_COLOR.house],
               "circle-stroke-color": "#ffffff", "circle-stroke-width": 2, "circle-opacity": ["case", ["==", ["get", "undated"], true], 0.5, 1] } });
    map.addLayer({ id: "mus-lb", type: "symbol", source: "mus", minzoom: 14, layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.2], "text-anchor": "top", "text-optional": true },
      paint: { "text-color": "#0b7285", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "mus-pt", (e) => {
      const f = e.features && e.features[0], c = f && museums.find((x) => x.id === f.properties.id);
      if (c) popupMus(c, e.lngLat);
    });
    map.on("mouseenter", "mus-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "mus-pt", () => { map.getCanvas().style.cursor = ""; });
    updateMuseums();
  }
  function updateMuseums() {
    syncLegend("showMus", "musLegend");
    if (!map.getLayer("mus-pt")) return;
    const on = $("showMus").checked;
    for (const id of ["mus-pt", "mus-lb"]) {
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["<=", ["get", "from"], year]);
      map.moveLayer(id);
    }
  }
  function updateMusUi() {
    const box = $("musLegend");
    if (box) {
      box.textContent = "";
      for (const k of Object.keys(MUS_COLOR)) { const s = document.createElement("span"); s.textContent = t().musKinds[k]; s.style.setProperty("--c", MUS_COLOR[k]); box.appendChild(s); }
      syncLegend("showMus", "musLegend");
    }
    const src = map && map.getSource && map.getSource("mus");
    if (src) src.setData({ type: "FeatureCollection", features: musFeats() });
  }
  const battleMapFeats = () => histEvents.map((ev, idx) => ({ ev, idx })).filter(({ ev }) => (ev.cat === "battle" || ev.cat === "invasion") && ev.place)
    .map(({ ev, idx }) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [ev.place.lng, ev.place.lat] },
      properties: { idx, year: ev.year, cat: ev.cat, label: `${ev.place[lang] || ev.place.en || ""} (${ev.date})` },
    }));
  function addBattleMap() {
    if (!histEvents.length || map.getSource("battle-map")) return;
    map.addSource("battle-map", { type: "geojson", data: { type: "FeatureCollection", features: battleMapFeats() } });
    map.addLayer({ id: "battle-pt", type: "circle", source: "battle-map", layout: { visibility: "none" },
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 6, 17, 11],
               "circle-color": ["case", ["==", ["get", "cat"], "battle"], "#c92a2a", "#e67700"],
               "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });
    map.addLayer({ id: "battle-lb", type: "symbol", source: "battle-map", minzoom: 13.5,
      layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.3], "text-anchor": "top", "text-optional": true },
      paint: { "text-color": "#a61e4d", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "battle-pt", (e) => {
      const f = e.features && e.features[0], ev = f && histEvents[f.properties.idx];
      if (ev) showHistEvent(ev);
    });
    map.on("mouseenter", "battle-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "battle-pt", () => { map.getCanvas().style.cursor = ""; });
    updateBattleMap();
  }
  function updateBattleMap() {
    if (!map.getLayer("battle-pt")) return;
    const on = $("showBattleMap").checked;
    for (const id of ["battle-pt", "battle-lb"]) {
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["<=", ["get", "year"], year]);
      map.moveLayer(id);
    }
  }
  function updateBattleMapUi() {
    const src = map && map.getSource && map.getSource("battle-map");
    if (src) src.setData({ type: "FeatureCollection", features: battleMapFeats() });
  }
  function popupMus(c, lngLat) {
    reopenPopup = () => popupMus(c, lngLat);
    const L = t(), el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = c.name[lang] || c.name.en;
    el.appendChild(h3);
    const row = (k, v) => { if (!v) return; const d = document.createElement("div"), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; d.appendChild(kk); d.appendChild(document.createTextNode(v)); el.appendChild(d); };
    const rr = document.createElement("div");
    rr.className = "k";
    rr.textContent = L.musKinds[c.kind] || c.kind;
    el.appendChild(rr);
    row(L.sciFounded, c.founded);
    row(L.sciBuilt, c.built);
    if (c.undated) row(L.sciFrom, L.relUndated);
    else if (!String(c.founded || "").includes(String(c.from))) row(L.sciFrom, String(c.from));
    if (c.addr) row(L.relAddr, c.addr[lang] || c.addr.en);
    cardPhotos(el, c);
    const n = document.createElement("div");
    n.className = "small";
    n.textContent = c.note[lang] || c.note.en;
    el.appendChild(n);
    const s = document.createElement("div");
    s.className = "src";
    s.appendChild(document.createTextNode(L.sciSrc + ": "));
    if (!c.src.length) s.appendChild(document.createTextNode(L.relRegSrc + " " + (c.regno ? L.relRegNo + " " + c.regno : L.relRegId + " " + c.rid)));
    c.src.forEach((u, i) => { const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURIComponent(u.replace("https://", "")).slice(0, 60); if (i) s.appendChild(document.createTextNode(" \u00B7 ")); s.appendChild(a); });
    el.appendChild(s);
    actions(el, null, fbRef("MUS", c.id, el));
    showPopup("340px", lngLat, el);
    addNamesakeTo(el, "MUS:" + c.id);
  }
  // local names: districts, gardens, hills, bridges, cemeteries with what the name means (Wikipedia, quotes checked); the file is loaded when the layer is switched on or the search is opened
  const PL_COLOR = { district: "#d6336c", garden: "#2b8a3e", hill: "#8d5524", bridge: "#1c7ed6", cemetery: "#495057", market: "#f08c00", bath: "#0ca678", area: "#7048e8", square: "#9c36b5", building: "#e8590c" };
  function ensurePlaces() {
    if (placesLoading) return placesLoading;
    const wait = 3000 - (Date.now() - placesFailedAt);                // after a failure (getJSON has tried four times) the next try is not earlier than after 3 s: it is made by a timer when the layer is still wanted
    if (wait > 0) { if (!placesTimer) placesTimer = setTimeout(() => { placesTimer = null; if (!places && ($("showPlaces").checked || !$("search").hidden)) ensurePlaces(); }, wait + 50); return null; }
    placesLoading = getJSON("data/places.json").then((d) => { places = d; searchIndex = null; addPlaces(); updatePlacesUi(); if (!$("search").hidden) renderSearch(); }).catch((e) => { console.error("places", e && e.message); places = null; placesLoading = null; placesFailedAt = Date.now(); });
    return placesLoading;
  }
  const folkNames = (c) => [...(c.f || []).flatMap((x) => Object.values(x.n)), ...Object.values(c.o || {}), ...Object.values(c.al || {})];                                   // the folk names of a place or a building (and the former and other names of a park: they join the search)
  const PU = (k) => (places && places.ui && places.ui[k] && (places.ui[k][lang] || places.ui[k].en)) || "";
  const placeName = (c) => c.n[lang] || c.n.en || c.n.ru || c.n.ka;                              // a name that lacks a language (a park that OSM names in Georgian only) is shown in the language that exists
  const placeFeats = () => places.items.map((c) => ({ type: "Feature", geometry: { type: "Point", coordinates: [c.lon, c.lat] }, properties: { id: c.id, kind: c.k, label: placeName(c) } }));
  function addPlaces() {
    if (!places || !places.items.length || map.getSource("places")) return;
    if (!map.isStyleLoaded()) { map.once("idle", addPlaces); return; }                       // as for mpAdd: the layer is added at the next idle
    map.addSource("places", { type: "geojson", data: { type: "FeatureCollection", features: placeFeats() } });
    const AREA_PAL = ["#e03131", "#1971c2", "#2f9e44", "#f08c00", "#7048e8", "#0c8599", "#c2255c", "#5c940d", "#d9480f", "#364fc7"];
    map.addSource("places-area", { type: "geojson", data: { type: "FeatureCollection", features: places.items.filter((c) => c.g).map((c, idx) => ({ type: "Feature", geometry: c.g, properties: { id: c.id, kind: c.k, col: c.k === "area" ? PL_COLOR.area : AREA_PAL[idx % AREA_PAL.length] } })) } });
    map.addLayer({ id: "places-area-fill", type: "fill", source: "places-area", layout: { visibility: "none" }, paint: { "fill-color": ["get", "col"], "fill-opacity": 0.10 } });
    map.addLayer({ id: "places-area-line", type: "line", source: "places-area", layout: { visibility: "none" }, paint: { "line-color": ["get", "col"], "line-width": 2, "line-opacity": 0.9 } });
    const col = ["match", ["get", "kind"]];
    for (const [k, c] of Object.entries(PL_COLOR)) col.push(k, c);
    col.push("#555");
    map.addLayer({ id: "places-pt", type: "circle", source: "places", layout: { visibility: "none" },
      paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 4, 17, 8], "circle-color": col, "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });
    map.addLayer({ id: "places-lb", type: "symbol", source: "places", minzoom: 13, layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.1], "text-anchor": "top", "text-optional": true },
      paint: { "text-color": "#7a1f45", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "places-pt", (e) => {
      const f = e.features && e.features[0], c = f && places.items.find((x) => x.id === f.properties.id);
      if (c) popupPlace(c, e.lngLat);
    });
    map.on("mouseenter", "places-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "places-pt", () => { map.getCanvas().style.cursor = ""; });
    updatePlaces();
  }
  function updatePlaces() {
    const on = $("showPlaces").checked;
    if (on && !places) ensurePlaces();
    syncLegend("showPlaces", "placesLegend");
    if (places && !map.getSource("places")) addPlaces();
    if (!map.getLayer("places-pt")) return;
    for (const id of ["places-area-fill", "places-area-line", "places-pt", "places-lb"]) { map.setLayoutProperty(id, "visibility", on ? "visible" : "none"); map.moveLayer(id); }
    applyPlaceAreas();
  }
  // the outlines of quarters and squares (the OSM contours) are drawn only when their own box is on; the outline of an area of the past (the hippodrome) goes with the layer
  function applyPlaceAreas() {
    const row = $("rowPlaceAreas");
    if (row) row.hidden = !$("showPlaces").checked;
    if (!map.getLayer("places-area-fill")) return;
    const f = $("showPlaceAreas").checked ? null : ["==", ["get", "kind"], "area"];
    for (const id of ["places-area-fill", "places-area-line"]) map.setFilter(id, f);
  }
  function updatePlacesUi() {
    const box = $("placesLegend");
    if (box) {
      box.textContent = "";
      const kinds = places ? [...new Set(places.items.map((c) => c.k))] : [];
      for (const k of Object.keys(PL_COLOR)) if (kinds.includes(k)) { const s = document.createElement("span"); s.textContent = PU("kind_" + k); s.style.setProperty("--c", PL_COLOR[k]); box.appendChild(s); }
      syncLegend("showPlaces", "placesLegend");
    }
    const src = map && map.getSource && map.getSource("places");
    if (src && places) src.setData({ type: "FeatureCollection", features: placeFeats() });
  }
  // the folk (slang) names of a place or of a building (c.f): the name in the languages that exist, what it means (own text of the answer with quotes), the pages
  const hostLabel = (u, l) => { const h = new URL(u).hostname; return /wikipedia[.]org$/.test(h) ? "Wikipedia (" + (l || h.split(".")[0]) + ")" : h.replace(/^www[.]/, ""); };
  function folkBlock(el, c, U) {
    for (const x of c.f || []) {
      const d = document.createElement("div"), kk = document.createElement("span"), b = document.createElement("b");
      kk.className = "k"; kk.textContent = U("folk") + ": "; d.appendChild(kk);
      b.textContent = "«" + [...new Set([x.n[lang], x.n.ka, x.n.ru, x.n.en].filter(Boolean))].join(" / ") + "»"; d.appendChild(b);
      el.appendChild(d);
      const m = x.m && (x.m[lang] || x.m.en);
      if (m) { const t2 = document.createElement("div"); t2.className = "small"; t2.textContent = m; el.appendChild(t2); }
      const s2 = document.createElement("div"); s2.className = "small src";
      s2.appendChild(document.createTextNode(U("src") + ": "));
      x.s.forEach((q, i) => { if (i) s2.appendChild(document.createTextNode("; ")); const a = document.createElement("a"); a.href = q.u; a.target = "_blank"; a.rel = "noopener"; a.textContent = hostLabel(q.u, q.l); s2.appendChild(a); });
      el.appendChild(s2);
    }
  }
  function popupPlace(c, lngLat) {
    reopenPopup = () => popupPlace(c, lngLat);
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = placeName(c);
    el.appendChild(h3);
    const add = (txt, cls) => { const d = document.createElement("div"); if (cls) d.className = cls; d.textContent = txt; el.appendChild(d); return d; };
    add(PU("kind_" + c.k), "k");
    if (c.a) add(c.a[lang] || c.a.en);
    const e = add("", "");
    if (!c.a && !c.e) e.remove();                                   // a place that exists only for its folk name
    else if (c.e) { const kk = document.createElement("span"); kk.className = "k"; kk.textContent = PU("etym") + ": "; e.appendChild(kk); e.appendChild(document.createTextNode(c.e[lang] || c.e.en)); }
    else if (c.ne) e.remove();                                      // an entry for which the question of the etymology is not asked (the former hippodrome)
    else { e.className = "small"; e.textContent = PU("no_etym"); }
    if (c.e && c.s.eq && c.s.eq.k === "dictionary") add(PU("dict_note"), "small");     // the meaning of a common word, not a source of the origin of the toponym
    if (c.g && c.k === "area") add(PU("area_note"), "small");                         // the contour of an area is not the exact boundary of the object of the past
    folkBlock(el, c, PU);
    if (c.ap) add(PU("approx"), "small");                           // a district of several streets: the point is on one of them
    if (c.pk) {                                                     // a park or garden that only OpenStreetMap names: the former and the other names, the note about the source
      const nameOf = (x) => x[lang] || x.ka || x.ru || x.en;
      for (const [fld, key] of [["o", "old_name"], ["al", "alt_name"]]) if (c[fld]) { const x = add("", ""), kk = document.createElement("span"); kk.className = "k"; kk.textContent = PU(key) + ": "; x.appendChild(kk); x.appendChild(document.createTextNode([...new Set([c[fld][lang], c[fld].ka, c[fld].ru, c[fld].en].filter(Boolean))].join(" / "))); }
      add(PU("park_note"), "small");
    }
    const s = add("", "src");
    s.appendChild(document.createTextNode(PU("src") + ": "));
    const srcLabel = (u, l) => { const h = new URL(u).hostname; return /wikipedia\.org$/.test(h) ? "Wikipedia (" + (l || h.split(".")[0]) + ")" : h.replace(/^www\./, ""); };
    const links = (c.a || c.pk) ? [[c.s.u, c.s.l]] : [];                      // the page of the description (a place that exists only for its folk name has none: the pages of its names are in the folk block)
    if (c.s.eq && c.s.eq.u && c.s.eq.u !== c.s.u) links.push([c.s.eq.u, c.s.eq.l]);
    for (const x of (c.s.eq && c.s.eq.more) || []) if (!links.some((l) => l[0] === x.u)) links.push([x.u, x.l]);               // the origin of the name may come from another page than the description
    if (c.wp) links.push([c.wp, new URL(c.wp).hostname.split(".")[0]]);                  // the article that the OSM tag names (a link only)
    links.forEach(([u, l], i) => { if (i) s.appendChild(document.createTextNode("; ")); const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = srcLabel(u, l); s.appendChild(a); });
    if (c.s.eq && c.s.eq.p) s.appendChild(document.createTextNode("; " + PU("enc") + " " + c.s.eq.p));
    if (!links.length) s.remove();
    actions(el, () => openInfo((body) => {
      infoLine(body, placeName(c) + ":");
      if (c.a) infoLine(body, PU("quote") + " (" + c.s.l + "): “" + c.s.aq + "”", "small");
      for (const x of c.f || []) for (const q of x.s) infoLine(body, PU("folk") + " «" + (x.n[lang] || x.n.ka || x.n.ru || x.n.en) + "» — " + PU("quote") + " (" + q.l + "): “" + q.q + "”", "small");
      if (c.s.eq) infoLine(body, PU("etym") + " — " + PU("quote") + " (" + c.s.eq.l + (c.s.eq.p ? ", " + PU("enc") + " " + c.s.eq.p : "") + "): “" + c.s.eq.q + "”", "small");
      for (const x of (c.s.eq && c.s.eq.more) || []) infoLine(body, PU("quote") + " (" + x.l + "): “" + x.q + "”", "small");      // the meaning of every part of a name has its own quote
      for (const x of (c.x && c.x.q) || []) infoLine(body, PU("quote") + " (" + x.l + "): “" + x.q + "”", "small");
      for (const u of new Set([(c.a || c.pk) ? c.s.u : null, c.wp, ...(c.f || []).flatMap((x) => x.s.map((q) => q.u)), c.s.eq && c.s.eq.u, ...(((c.s.eq && c.s.eq.more) || []).map((x) => x.u))].filter(Boolean))) { const d = infoLine(body, "", "small"), l = document.createElement("a"); l.href = u; l.target = "_blank"; l.rel = "noopener"; l.textContent = decodeURI(u); d.appendChild(l); }
      infoLine(body, PU("attr"), "small");
      infoLine(body, "OpenStreetMap contributors (ODbL): geometry");
    }), { id: c.id, name: c.n.en, reg: "-", link: "pl:" + c.id });
    showPopup("340px", lngLat, el);
  }
  // monuments, sculptures and memorial plaques: two lazy layers (data/sculptures.json, data/plaques.json), clustered; a monument appears in the year of its installation, a plaque in the first year of the life that
  // its inscription names (never the year of the plaque); the objects without a year are shown by a sub box; an object without a name is labelled by its type and the nearest street
  const MON_COLOR = { sculpture: "#e67700", bust: "#862e9c", monument: "#1864ab", statue: "#c92a2a", memorial: "#343a40", relief: "#0b7285" }, PLQ_COLOR = "#a61e4d";
  const MOD_COLOR = "#364fc7";                                       // the buildings of Soviet modernism: a third layer of the same kind (data/modernism.json), every building has a year of the end of the building
  const MP = { mon: { file: "data/sculptures.json", chk: "showMon", sub: "showMonUndated", leg: "monLegend" }, plq: { file: "data/plaques.json", chk: "showPlq", sub: "showPlqUndated", leg: "plqLegend" }, mod: { file: "data/modernism.json", chk: "showMod", sub: null, leg: "modLegend" } };
  const mpU = (k, key) => { const m = MP[key].data; return (m && m.ui && m.ui[k] && (m.ui[k][lang] || m.ui[k].en)) || ""; };
  function mpLoad(key) {
    const m = MP[key];
    if (m.loading) return m.loading;
    const wait = 3000 - (Date.now() - (m.failedAt || 0));            // as for the places: a new try after a failure not earlier than after 3 s, by a timer while the layer is switched on
    if (wait > 0) { if (!m.timer) m.timer = setTimeout(() => { m.timer = null; if (!m.data && $(m.chk).checked) mpLoad(key); }, wait + 50); return null; }
    m.loading = getJSON(m.file).then((d) => { m.data = d; m.byId = new Map(d.items.map((c) => [c.id, c])); searchIndex = null; mpAdd(key); updateMPUi(); }).catch((e) => { console.error(key, e && e.message); m.data = null; m.loading = null; m.failedAt = Date.now(); });
    return m.loading;
  }
  function mpName(key, c) {
    const nm = c.n[lang] || c.n.en || c.n.ru || c.n.ka;
    if (nm) return nm;
    const s = c.st && MP[key].data.streets[c.st];
    return (mpU("k_" + (key === "plq" ? "plaque" : c.k), key)) + (s ? ", " + (s[lang] || s.en) : "");
  }
  let sliding = false;
  function mpVisible(key, c) { return c.y != null ? c.y <= year : !!(MP[key].sub && $(MP[key].sub).checked); }
  function mpYearFilter(key) {
    const subOn = !!(MP[key].sub && $(MP[key].sub).checked);
    const vis = subOn ? ["any", ["get", "undated"], ["<=", ["get", "y"], year]] : ["all", ["!", ["get", "undated"]], ["<=", ["get", "y"], year]];
    return ["all", ["!", ["has", "point_count"]], vis];
  }
  function mpFeats(key, all = false) {
    const items = all ? MP[key].data.items : MP[key].data.items.filter((c) => mpVisible(key, c));
    return items.map((c) => ({ type: "Feature", geometry: { type: "Point", coordinates: [c.lon, c.lat] }, properties: { id: c.id, kind: c.k || "plaque", label: mpName(key, c), undated: c.y == null, y: c.y != null ? c.y : -99999 } }));
  }
  function mpAdd(key) {
    const m = MP[key];
    if (!m.data || !m.data.items.length || map.getSource(key + "s")) return;
    if (!map.isStyleLoaded()) { map.once("idle", () => mpAdd(key)); return; }                // the style is busy (other sources are loading): the layer is added at the next idle, not forgotten
    const col = key === "mon" ? ["match", ["get", "kind"], ...Object.entries(MON_COLOR).flat(), "#555"] : key === "mod" ? MOD_COLOR : PLQ_COLOR, base = key === "mon" ? "#1864ab" : key === "mod" ? MOD_COLOR : PLQ_COLOR;
    const clustered = key !== "mod";
    map.addSource(key + "s", clustered ? { type: "geojson", cluster: true, clusterMaxZoom: 15, clusterRadius: 38, data: { type: "FeatureCollection", features: mpFeats(key) } } : { type: "geojson", data: { type: "FeatureCollection", features: mpFeats(key, true) } });
    map.addLayer({ id: key + "-cl", type: "circle", source: key + "s", filter: clustered ? ["has", "point_count"] : ["==", "id", "__none__"], layout: { visibility: "none" }, paint: { "circle-color": base, "circle-opacity": 0.85, "circle-radius": ["step", ["get", "point_count"], 13, 10, 17, 40, 22], "circle-stroke-color": "#fff", "circle-stroke-width": 2 } });
    map.addLayer({ id: key + "-cn", type: "symbol", source: key + "s", filter: clustered ? ["has", "point_count"] : ["==", "id", "__none__"], layout: { visibility: "none", "text-field": ["get", "point_count_abbreviated"], "text-font": ["Noto Sans Bold"], "text-size": 12 }, paint: { "text-color": "#fff" } });
    map.addLayer({ id: key + "-pt", type: "circle", source: key + "s", filter: mpYearFilter(key), layout: { visibility: "none" }, paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 4, 17, 8], "circle-color": col, "circle-stroke-color": "#fff", "circle-stroke-width": 2, "circle-opacity": ["case", ["get", "undated"], 0.55, 1] } });
    map.addLayer({ id: key + "-lb", type: "symbol", source: key + "s", minzoom: 16, filter: mpYearFilter(key), layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 11, "text-offset": [0, 1.1], "text-anchor": "top", "text-optional": true }, paint: { "text-color": "#212529", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", key + "-pt", (e) => { const f = e.features && e.features[0], c = f && m.byId.get(f.properties.id); if (c) popupMP(key, c, e.lngLat); });
    map.on("click", key + "-cl", (e) => {
      const f = map.queryRenderedFeatures(e.point, { layers: [key + "-cl"] })[0];
      map.getSource(key + "s").getClusterExpansionZoom(f.properties.cluster_id).then((z) => map.easeTo({ center: f.geometry.coordinates, zoom: z + 0.5 }));
    });
    for (const l of [key + "-pt", key + "-cl"]) { map.on("mouseenter", l, () => { map.getCanvas().style.cursor = "pointer"; }); map.on("mouseleave", l, () => { map.getCanvas().style.cursor = ""; }); }
    m.sig = null; m.langSig = lang;
    updateMP(key);
  }
  function updateMP(key) {
    const m = MP[key], on = $(m.chk).checked;
    if (m.sub) $(m.sub).closest("label").hidden = !on;
    if (on && !m.data) mpLoad(key);
    syncLegend(m.chk, m.leg);
    if (m.data && !map.getSource(key + "s")) mpAdd(key);
    if (!map.getSource(key + "s")) return;
    clearTimeout(m.timer);
    if (on) {
      const flt = mpYearFilter(key);
      map.setFilter(key + "-pt", flt);
      map.setFilter(key + "-lb", flt);
      if (key === "mod") {
        if (m.langSig !== lang) { m.langSig = lang; map.getSource(key + "s").setData({ type: "FeatureCollection", features: mpFeats(key, true) }); }
      } else {
        const curSig = () => [year, m.sub ? $(m.sub).checked : "", lang].join("|");
        if (m.sig !== curSig()) {
          const applyData = () => {
            const s = curSig();
            if (m.sig === s || !map.getSource(key + "s")) return;
            m.sig = s;
            map.getSource(key + "s").setData({ type: "FeatureCollection", features: mpFeats(key) });
          };
          if (sliding) m.timer = setTimeout(applyData, 160);
          else applyData();
        }
      }
    }
    for (const l of ["cl", "cn", "pt", "lb"]) { map.setLayoutProperty(key + "-" + l, "visibility", on ? "visible" : "none"); map.moveLayer(key + "-" + l); }
  }
  function updateMPUi() {
    for (const key of ["mon", "plq", "mod"]) {
      const box = $(MP[key].leg), m = MP[key];
      if (box) {
        box.textContent = "";
        const kinds = m.data ? [...new Set(m.data.items.map((c) => c.k))].filter(Boolean) : [];
        for (const k of Object.keys(MON_COLOR)) if (key === "mon" && kinds.includes(k)) { const s = document.createElement("span"); s.textContent = mpU("k_" + k, key); s.style.setProperty("--c", MON_COLOR[k]); box.appendChild(s); }
        if (key === "plq" && m.data) { const s = document.createElement("span"); s.textContent = mpU("k_plaque", key); s.style.setProperty("--c", PLQ_COLOR); box.appendChild(s); }
        if (key === "mod" && m.data) { const s = document.createElement("span"); s.textContent = mpU("k_modernism", key); s.style.setProperty("--c", MOD_COLOR); box.appendChild(s); }
        syncLegend(m.chk, m.leg);
      } else {                                                        // a layer of one kind (plaques, modernism) has no legend line of its own: its colour is a dot in the row of the box
        const lb = $(m.chk).closest("label");
        if (lb) { lb.classList.add("ldot"); lb.style.setProperty("--c", key === "mod" ? MOD_COLOR : PLQ_COLOR); }
      }
      if (m.sig) m.sig = null;
      updateMP(key);
    }
  }
  // a building of Soviet modernism: the year, architects, what it was built for and what it is now, the condition, the description, folk names, a photograph, the sources (every source has its quotation in the details)
  function popupMod(c, lngLat) {
    const d = MP.mod.data, U = (k) => mpU(k, "mod");
    reopenPopup = () => popupMod(c, lngLat);
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = c.n[lang] || c.n.en;
    el.appendChild(h3);
    const add = (txt, cls) => { const x = document.createElement("div"); if (cls) x.className = cls; x.textContent = txt; el.appendChild(x); return x; };
    const row = (k, v) => { if (!v) return; const x = add("", ""), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; x.appendChild(kk); x.appendChild(document.createTextNode(v)); };
    add(U("k_modernism"), "k");
    if (c.d && (c.d[lang] || c.d.en)) add(c.d[lang] || c.d.en);
    row(U("built"), c.y != null ? String(c.y) : "");
    row(U("architects"), (c.ar || []).join(", "));
    row(U("was"), c.ft && (c.ft[lang] || c.ft.en));
    row(U("now"), c.fn && (c.fn[lang] || c.fn.en));
    row(U("status"), U("st_" + c.st));
    folkBlock(el, c, U);
    mpPhoto(el, c, d, U, c.n[lang] || c.n.en, add);
    const s = add("", "src");
    s.appendChild(document.createTextNode(U("src") + ": "));
    c.s.forEach((q, i) => { if (i) s.appendChild(document.createTextNode("; ")); const a = document.createElement("a"); a.href = q.u; a.target = "_blank"; a.rel = "noopener"; a.textContent = hostLabel(q.u, q.l); s.appendChild(a); });
    const origin = { osm: "OpenStreetMap contributors (ODbL): geometry", wikidata: "Wikidata: coordinates", wikipedia: "Wikipedia: coordinates", page: "coordinates: " + (c.g && c.g.ref) }[c.g && c.g.how] || "";
    actions(el, () => openInfo((body) => {
      infoLine(body, (c.n[lang] || c.n.en) + ":");
      for (const q of c.s) infoLine(body, U("quote") + " (" + q.l + ", " + q.f + "): “" + q.q + "”", "small");
      for (const x of c.f || []) for (const q of x.s) infoLine(body, U("folk") + " «" + (x.n[lang] || x.n.ka || x.n.ru || x.n.en) + "» — " + U("quote") + " (" + q.l + "): “" + q.q + "”", "small");
      for (const u of new Set([...c.s.map((q) => q.u), ...(c.f || []).flatMap((x) => x.s.map((q) => q.u))])) { const dd = infoLine(body, "", "small"), l = document.createElement("a"); l.href = u; l.target = "_blank"; l.rel = "noopener"; l.textContent = decodeURI(u); dd.appendChild(l); }
      if (c.wd) infoLine(body, "Wikidata: " + c.wd, "small");
      infoLine(body, U("attr"), "small");
      if (origin) infoLine(body, origin, "small");
    }), { id: "MOD:" + c.id, name: c.n.en || "", reg: "-", link: "md:" + c.id });
    showPopup("340px", lngLat, el);
  }
  // the photograph of a card of the monuments layers (data of the layer: photos[file] = {thumb, page, author, license}); c.phn: found by the coordinates only
  function mpPhoto(el, c, d, U, alt, add) {
    const f = c.ph && d.photos[c.ph];
    if (!(f && f.thumb)) return;
    const fig = document.createElement("figure"), a = document.createElement("a"), img = document.createElement("img");
    fig.className = "ph main"; a.href = f.page; a.target = "_blank"; a.rel = "noopener"; img.src = f.thumb; img.loading = "lazy"; img.alt = alt; if (f.w && f.h) { img.width = f.w; img.height = f.h; } a.appendChild(img); fig.appendChild(a);
    const box = document.createElement("div"); box.className = "photos"; box.appendChild(fig); el.appendChild(box);
    const cr = add("", "small phcred");
    cr.appendChild(document.createTextNode(U("photo") + " · " + [f.author || "?", f.license || ""].filter(Boolean).join(" · ") + " · "));
    const l = document.createElement("a"); l.href = f.page; l.target = "_blank"; l.rel = "noopener"; l.textContent = "Commons"; cr.appendChild(l);
    if (c.phn) add(t().photo, "small");                                       // found by the coordinates only: it may show a neighbouring object
  }
  function popupMP(key, c, lngLat) {
    if (key === "mod") return popupMod(c, lngLat);
    const m = MP[key], d = m.data, U = (k) => mpU(k, key);
    reopenPopup = () => popupMP(key, c, lngLat);
    const el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = mpName(key, c);
    el.appendChild(h3);
    const add = (txt, cls) => { const x = document.createElement("div"); if (cls) x.className = cls; x.textContent = txt; el.appendChild(x); return x; };
    const row = (k, v) => { if (!v) return; const x = add("", ""), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; x.appendChild(kk); x.appendChild(document.createTextNode(v)); };
    add(U("k_" + (key === "plq" ? "plaque" : c.k)), "k");
    if (key === "mon") row(U("year"), c.y != null ? String(c.y) : U("year_unknown"));
    else if (c.y != null) add(U("lived_from").replace("{y}", c.y), "small");
    if (c.d && c.d[lang]) { if (c.dw) add(U(key === "plq" ? "from_wiki_person" : "from_wiki"), "k"); add(c.d[lang], "small"); }          // the description of OSM / Wikipedia, in the language that exists; a Wikipedia text is labelled (about the person on a plaque)
    if (key === "mon") { row(U("sculptor"), c.sc && typeof c.sc === "object" ? (c.sc[lang] || c.sc.en) : c.sc); row(U("architect"), c.ar); row(U("material"), c.mat ? U("mat_" + c.mat) : ""); }
    const s = c.st && d.streets[c.st];
    if (s) row(U("where"), s[lang] || s.en);
    if (key === "plq" && c.ins) add(U("inscription") + ": " + c.ins, "small");
    mpPhoto(el, c, d, U, mpName(key, c), add);
    const wl = [lang, "en", "ka", "ru"].find((l2) => c.w && c.w[l2]);
    if (wl) { const x = add("", "src"), a = document.createElement("a"); a.href = c.w[wl]; a.target = "_blank"; a.rel = "noopener"; a.textContent = "Wikipedia (" + wl + ")"; x.appendChild(a); }
    actions(el, () => openInfo((body) => { infoLine(body, mpName(key, c) + ":"); for (const q of c.dq || []) infoLine(body, U("quote") + " (" + q.l + "): “" + q.q + "”", "small"); infoLine(body, U("attr"), "small"); infoLine(body, "OpenStreetMap contributors (ODbL): geometry"); }), { id: (key === "mon" ? "MON:" : "PLQ:") + c.id, name: c.n.en || "", reg: "-", link: (key === "mon" ? "mn:" : "pq:") + c.id });
    showPopup("320px", lngLat, el);
  }
  for (const id of ["showMon", "showMonUndated", "showPlq", "showPlqUndated", "showMod"]) $(id).addEventListener("change", () => updateMP(id.startsWith("showMon") ? "mon" : id === "showMod" ? "mod" : "plq"));
  $("showPlaces").addEventListener("change", updatePlaces);
  $("showPlaceAreas").addEventListener("change", applyPlaceAreas);
  $("showSci").addEventListener("change", updateScience);
  $("showEdu").addEventListener("change", updateEducation);
  $("showMus").addEventListener("change", updateMuseums);
  $("showBattles").addEventListener("change", () => { if (histEvents.length) buildEvMarks(); });

  // religious buildings of different religions: points that appear in the year of the building and disappear when it was destroyed
  const REL_COLOR = { orthodox: "#b8860b", russian: "#6741d9", lutheran: "#868e96", yazidi: "#74b816", armenian: "#c2255c", catholic: "#1971c2", jewish: "#2f9e44", muslim: "#087f5b", zoroastrian: "#e8590c", christian: "#8d6e63", christianOsm: "#8d6e63" };
  let relExtra = { ui: {}, streets: {} };                                                // data/religious_osm.json: the buildings of OpenStreetMap that are not in the curated layer and the register (loaded after the first screen)
  const relNameOf = (k, l) => { const lg = l || lang; return (T[lg] && T[lg].relNames[k]) || (relExtra.ui[k] && (relExtra.ui[k][lg] || relExtra.ui[k].en)) || k; };
  function relTitle(r) {                                                                 // the name; a building without a name is "denomination, nearest street"
    const nm = r.name[lang] || r.name.en || r.name.ru || r.name.ka;
    if (nm) return nm;
    const st = r.st && relExtra.streets[r.st];
    return relNameOf(r.rel) + (st ? ", " + (st[lang] || st.en) : "");
  }
  const relFeats = () => religious.map((r) => ({ type: "Feature", geometry: { type: "Point", coordinates: [r.lon, r.lat] },
    properties: { id: r.id, from: r.from, to: r.to === undefined ? 99999 : r.to, color: REL_COLOR[r.rel] || "#555", undated: !!r.undated, label: relTitle(r) } }));
  let relOsmLoading = null, relOsmFailedAt = 0;
  function loadReligiousOsm() {
    if (relOsmLoading || Date.now() - relOsmFailedAt < 3000) return;
    relOsmLoading = getJSON("data/religious_osm.json").then((d) => {
      relExtra = { ui: d.ui || {}, streets: d.streets || {} };
      for (const r of d.items) religious.push(r);
      searchIndex = null;
      const src = map.getSource("rel");
      if (src) src.setData({ type: "FeatureCollection", features: relFeats() });
      buildRelLegend();
    }).catch((e) => { console.error("religious_osm", e && e.message); relOsmLoading = null; relOsmFailedAt = Date.now(); setTimeout(loadReligiousOsm, 3500); });
  }
  function addReligious() {
    if (!religious.length || map.getSource("rel")) return;
    map.addSource("rel", { type: "geojson", data: { type: "FeatureCollection", features: relFeats() } });
    map.addLayer({ id: "rel-pt", type: "circle", source: "rel", layout: { visibility: "none" }, paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 5, 17, 10], "circle-color": ["get", "color"], "circle-opacity": ["case", ["get", "undated"], 0.55, 1], "circle-stroke-color": "#ffffff", "circle-stroke-width": 2 } });   // pale: the register gives no date
    map.addLayer({ id: "rel-lb", type: "symbol", source: "rel", minzoom: 14.5, layout: { visibility: "none", "text-field": ["get", "label"], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, 1.2], "text-anchor": "top", "text-optional": true }, paint: { "text-color": "#222222", "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    map.on("click", "rel-pt", (e) => {
      const f = e.features && e.features[0], r = f && religious.find((x) => x.id === f.properties.id);
      if (r) popupRel(r, e.lngLat);
    });
    map.on("mouseenter", "rel-pt", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "rel-pt", () => { map.getCanvas().style.cursor = ""; });
    updateReligious();
  }
  let relLegendKey = "", relLegendOpen = false;
  function buildRelLegend() {
    const box = $("relLegend");
    if (!box) return;
    const present = new Set();
    for (const r of religious) if (r.from <= year && (r.to === undefined || r.to > year)) present.add(r.rel);      // the same rule as the filter of the layer
    const keys = Object.keys(REL_COLOR).filter((k) => present.has(k));
    const key = lang + "|" + keys.join(",");
    if (key !== relLegendKey) {
      relLegendKey = key;
      box.textContent = "";
      if (keys.length) {
        const d = document.createElement("details"), sm = document.createElement("summary"), list = document.createElement("div");
        d.open = relLegendOpen;
        d.addEventListener("toggle", () => { relLegendOpen = d.open; });
        sm.setAttribute("aria-label", t().legTitle); sm.title = t().legTitle;
        list.className = "rlist";
        for (const k of keys) {
          const dot = document.createElement("i"); dot.className = "rdot"; dot.style.setProperty("--c", REL_COLOR[k]); sm.appendChild(dot);
          const s = document.createElement("span"); s.textContent = relNameOf(k); s.style.setProperty("--c", REL_COLOR[k]);
          if (k === "christian" || k === "christianOsm") s.className = "wide";
          list.appendChild(s);
        }
        d.appendChild(sm); d.appendChild(list); box.appendChild(d);
      }
    }
    syncLegend("showRel", "relLegend");
  }
  function updateReligious() {
    buildRelLegend();
    if (!map.getLayer("rel-pt")) return;
    const on = $("showRel").checked;
    for (const id of ["rel-pt", "rel-lb"]) {
      map.moveLayer(id);                                              // to the top: above the topographic map and the points of the register (the layer of science and culture goes above this one)
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      map.setFilter(id, ["all", ["<=", ["get", "from"], year], [">", ["get", "to"], year]]);
    }
  }
  function updateRelUi() {
    buildRelLegend();
    const src = map && map.getSource && map.getSource("rel");
    if (src) src.setData({ type: "FeatureCollection", features: relFeats() });
  }
  function popupRel(r, lngLat) {
    reopenPopup = () => popupRel(r, lngLat);
    const L = t(), el = document.createElement("div");
    el.className = "pop";
    const h3 = document.createElement("h3");
    h3.textContent = relTitle(r);
    el.appendChild(h3);
    const row = (k, v) => { if (!v) return; const d = document.createElement("div"), kk = document.createElement("span"); kk.className = "k"; kk.textContent = k + ": "; d.appendChild(kk); d.appendChild(document.createTextNode(v)); el.appendChild(d); };
    const rr = document.createElement("div");
    rr.className = "k";
    rr.textContent = relNameOf(r.rel);
    el.appendChild(rr);
    row(L.relBuilt, r.undated ? (r.osm ? relNameOf("relUndatedOsm") : L.relUndated) : r.date);      // an OSM building: "not given in OpenStreetMap" (the register wording is for the register)
    if (r.approx) row(L.relApprox, "≈");
    if (r.to !== undefined) row(L.relGone, String(r.to));
    if (r.status) row(L.relStatus, r.status[lang] || r.status.en);
    if (r.addr) row(L.relAddr, r.addr[lang] || r.addr.en);
    cardPhotos(el, r);
    const n = document.createElement("div");
    n.className = "small";
    n.textContent = r.note ? (r.note[lang] || r.note.en) : "";
    if (r.note) el.appendChild(n);
    const s = document.createElement("div");
    s.className = "src";
    s.appendChild(document.createTextNode(L.relSrc + ": "));
    if (r.osm) { const a = document.createElement("a"); a.href = "https://www.openstreetmap.org/" + r.osm; a.target = "_blank"; a.rel = "noopener"; a.textContent = "OpenStreetMap"; s.appendChild(a); if (r.src.length) s.appendChild(document.createTextNode("; ")); }
    else if (!r.src.length) s.appendChild(document.createTextNode(L.relRegSrc + " " + (r.regno ? L.relRegNo + " " + r.regno : L.relRegId + " " + r.rid)));      // a register object: no web page to link to
    r.src.forEach((u, i) => { const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener"; a.textContent = decodeURIComponent(u.replace("https://", "")).slice(0, 60); if (i) s.appendChild(document.createTextNode(" \u00B7 ")); s.appendChild(a); });
    el.appendChild(s);
    actions(el, null, fbRef("REL", r.id, el));
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
    for (const c of education) idx.push({ kind: "d", c, key: normQ([c.name.ru, c.name.en, c.name.ka, c.built, c.from, T.ru.eduKinds[c.kind], T.en.eduKinds[c.kind]].join(" ")) });
    for (const c of museums) idx.push({ kind: "mu", c, key: normQ([c.name.ru, c.name.en, c.name.ka, c.founded, c.built, c.from, T.ru.musKinds[c.kind], T.en.musKinds[c.kind]].join(" ")) });
    for (const r of religious) idx.push({ kind: "r", r, key: normQ([r.name.ru, r.name.en, r.name.ka, r.date, relNameOf(r.rel), relNameOf(r.rel, "en")].join(" ")) });
    for (const st of stNames) {                                 // streets: the name today and every former name (also the ones without a year) in three languages
      const nm = [st.now.ru, st.now.en, st.now.ka];
      for (const iv of st.iv) if (iv[2]) nm.push(iv[2].ru, iv[2].en, iv[2].ka);
      for (const u of st.undated || []) nm.push(u.ru, u.en, u.ka);
      idx.push({ kind: "t", st, key: normQ(nm.join(" ")) });
    }
    for (const f of trStations) { const p = f.properties; idx.push({ kind: "m", f, key: normQ([p.name_ru, p.name_en, p.name_ka].join(" ")) }); }      // the stations of the metro
    for (const c of (places ? places.items : [])) idx.push({ kind: "p", c, key: normQ([c.n.ru, c.n.en, c.n.ka, ...folkNames(c)].join(" ")) });                           // local names
    for (const key of ["mon", "plq", "mod"]) for (const c of (MP[key].data ? MP[key].data.items : [])) if (c.n.ru || c.n.en || c.n.ka) idx.push({ kind: key === "plq" ? "q" : "k", key2: key, c, key: normQ([c.n.ru, c.n.en, c.n.ka, ...folkNames(c)].join(" ")) });      // monuments and plaques that are loaded and have a name
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
  let miniSearch = null, miniLoading = null;
  const msTok = (s) => String(s || "").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/ё/g, "е").split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  function ensureMiniSearch() {
    if (miniSearch || miniLoading) return;
    miniLoading = Promise.all([
      window.MiniSearch ? Promise.resolve() : verUrl("vendor/minisearch.js").then((vu) => new Promise((res, rej) => { const sc = document.createElement("script"); sc.src = vu; sc.onload = res; sc.onerror = rej; document.head.appendChild(sc); })),
      getJSON("data/search_index.json", 2),
    ]).then(([, docs]) => {
      const ms = new window.MiniSearch({
        fields: ["n", "ex"],
        storeFields: ["id", "y", "l"],
        tokenize: msTok,
        processTerm: (term) => term.replace(/ё/g, "е"),
      });
      ms.addAll(docs);
      miniSearch = ms;
      if (!$("search").hidden && $("searchQ").value) renderSearch();
    }).catch(() => { miniLoading = null; });
  }
  function runSearch(q) {
    const toks = normQ(q).split(" ").filter(Boolean);
    const rows = [];
    if (!toks.length) return rows;
    if (/^\d{3,4}$/.test(toks[0]) && toks.length === 1 && +toks[0] >= MIN && +toks[0] <= MAX) rows.push({ kind: "y", year: +toks[0] });
    if (miniSearch) {
      const hits = miniSearch.search(q, { combineWith: "AND", boost: { n: 3, ex: 1.5 }, prefix: true, fuzzy: (term) => (term.length >= 5 ? 0.2 : false) });
      for (const h of hits.slice(0, 40)) rows.push({ kind: "msx", doc: h });
      rows.more = hits.length > 40;
      return rows;
    }
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
      else if (r.kind === "d") { a.textContent = "\uD83C\uDFEB " + (r.c.name[lang] || r.c.name.en); b.textContent = [L.eduKinds[r.c.kind], r.c.undated ? L.relUndated : (r.c.built || r.c.from)].filter(Boolean).join(" \u00B7 "); }
      else if (r.kind === "r") { a.textContent = "\u26EA " + relTitle(r.r); b.textContent = [relNameOf(r.r.rel), r.r.date, r.r.to ? L.relGone + " " + r.r.to : ""].filter(Boolean).join(" \u00B7 "); }
      else if (r.kind === "e") { a.textContent = (EV_ICON[r.ev.cat] || EV_ICON.other) + " " + (r.ev[lang] || r.ev.en); b.textContent = r.ev.date + " \u00B7 " + (L.evCats[r.ev.cat] || ""); }
      else if (r.kind === "m") { const mp = r.f.properties; a.textContent = "\u24C2 " + (mp["name_" + lang] || mp.name_en); b.textContent = L.trKinds.metro_station + " \u00B7 " + L.trPeriod(+mp.y0, 9999, -1, -1); }
      else if (r.kind === "p") { a.textContent = "\uD83D\uDCCD " + (r.c.n[lang] || r.c.n.en); b.textContent = PU("kind_" + r.c.k); }
      else if (r.kind === "k" || r.kind === "q") { a.textContent = (r.key2 === "mod" ? "\uD83C\uDFDB " : r.kind === "k" ? "\uD83D\uDDFF " :"\uD83D\uDD16 ") + mpName(r.key2, r.c); b.textContent = [mpU("k_" + (r.kind === "q" ? "plaque" : r.c.k), r.key2), r.c.y != null ? r.c.y : ""].filter(Boolean).join(" \u00B7 "); }
      else if (r.kind === "t") {
        a.textContent = "\uD83D\uDEE3 " + (r.st.now[lang] || r.st.now.en);
        const old = [...r.st.iv.filter((iv) => iv[2]).map((iv) => pickName(iv[2])), ...(r.st.undated || []).map((u) => pickName(u))];
        b.textContent = old.slice(0, 4).join(" \u00B7 ") + (old.length > 4 ? " ..." : "");
      }
      else if (r.kind === "msx") {
        const [pfx, ...rest] = r.doc.id.split(":"), id = rest.join(":");
        const ico = { o: "\uD83C\uDFDB\uFE0F ", e: "\uD83D\uDCC5 ", u: "\uD83D\uDC51 ", sc: "\uD83D\uDD2C ", ed: "\uD83C\uDFEB ", mu: "\uD83C\uDFDB ", rl: "\u26EA ", st: "\uD83D\uDEE3 ", ms: "\u24C2 ", pl: "\uD83D\uDCCD ", mn: "\uD83D\uDDFF ", pq: "\uD83D\uDD16 ", md: "\uD83C\uDFDB " }[pfx] || "";
        const li = lang === "ru" ? 0 : lang === "ka" ? 2 : 1;
        a.textContent = ico + (r.doc.l[li] || r.doc.l[1] || r.doc.l[0] || r.doc.l[2] || "\u2014");
        if (pfx === "ms") b.textContent = L.trKinds.metro_station + (r.doc.y != null ? " \u00B7 " + L.trPeriod(+r.doc.y, 9999, -1, -1) : "");
        else if (pfx === "st") {
          const st = stNames.find((x) => (x.geom || x.now.en) === id);
          if (st) { const old = [...st.iv.filter((iv) => iv[2]).map((iv) => pickName(iv[2])), ...(st.undated || []).map((u) => pickName(u))]; b.textContent = old.slice(0, 4).join(" \u00B7 ") + (old.length > 4 ? " ..." : ""); }
        } else if (pfx === "pl" && places) {
          const c = places.items.find((x) => x.id === id);
          if (c) b.textContent = PU("kind_" + c.k);
        } else b.textContent = r.doc.y != null ? String(r.doc.y) : "";
      }
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
    ensureMiniSearch();
    if (!places) ensurePlaces();                                   // the local names join the search as soon as their file is loaded
    $("searchQ").focus(); $("searchQ").select();
    if ($("searchQ").value) renderSearch();
  }
  function pickSearch(r) {
    closeSearch();
    if (r.kind === "msx") {
      const [pfx, ...rest] = r.doc.id.split(":"), id = rest.join(":");
      if (pfx === "e" && histEvents[+id]) r = { kind: "e", ev: histEvents[+id] };
      else if (pfx === "u" && rulersData) { const u = rulersData.rulers.concat(rulersData.states).find((x) => x.id === id); if (u) r = { kind: "u", u }; }
      else if (pfx === "o") { const f = monAllById.get(id); if (f) r = { kind: "o", f }; }
      else if (pfx === "rl") { const c = religious.find((x) => x.id === id); if (c) r = { kind: "r", r: c }; }
      else if (pfx === "sc") { const c = science.find((x) => x.id === id); if (c) r = { kind: "s", c }; }
      else if (pfx === "ed") { const c = education.find((x) => x.id === id); if (c) r = { kind: "d", c }; }
      else if (pfx === "mu") { const c = museums.find((x) => x.id === id); if (c) r = { kind: "mu", c }; }
      else if (pfx === "st") { const st = stNames.find((x) => (x.geom || x.now.en) === id); if (st) r = { kind: "t", st }; }
      else if (pfx === "ms") { const f = trStations.find((x) => x.properties.id === id); if (f) r = { kind: "m", f }; }
      else if (pfx === "pl" && places) { const c = places.items.find((x) => x.id === id); if (c) r = { kind: "p", c }; }
      else if (pfx === "mn" || pfx === "pq" || pfx === "md") {
        const k2 = pfx === "mn" ? "mon" : pfx === "md" ? "mod" : "plq";
        const c = MP[k2].byId && MP[k2].byId.get(id);
        if (c) r = { kind: pfx === "pq" ? "q" : "k", key2: k2, c };
      }
      if (r.kind === "msx") { openLinked(r.doc.id); return; }
    }
    let target = year;
    if (r.kind === "y") target = r.year;
    else if (r.kind === "e") target = r.ev.year;
    else if (r.kind === "u") target = (year >= r.u.from && year < r.u.to) ? year : Math.floor(r.u.from);
    else if (r.kind === "s") target = Math.max(year, r.c.from);
    else if (r.kind === "d") target = Math.max(year, r.c.from);
    else if (r.kind === "mu") target = Math.max(year, r.c.from);
    else if (r.kind === "r") target = (year >= r.r.from && (r.r.to === undefined || year < r.r.to)) ? year : r.r.from;
    else if (r.kind === "m") target = Math.max(year, r.f.properties.y0);
    else if (r.kind === "p") target = year;
    else if (r.kind === "k" || r.kind === "q") target = r.c.y != null ? Math.max(year, r.c.y) : year;
    else if (r.kind === "t") { const own = r.st.iv.find((iv) => iv[2] && year >= iv[0] && year < iv[1]); target = own ? year : (r.st.iv.find((iv) => iv[2]) || [year])[0]; }
    else target = (r.f && typeof r.f.properties.ye === "number") ? Math.max(year, r.f.properties.ye) : year;
    year = target;
    update();
    if (r.kind === "e") { showHistEvent(r.ev); return; }
    if (r.kind === "t") { showStreetCard(r.st, true); return; }
    if (r.kind === "m") {
      const c = r.f.geometry.coordinates;
      map.flyTo({ center: c, zoom: Math.max(map.getZoom(), 16), duration: 1200 });
      transportPopup({ ...r.f.properties, src: JSON.stringify(r.f.properties.src || []) }, { lng: c[0], lat: c[1] });
      return;
    }
    if (r.kind === "k" || r.kind === "q") {
      const m = MP[r.key2];
      $(m.chk).checked = true; if (r.c.y == null && m.sub) $(m.sub).checked = true; updateMP(r.key2);
      if (openPop) openPop.remove();
      map.flyTo({ center: [r.c.lon, r.c.lat], zoom: Math.max(map.getZoom(), 17), duration: 1200 });
      popupMP(r.key2, r.c, { lng: r.c.lon, lat: r.c.lat });
      return;
    }
    if (r.kind === "p") {
      $("showPlaces").checked = true; updatePlaces();
      if (openPop) openPop.remove();
      map.flyTo({ center: [r.c.lon, r.c.lat], zoom: Math.max(map.getZoom(), 15.5), duration: 1200 });
      popupPlace(r.c, { lng: r.c.lon, lat: r.c.lat });
      return;
    }
    if (r.kind === "u") {
      $("showRulers").checked = true; buildRulersBand(); updateRuleLine(); syncFilterUi();
      showRulerCard(r.u);
      return;
    }
    if (r.kind === "s") {
      $("showSci").checked = true; updateScience();
      map.flyTo({ center: [r.c.lon, r.c.lat], zoom: Math.max(map.getZoom(), 16.5), duration: 1200 });
      popupSci(r.c, { lng: r.c.lon, lat: r.c.lat });
      return;
    }
    if (r.kind === "d") {
      $("showEdu").checked = true; updateEducation();
      map.flyTo({ center: [r.c.lon, r.c.lat], zoom: Math.max(map.getZoom(), 16.5), duration: 1200 });
      popupEdu(r.c, { lng: r.c.lon, lat: r.c.lat });
      return;
    }
    if (r.kind === "mu") {
      $("showMus").checked = true; updateMuseums();
      map.flyTo({ center: [r.c.lon, r.c.lat], zoom: Math.max(map.getZoom(), 16.5), duration: 1200 });
      popupMus(r.c, { lng: r.c.lon, lat: r.c.lat });
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
  window.addEventListener("resize", () => { if (urbanSnaps.length || plans.length) buildTicks(); buildEpochBand(); buildRulersBand(); });
  $("slider").value = Math.round(y2v(year));
  $("year").textContent = year;
})();
