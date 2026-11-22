// Checks of the data and of the texts of the site; run by hand (node tests/check_data.mjs) and by the workflow before every deploy.
// They stop the deploy when a translation is missing, when a Georgian text is not Georgian (Cyrillic, English), when a file that the page
// needs is missing or a JSON file is broken. No dependencies: only Node.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const SITE = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "site");
const errors = [];
const warns = [];
const err = (m) => errors.push(m);
const GE = /[ა-ჿ]/g, CY = /[Ѐ-ӿ]/g, LAT = /[A-Za-z]/g;
const count = (re, s) => (s.match(re) || []).length;

// ---- all JSON files parse -------------------------------------------------------------------------------
function listFiles(dir, ext, out = []) {
  for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, f.name);
    if (f.isDirectory()) listFiles(p, ext, out);
    else if (ext.some((e) => f.name.endsWith(e))) out.push(p);
  }
  return out;
}
const rel = (p) => path.relative(SITE, p).split(path.sep).join("/");
const data = {};
for (const p of listFiles(path.join(SITE, "data"), [".json", ".geojson"]).concat([path.join(SITE, "manifest.webmanifest")])) {
  try { data[rel(p)] = JSON.parse(fs.readFileSync(p, "utf8")); } catch (e) { err(`${rel(p)}: not valid JSON (${e.message})`); }
}

