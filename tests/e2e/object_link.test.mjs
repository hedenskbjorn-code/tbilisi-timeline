// A link to an OBJECT (not to the year and the view of the map): ?o=<kind>:<id> opens the card of the object; the address bar follows the open card; the icon of the link in the card copies it.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });
const read = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));

async function viaLink(o, title) {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en&o=${encodeURIComponent(o)}#2026`);
  await waitReady(page);
  await page.waitForFunction((t) => [...document.querySelectorAll(".maplibregl-popup .pop h3, #imTitle")].some((h) => h.textContent.includes(t)), title, { timeout: 20000 });
  return page;
}

const RL = read("religious.json"), RO = read("religious_osm.json").items, SC = read("science.json"), ED = read("education.json"), PL = read("places.json").items, MON = read("sculptures.json").items, PQ = read("plaques.json").items;
const CASES = [
  ["a curated religious building", "rl:" + RL.find((x) => x.name.en && x.from <= 2000 && x.to === undefined).id, RL.find((x) => x.name.en && x.from <= 2000 && x.to === undefined).name.en],
  ["a religious building of OpenStreetMap", "rl:" + RO.find((x) => x.name.en && x.name.ka && x.name.ru).id, RO.find((x) => x.name.en && x.name.ka && x.name.ru).name.en],
  ["a science and culture object", "sc:" + SC[0].id, SC[0].name.en],
  ["an education object (the layer is off by default)", "ed:" + ED[0].id, ED[0].name.en],
  ["a local name", "pl:" + PL.find((x) => x.n.en === "Mushtaidi Garden").id, "Mushtaidi Garden"],
  ["a monument without a year", "mn:" + MON.find((x) => x.y == null && x.n.en).id, MON.find((x) => x.y == null && x.n.en).n.en],
  ["a plaque", "pq:" + PQ.find((x) => x.n.en).id, PQ.find((x) => x.n.en).n.en],
  ["a metro station", "ms:metrost_Samgori", "Samgori"],
];
for (const [name, o, title] of CASES) {
  test(`the link ?o=${o.slice(0, 18)}… opens the card of ${name}`, async () => {
    const page = await viaLink(o, title);
    assert.ok((await page.evaluate(() => new URL(location.href).searchParams.get("o"))) === o, "the address bar keeps the link while the card is open");
    assert.equal(await page.locator("#objShare").count(), 1, "the icon of the link is in the card");
    await page.ctx.close();
  });
}

test("a link to a street opens its card and the address bar keeps the link until the window is closed", async () => {
  const st = read("street_names.json").streets.find((s) => s.now.en === "Kita Abashidze Street");
  const key = st.geom || st.now.en;
  const page = await viaLink("st:" + key, st.now.en);
  assert.equal(await page.evaluate(() => new URL(location.href).searchParams.get("o")), "st:" + key);
  await page.click("#imClose");
  assert.equal(await page.evaluate(() => new URL(location.href).searchParams.get("o")), null, "closed: the link is removed from the address bar");
  await page.ctx.close();
});

test("the icon of the link in a card copies the link to that object and the card closes with the parameter removed", async () => {
  const c = PL.find((x) => x.n.en === "Mushtaidi Garden");
  const page = await viaLink("pl:" + c.id, "Mushtaidi Garden");
  await page.ctx.grantPermissions(["clipboard-read", "clipboard-write"], { origin: server.url });
  await page.click("#objShare");
  await page.waitForFunction(() => document.getElementById("objShare").textContent === "✓", null, { timeout: 5000 });
  const link = await page.evaluate(() => navigator.clipboard.readText());
  assert.equal(new URL(link).searchParams.get("o"), "pl:" + c.id, link);
  await page.locator(".maplibregl-popup-close-button").first().click();
  await page.waitForFunction(() => !new URL(location.href).searchParams.has("o"), null, { timeout: 5000 });
  await page.ctx.close();
});
