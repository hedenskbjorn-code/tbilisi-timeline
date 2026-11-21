// Names and addresses of register objects in English and Russian, made by the same module as on the site (site/translit.js + site/data/names_i18n.json).
// Usage: node tools/translit_names.mjs <in.json> <out.json>   in: [{id, name, address, wp}]   out: {id: {ru: {name, address}, en: {name, address}}}
import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const ctx = { window: {} };
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root, "site", "translit.js"), "utf8"), ctx);
const G = ctx.window.GeoTr;
G.setDict(JSON.parse(fs.readFileSync(path.join(root, "site", "data", "names_i18n.json"), "utf8")));
const items = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = {};
for (const it of items) {
  out[it.id] = {};
  for (const l of ["ru", "en"]) {
    out[it.id][l] = { name: G.nameInfo(it.name, l, it.wp || undefined).text, address: it.address ? G.address(it.address, l) : "" };
  }
}
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
console.log(Object.keys(out).length, "names");