// ---- the list of literature (made by tools/build_bibliography.py) -------------------------------------------
{
  const b = data["data/bibliography.json"];
  if (!b) err("data/bibliography.json: missing (python tools/build_bibliography.py)");
  else {
    const ev = data["data/history_events.json"]?.events?.length;
    if (b.events !== ev) err(`data/bibliography.json: made for ${b.events} events, the data has ${ev}; run python tools/build_bibliography.py`);
    for (const g of ["books", "consulted"]) {
      if (!Array.isArray(b[g]) || !b[g].length) err(`data/bibliography.json: no ${g}`);
      for (const x of b[g] || []) {
        if (typeof x.ref !== "string" || !x.ref.trim()) err(`data/bibliography.json: an entry of ${g} without ref`);
        for (const l of x.links || []) if (!/^https?:\/\//.test(l.u || "")) err(`data/bibliography.json: bad link ${JSON.stringify(l)}`);
      }
    }
    if (!Array.isArray(b.web) || !b.web.length) err("data/bibliography.json: no web");
  }
}

// ---- every local picture of the window "Views" has its small copy (tools/make_view_thumbs.py) ---------------------
{
  const views = data["data/views.json"];
  if (Array.isArray(views)) for (const v of views) {
    if (/^https?:/.test(v.image || "")) continue;
    const name = path.basename(v.image).replace(/\.\w+$/, ".webp");
    if (!fs.existsSync(path.join(SITE, "data", "views", "thumb", name))) err(`data/views.json: ${v.id} has no thumbnail data/views/thumb/${name} (run python tools/make_view_thumbs.py)`);
  }
}

// ---- the plans: every plan has a light copy for the first screen (tools/make_plan_overviews.py) ----------
for (const p of JSON.parse(fs.readFileSync(path.join(SITE, "data", "plans.json"), "utf8"))) {
  if (!p.overview || !fs.existsSync(path.join(SITE, p.overview))) err(`data/plans.json: the plan ${p.id} has no light copy (run python tools/make_plan_overviews.py)`);
  else if (fs.statSync(path.join(SITE, p.overview)).size >= fs.statSync(path.join(SITE, p.image)).size) err(`data/plans.json: the light copy of ${p.id} is not lighter than the plan`);
}

// ---- JavaScript syntax of the files of the site (not the vendor) ------------------------------------------
// the entry app.js and the files of site/js are ES modules (checked by node --check as modules), the other files are classic scripts
const MODULES = ["app.js", ...(fs.existsSync(path.join(SITE, "js")) ? fs.readdirSync(path.join(SITE, "js"), { recursive: true }).filter((f) => String(f).endsWith(".js")).map((f) => "js/" + String(f).split(path.sep).join("/")) : [])];
for (const f of fs.readdirSync(SITE).filter((f) => f.endsWith(".js") && f !== "app.js")) {
  const p = path.join(SITE, f);
  try { new vm.Script(fs.readFileSync(p, "utf8"), { filename: p }); } catch (e) { err(`${rel(p)}: syntax error (${e.message})`); }
}
for (const f of MODULES) {
  const r = spawnSync(process.execPath, ["--check", "--input-type=module"], { input: fs.readFileSync(path.join(SITE, f), "utf8"), encoding: "utf8" });
  if (r.status !== 0) err(`${f}: syntax error as a module (${(r.stderr || "").split(String.fromCharCode(10)).find((l) => /Error/.test(l)) || "see node --check"})`);
}

// ---- the rule for a text in three languages ---------------------------------------------------------------
// ru: the original; en: must not contain Cyrillic and must be Latin when ru is a text; ka: must be Georgian, without Cyrillic.
function checkTriple(where, o, { allowEmpty = false } = {}) {
  const { ru, en, ka } = o;
  if (![ru, en, ka].every((x) => typeof x === "string")) return;
  if (!ru.trim()) { if (en.trim() || ka.trim()) err(`${where}: ru is empty but en/ka are not`); return; }
  // a single Cyrillic letter in quotes is a letter that is described ("in the form of the Russian letter T"), not a text
  const noLetters = (s) => s.replace(/[„"“]([Ѐ-ӿ])[“”"]/g, "$1".replace("$1", ""));
  const en0 = en, ka0 = ka;
  const ruWords = count(CY, ru) >= 3;
  if (!allowEmpty && !en.trim()) err(`${where}: en is empty`);
  if (!allowEmpty && !ka.trim()) err(`${where}: ka is empty`);
  if (count(CY, noLetters(en0)) > 0) err(`${where}: en contains Cyrillic: ${en.slice(0, 60)}`);
  if (count(CY, noLetters(ka0)) > 0) err(`${where}: ka contains Cyrillic: ${ka.slice(0, 60)}`);
  if (ruWords && ka.trim() && count(GE, ka) === 0) err(`${where}: ka has no Georgian letters (a foreign text?): ${ka.slice(0, 60)}`);
  if (ruWords && en.trim() && count(LAT, en) === 0) err(`${where}: en has no Latin letters: ${en.slice(0, 60)}`);
}
function walkTriples(file, node, trail = "") {
  if (Array.isArray(node)) node.forEach((v, i) => walkTriples(file, v, `${trail}[${i}]`));
  else if (node && typeof node === "object") {
    if ("ru" in node && "en" in node && "ka" in node) checkTriple(`${file}${trail}`, node);
    for (const [k, v] of Object.entries(node)) walkTriples(file, v, `${trail}/${k}`);
  }
}
for (const [f, d] of Object.entries(data)) walkTriples(f, d);

// ---- the dictionaries of the interface (i18n.js) --------------------------------------------------------------
let T = null;
try {
  const ctx = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(SITE, "i18n.js"), "utf8"), ctx);
  T = ctx.window.TT_I18N;
} catch (e) { err(`i18n.js: cannot be loaded (${e.message})`); }
if (T) {
  const langs = ["ru", "en", "ka"];
  // the labels that exist only for the English and the Russian interface (the Georgian one shows the Georgian original names as they are)
  const KA_NOT_NEEDED = new Set(["trNote", "trOrig"]);
  for (const l of langs) if (!T[l]) err(`i18n.js: no language ${l}`);
  const walk = (a, b, c, trail) => {
    const ks = new Set([...Object.keys(a || {}), ...Object.keys(b || {}), ...Object.keys(c || {})]);
    for (const k of ks) {
      const vs = [a?.[k], b?.[k], c?.[k]], w = trail + k;
      if (KA_NOT_NEEDED.has(k) && vs[2] === undefined && vs[0] !== undefined && vs[1] !== undefined) continue;
      if (vs.some((v) => v === undefined)) { err(`i18n.js: key "${w}" is missing in ${langs.filter((_, i) => vs[i] === undefined).join(", ")}`); continue; }
      const types = new Set(vs.map((v) => (Array.isArray(v) ? "array" : typeof v)));
      if (types.size > 1) { err(`i18n.js: key "${w}" has different types in the languages`); continue; }
      if (typeof vs[0] === "string") checkTriple(`i18n.js ${w}`, { ru: vs[0], en: vs[1], ka: vs[2] });
      else if (Array.isArray(vs[0])) vs.forEach((v, i) => v.forEach((x, j) => { if (typeof x === "string" && i > 0) checkTriple(`i18n.js ${w}[${j}] (${langs[i]})`, { ru: vs[0][j] ?? "", en: i === 1 ? x : vs[1][j] ?? "", ka: i === 2 ? x : vs[2][j] ?? "" }); }));
      else if (vs[0] && typeof vs[0] === "object") walk(vs[0], vs[1], vs[2], w + ".");
    }
  };
  walk(T.ru, T.en, T.ka, "");
}

