// The layer "Local names": the file is lazy, the layer is off by default, the card says what the place is and where the name comes from (or that the source does not say), the search finds the places.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
import { DATA } from "./helpers.mjs";

let server, browser, page, reqs;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1960`);
  reqs = [];
  page.on("request", (r) => reqs.push(r.url()));
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const PL = JSON.parse(fs.readFileSync(path.join(DATA, "places.json"), "utf8"));

test("the file of the places is not loaded with the first screen and the layer is off", async () => {
  assert.ok(!reqs.some((u) => u.includes("places.json")), "places.json is lazy");
  assert.equal(await page.isChecked("#showPlaces"), false);
});

test("the check box loads the file, shows all the places and a legend with the kinds", async () => {
  await page.check("#showPlaces");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("places"), null, { timeout: 15000 });
  const n = await page.evaluate(() => window.TT_E2E.map.getSource("places").serialize().data.features.length);
  assert.equal(n, PL.items.length);
  assert.equal(await page.evaluate(() => window.TT_E2E.map.getLayoutProperty("places-pt", "visibility")), "visible");
  const leg = await page.locator("#placesLegend").innerText();
  for (const k of new Set(PL.items.map((x) => x.k))) assert.ok(leg.includes(PL.ui["kind_" + k].en), "legend: " + k);
});

async function openCard(id) {
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));      // an earlier card is closed
  const c = PL.items.find((x) => x.id === id);
  const pt = await page.evaluate((c) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: 16 }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, c);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  return { c, pop };
}

test("the card of the Mushtaidi garden: what it is, the origin of the name, the source", async () => {
  const id = PL.items.find((x) => x.n.en === "Mushtaidi Garden").id;
  const { c, pop } = await openCard(id);
  const txt = await pop.innerText();
  assert.ok(txt.includes(c.n.en), txt);
  assert.match(txt, /Origin of the name: /);
  assert.ok(txt.includes(c.e.en.slice(0, 30)), "the etymology text: " + txt);
  assert.match(txt, /Source: Wikipedia \(/);
  await page.keyboard.press("Escape");
});

test("a place without an etymology in the source says so", async () => {
  const c0 = PL.items.find((x) => !x.e && x.k === "bridge");
  const { pop } = await openCard(c0.id);
  assert.match(await pop.innerText(), /The source does not say where the name comes from/);
  await page.locator(".maplibregl-popup .actions a.fb").first().click();
  await page.waitForFunction(() => !document.getElementById("imBody").closest("#infoModal").hidden, null, { timeout: 15000 });
  const body = await page.locator("#imBody").innerText();
  assert.ok(body.includes("“" + c0.s.aq + "”"), "the quote of the source");
  assert.match(body, /CC BY-SA/);
  await page.keyboard.press("Escape");
});

test("the search finds a place by its name in three languages and opens its card", async () => {
  await page.click("#btnSearch");
  await page.fill("#searchQ", "Mushtaidi");
  await page.waitForSelector("#searchRes li");
  const first = await page.locator("#searchRes li", { hasText: "📍" }).first().innerText();
  assert.match(first, /Garden or park/);
  await page.locator("#searchRes li", { hasText: "📍" }).first().click();
  await page.waitForFunction(() => /Origin of the name/.test([...document.querySelectorAll(".maplibregl-popup .pop")].map((p) => p.innerText).join("|")), null, { timeout: 15000 });
  assert.equal(await page.locator(".maplibregl-popup .pop").count(), 1, "one card is open");
});

test("the former hippodrome is an area with a contour, the opening year, the plan of the Central Park, a note about the contour and no closing year", async () => {
  await page.check("#showPlaces");
  const c = PL.items.find((x) => x.id === "area-saburtalo-hippodrome");
  assert.ok(c && c.g, "the entry has a contour");
  assert.equal(await page.evaluate(() => window.TT_E2E.map.getLayoutProperty("places-area-fill", "visibility")), "visible");
  const { pop } = await openCard(c.id);
  const txt = await pop.innerText();
  assert.match(txt, /opened in 1959/);
  assert.match(txt, /Central Park is planned here/);
  assert.match(txt, /sources do not say in which year the races stopped/);
  assert.match(txt, /the hippodrome was larger/, "the note about the contour");
  assert.ok(!/Origin of the name|does not say where the name comes from/.test(txt), "no question of etymology for the area");
  assert.ok(Math.abs(c.lat - 41.7198) < 0.002 && Math.abs(c.lon - 44.7533) < 0.003, "the centre of the contour");
  await page.keyboard.press("Escape");
});

test("the check box turns the layer off", async () => {
  await page.uncheck("#showPlaces");
  assert.equal(await page.evaluate(() => window.TT_E2E.map.getLayoutProperty("places-pt", "visibility")), "none");
});
