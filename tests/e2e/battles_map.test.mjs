// The layer "Battles and sieges on the map" (#showBattleMap): off by default, cumulative filter by year,
// clicking a point opens the event card with source and report link, and labels follow the interface language.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1800`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const EV = JSON.parse(fs.readFileSync(path.join(DATA, "history_events.json"), "utf8")).events;
const WITH_PLACE = EV.filter((e) => (e.cat === "battle" || e.cat === "invasion") && e.place);

test("off by default and turns on with #showBattleMap", async () => {
  assert.ok(WITH_PLACE.length >= 49, "expected >= 49 battle/invasion events with coordinates");
  assert.equal(await page.isChecked("#showBattleMap"), false);
  const vis0 = await page.evaluate(() => window.TT_E2E.map.getLayoutProperty("battle-pt", "visibility"));
  assert.equal(vis0, "none");

  await page.evaluate(() => { const f = document.getElementById("filters"); if (f.hidden) document.getElementById("btnFilters").click(); const d = document.querySelector('details[data-sec="f-adv"]'); if (d && !d.open) d.open = true; });
  await page.check("#showBattleMap");
  await page.waitForTimeout(250);
  const vis1 = await page.evaluate(() => window.TT_E2E.map.getLayoutProperty("battle-pt", "visibility"));
  assert.equal(vis1, "visible");
});

test("cumulative filter by year shows events up to selected year", async () => {
  const count1800 = await page.evaluate(() => {
    const f = window.TT_E2E.map.getFilter("battle-pt");
    const feats = window.TT_E2E.map.getSource("battle-map").serialize().data.features;
    return { f, n: feats.filter((x) => x.properties.year <= window.TT_E2E.year).length };
  });
  assert.equal(count1800.n, WITH_PLACE.filter((e) => e.year <= 1800).length);

  await page.evaluate(() => { location.hash = "#1700"; });
  await page.waitForTimeout(250);
  const count1700 = await page.evaluate(() => {
    const feats = window.TT_E2E.map.getSource("battle-map").serialize().data.features;
    return feats.filter((x) => x.properties.year <= window.TT_E2E.year).length;
  });
  assert.equal(count1700, WITH_PLACE.filter((e) => e.year <= 1700).length);
  assert.ok(count1700 < count1800.n, "1749 and 1795 events must be hidden in 1700");

  await page.evaluate(() => { location.hash = "#1800"; });
  await page.waitForTimeout(250);
});

test("clicking a battle point opens its event card and labels switch language", async () => {
  const ev1749 = WITH_PLACE.find((e) => e.year === 1749);
  assert.ok(ev1749, "1749 siege event exists");
  const pt = await page.evaluate((p) => {
    const m = window.TT_E2E.map;
    m.jumpTo({ center: [p.lng, p.lat], zoom: 16 });
    return new Promise((r) => m.once("idle", () => r(m.project([p.lng, p.lat]))));
  }, ev1749.place);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  await page.locator("#infoModal:not([hidden])").waitFor({ timeout: 10000 });
  const infoTxt = await page.locator("#infoModal").innerText();
  assert.ok(/Narikala|1749|Erekle|Abdul-Beg|628|1524/i.test(infoTxt), "info card shows battle/siege details: " + infoTxt.slice(0, 120));
  assert.ok((await page.locator("#imReport").count()) === 1, "report button present");

  await page.click("#btnMore");
  await page.selectOption("#lang", "ka");
  await page.waitForTimeout(250);
  const kaLabel = await page.evaluate(() => {
    const feats = window.TT_E2E.map.getSource("battle-map").serialize().data.features;
    return feats.find((x) => x.properties.year === 1749)?.properties.label || "";
  });
  assert.ok(kaLabel.includes("ნარიყალას ციხე"), "ka label updated: " + kaLabel);
});
