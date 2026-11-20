// Checks of the data and of the texts of the site; run by hand (node tests/check_data.mjs) and by the workflow before every deploy.
// They stop the deploy when a translation is missing, when a Georgian text is not Georgian (Cyrillic, English), when a file that the page
// needs is missing or a JSON file is broken. No dependencies: only Node.
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

// ---- JavaScript syntax of the files of the site (not the vendor) ------------------------------------------
for (const p of fs.readdirSync(SITE).filter((f) => f.endsWith(".js")).map((f) => path.join(SITE, f))) {
  try { new vm.Script(fs.readFileSync(p, "utf8"), { filename: p }); } catch (e) { err(`${rel(p)}: syntax error (${e.message})`); }
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
    else for (const s of x.src) { const u = typeof s === "string" ? s : s?.url; if (!/^https?:\/\//.test(u || "")) err(`${w}: bad source ${JSON.stringify(s)}`); }
    if (x.note) {
      for (const l of ["ru", "en", "ka"]) if (!x.note[l] || !String(x.note[l]).trim()) err(`${w}: note.${l} is missing`);
    }
    if (x.place && !(Number.isFinite(x.place.lng) && Number.isFinite(x.place.lat))) err(`${w}: place without coordinates`);
  });
}

// ---- the changelog ---------------------------------------------------------------------------------------------
const cl = data["data/changelog.json"];
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

// ---- the files that the page needs ------------------------------------------------------------------------------
const html = fs.readFileSync(path.join(SITE, "index.html"), "utf8");
const scripts = [...html.matchAll(/<script[^>]*\ssrc="([^"]+)"/g)].map((m) => m[1]).filter((s) => !/^https?:/.test(s));
for (const s of scripts) if (!fs.existsSync(path.join(SITE, s))) err(`index.html: the script ${s} does not exist`);
if (scripts.indexOf("i18n.js") < 0 || scripts.indexOf("i18n.js") > scripts.indexOf("app.js")) err("index.html: i18n.js must be loaded before app.js");
const sw = fs.readFileSync(path.join(SITE, "sw.js"), "utf8");
const shell = JSON.parse((sw.match(/const SHELL = (\[[^\]]*\])/) || [])[1] || "[]");
for (const f of shell) if (f !== "./" && !fs.existsSync(path.join(SITE, f))) err(`sw.js: the file ${f} of the shell does not exist`);
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
