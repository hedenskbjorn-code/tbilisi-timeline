// The lazy layers are loaded quietly when the browser is idle after the first screen (?idleload=1 switches it on in a test), so that the search finds their objects with no box ticked;
// without it (?e2e alone) the files stay lazy.
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

test("the search finds a park and a building of modernism with no layer switched on", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&idleload=1&base=off&nostats=1&lang=en#1990`);
  const reqs = [];
  page.on("request", (r) => reqs.push(r.url()));
  await waitReady(page);
  await page.waitForFunction(() => window.TT_E2E.map.getSource("places") && window.TT_E2E.map.getSource("mods") && window.TT_E2E.map.getSource("mons"), null, { timeout: 30000, polling: 500 });
  for (const f of ["places", "modernism", "sculptures", "plaques", "mtskheta_tour"]) assert.ok(reqs.some((u) => u.includes(f + ".json")), f + ".json was loaded");
  for (const id of ["#showPlaces", "#showMod", "#showMon", "#showPlq"]) assert.equal(await page.isChecked(id), false, id + " stays off");
  await page.click("#btnSearch");
  await page.fill("#searchQ", "Vaso Godziashvili");
  await page.waitForSelector("#searchRes li");
  assert.ok((await page.locator("#searchRes").innerText()).includes("Vaso Godziashvili Garden"));
  await page.fill("#searchQ", "Armaziskhevi");
  await page.waitForTimeout(400);
  assert.ok((await page.locator("#searchRes").innerText()).includes("Armaziskhevi"));
  await page.fill("#searchQ", "Palace of Rituals");
  await page.waitForTimeout(400);
  assert.ok((await page.locator("#searchRes").innerText()).includes("Palace of Rituals"));
  await page.ctx.close();
});

test("without idleload the files stay lazy", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1990`);
  const reqs = [];
  page.on("request", (r) => reqs.push(r.url()));
  await waitReady(page);
  await page.waitForTimeout(3000);
  assert.ok(!reqs.some((u) => /\/(places|modernism|sculptures|plaques|mtskheta_tour)\.json/.test(u)));
  await page.ctx.close();
});
