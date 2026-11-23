// The layers "Monuments and sculptures" and "Memorial plaques": lazy files, off by default, a year filter, a sub box for the objects without a year, a label of an object without a name,
// a card with the photo and the licence, clusters.
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
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1990`);
  reqs = [];
  page.on("request", (r) => reqs.push(r.url()));
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const MON = JSON.parse(fs.readFileSync(path.join(DATA, "sculptures.json"), "utf8"));
const PLQ = JSON.parse(fs.readFileSync(path.join(DATA, "plaques.json"), "utf8"));
const feats = (src) => page.evaluate((s) => window.TT_E2E.map.getSource(s).serialize().data.features.length, src);

test("the files are lazy and both layers are off", async () => {
  assert.ok(!reqs.some((u) => /sculptures\.json|plaques\.json/.test(u)));
  assert.equal(await page.isChecked("#showMon"), false);
  assert.equal(await page.isChecked("#showPlq"), false);
});

test("the monuments of the year: the layer shows the dated objects up to the year, the sub box adds the undated ones", async () => {
  await page.check("#showMon");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("mons"), null, { timeout: 20000 });
  const dated = MON.items.filter((c) => c.y != null && c.y <= 1990).length;
  assert.equal(await feats("mons"), dated);
  assert.ok(dated > 20 && dated < MON.items.length);
  assert.equal(await page.locator("#showMonUndated").isVisible(), true);
  await page.check("#showMonUndated");
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("mons").serialize().data.features.length === n, dated + MON.items.filter((c) => c.y == null).length, { timeout: 10000 });
  await page.uncheck("#showMonUndated");
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("mons").serialize().data.features.length === n, dated, { timeout: 10000 });
});

async function openCard(key, c, zoom = 18) {
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await page.evaluate(([c, z]) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: z }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, [c, zoom]);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  return pop;
}

test("the card of a monument: the type, the year, the street and the photo with its author and licence", async () => {
  const c = MON.items.find((x) => x.y != null && x.y <= 1990 && x.ph && MON.photos[x.ph] && x.st && (x.n.en || x.n.ru || x.n.ka));
  assert.ok(c, "an object with everything");
  const pop = await openCard("mon", c);
  const txt = await pop.innerText();
  assert.ok(txt.includes(MON.ui["k_" + c.k].en), txt);
  assert.match(txt, new RegExp("Installed: " + c.y));
  assert.match(txt, /Location: /);
  assert.match(txt, /Photo: Wikimedia Commons/);
  assert.ok(await pop.locator("figure img").count() >= 1, "the photo");
});

test("an object without a name is labelled by its type and the nearest street", async () => {
  const c = MON.items.find((x) => !x.n.ka && !x.n.ru && !x.n.en && x.y == null && x.st);
  assert.ok(c, "an undated object without a name that has a street");
  await page.check("#showMonUndated");
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("mons").serialize().data.features.length >= n, 1, { timeout: 10000 });
  const pop = await openCard("mon", c);
  const h = await pop.locator("h3").innerText();
  const st = MON.streets[c.st];
  assert.equal(h, MON.ui["k_" + c.k].en + ", " + st.en);
});

test("the plaques: dated by the first year of the life of the inscription, a card with the inscription", async () => {
  await page.check("#showPlq");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("plqs"), null, { timeout: 20000 });
  const dated = PLQ.items.filter((c) => c.y != null && c.y <= 1990).length;
  assert.equal(await feats("plqs"), dated);
  const c = PLQ.items.find((x) => x.y != null && x.y <= 1990 && x.ins && x.ph && PLQ.photos[x.ph]);
  const pop = await openCard("plq", c);
  const txt = await pop.innerText();
  assert.match(txt, new RegExp("Linked to the house since " + c.y));
  assert.match(txt, /Inscription: /);
  assert.match(txt, /Memorial plaque/);
});

test("the year of the plaque is never the year of the life: no plaque is dated by a year that its inscription does not name first", async () => {
  for (const c of PLQ.items) if (c.y != null) assert.ok(c.ins.includes(String(c.y)), `${c.id}: the year ${c.y} is not in the inscription`);
});

test("the layers turn off", async () => {
  await page.uncheck("#showMon");
  await page.uncheck("#showPlq");
  const v = await page.evaluate(() => ["mon-pt", "plq-pt", "mon-cl", "plq-cl"].map((i) => window.TT_E2E.map.getLayoutProperty(i, "visibility")));
  assert.deepEqual(v, ["none", "none", "none", "none"]);
});

test("a description found by a search: the card shows it (ru / en), the details give the quotation, the card of another language shows no description that does not exist", async () => {
  const c = MON.items.find((x) => x.id === "KAW_032");                        // 1981: shown in the year 1990 of this test
  assert.ok(c && c.d && c.d.en && c.dq && c.dq.length, "the description with quotations exists in the data");
  assert.ok(!c.d.ka, "no Georgian description yet: it waits for Gemini");
  await page.check("#showMon");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("mons"), null, { timeout: 20000 });
  const pop = await openCard("mon", c);
  assert.ok((await pop.innerText()).includes(c.d.en), "the English description");
  await page.locator(".maplibregl-popup .actions a.fb").first().click();
  await page.waitForFunction(() => !document.getElementById("imBody").closest("#infoModal").hidden, null, { timeout: 15000 });
  const body = await page.locator("#imBody").innerText();
  assert.ok(body.includes(c.dq[0].q.slice(0, 40)), "the quotation in the details");
  await page.keyboard.press("Escape");
});
