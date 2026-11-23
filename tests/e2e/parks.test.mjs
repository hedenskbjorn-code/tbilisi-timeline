// The parks and gardens that only OpenStreetMap names (tools/apply_parks.py) are in the layer "Local names": a point and a card with the name, the former name and the source.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1990`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const PL = JSON.parse(fs.readFileSync(path.join(DATA, "places.json"), "utf8"));
const PARKS = PL.items.filter((c) => c.pk);

test("the layer has the parks of OSM, among them the Vaso Godziashvili Garden with its former name", async () => {
  assert.ok(PARKS.length >= 80, "parks: " + PARKS.length);
  const g = PARKS.find((c) => c.id === "park-r1734212");
  assert.ok(g, "Vaso Godziashvili Garden (OSM relation 1734212)");
  assert.equal(g.n.en, "Vaso Godziashvili Garden");
  assert.equal(g.o.en, "Red Garden");
  assert.ok(PARKS.every((c) => c.k === "garden" && !c.a && !c.e && /^https:\/\/www\.openstreetmap\.org\//.test(c.s.u)));
});

async function openCard(c, zoom = 16.5) {
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await page.evaluate(([c, z]) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: z }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, [c, zoom]);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  return pop;
}

test("the card of the Godziashvili Garden: the name, the former name Red Garden, the OSM source", async () => {
  await page.check("#showPlaces");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("places"), null, { timeout: 20000 });
  const g = PARKS.find((c) => c.id === "park-r1734212");
  const pop = await openCard(g);
  const txt = await pop.innerText();
  assert.ok(txt.includes("Vaso Godziashvili Garden"), txt);
  assert.ok(txt.includes("Former name: Red Garden"), txt);
  assert.ok(txt.includes("Garden or park"), txt);
  assert.equal(await pop.locator("a[href='https://www.openstreetmap.org/relation/1734212']").count(), 1);
});

test("a park whose name lacks English still has a title (no 'undefined')", async () => {
  const c = PARKS.find((x) => !x.n.en);
  if (!c) return;                                                               // all the names have English: nothing to show
  const pop = await openCard(c);
  const txt = await pop.innerText();
  assert.ok(!txt.includes("undefined"), txt);
  assert.ok(txt.includes(c.n.ru || c.n.ka), txt);                                // the name that exists: English, else Russian, else Georgian
});

test("the search finds a park by its former name", async () => {
  await page.click("#btnSearch");
  await page.fill("#searchQ", "Red Garden");
  await page.waitForSelector("#searchRes li");
  assert.ok((await page.locator("#searchRes").innerText()).includes("Vaso Godziashvili Garden"));
  await page.keyboard.press("Escape");
});