// ---- the route "Entrance halls of Tbilisi" (data/entrances.json) --------------------------------------------------
const en = data["data/entrances.json"];
if (en) {
  for (const l of ["ru", "en", "ka"]) if (!String(en.door_note?.[l] || "").trim()) err(`entrances.json: door_note.${l} is missing`);
  if (!Array.isArray(en.parts) || !en.parts.length) err("entrances.json: no parts");
  let expectN = 1;
  for (const p of en.parts || []) {
    if (!(p.route?.coords?.length >= 2)) err(`entrances.json ${p.id}: no route line`);
    (p.stops || []).forEach((s, i) => {
      const w = `entrances.json ${p.id} stop ${i + 1} (${s.address?.en})`;
      if (s.n !== expectN++) err(`${w}: the numbers are not in the order (expected ${expectN - 1}, got ${s.n})`);
      if (!(Number.isFinite(s.lat) && Number.isFinite(s.lon))) err(`${w}: no coordinates`);
      if (!Array.isArray(s.src) || !s.src.length) err(`${w}: no source`);
      else for (const x of s.src) if (!x.label || (x.url && !/^https?:\/\//.test(x.url))) err(`${w}: bad source ${JSON.stringify(x)}`);
      // a photo only with the author, a free licence of Creative Commons (BY or BY-SA) and the page of the file
      for (const ph of s.photos || []) {
        if (!/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(ph.page || "")) err(`${w}: a photo without the page of the file`);
        if (!String(ph.author || "").trim()) err(`${w}: a photo without the author (${ph.page})`);
        if (!/^CC BY(-SA)? [0-9.]+$/.test(ph.license || "")) err(`${w}: a photo without a free licence (${ph.page}: ${ph.license})`);
        if (!/^https:\/\/(thumb|upload)\.wikimedia\.org\//.test(ph.thumb || "")) err(`${w}: a photo is not on thumb.wikimedia.org or upload.wikimedia.org (the policy of the page)`);
      }
      for (const k of ["name", "address", "year", "desc"]) for (const l of ["ru", "en", "ka"]) if (!String(s[k]?.[l] || "").trim()) err(`${w}: ${k}.${l} is missing`);
      // a door code is never published: no sequences like "code 38" or a number next to the word code / lock
      const all = JSON.stringify(s) + JSON.stringify(en.door_note);
      if (/(код[а-я]* (замк|домофон)|door code[s]? (is|are|of) \d|კოდი[^.]{0,20}\d{2})/i.test(all.replace(/Кодов замков здесь нет/g, ""))) err(`${w}: looks like a door code`);
    });
  }
}

// ---- the events ---------------------------------------------------------------------------------------------------
const ev = data["data/history_events.json"]?.events;
if (ev) {
  const cats = new Set(Object.keys(T?.ru?.evCats || {}));
  let prev = -1e9;
  ev.forEach((x, i) => {
    const w = `history_events[${i}] (${x.year} ${x.date})`;
    if (!(x.year >= prev)) err(`${w}: not in the order of the years`);
    prev = x.year;
    if (!/^[0-9][0-9.\- ]*$/.test(String(x.date))) err(`${w}: date "${x.date}" is not numeric`);
    if (cats.size && !cats.has(x.cat)) err(`${w}: unknown category "${x.cat}"`);
    if (!Array.isArray(x.src) || !x.src.length) err(`${w}: no source`);
    else for (const s of x.src) {
      const u = typeof s === "string" ? s : s?.url;
      // a book without a link is allowed: {"label": "<the reference>, PDF p. N", "book": true}; the label must name a page
      if (s && typeof s === "object" && s.book === true && !s.url) { if (!/(\bp\.|\bс\.|გვ\.)\s*\d/.test(s.label || "")) err(`${w}: a book source without a page ${JSON.stringify(s)}`); continue; }
      if (!/^https?:\/\//.test(u || "")) err(`${w}: bad source ${JSON.stringify(s)}`);
    }
    if (x.note) {
      for (const l of ["ru", "en", "ka"]) if (!x.note[l] || !String(x.note[l]).trim()) err(`${w}: note.${l} is missing`);
    }
    if (x.place && !(Number.isFinite(x.place.lng) && Number.isFinite(x.place.lat))) err(`${w}: place without coordinates`);
  });
}

// ---- the street names ------------------------------------------------------------------------------------------
const sn = data["data/street_names.json"]?.streets, sg = data["data/street_geom.json"];
if (sn && sg) {
  const keys = new Set();
  const cyr = /[Ѐ-ӿ]/;
  sn.forEach((s, i) => {
    const w = `street_names[${i}] (${s.now?.en})`;
    for (const l of ["ru", "en", "ka"]) if (!s.now?.[l] || !String(s.now[l]).trim()) err(`${w}: now.${l} is missing`);
    for (const l of ["en", "ka"]) if (cyr.test(s.now?.[l] || "")) err(`${w}: Cyrillic in now.${l}`);
    const key = s.geom || s.now?.en;
    if (keys.has(key)) err(`${w}: the key of the geometry "${key}" is used twice`);
    keys.add(key);
    // the geometry is required unless the street is marked "nogeom" (no line in OpenStreetMap: it has the card and the search only)
    if (!s.nogeom && !sg[key]) err(`${w}: no geometry "${key}" (mark the street nogeom if there is no line)`);
    if (s.nogeom && sg[key]) err(`${w}: marked nogeom but has a geometry`);
    let prevTo = -1e9;
    (s.iv || []).forEach((iv, j) => {
      if (!(Number.isInteger(iv[0]) && Number.isInteger(iv[1]) && iv[0] < iv[1])) err(`${w}: interval ${j} has bad years ${JSON.stringify(iv.slice(0, 2))}`);
      if (iv[2]) {
        for (const l of ["ru", "en", "ka"]) if (!iv[2][l]) err(`${w}: interval ${j} has no name in ${l}`);
        for (const l of ["en", "ka"]) if (cyr.test(iv[2][l] || "")) err(`${w}: Cyrillic in the ${l} name of interval ${j}`);
      }
      if (iv[0] < prevTo - 0 && iv[2] && s.iv[j - 1]?.[2] && iv[0] < s.iv[j - 1][1]) err(`${w}: intervals ${j - 1} and ${j} overlap`);
      prevTo = iv[1];
    });
    for (const u of s.undated || []) for (const l of ["ru", "en", "ka"]) if (!u[l]) err(`${w}: an undated name without ${l}`);
    if (s.note) err(`${w}: the note belongs in street_notes.json (tools/split_street_notes.py)`);
    if (!s.src && !s.book) err(`${w}: no source (src or book)`);
    if (s.src && !/^https?:\/\//.test(s.src)) err(`${w}: bad src`);
    if (s.book && !/PDF p\. \d+/.test(s.book)) err(`${w}: the book without a page`);
  });
  for (const k of Object.keys(sg)) if (!keys.has(k)) err(`street_geom: the geometry "${k}" belongs to no street (squares and the like are listed in street_names too)`);
  // the notes of the streets (loaded when a card is opened): one per street key, three languages, no Cyrillic in en/ka
  const sno = data["data/street_notes.json"]?.notes;
  if (!sno) err("street_notes.json is missing");
  else for (const [k, n] of Object.entries(sno)) {
    if (!keys.has(k)) err(`street_notes: the note "${k}" belongs to no street`);
    for (const l of ["ru", "en", "ka"]) if (!n[l] || !String(n[l]).trim()) err(`street_notes "${k}": note.${l} is missing`);
    for (const l of ["en", "ka"]) if (cyr.test(n[l] || "")) err(`street_notes "${k}": Cyrillic in note.${l}`);
  }
  // the objects on the streets (loaded when a card is opened): the key of a street, the kind and the role from the lists, three languages, no Cyrillic in en/ka, years as numbers
  const sob = data["data/street_objects.json"]?.objects;
  const OK = ["building", "monument", "church", "vanished", "memorial", "planner"], OR = ["architect", "sculptor", "resident", "surveyor", "builder", "founder", "namesake", "other"];
  if (!sob) err("street_objects.json is missing");
  else for (const [k, list] of Object.entries(sob)) {
    if (!keys.has(k)) err(`street_objects: the objects of "${k}" belong to no street`);
    list.forEach((o, i) => {
      const w = `street_objects "${k}"[${i}]`;
      if (!OK.includes(o.k)) err(`${w}: kind ${o.k}`);
      if (o.r != null && !OR.includes(o.r)) err(`${w}: role ${o.r}`);
      if (o.y != null && !(Array.isArray(o.y) && o.y.length >= 1 && o.y.length <= 2 && o.y.every(Number.isInteger))) err(`${w}: bad years`);
      for (const f of ["n", "p"]) {
        if (f === "p" && o.p == null) continue;
        for (const l of ["ru", "en", "ka"]) if (!o[f]?.[l] || !String(o[f][l]).trim()) err(`${w}: ${f}.${l} is missing`);
        for (const l of ["en", "ka"]) if (cyr.test(o[f]?.[l] || "")) err(`${w}: Cyrillic in ${f}.${l}`);
      }
      if (/პროსპექტ/.test(o.n?.ka || "")) err(`${w}: the calque of "prospect" in the Georgian name`);
    });
  }
}

// ---- the names of the metro stations: the Russian name is a translation, not a transliteration of the Georgian one (the remark of the owner, 2026-11-22: "Сахельмципо университети") ----------
{
  const TRANSLIT = /(моедани|университети|театри|гамзири|институти|сахелмцип|вагзлис)/i;
  for (const f of data["data/transport.json"]?.features || []) {
    const p = f.properties;
    if (p.kind !== "metro_station") continue;
    if (!p.name_ru || !/[А-Яа-я]/.test(p.name_ru)) err(`transport.json ${p.id}: name_ru is empty or not Russian`);
    else if (TRANSLIT.test(p.name_ru)) err(`transport.json ${p.id}: name_ru "${p.name_ru}" is a transliteration of the Georgian name (give the translation)`);
  }
}

// ---- the changelog ---------------------------------------------------------------------------------------------
const cl = data["data/changelog.json"];
{
  const vj = data["data/version.json"];                  // the button of the version reads this small file (python tools/build_version.py)
  if (!vj) err("data/version.json is missing (python tools/build_version.py)");
  else if (Array.isArray(cl) && cl.length && (vj.version !== cl[0].version || vj.date !== cl[0].date)) err(`data/version.json (${vj.version}, ${vj.date}) differs from the first entry of the changelog (${cl[0].version}, ${cl[0].date}); run python tools/build_version.py`);
}
if (Array.isArray(cl)) {
  const ver = (v) => String(v).split(".").map(Number);
  const cmp = (a, b) => { for (let i = 0; i < 3; i++) if (a[i] !== b[i]) return a[i] - b[i]; return 0; };
  cl.forEach((v, i) => {
    if (!/^\d+\.\d+\.\d+$/.test(v.version)) err(`changelog[${i}]: bad version ${v.version}`);
    if (i > 0 && cmp(ver(cl[i - 1].version), ver(v.version)) <= 0) err(`changelog[${i}]: versions are not in descending order (${cl[i - 1].version}, ${v.version})`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(v.date || "")) err(`changelog[${i}]: bad date`);
    if (!v.items?.length) err(`changelog[${i}]: no items`);
    (v.items || []).forEach((it, j) => { if (!["new", "fix"].includes(it.t)) err(`changelog[${i}].items[${j}]: type ${it.t}`); });
  });
}

// ---- population -------------------------------------------------------------------------------------------------
const pop = data["data/population.json"];
if (pop?.points) {
  let prev = -1e9;
  pop.points.forEach((p, i) => {
    if (!(p.y >= prev)) err(`population[${i}]: years are not in order`);
    prev = p.y;
    if (!Number.isFinite(p.v)) err(`population[${i}]: no value`);
    if (p.s && !pop.sources?.[p.s]) err(`population[${i}]: unknown source "${p.s}"`);
  });
}

// ---- the layer "Local names" (data/places.json, made by tools/apply_places.py) ------------------------------------
{
  const pl = data["data/places.json"];
  const KINDS = ["district", "garden", "hill", "bridge", "cemetery", "market", "bath", "area"];
  if (!pl) err("data/places.json is missing (python tools/apply_places.py)");
  else {
    const ids = new Set();
    for (const k of KINDS) for (const l of ["ru", "en"]) if (!pl.ui?.["kind_" + k]?.[l]) err(`places.json: the string kind_${k} (${l}) is missing`);
    for (const k of ["etym", "no_etym", "src", "quote", "attr"]) for (const l of ["ru", "en"]) if (!pl.ui?.[k]?.[l]) err(`places.json: the string ${k} (${l}) is missing`);
    pl.items.forEach((c, i) => {
      const w = `places.json[${i}] ${c.id}`;
      if (ids.has(c.id)) err(`${w}: duplicate id`); ids.add(c.id);
      if (!KINDS.includes(c.k)) err(`${w}: unknown kind ${c.k}`);
      if (!(c.lon > 44.6 && c.lon < 45.1 && c.lat > 41.6 && c.lat < 41.9)) err(`${w}: the point is outside Tbilisi`);
      for (const f of ["n", "a"]) for (const l of ["ru", "en", "ka"]) if (!c[f]?.[l] || !String(c[f][l]).trim()) err(`${w}: ${f}.${l} is missing`);
      if (c.e) for (const l of ["ru", "en", "ka"]) if (!c.e[l]) err(`${w}: e.${l} is missing`);
      for (const f of ["n", "a", "e"]) if (c[f]) for (const l of ["en", "ka"]) if (CY.test(c[f][l] || "")) err(`${w}: Cyrillic in ${f}.${l}`);
      if (!c.s?.u?.startsWith("https://") || !c.s.aq) err(`${w}: the source of the description (link and quote) is missing`);
      if (c.e && !(c.s.eq?.u && c.s.eq.q)) err(`${w}: an etymology without a quote of the source`);
      if (!c.e && c.s.eq) err(`${w}: a quote of the etymology without the etymology`);
    });
  }
}

// ---- monuments, sculptures and plaques (data/sculptures.json, data/plaques.json, made by tools/apply_monuments.py) --
for (const [file, kinds] of [["data/sculptures.json", ["sculpture", "bust", "monument", "statue", "memorial", "relief"]], ["data/plaques.json", null]]) {
  const f = data[file];
  if (!f) { err(`${file} is missing (python tools/apply_monuments.py)`); continue; }
  const ids = new Set();
  for (const k of ["layer_mon", "layer_plq", "k_plaque", "year_unknown", "where", "photo", "attr"]) for (const l of ["ru", "en"]) if (!f.ui?.[k]?.[l]) err(`${file}: the string ${k} (${l}) is missing`);
  f.items.forEach((c, i) => {
    const w = `${file}[${i}] ${c.id}`;
    if (ids.has(c.id)) err(`${w}: duplicate id`); ids.add(c.id);
    if (kinds && !kinds.includes(c.k)) err(`${w}: unknown kind ${c.k}`);
    if (kinds && !f.ui?.["k_" + c.k]?.en) err(`${w}: no string for the kind ${c.k}`);
    if (!(c.lon > 44.66 && c.lon < 45.02 && c.lat > 41.62 && c.lat < 41.86)) err(`${w}: the point is outside Tbilisi`);
    for (const l of ["en", "ka"]) if (CY.test(c.n?.[l] || "")) err(`${w}: Cyrillic in n.${l}`);
    if (c.y != null && !(Number.isInteger(c.y) && c.y > 1000 && c.y < 2100)) err(`${w}: the year ${c.y}`);
    if (!kinds && c.y != null && !String(c.ins || "").includes(String(c.y))) err(`${w}: the first year of life ${c.y} is not in the inscription`);
    if (c.ph && !(f.photos?.[c.ph]?.thumb && f.photos[c.ph].license && f.photos[c.ph].page)) err(`${w}: the photo ${c.ph} has no thumbnail, licence or page`);
    if (c.st && !f.streets?.[c.st]) err(`${w}: the street ${c.st} is not in the list`);
  });
  for (const [k, s] of Object.entries(f.streets || {})) for (const l of ["ru", "en", "ka"]) if (!s[l]) err(`${file}: the street ${k} has no ${l}`);
}

// ---- the files that the page needs ------------------------------------------------------------------------------
const html = fs.readFileSync(path.join(SITE, "index.html"), "utf8");
const scripts = [...html.matchAll(/<script[^>]*\ssrc="([^"]+)"/g)].map((m) => m[1]).filter((s) => !/^https?:/.test(s));
for (const s of scripts) if (!fs.existsSync(path.join(SITE, s))) err(`index.html: the script ${s} does not exist`);
if (scripts.indexOf("i18n.js") < 0 || scripts.indexOf("i18n.js") > scripts.indexOf("app.js")) err("index.html: i18n.js must be loaded before app.js");
const sw = fs.readFileSync(path.join(SITE, "sw.js"), "utf8");
for (const f of MODULES) {                                  // every module that is imported exists; the shell of the service worker holds all the modules (the site works offline)
  const code = fs.readFileSync(path.join(SITE, f), "utf8");
  for (const m of code.matchAll(/(?:import|export)[^"';]*?from\s*"(\.[^"]+)"/g)) if (!fs.existsSync(path.join(SITE, path.dirname(f), m[1]))) err(`${f}: the module ${m[1]} does not exist`);
}
const shell = JSON.parse((sw.match(/const SHELL = (\[[^\]]*\])/) || [])[1] || "[]");
for (const f of shell) if (f !== "./" && !fs.existsSync(path.join(SITE, f))) err(`sw.js: the file ${f} of the shell does not exist`);
for (const f of MODULES) if (!shell.includes(f)) err(`sw.js: the module ${f} is not in the shell of the service worker`);
for (const s of scripts) if (!s.startsWith("vendor/") && !shell.includes(s)) warns.push(`sw.js: ${s} is not in the shell (it will not work offline)`);
for (const v of data["data/views.json"] || []) if (v.image && !/^https?:/.test(v.image) && !fs.existsSync(path.join(SITE, v.image))) err(`views.json ${v.id}: the image ${v.image} does not exist`);

for (const w of warns) console.log("warning:", w);
if (errors.length) {
  console.log(`\n${errors.length} problem(s):`);
  for (const e of errors.slice(0, 200)) console.log(" -", e);
  if (errors.length > 200) console.log(` ... and ${errors.length - 200} more`);
  process.exit(1);
}
console.log(`ok: ${Object.keys(data).length} JSON files, ${ev?.length ?? 0} events, ${cl?.length ?? 0} versions, ${Object.keys(T?.ru || {}).length} interface keys`);
