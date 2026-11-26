// Checks of the data and of the texts of the site; run by hand (node tests/check_data.mjs) and by the workflow before every deploy.
// They stop the deploy when a translation is missing, when a Georgian text is not Georgian (Cyrillic, English), when a file that the page
// needs is missing or a JSON file is broken. No dependencies: only Node.
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import Ajv from "ajv";

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
    for (const [k, v] of Object.entries(node)) { if ((k === "n" || k === "name" || k === "o" || k === "al") && node.pend === 1) continue; walkTriples(file, v, `${trail}/${k}`); }      // "pend": the name of a new object waits for the translation (Gemini), the page shows the name that exists
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
  const KINDS = ["district", "garden", "hill", "bridge", "cemetery", "market", "bath", "area", "square", "building"];
  if (!pl) err("data/places.json is missing (python tools/apply_places.py)");
  else {
    const ids = new Set();
    for (const k of KINDS) for (const l of ["ru", "en"]) if (!pl.ui?.["kind_" + k]?.[l]) err(`places.json: the string kind_${k} (${l}) is missing`);
    for (const k of ["etym", "no_etym", "src", "quote", "attr", "folk"]) for (const l of ["ru", "en"]) if (!pl.ui?.[k]?.[l]) err(`places.json: the string ${k} (${l}) is missing`);
    for (const [k, v] of Object.entries(pl.ui || {})) if (v.pending_ka) err(`places.json: the string ${k} waits for the Georgian text (pending_ka): the data is not to be published yet`);
    pl.items.forEach((c, i) => {
      const w = `places.json[${i}] ${c.id}`;
      if (ids.has(c.id)) err(`${w}: duplicate id`); ids.add(c.id);
      if (!KINDS.includes(c.k)) err(`${w}: unknown kind ${c.k}`);
      if (!(c.lon > 44.6 && c.lon < 45.1 && c.lat > 41.6 && c.lat < 41.9)) err(`${w}: the point is outside Tbilisi`);
      if (c.pk) {                                                                       // a park or garden that only OpenStreetMap names (tools/apply_parks.py): a name in some language, the OSM object as the source
        if (!Object.values(c.n || {}).some((v) => v && v.trim())) err(`${w}: no name`);
        if (!/^https:\/\/www\.openstreetmap\.org\/(way|relation|node)\/\d+$/.test(c.s?.u || "")) err(`${w}: the OSM object is not the source`);
        for (const l of ["en", "ka"]) for (const f of ["n", "o", "al"]) if (CY.test(c[f]?.[l] || "")) err(`${w}: Cyrillic in ${f}.${l}`);
        if (c.a || c.e) err(`${w}: a park of OSM has no description of its own`);
        if (c.pend !== 1 && !["ru", "en", "ka"].every((l) => c.n?.[l])) err(`${w}: a name lacks a language but is not marked pend`);
      } else for (const f of (c.f && !c.a ? ["n"] : ["n", "a"])) for (const l of ["ru", "en", "ka"]) if (!c[f]?.[l] || !String(c[f][l]).trim()) err(`${w}: ${f}.${l} is missing`);
      for (const [j, x] of (c.f || []).entries()) {                                  // the folk names (tools/apply_folk.py): a name, a meaning in 3 languages, pages with quotations
        const ww = `${w} f[${j}]`;
        if (!Object.values(x.n || {}).some(Boolean)) err(`${ww}: no name`);
        if (x.m) for (const l of ["ru", "en", "ka"]) if (!x.m[l]?.trim()) err(`${ww}: m.${l} is missing`);
        for (const l of ["en", "ka"]) if (CY.test(x.m?.[l] || "") || CY.test(x.n?.[l] || "")) err(`${ww}: Cyrillic in ${l}`);
        if (!x.s?.length || x.s.some((q) => !q.u?.startsWith("https://") || !q.q)) err(`${ww}: a page without a quotation`);
      }
      if (c.e) for (const l of ["ru", "en", "ka"]) if (!c.e[l]) err(`${w}: e.${l} is missing`);
      for (const f of ["n", "a", "e"]) if (c[f]) for (const l of ["en", "ka"]) if (CY.test(c[f][l] || "")) err(`${w}: Cyrillic in ${f}.${l}`);
      if (!c.pk && (!c.s?.u?.startsWith("https://") || !c.s.aq)) err(`${w}: the source of the description (link and quote) is missing`);
      if (c.e && !((c.s.eq?.u || Number.isInteger(c.s.eq?.p)) && c.s.eq.q)) err(`${w}: an etymology without a quote of the source (a page of a site or a page of the encyclopedia)`);
      if (c.s.eq?.u && !/^https:\/\/((ka|ru|en)\.(wikipedia|wiktionary)\.org|(www\.)?georgianencyclopedia\.ge|(www\.)?ena\.ge)\//.test(c.s.eq.u)) err(`${w}: the source of the etymology is not on an allowed site: ${c.s.eq.u}`);
      if (!c.e && c.s.eq) err(`${w}: a quote of the etymology without the etymology`);
      for (const x of c.s.eq?.more || []) if (!x.q || !/^https:\/\/((ka|ru|en)\.(wikipedia|wiktionary)\.org|(www\.)?georgianencyclopedia\.ge|(www\.)?ena\.ge)\//.test(x.u || "")) err(`${w}: a quote of a part of the name without a source on an allowed site`);
    });
  }
}

// ---- the tour (data/tour.json): every step has its text in three languages (a step whose Georgian text is still to come stops the deploy, like the other strings that wait for Gemini)
{
  const tour = data["data/tour.json"];
  if (tour) tour.steps.forEach((st, i) => { for (const f of ["title", "text"]) for (const l of ["ru", "en", "ka"]) if (!st[f]?.[l]) err(`tour.json step ${i + 1} (${st.title?.en || st.title?.ru}): ${f}.${l} is missing (the Georgian text waits for Gemini)`); });
}

// ---- the layer "Soviet modernism" (data/modernism.json, made by tools/build_modernism.py) ----------------------------
{
  const md = data["data/modernism.json"];
  if (!md) err("data/modernism.json is missing (python tools/build_modernism.py)");
  else {
    const ids = new Set(), host = (u) => new URL(u).hostname.replace(/^www\./, "");
    for (const [k, v] of Object.entries(md.ui || {})) {
      if (v.pending_ka) err(`modernism.json: the string ${k} waits for the Georgian text (pending_ka): the data is not to be published yet`);
      else for (const l of ["ru", "en", "ka"]) if (!v[l]) err(`modernism.json: the string ${k} (${l}) is missing`);
    }
    for (const k of ["layer_mod", "k_modernism", "built", "architects", "was", "now", "status", "st_existing", "st_renovated", "st_abandoned", "st_demolished", "quote", "src", "photo", "folk", "attr"]) if (!md.ui?.[k]) err(`modernism.json: the string ${k} is missing`);
    if (md.items.length < 10) err(`modernism.json: only ${md.items.length} buildings`);
    md.items.forEach((c, i) => {
      const w = `modernism.json[${i}] ${c.id}`;
      if (ids.has(c.id)) err(`${w}: duplicate id`); ids.add(c.id);
      if (c.k !== "modernism") err(`${w}: kind ${c.k}`);
      if (!(c.lon > 44.66 && c.lon < 45.02 && c.lat > 41.62 && c.lat < 41.86)) err(`${w}: the point is outside Tbilisi`);
      if (!c.g?.how || !c.g?.ref) err(`${w}: the origin of the point is not named`);
      if (!Number.isInteger(c.y) || c.y < 1950 || c.y > 1995) err(`${w}: the year ${c.y}`);
      if (!["existing", "renovated", "abandoned", "demolished"].includes(c.st)) err(`${w}: status ${c.st}`);
      for (const f of ["n", "d"]) for (const l of ["ru", "en", "ka"]) if (!String(c[f]?.[l] || "").trim()) err(`${w}: ${f}.${l} is missing`);
      for (const f of ["n", "d", "ft", "fn"]) if (c[f]) for (const l of ["en", "ka"]) if (CY.test(c[f][l] || "")) err(`${w}: Cyrillic in ${f}.${l}`);
      if (JSON.stringify(c).includes("პროსპექტი")) err(`${w}: the word პროსპექტი (must be გამზირი)`);
      if (!(c.s || []).length || (c.s || []).some((q) => !q.u?.startsWith("https://") || !q.q || !q.f)) err(`${w}: a source without a link, quotation or kind of fact`);
      if (new Set((c.s || []).map((q) => host(q.u))).size < 2 && !(c.s || []).some((q) => /(wikipedia\.org|georgianencyclopedia\.ge)$/.test(host(q.u)))) err(`${w}: sources are not on two different sites`);
      if (!(c.s || []).some((q) => q.f === "style")) err(`${w}: no source that says that the building is modernist`);
      if (c.ph && !(md.photos?.[c.ph]?.thumb && md.photos[c.ph].license && md.photos[c.ph].page)) err(`${w}: the photo ${c.ph} has no thumbnail, licence or page`);
      for (const [j, x] of (c.f || []).entries()) {
        const ww = `${w} f[${j}]`;
        if (!Object.values(x.n || {}).some(Boolean)) err(`${ww}: no name`);
        if (x.m) for (const l of ["ru", "en", "ka"]) if (!x.m[l]?.trim()) err(`${ww}: m.${l} is missing`);
        if (!x.s?.length || x.s.some((q) => !q.u?.startsWith("https://") || !q.q)) err(`${ww}: a page without a quotation`);
      }
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
    if (c.dq && (!c.d || c.dq.some((q) => !q.u?.startsWith("https://") || !q.q))) err(`${w}: quotations of a description without the description or without a link`);
    if (c.dq && ["en", "ka"].some((l) => CY.test(c.d?.[l] || ""))) err(`${w}: Cyrillic in the description (en / ka)`);
    if (c.ph && !(f.photos?.[c.ph]?.thumb && f.photos[c.ph].license && f.photos[c.ph].page)) err(`${w}: the photo ${c.ph} has no thumbnail, licence or page`);
    if (c.st && !f.streets?.[c.st]) err(`${w}: the street ${c.st} is not in the list`);
  });
  for (const [k, s] of Object.entries(f.streets || {})) for (const l of ["ru", "en", "ka"]) if (!s[l]) err(`${file}: the street ${k} has no ${l}`);
}

// ---- the places of worship of OpenStreetMap (data/religious_osm.json, made by tools/build_religious_osm.py) -----------
{
  const ro = data["data/religious_osm.json"];
  const RELS = ["orthodox", "russian", "lutheran", "yazidi", "armenian", "catholic", "jewish", "muslim", "zoroastrian", "christian", "christianOsm"];
  if (!ro) err("data/religious_osm.json is missing (python tools/build_religious_osm.py)");
  else {
    const ids = new Set(), main = new Set((data["data/religious.json"] || []).map((x) => x.id));
    for (const [k, v] of Object.entries(ro.ui || {})) {
      if (v.pending_ka) err(`religious_osm.json: the string ${k} waits for the Georgian text (pending_ka): the data is not to be published yet`);
      else for (const l of ["ru", "en", "ka"]) if (!v[l]) err(`religious_osm.json: the string ${k} (${l}) is missing`);
    }
    for (const r of ro.items) {
      const w = `religious_osm.json ${r.id}`;
      if (ids.has(r.id) || main.has(r.id)) err(`${w}: duplicate id`); ids.add(r.id);
      if (!RELS.includes(r.rel)) err(`${w}: unknown denomination ${r.rel}`);
      if (r.rel === "christianOsm" && !ro.ui?.christianOsm) err(`${w}: no string for the denomination`);
      if (!(r.lon > 44.66 && r.lon < 45.02 && r.lat > 41.62 && r.lat < 41.86)) err(`${w}: the point is outside Tbilisi`);
      if (!/^(node|way|relation)\/\d+$/.test(r.osm)) err(`${w}: the OSM id ${r.osm}`);
      for (const l of ["en", "ka"]) if (CY.test(r.name?.[l] || "")) err(`${w}: Cyrillic in name.${l}`);
      if (r.st && !ro.streets?.[r.st]) err(`${w}: the street ${r.st} is not in the list`);
      if (!Array.isArray(r.src) || r.src.some((u) => !/^https:\/\/(ka|ru|en)\.wikipedia\.org\//.test(u))) err(`${w}: src`);
    }
  }
}

// ---- the files that the page needs ------------------------------------------------------------------------------
const html = fs.readFileSync(path.join(SITE, "index.html"), "utf8");
const scripts = [...html.matchAll(/<script[^>]*\ssrc="([^"]+)"/g)].map((m) => m[1].split("?")[0]).filter((s) => !/^https?:/.test(s));
for (const s of scripts) if (!fs.existsSync(path.join(SITE, s))) err(`index.html: the script ${s} does not exist`);
if (scripts.indexOf("i18n.js") < 0 || scripts.indexOf("i18n.js") > scripts.indexOf("app.js")) err("index.html: i18n.js must be loaded before app.js");
const sw = fs.readFileSync(path.join(SITE, "sw.js"), "utf8");
for (const f of MODULES) {                                  // every module that is imported exists; the shell of the service worker holds all the modules (the site works offline)
  const code = fs.readFileSync(path.join(SITE, f), "utf8");
  for (const m of code.matchAll(/(?:(?:import|export)[^"';]*?from\s*|import\()"(\.[^"]+)"/g)) {
    if (!fs.existsSync(path.join(SITE, path.dirname(f), m[1].split("?")[0]))) err(`${f}: the module ${m[1]} does not exist`);
  }
}
const shell = JSON.parse((sw.match(/const SHELL = (\[[^\]]*\])/) || [])[1] || "[]");
const shellPaths = shell.map((url) => url.split("?")[0]);
for (const f of shellPaths) if (!fs.existsSync(path.join(SITE, f))) err(`sw.js: the file ${f} of the shell does not exist`);
for (const f of MODULES) if (!shellPaths.includes(f)) err(`sw.js: the module ${f} is not in the shell of the service worker`);
for (const s of scripts) if (!shellPaths.includes(s)) err(`sw.js: ${s} is not in the shell (it will not work offline)`);
for (const v of data["data/views.json"] || []) if (v.image && !/^https?:/.test(v.image) && !fs.existsSync(path.join(SITE, v.image))) err(`views.json ${v.id}: the image ${v.image} does not exist`);

// ---- strict schema, LLM-corruption, photos, tours, scale sync and event guards (2026-11-24) -----------------------
{
  const ni = data["data/names_i18n.json"];
  if (!ni) err("data/names_i18n.json: missing");
  else if (Object.keys(ni).sort().join(",") !== "names,streets") {
    err(`data/names_i18n.json: top-level keys must be strictly names,streets (got ${Object.keys(ni).sort().join(",")})`);
  }
}

{
  const TRUNC = /(?:\((?:груз|греч|арм|укр|нем|фр|лат|перс|тур)\.|[—–-]\s*გ\.|\[?\s*ძვ\.|სოფ\.|ახლანდ\.|\bSt\.|[—–-]\s*\))$/;
  const LLM_JUNK = /(\[insert|отсутствует в|not provided|missing from|missing in source|cannot complete|birthdate is unknown|birth date is unknown|no information provided|as an ai)/i;
  const REP_LOOP = /\b(\S+\s+\S+\s+\S+)(?:\s+\1){2,}/i;
  const GE_ONE = /[ა-ჰ]/, CY_ONE = /[А-Яа-яЁё]/;
  for (const [file, d] of [["data/sculptures.json", data["data/sculptures.json"]], ["data/plaques.json", data["data/plaques.json"]]]) {
    for (const c of d?.items || []) {
      if (!c.dw) continue;
      if (!c.d || !Object.values(c.d).some(Boolean)) err(`${file} ${c.id}: dw without a description`);
      if (!c.w || !Object.keys(c.w).length) err(`${file} ${c.id}: dw without Wikipedia link`);
      for (const [l, t] of Object.entries(c.d || {})) {
        if (!t) continue;
        if (t.length > 330) err(`${file} ${c.id} ${l}: dw too long (${t.length} > 330)`);
        if (t.includes("\u0301")) err(`${file} ${c.id} ${l}: dw contains combining stress mark`);
        if (l === "ka" && (!GE_ONE.test(t) || CY_ONE.test(t))) err(`${file} ${c.id} ka: dw has Cyrillic or no Georgian letters`);
        if (l === "en" && CY_ONE.test(t)) err(`${file} ${c.id} en: dw contains Cyrillic`);
        if (TRUNC.test(t.trim())) err(`${file} ${c.id} ${l}: dw looks truncated (${t.slice(-30)})`);
        if (LLM_JUNK.test(t)) err(`${file} ${c.id} ${l}: dw contains LLM placeholder/refusal`);
        if (REP_LOOP.test(t)) err(`${file} ${c.id} ${l}: dw contains LLM repetition loop`);
      }
    }
  }
}

{
  const photos = data["data/photos.json"] || {};
  for (const [k, v] of Object.entries(photos)) {
    if (!String(v?.thumb || "").trim()) err(`photos.json ${k}: thumb is missing`);
    if (!String(v?.license || "").trim()) err(`photos.json ${k}: license is missing`);
    if (!String(v?.page || "").trim()) err(`photos.json ${k}: page is missing`);
    if (/[\r\n]/.test(String(v?.author || "")) || /Unknown authorUnknown author/i.test(String(v?.author || ""))) {
      err(`photos.json ${k}: dirty or multiline author`);
    }
    if (/\.svg(?:$|\?)/i.test(String(v?.thumb || "")) || /\.svg(?:$|\?)/i.test(String(v?.page || ""))) {
      err(`photos.json ${k}: SVG URL is not allowed as a monument photo`);
    }
    if (/[?&]utm_(source|medium|campaign)=/i.test(String(v?.thumb || "")) || /[?&]utm_(source|medium|campaign)=/i.test(String(v?.page || ""))) {
      err(`photos.json ${k}: utm_ tracking parameter in URL`);
    }
  }

  const rad = (deg) => (deg * Math.PI) / 180;
  const havKm = ([lon1, lat1], [lon2, lat2]) => {
    const dLat = rad(lat2 - lat1), dLon = rad(lon2 - lon1);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 2 * 6371 * Math.asin(Math.sqrt(h));
  };
  function distanceToRouteM(stop, coords) {
    const latScale = 6371000 * rad(1), lonScale = latScale * Math.cos(rad(stop.lat));
    const points = coords.map(([lon, lat]) => [(lon - stop.lon) * lonScale, (lat - stop.lat) * latScale]);
    let nearest = Infinity;
    for (let i = 1; i < points.length; i++) {
      const [x, y] = points[i - 1], [endX, endY] = points[i];
      const dx = endX - x, dy = endY - y, lengthSquared = dx * dx + dy * dy;
      const t = lengthSquared ? Math.max(0, Math.min(1, -(x * dx + y * dy) / lengthSquared)) : 0;
      nearest = Math.min(nearest, Math.hypot(x + t * dx, y + t * dy));
    }
    return nearest;
  }
  for (const file of ["data/mtskheta_tour.json", "data/museum_tours.json"]) {
    const tour = data[file];
    if (!Array.isArray(tour?.parts) || !tour.parts.length) { err(`${file}: no parts`); continue; }
    for (const p of tour.parts) {
      const coords = p.route?.coords || [], stops = p.stops || [];
      if (!stops.length) err(`${file} ${p.id}: no stops`);
      if (coords.length < stops.length * 3) err(`${file} ${p.id}: route has too few points (${coords.length} for ${stops.length} stops)`);
      let actualKm = 0;
      for (let i = 0; i < coords.length - 1; i++) actualKm += havKm(coords[i], coords[i + 1]);
      if (!(Number.isFinite(p.route?.length_km) && p.route.length_km > 0)) err(`${file} ${p.id}: invalid route.length_km`);
      else if (Math.abs(actualKm - p.route.length_km) > Math.max(0.5, p.route.length_km * 0.25)) {
        err(`${file} ${p.id}: route length mismatch (declared ${p.route.length_km} km, coords ${actualKm.toFixed(2)} km)`);
      }
      for (let idx = 0; idx < stops.length; idx++) {
        const s = stops[idx];
        const w = `${file} ${p.id} stop ${s.id || s.n}`;
        if (!(Number.isFinite(s.lat) && Number.isFinite(s.lon))) err(`${w}: missing coordinates`);
        else if (file === "data/mtskheta_tour.json" && p.id === "armazi") {
          const distanceM = distanceToRouteM(s, coords);
          if (distanceM > 100) err(`${w}: ${Math.round(distanceM)} m from the route (maximum 100 m)`);
        }
        if (idx > 0 && Number.isFinite(s.leg_m)) {
          const directM = havKm([stops[idx - 1].lon, stops[idx - 1].lat], [s.lon, s.lat]) * 1000;
          if (directM > 50 && s.leg_m < directM * 0.8) err(`${w}: leg_m (${s.leg_m} m) < direct distance (${Math.round(directM)} m)`);
        }
        for (const k of ["name", "address", "year", "desc"]) {
          for (const l of ["ru", "en", "ka"]) if (!String(s[k]?.[l] || "").trim()) err(`${w}: ${k}.${l} is missing`);
        }
        for (const item of String(s.ph || "").split("|").map((x) => x.trim()).filter(Boolean)) {
          if (!(item in photos)) err(`${w}: photo "${item}" not found in photos.json`);
        }
      }
    }
  }
}

{
  const appJs = fs.readFileSync(path.join(SITE, "app.js"), "utf8");
  const mMin = appJs.match(/const\s+MIN\s*=\s*(\d+)/);
  const mKnots = appJs.match(/const\s+FULL_KNOTS\s*=\s*\[\[(\d+),/);
  const rulers = data["data/rulers.json"];
  if (!mMin || !mKnots) err("app.js: could not parse MIN or FULL_KNOTS");
  else {
    const minYear = Number(mMin[1]), knotsStart = Number(mKnots[1]);
    if (knotsStart !== minYear) err(`app.js: FULL_KNOTS start (${knotsStart}) !== MIN (${minYear})`);
    const firstFrom = rulers?.states?.[0]?.from;
    if (!(Number.isFinite(firstFrom) && firstFrom <= minYear)) {
      err(`rulers.json: states[0].from (${firstFrom}) > app.js MIN (${minYear})`);
    }
  }
}

if (ev) {
  const battleCount = ev.filter((e) => (e.cat === "battle" || e.cat === "invasion") && e.place).length;
  if (battleCount < 49) err(`history_events.json: expected >= 49 battle/invasion events with place, got ${battleCount}`);
  const rawHist = fs.readFileSync(path.join(SITE, "data", "history_events.json"), "utf8");
  if (rawHist.split(/\r?\n/).length < ev.length) err("history_events.json: must stay multi-line (one event per line, not minified)");
  const seenEv = new Set();
  for (const e of ev) {
    const key = `${e.year}|${e.date}|${e.ru || ""}`;
    if (seenEv.has(key)) err(`history_events.json: duplicate event (${e.year} ${e.date}: ${(e.ru || "").slice(0, 50)})`);
    seenEv.add(key);
  }
}

// ---- cross-layer date consistency: religious.json (rid) vs monuments.json ------------------------------
{
  const monById = new Map((data["data/monuments.json"]?.features || []).map((f) => [f.properties.id, f.properties]));
  for (const r of data["data/religious.json"] || []) {
    if (r.rid == null || r.id === "reg3049") continue; // reg3049 keeps verified 1863-1864 date from patch 1.8.1 (religious_data.test.mjs)
    const m = monById.get(r.rid);
    if (!m) { err(`religious.json ${r.id}: rid ${r.rid} not found in monuments.json`); continue; }
    if (typeof m.ye === "number") {
      if (r.undated) err(`religious.json ${r.id}: marked undated while monuments.json has ye=${m.ye}`);
      if (r.from !== m.ye) err(`religious.json ${r.id}: from=${r.from} !== monuments.json ye=${m.ye}`);
      const wantDate = (m.y0 != null && m.y1 != null) ? (m.y0 === m.y1 ? String(m.y0) : `${m.y0}–${m.y1}`) : null;
      if (wantDate && r.date !== wantDate) err(`religious.json ${r.id}: date="${r.date}" !== monuments.json "${wantDate}"`);
    } else {
      if (!r.undated || r.from !== 364 || r.date !== "") err(`religious.json ${r.id}: undated mismatch with monuments.json`);
    }
  }
}

// ---- dataset ID uniqueness (preserving valid id=0) and photo references ---------------------------------
{
  const photos = data["data/photos.json"] || {};
  const layers = [
    ["data/monuments.json", (data["data/monuments.json"]?.features || []).map((f) => f.properties), true],
    ["data/lost.json", (data["data/lost.json"]?.features || []).map((f) => ({ id: f.id, ...(f.properties || {}) })), true],
    ["data/religious.json", data["data/religious.json"] || [], true],
    ["data/religious_osm.json", data["data/religious_osm.json"]?.items || [], true],
    ["data/science.json", data["data/science.json"] || [], true],
    ["data/education.json", data["data/education.json"] || [], true],
    ["data/museums.json", data["data/museums.json"] || [], true],
    ["data/places.json", data["data/places.json"]?.items || [], true],
    ["data/sculptures.json", data["data/sculptures.json"]?.items || [], false],
    ["data/plaques.json", data["data/plaques.json"]?.items || [], false],
    ["data/modernism.json", data["data/modernism.json"]?.items || [], false],
  ];
  for (const [file, items, checkPh] of layers) {
    const seen = new Set();
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      if (it.id === null || it.id === undefined || it.id === "") { err(`${file}[${i}]: missing id`); continue; }
      if (seen.has(it.id)) err(`${file}: duplicate id ${it.id}`);
      seen.add(it.id);
      if (checkPh && it.ph) {
        for (const ph of String(it.ph).split("|").map((x) => x.trim()).filter(Boolean)) {
          if (!(ph in photos)) err(`${file} ${it.id}: photo "${ph}" not found in photos.json`);
        }
      }
    }
  }
}

// ---- unified object catalog (tools/build_catalog.py) ----------------------------------------------------
{
  const cat = data["data/catalog.json"];
  if (!cat || !Array.isArray(cat.items) || !cat.by_ref) err("data/catalog.json: missing or invalid (run python -P tools/build_catalog.py)");
  else {
    const known = new Set([
      ...(data["data/monuments.json"]?.features || []).map((f) => `o:${f.properties.id}`),
      ...(data["data/religious.json"] || []).map((x) => `rl:${x.id}`),
      ...(data["data/science.json"] || []).map((x) => `sc:${x.id}`),
      ...(data["data/education.json"] || []).map((x) => `ed:${x.id}`),
      ...(data["data/museums.json"] || []).map((x) => `mu:${x.id}`),
    ]);
    const seenIds = new Set();
    const seenRefs = new Set();
    for (const it of cat.items) {
      if (!it.id || seenIds.has(it.id)) err(`data/catalog.json: invalid or duplicate id ${it.id}`);
      seenIds.add(it.id);
      for (const ref of it.refs || []) {
        if (!known.has(ref)) err(`data/catalog.json ${it.id}: unknown ref ${ref}`);
        if (seenRefs.has(ref)) err(`data/catalog.json: ref ${ref} appears in multiple catalog items`);
        seenRefs.add(ref);
        if (cat.by_ref[ref] !== it.id) err(`data/catalog.json: by_ref[${ref}] mismatch`);
      }
    }
  }
}

// ---- cache-busting manifest (tools/gen_manifest.py) and CI e2e shard coverage ----------------------------
{
  const mf = data["data/manifest.json"];
  if (!mf || !mf.v || !mf.f) err("data/manifest.json: missing (run python -P tools/gen_manifest.py)");
  else {
    const sha8 = (p) => crypto.createHash("sha256").update(fs.readFileSync(p).toString("latin1").replace(/\r\n/g, "\n"), "latin1").digest("hex").slice(0, 8);
    const dataFiles = fs.readdirSync(path.join(SITE, "data")).filter((f) => f.endsWith(".json") && f !== "manifest.json").sort();
    for (const f of dataFiles) {
      const want = sha8(path.join(SITE, "data", f));
      if (mf.f["data/" + f] !== want) err(`data/manifest.json: hash mismatch for data/${f} (run python -P tools/gen_manifest.py)`);
    }
    const msJs = path.join(SITE, "vendor", "minisearch.js");
    if (fs.existsSync(msJs) && mf.f["vendor/minisearch.js"] !== sha8(msJs)) err("data/manifest.json: hash mismatch for vendor/minisearch.js (run python -P tools/gen_manifest.py)");
    const idxHtml = fs.readFileSync(path.join(SITE, "index.html"), "utf8");
    const appJs = fs.readFileSync(path.join(SITE, "app.js"), "utf8");
    for (const f of MODULES.filter((p) => p !== "app.js")) {
      const url = `${f}?v=${sha8(path.join(SITE, f))}`;
      if (!appJs.includes(`"./${url}"`) || !shell.includes(url)) err(`${f}: module import and offline shell must both use ${url}`);
    }
    const wantApp = sha8(path.join(SITE, "app.js"));
    if (!idxHtml.includes(`src="app.js?v=${wantApp}"`)) err(`site/index.html: app.js?v=${wantApp} is out of date (run python -P tools/gen_manifest.py)`);
    for (const [, url] of idxHtml.matchAll(/(?:src|href)="([^"/][^"?#]*\?v=[0-9a-f]{8})"/g)) {
      if (!shell.includes(url)) err(`sw.js: missing versioned shell resource ${url}`);
    }
    for (const url of shell.filter((u) => u !== "data/manifest.json")) {
      const [rel, version] = url.split("?v=");
      const full = path.join(SITE, rel);
      if (fs.existsSync(full) && (version || mf.f[rel]) !== sha8(full)) err(`sw.js: hash mismatch for shell resource ${url}`);
    }
    if (!shell.includes("data/manifest.json")) err("sw.js: the offline shell must include its manifest");
    if (!sw.includes(`VERSION = "tt-${mf.v}"`)) err(`site/sw.js: VERSION does not match manifest v=${mf.v} (run python -P tools/gen_manifest.py)`);
  }
  const wfPath = path.join(SITE, "..", ".github", "workflows", "pages.yml");
  if (fs.existsSync(wfPath)) {
    const wf = fs.readFileSync(wfPath, "utf8");
    for (const f of fs.readdirSync(path.join(SITE, "..", "tests", "e2e")).filter((x) => x.endsWith(".test.mjs"))) {
      if (!wf.includes(f)) err(`.github/workflows/pages.yml: e2e test ${f} is not listed in any shard`);
    }
  }
}

// ---- JSON Schema contract validation (Ajv) ---------------------------------------------------------------
{
  const ajv = new Ajv({ allErrors: false, allowUnionTypes: true });
  const schemasDir = path.join(SITE, "..", "tests", "schemas");
  if (fs.existsSync(schemasDir)) {
    for (const sf of fs.readdirSync(schemasDir).filter((f) => f.endsWith(".schema.json")).sort()) {
      const target = "data/" + sf.replace(".schema.json", ".json");
      if (!data[target]) { err(`${target}: missing for schema ${sf}`); continue; }
      const validate = ajv.compile(JSON.parse(fs.readFileSync(path.join(schemasDir, sf), "utf8")));
      if (!validate(data[target])) {
        const e0 = validate.errors?.[0];
        err(`${target}: schema error at ${e0?.instancePath || "/"} (${e0?.message || "invalid"})`);
      }
    }
  }
}

// ---- Anti-hallucination & format bloat guards (2026-11-26) -----------------------------------------------
{
  // 1. Native compact JSON format guard (prevents accidental indent=1 bloating diffs and first-screen/lazy payload)
  for (const rel of ["data/monuments.json", "data/places.json", "data/religious.json", "data/catalog.json"]) {
    if (!fs.existsSync(path.join(SITE, rel))) continue;
    const raw = fs.readFileSync(path.join(SITE, rel), "utf8");
    const lines = raw.split(/\r?\n/).filter((l) => l.length > 0).length;
    if (lines > 5) err(`${rel}: expanded to ${lines} lines (must stay compact JSON)`);
  }

  // 2. Foreign script leaks on places.json a/e and catalog_links.json phases + chronology vs monuments.json
  const RE_BAD_FOREIGN = /[\u0370-\u03FF\u0600-\u06FFıİğĞşŞ]/;
  const RE_CYR_LEAK = /[\u0400-\u04FF]/;
  for (const c of data["data/places.json"]?.items || []) {
    for (const fld of ["a", "e"]) {
      const d = c[fld];
      if (!d || typeof d !== "object") continue;
      for (const lg of ["ru", "en", "ka"]) {
        const t = String(d[lg] || "");
        if (RE_BAD_FOREIGN.test(t)) err(`places.json ${c.id}.${fld}.${lg}: foreign script leak`);
        if ((lg === "ka" || lg === "en") && RE_CYR_LEAK.test(t)) err(`places.json ${c.id}.${fld}.${lg}: Cyrillic character leak`);
      }
    }
  }
  const catLinksPath = path.join(SITE, "..", "data", "curated", "catalog_links.json");
  if (fs.existsSync(catLinksPath)) {
    const catLinks = JSON.parse(fs.readFileSync(catLinksPath, "utf8"));
    const monById = new Map((data["data/monuments.json"]?.features || []).map((f) => [String(f.properties?.id), f.properties]));
    for (const e of catLinks.links || []) {
      const refs = (e.refs || []).filter((r) => r.startsWith("o:")).map((r) => r.slice(2));
      for (const ph of e.phases || []) {
        for (const lg of ["ru", "en", "ka"]) {
          const t = String(ph[lg] || "");
          if (RE_BAD_FOREIGN.test(t)) err(`catalog_links.json ${e.cat} phase.${lg}: foreign script leak`);
          if ((lg === "ka" || lg === "en") && RE_CYR_LEAK.test(t)) err(`catalog_links.json ${e.cat} phase.${lg}: Cyrillic character leak`);
        }
        if (!e.conflict_note) {
          for (const oid of refs) {
            const m = monById.get(oid);
            if (!m || m.y0 == null || m.y1 == null) continue;
            if (ph.y0 != null && ph.y1 != null && (ph.y0 > m.y1 || ph.y1 < m.y0)) {
              err(`catalog_links.json ${e.cat}: structured phase ${ph.y0}..${ph.y1} does not overlap o:${oid} ${m.y0}..${m.y1}`);
            }
            const comb = `${ph.ru || ""} | ${ph.en || ""} | ${ph.ka || ""}`;
            if (/(early\s+19th|нач(?:ало|але)\s+XIX|XIX\s*ს\.?\s*დასაწყის)/i.test(comb) && m.y0 >= 1850) {
              warns.push(`catalog_links.json ${e.cat}: text mentions early 19th c. while o:${oid} has y0=${m.y0}`);
            }
            if (/(late\s+19th|кон(?:ец|це)\s+XIX|XIX\s*ს\.?\s*დასასრულ)/i.test(comb) && m.y1 <= 1840) {
              warns.push(`catalog_links.json ${e.cat}: text mentions late 19th c. while o:${oid} has y1=${m.y1}`);
            }
          }
        }
      }
    }
  }
}

for (const w of warns) console.log("warning:", w);
if (errors.length) {
  console.log(`\n${errors.length} problem(s):`);
  for (const e of errors.slice(0, 200)) console.log(" -", e);
  if (errors.length > 200) console.log(` ... and ${errors.length - 200} more`);
  process.exit(1);
}
console.log(`ok: ${Object.keys(data).length} JSON files, ${ev?.length ?? 0} events, ${cl?.length ?? 0} versions, ${Object.keys(T?.ru || {}).length} interface keys`);
