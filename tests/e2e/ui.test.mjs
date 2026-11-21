// Search, cards, windows, the list of sections, the version.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, realErrors, DATA } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

async function main(hash = "#1887", extra = "") {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en${extra}${hash}`);
  await waitReady(page);
  return page;
}
async function search(page, q) {
  await page.click("#btnSearch");
  await page.fill("#searchQ", q);
  await page.waitForSelector("#searchRes li");
}

test("search: a religious building opens its card with photographs and the layer is shown", async () => {
  const page = await main();
  await search(page, "Great Synagogue");
  await page.locator("#searchRes li", { hasText: "⛪" }).first().click();
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  assert.match(await pop.innerText(), /Great Synagogue/);
  assert.equal(await pop.locator(".photos img").count(), 2);
  assert.match(await pop.locator(".phcred").innerText(), /Commons/);
  assert.deepEqual(realErrors(page), []);
  await page.ctx.close();
});

test("search: a school opens its card and turns the layer Education on", async () => {
  const page = await main();
  await search(page, "Cycling School");
  await page.locator("#searchRes li", { hasText: "🏫" }).first().click();
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  assert.match(await pop.innerText(), /School or educational institution/);
  assert.equal(await page.isChecked("#showEdu"), true);
  await page.ctx.close();
});

test("search: a year goes to the year", async () => {
  const page = await main();
  await search(page, "1735");
  await page.locator("#searchRes li").first().click();
  await page.waitForFunction(() => window.TT_E2E.year === 1735);
  await page.ctx.close();
});

test("search: places and events are found", async () => {
  const page = await main();
  await search(page, "Krtsanisi");
  assert.ok((await page.locator("#searchRes li").count()) > 0);
  await page.ctx.close();
});

test("the address ?o=<id> opens the card of the object of the register", async () => {
  const page = await main("#1930", "&o=3049");
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 20000 });
  assert.match(await pop.innerText(), /Javakhishvili/);
  await page.ctx.close();
});

test("the list of sections leads to the other pages and keeps the language", async () => {
  const page = await main("#1887");
  await page.selectOption("#pagesSel", "entrances/");
  await page.waitForURL(/\/entrances\/\?lang=en/);
  assert.equal(await page.locator("#pagesSel").inputValue(), "../entrances/");
  await page.selectOption("#pagesSel", "../run/");
  await page.waitForURL(/\/run\/\?lang=en/);
  await page.selectOption("#pagesSel", "../");
  await page.waitForURL(/\/\?lang=en/);
  await page.ctx.close();
});

test("the window Views lists all the pictures and opens the viewer", async () => {
  const page = await main("#1905");
  const views = JSON.parse(fs.readFileSync(path.join(DATA, "views.json"), "utf8"));
  await page.click("#btnViews");
  await page.check("#viewsAll");
  await page.waitForFunction((n) => document.querySelectorAll("#vgrid button").length === n, views.length, { timeout: 15000 });
  assert.ok((await page.locator("#vgrid button", { hasText: /Fedoseev/ }).count()) >= 1);
  await page.locator("#vgrid button").first().click();
  await page.waitForFunction(() => { const m = document.getElementById("viewModal"); return m && !m.hidden; });
  await page.ctx.close();
});

test("the button of the version shows the current version of the changelog", async () => {
  const page = await main();
  const log = JSON.parse(fs.readFileSync(path.join(DATA, "changelog.json"), "utf8"));
  const want = "v" + log[0].version.replace(/\.0$/, "");
  assert.equal((await page.textContent("#btnVersion")).trim(), want);
  await page.ctx.close();
});

test("the map is not black: the canvas exists and has the size of the window", async () => {
  const page = await main();
  const box = await page.locator(".maplibregl-canvas").first().boundingBox();
  assert.ok(box.width > 600 && box.height > 400);
  await page.ctx.close();
});
