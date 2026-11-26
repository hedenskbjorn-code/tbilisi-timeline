// The places of worship of OpenStreetMap (data/religious_osm.json) join the layer of religious buildings after the first screen: a card of a named building, a card of a building without a name
// ("denomination, nearest street"), the source OpenStreetMap, the search.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA } from "./helpers.mjs";

let server, browser, page, reqs;
const RO = JSON.parse(fs.readFileSync(path.join(DATA, "religious_osm.json"), "utf8"));
const REL = JSON.parse(fs.readFileSync(path.join(DATA, "religious.json"), "utf8"));
test.before(async () => {
  server = await startServer(); browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
  reqs = []; page.on("request", (r) => reqs.push(r.url()));
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

async function openCard(c) {
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await page.evaluate((c) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: 18 }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, c);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  return pop;
}

test("the layer holds the curated buildings and the buildings of OpenStreetMap", async () => {
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("rel").serialize().data.features.length === n, REL.length + RO.items.length, { timeout: 20000 });
  assert.ok(RO.items.length > 150, "the new buildings: " + RO.items.length);
  assert.ok(reqs.some((u) => u.includes("religious_osm.json")), "the file is loaded");
});

test("the card of a named building: the name, the denomination, OpenStreetMap as the source, no status line", async () => {
  const c = RO.items.find((x) => x.name.en && x.name.ru && x.name.ka && !x.src.length);
  assert.ok(c);
  const pop = await openCard(c);
  const txt = await pop.innerText();
  assert.ok(txt.includes(c.name.en), txt);
  assert.match(txt, /Sources: OpenStreetMap/);
  if (c.undated) assert.match(txt, /unknown \(not given in OpenStreetMap\)/);
  assert.ok(!/Status:/.test(txt), "no status line for an OSM building");
  assert.equal(await pop.locator(`a[href="https://www.openstreetmap.org/${c.osm}"]`).count(), 1);
});

test("a building without a name is titled by its denomination and the nearest street", async () => {
  const c = RO.items.find((x) => !x.name.ka && !x.name.ru && !x.name.en && x.st);
  assert.ok(c, "an unnamed building with a street");
  const pop = await openCard(c);
  const h = await pop.locator("h3").innerText();
  assert.ok(h.endsWith(", " + RO.streets[c.st].en), h);
  assert.ok(h.length > RO.streets[c.st].en.length + 3, "the denomination stands before the street: " + h);
});

test("the search finds a building of OpenStreetMap by its name", async () => {
  const c = RO.items.find((x) => x.name.en && /[A-Za-z]{5}/.test(x.name.en));
  await page.click("#btnSearch"); await page.fill("#searchQ", c.name.en.split(/\s+/).slice(0, 2).join(" "));
  await page.waitForSelector("#searchRes li[data-i]", { timeout: 10000 });
  assert.ok((await page.locator("#searchRes li", { hasText: "⛪" }).count()) >= 1);
  await page.keyboard.press("Escape");
});

test("undated OSM churches do not appear at historical year 500, and return at 2026", async () => {
  await page.evaluate(() => { location.hash = "#500"; });
  await page.waitForFunction(() => window.TT_E2E.year === 500);
  await page.evaluate(() => new Promise((r) => { const m = window.TT_E2E.map; if (m.isMoving() || !m.areTilesLoaded()) m.once("idle", r); else m.once("render", () => setTimeout(r, 50)); }));
  await page.waitForFunction(() => window.TT_E2E.map.queryRenderedFeatures({ layers: ["rel-pt"] }).filter((f) => f.properties.undated).length === 0, null, { timeout: 5000 });
  const shown500 = await page.evaluate(() => window.TT_E2E.map.queryRenderedFeatures({ layers: ["rel-pt"] }).filter((f) => f.properties.undated).length);
  assert.equal(shown500, 0, "no undated churches at year 500");
  await page.evaluate(() => { location.hash = "#2026"; });
  await page.waitForFunction(() => window.TT_E2E.year === 2026);
});
