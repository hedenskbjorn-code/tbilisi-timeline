// The quarters, squares and bridges that only OpenStreetMap names (tools/apply_osm_names.py, the names from the answer of Gemini) are in the layer "Local names": a point and a card with the name in the language
// of the page, the kind, the OSM source and no description of its own; the administrative districts and the villages outside the city are not among them.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA, tick } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const PL = JSON.parse(fs.readFileSync(path.join(DATA, "places.json"), "utf8"));
const OSMN = PL.items.filter((c) => c.id.startsWith("osm-"));

test("the data: about a hundred places, three kinds, the OSM object as the source, names in three languages in the right script, no description, no administrative district, inside the city", () => {
  assert.ok(OSMN.length >= 100, "places from the names of OSM: " + OSMN.length);
  assert.deepEqual([...new Set(OSMN.map((c) => c.k))].sort(), ["bridge", "district", "square"]);
  const GE = /[ა-ჰ]/, CY = /[А-Яа-яЁё]/, LAT = /[A-Za-z]/;
  for (const c of OSMN) {
    assert.equal(c.pk, 1, c.id);
    assert.ok(!c.a && !c.e && !c.f, `${c.id}: a place of OSM has no description of its own`);
    assert.match(c.s.u, /^https:\/\/www\.openstreetmap\.org\/(node|way|relation)\/\d+$/, c.id);
    assert.ok(GE.test(c.n.ka) && !CY.test(c.n.ka), `${c.id}: ka ${c.n.ka}`);
    assert.ok(CY.test(c.n.ru) && !GE.test(c.n.ru), `${c.id}: ru ${c.n.ru}`);
    assert.ok(LAT.test(c.n.en) && !CY.test(c.n.en) && !GE.test(c.n.en), `${c.id}: en ${c.n.en}`);
    assert.ok(!c.n.ka.includes("რაიონი"), `${c.id}: an administrative district is in the layer of districts: ${c.n.ka}`);
    assert.ok(!c.n.ka.includes("პროსპექტი"), c.id);
    assert.ok(c.lon > 44.6 && c.lon < 45.1 && c.lat > 41.6 && c.lat < 41.9, `${c.id}: outside Tbilisi`);
  }
  assert.equal(new Set(OSMN.map((c) => c.id)).size, OSMN.length, "unique ids");
  for (const bad of ["Akhali Mtskheta", "Jikhura", "Gora", "Zemo Vaziani"]) assert.ok(!OSMN.some((c) => c.n.en === bad), bad + " is a village outside the city");
  // the pins that were dropped as duplicates of the quarters do not come back as new cards
  for (const id of ["osm-n11373213800", "osm-n11373213801", "osm-n11373213802"]) assert.ok(!PL.items.some((c) => c.id === id), id);
});

test("the layer draws them and the card of a bridge says the name, the kind and the source", async () => {
  await tick(page, "#showPlaces", true);
  await page.waitForFunction(() => window.TT_E2E.map.getSource("places"), null, { timeout: 20000 });
  const n = await page.evaluate(() => window.TT_E2E.map.getSource("places").serialize().data.features.filter((f) => String(f.properties.id).startsWith("osm-")).length);
  assert.equal(n, OSMN.length, "every place of OSM is a point of the layer");
  const c = OSMN.find((x) => x.k === "bridge");
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await page.evaluate(([c]) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: 17 }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, [c]);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  const txt = await pop.innerText();
  assert.ok(txt.includes(c.n.en), txt);
  assert.ok(!txt.includes("undefined"), txt);
  assert.ok(await pop.locator(`a[href="${c.s.u}"]`).count() >= 1, "the OSM link on the card");
});
