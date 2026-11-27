// Every card of the map and the window of a street / an event has a way to report a problem: the cards of religious buildings, science and culture and education had none.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

const read = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));
const REPORT = "Report a problem with this object";

async function card(c, box) {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
  await waitReady(page);
  if (box) await page.check(box);
  await page.waitForTimeout(800);
  const pt = await page.evaluate((c) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: 18 }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, c);
  const b = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(b.x + pt.x, b.y + pt.y);
  await page.locator(".maplibregl-popup .pop").waitFor({ timeout: 15000 });
  return page;
}

for (const [name, file, box, pick] of [
  ["religious building", "religious.json", null, (x) => Number.isFinite(x.from) && x.from <= 2000 && x.to === undefined],
  ["science and culture", "science.json", null, (x) => Number.isFinite(x.from) && x.from <= 2000],
  ["education", "education.json", "#showEdu", (x) => Number.isFinite(x.from) && x.from <= 2000],
]) {
  test(`the card of a ${name} has the report link and it opens the form with the object`, async () => {
    const c = read(file).find(pick);
    assert.ok(c);
    const page = await card(c, box);
    const links = page.locator(".maplibregl-popup .actions a.fb:not(#objShare)");                   // the report link; the icon of the link to the object is another thing
    assert.equal(await links.count(), 1, "only the report link: the card has no details window");
    assert.equal(await links.first().innerText(), REPORT);
    await links.first().click();
    await page.waitForFunction(() => !document.getElementById("fbModal").hidden, null, { timeout: 5000 });
    const ctx = await page.locator("#fbCtx").inputValue();
    assert.match(ctx, /object=.+ \(reg -, id (REL|SCI|EDU):/, ctx);
    await page.ctx.close();
  });
}

test("the window of a street has the button 'report a problem' beside 'Close' and it opens the form", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1960`);
  await waitReady(page);
  await page.click("#btnSearch"); await page.fill("#searchQ", "Kita Abashidze");
  await page.locator("#searchRes li").filter({ hasText: "🛣" }).first().click();
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  const btn = page.locator("#imReport");
  assert.equal(await btn.isVisible(), true);
  assert.equal(await btn.innerText(), REPORT);
  await btn.click();
  await page.waitForFunction(() => !document.getElementById("fbModal").hidden && document.getElementById("infoModal").hidden, null, { timeout: 5000 });
  assert.match(await page.locator("#fbCtx").inputValue(), /object=.*Abashidze.* \(reg -, id info\)/);
  await page.ctx.close();
});

test("the viewer of the views has the button 'report a problem' and it opens the form with the view", async () => {
  const views = read("views.json");
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1960`);
  await waitReady(page);
  await page.click("#btnViews");
  await page.check("#viewsAll");                                     // all the pictures, whatever the year
  await page.waitForFunction((n) => document.querySelectorAll("#vgrid button").length === n, views.length, { timeout: 15000 });
  await page.locator("#vgrid button").first().click();
  await page.waitForFunction(() => !document.getElementById("viewModal").hidden, null, { timeout: 5000 });
  assert.equal(await page.locator("#vmReport").innerText(), REPORT);
  await page.click("#vmReport");
  await page.waitForFunction(() => !document.getElementById("fbModal").hidden && document.getElementById("viewModal").hidden, null, { timeout: 5000 });
  assert.match(await page.locator("#fbCtx").inputValue(), /object=.+ \(reg -, id view:/);
  await page.ctx.close();
});

for (const [name, url] of [["entrances", "/entrances/"], ["run", "/run/"], ["museums", "/museums/"], ["mtskheta", "/mtskheta/"], ["lost", "/lost/"]]) {
  test(`the page /${name}/ has a link "Report a problem" that opens the form of the main page`, async () => {
    const page = await openPage(browser, `${server.url}${url}?e2e=1&nostats=1&lang=en`);
    const a = page.locator("#report");
    await a.waitFor({ timeout: 15000 });
    assert.equal(await a.innerText(), "Report a problem");
    assert.equal(await a.getAttribute("href"), "../?report=" + name + "&lang=en");
    await Promise.all([page.waitForURL((u) => !/\/(entrances|run|museums|mtskheta|lost)\//.test(u.pathname), { timeout: 15000 }), a.click()]);
    await page.waitForFunction(() => !document.getElementById("fbModal").hidden, null, { timeout: 15000 });
    assert.match(await page.locator("#fbCtx").inputValue(), new RegExp("object=page " + name));
    assert.ok(!/report=/.test(page.url()), "the parameter is removed from the address: " + page.url());
    await page.ctx.close();
  });
}
