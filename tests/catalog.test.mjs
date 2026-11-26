import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "site", "data");
const cat = JSON.parse(fs.readFileSync(path.join(DATA, "catalog.json"), "utf8"));
const byId = new Map(cat.items.map((x) => [x.id, x]));

test("unified catalog links register and curated layers under one stable ID", () => {
  assert.equal(cat.by_ref["o:3564"], cat.by_ref["rl:atashgah"]);
  assert.equal(cat.by_ref["o:3433"], cat.by_ref["rl:sioni"]);
  assert.equal(cat.by_ref["o:3914"], cat.by_ref["rl:anchiskhati"]);
  assert.equal(cat.by_ref["o:38197"], cat.by_ref["rl:reg38197"]);
  assert.equal(cat.by_ref["o:4157"], cat.by_ref["sc:janashia"]);
  assert.equal(cat.by_ref["sc:janashia"], cat.by_ref["mu:janashia"]);
  assert.equal(cat.by_ref["sc:artmuseum"], cat.by_ref["mu:artmuseum"]);
  assert.equal(cat.by_ref["sc:open_air"], cat.by_ref["mu:open_air"]);
  assert.equal(cat.by_ref["sc:soviet_occupation"], "cat:cur:soviet_occupation");
  assert.equal(byId.get("cat:cur:soviet_occupation").housed_in, "cat:reg:4157");
});

test("unified catalog tracks cross-layer date conflicts and resolved matches", () => {
  const atash = byId.get(cat.by_ref["rl:atashgah"]);
  assert.equal(atash.date_conflict, false);
  assert.equal(atash.phases.length, 2);
  assert.equal(atash.dates["rl:atashgah"].ye, 700);
  assert.equal(byId.get(cat.by_ref["rl:sioni"]).phases.length, 2);
  assert.equal(byId.get(cat.by_ref["rl:anchiskhati"]).phases.length, 2);
  assert.equal(byId.get(cat.by_ref["o:3616"]).phases.length, 2);
  assert.equal(byId.get(cat.by_ref["rl:juma"]).phases.length, 2);
  assert.equal(byId.get(cat.by_ref["rl:lurji"]).phases.length, 2);
  assert.equal(byId.get(cat.by_ref["rl:reg3049"]).phases.length, 2);
  assert.equal(byId.get(cat.by_ref["o:38197"]).date_conflict, false);
  assert.equal(byId.get(cat.by_ref["rl:metekhi"]).date_conflict, false, "1278-1289 is the same range");
});
