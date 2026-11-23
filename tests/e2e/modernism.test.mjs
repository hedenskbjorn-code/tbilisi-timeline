// The layer "Soviet modernism" (data/modernism.json): a lazy file, off by default, a building appears in the year of the end of its construction, the card (architects, function then and now,
// condition, photo with licence, sources with a link to every source), the details with the quotations, the link to the object, the search, and the folk names of the layer of places.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA } from "./helpers.mjs";

let server, browser, page, reqs;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1990`);
  reqs = [];
  page.on("request", (r) => reqs.push(r.url()));
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const MOD = JSON.parse(fs.readFileSync(path.join(DATA, "modernism.json"), "utf8"));
const PLACES = JSON.parse(fs.readFileSync(path.join(DATA, "places.json"), "utf8"));
const feats = () => page.evaluate(() => window.TT_E2E.map.getSource("mods").serialize().data.features.length);

async function openCard(c, zoom = 17) {
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await page.evaluate(([c, z]) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: z }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, [c, zoom]);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  return pop;
}

test("the file is lazy and the layer is off", async () => {
  assert.ok(!reqs.some((u) => /modernism\.json/.test(u)));
  assert.equal(await page.isChecked("#showMod"), false);
});

test("a building appears in the year of the end of its construction", async () => {
  await page.check("#showMod");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("mods"), null, { timeout: 20000 });
  assert.equal(await feats(), MOD.items.filter((c) => c.y <= 1990).length);
  assert.ok(MOD.items.some((c) => c.y > 1990) || MOD.items.every((c) => c.y <= 1990));
  const legend = await page.locator("#modLegend").innerText();
  assert.match(legend, /Soviet modernism/);
});

test("the card of a building: year, architects, function, condition, photo with its licence, sources", async () => {
  const c = MOD.items.find((x) => x.y <= 1990 && x.ph && x.ar.length && x.ft && x.fn);
  assert.ok(c, "a building with everything");
  const pop = await openCard(c);
  const txt = await pop.innerText();
  assert.ok(txt.includes(c.n.en), txt);
  assert.match(txt, new RegExp("Built: " + c.y));
  assert.ok(txt.includes("Architects: " + c.ar.join(", ")), txt);
  assert.ok(txt.includes(c.d.en), "the description");
  assert.ok(txt.includes("Built as: "), txt);
  assert.ok(txt.includes("Now: "), txt);
  const ph = MOD.photos[c.ph];
  assert.ok(await pop.locator(`img[src="${ph.thumb}"]`).count() === 1, "the photo");
  assert.ok(txt.includes(ph.license), "the licence");
  assert.equal(await pop.locator(".src a").count(), c.s.length, "a link for each source");
  assert.ok(await pop.locator("a[href^='https://commons.wikimedia.org/']").count() >= 1);
});

test("the details give a quotation for every source and the origin of the point", async () => {
  const c = MOD.items.find((x) => x.y <= 1990 && x.ph);
  const pop = await openCard(c);
  await page.locator(".maplibregl-popup .actions a.fb").first().click();
  await page.waitForFunction(() => !document.getElementById("imBody").closest("#infoModal").hidden, null, { timeout: 15000 });
  const txt = await page.locator("#imBody").innerText();
  await page.keyboard.press("Escape");
  for (const q of c.s) assert.ok(txt.includes(q.q.slice(0, 40)), "the quotation of " + q.u);
  assert.match(txt, /ODbL|Wikidata|coordinates/);
});

test("a building without a photo has a card without a picture", async () => {
  const c = MOD.items.find((x) => x.y <= 1990 && !x.ph);
  assert.ok(c, "a building without a photo exists");
  const pop = await openCard(c);
  assert.equal(await pop.locator("img").count(), 0);
});

test("the link ?o=md:<id> opens the card of the building", async () => {
  const c = MOD.items[0];
  const p2 = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en&o=${encodeURIComponent("md:" + c.id)}#1990`);
  await waitReady(p2);
  await p2.locator(".maplibregl-popup .pop h3").waitFor({ timeout: 20000 });
  assert.equal(await p2.locator(".maplibregl-popup .pop h3").innerText(), c.n.en);
  assert.equal(await p2.isChecked("#showMod"), true);
  await p2.ctx.close();
});

test("the search finds a building by its name and by its folk name", async () => {
  const c = MOD.items.find((x) => (x.f || []).length);
  assert.ok(c, "a building with a folk name");
  await page.click("#btnSearch");
  await page.fill("#searchQ", c.n.en.slice(0, 12));
  await page.waitForSelector("#searchRes li");
  const txt = await page.locator("#searchRes").innerText();
  assert.ok(txt.includes(c.n.en), txt);
  const folk = Object.values(c.f[0].n).find(Boolean);
  await page.fill("#searchQ", folk);
  await page.waitForTimeout(400);
  assert.ok((await page.locator("#searchRes").innerText()).includes(c.n.en), "found by the folk name " + folk);
  await page.keyboard.press("Escape");
});

test("the folk names of the places: a card shows the name, the meaning and the pages; a rude name is not there", async () => {
  const withF = PLACES.items.filter((c) => c.f);
  assert.ok(withF.length >= 10, "folk names exist: " + withF.length);
  assert.ok(!JSON.stringify(PLACES).includes("Always Ultra"), "the rude nickname is left out");
  await page.check("#showPlaces");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("places"), null, { timeout: 20000 });
  const c = withF.find((x) => x.f[0].m && x.f[0].n.ka && x.id.startsWith("district-"));
  assert.ok(c, "a place with a folk name and a meaning");
  const pop = await openCard(c, 15.5);
  const txt = await pop.innerText();
  assert.ok(txt.includes("Folk name"), txt);
  assert.ok(txt.includes(c.f[0].n.ka), txt);
  assert.ok(txt.includes(c.f[0].m.en), txt);
  const folkOnly = withF.find((x) => !x.a);
  assert.ok(folkOnly, "a place that exists for its folk name only");
  const pop2 = await openCard(folkOnly, 16.5);
  assert.ok((await pop2.innerText()).includes("Folk name"));
});
