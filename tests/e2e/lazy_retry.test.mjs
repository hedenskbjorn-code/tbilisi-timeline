// A layer whose lazy file fails to load must come back: getJSON tries again by itself, and after all its tries have failed the next switch on tries once more (not earlier than after 3 s).
// Also: the photographs of the cards carry their size from the data (the card does not jump when the picture arrives: CLS).
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

const LAYERS = [["places", "#showPlaces", "places"], ["sculptures", "#showMon", "mons"], ["plaques", "#showPlq", "plqs"]];

for (const [file, box, source] of LAYERS) {
  test(`${file}: one failed request is retried by itself and the layer appears`, async () => {
    const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
    let n = 0;
    await page.route(`**/data/${file}.json*`, (r) => { n++; return n <= 1 ? r.abort("failed") : r.continue(); });
    await waitReady(page);
    await page.check(box);
    await page.waitForFunction((s) => window.TT_E2E.map.getSource(s), source, { timeout: 15000 });
    assert.ok(n >= 2, "a second request was made");
    await page.ctx.close();
  });

  test(`${file}: after all the tries have failed the next switch on loads the layer`, async () => {
    const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
    let n = 0;
    await page.route(`**/data/${file}.json*`, (r) => { n++; return n <= 4 ? r.abort("failed") : r.continue(); });
    await waitReady(page);
    await page.check(box);
    await page.waitForFunction(() => true);
    await page.waitForTimeout(4500);                                    // the four tries (0.4 + 0.8 + 1.2 s) have failed
    assert.equal(await page.evaluate((s) => !!window.TT_E2E.map.getSource(s), source), false, "the layer is empty after four failures");
    await page.uncheck(box); await page.check(box);
    await page.waitForFunction((s) => window.TT_E2E.map.getSource(s), source, { timeout: 15000 });
    await page.ctx.close();
  });
}

test("the photographs of the cards have their width and height from the data", async () => {
  const MON = JSON.parse(fs.readFileSync(path.join(DATA, "sculptures.json"), "utf8"));
  for (const [t, f] of Object.entries(MON.photos)) assert.ok(f.w > 0 && f.h > 0, `sculptures.json: the photo ${t} has no size`);
  const c = MON.items.find((x) => x.y != null && x.ph && MON.photos[x.ph]);
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
  await waitReady(page);
  await page.check("#showMon");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("mons"), null, { timeout: 15000 });
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await page.evaluate((c) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: 18 }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, c);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const img = page.locator(".maplibregl-popup .pop figure img").first();
  await img.waitFor({ timeout: 15000 });
  const f = MON.photos[c.ph];
  assert.equal(await img.getAttribute("width"), String(f.w));
  assert.equal(await img.getAttribute("height"), String(f.h));
  await page.ctx.close();
});

test("the photographs of the cards of the register: every image has width and height before it is loaded", async () => {
  const photos = JSON.parse(fs.readFileSync(path.join(DATA, "photos.json"), "utf8"));
  for (const [t, f] of Object.entries(photos)) if (f.thumb) assert.ok(f.w > 0 && f.h > 0, `photos.json: the photo ${t} has no size`);
  const REL = JSON.parse(fs.readFileSync(path.join(DATA, "religious.json"), "utf8"));
  const c = REL.find((x) => x.ph && String(x.ph).split("|").some((t) => photos[t] && photos[t].thumb) && Number.isFinite(x.from) && x.from <= 2020 && x.to === undefined);
  assert.ok(c, "a religious building with a photograph");
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
  await waitReady(page);
  const pt = await page.evaluate((c) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: 18 }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, c);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  await page.locator(".maplibregl-popup .pop .photos img").first().waitFor({ timeout: 15000 });
  const bad = await page.evaluate(() => [...document.querySelectorAll(".maplibregl-popup .pop .photos img")].filter((i) => !(i.getAttribute("width") && i.getAttribute("height"))).length);
  assert.equal(bad, 0, "images without width/height attributes");
  await page.ctx.close();
});
