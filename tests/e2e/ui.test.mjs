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

async function openSioni(w, h) {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1887`, { width: w, height: h });
  await waitReady(page);
  if (w < 1100) await page.click("#btnSearch");
  else await page.click("#btnSearch");
  await page.fill("#searchQ", "Sioni");
  await page.waitForSelector("#searchRes li");
  await page.locator("#searchRes li", { hasText: "\u26EA" }).first().click();
  await page.locator(".maplibregl-popup .pop").waitFor({ timeout: 15000 });
  await page.waitForTimeout(1800);                                   // the camera flies to the object and the card is fitted when it stops
  return page;
}

for (const [w, h] of [[1280, 800], [1024, 768], [390, 844]]) {
  test(`a card opened from the search is below the time bar and its close button can be clicked, ${w}x${h}`, async () => {
    const page = await openSioni(w, h);
    const m = await page.evaluate(() => {
      const b = document.querySelector(".maplibregl-popup-close-button");
      const r = b.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return { covered: !(hit === b || b.contains(hit)), top: document.querySelector(".maplibregl-popup").getBoundingClientRect().top, bar: document.getElementById("timebar").getBoundingClientRect().bottom };
    });
    assert.equal(m.covered, false, "the close button is covered by another element");
    assert.ok(m.top >= m.bar - 1, `the card (top ${m.top}) is under the time bar (bottom ${m.bar})`);
    await page.locator(".maplibregl-popup-close-button").click();
    assert.equal(await page.locator(".maplibregl-popup").count(), 0);
    await page.ctx.close();
  });
}

test("Esc closes the open card of the map", async () => {
  const page = await openSioni(1280, 800);
  await page.keyboard.press("Escape");
  assert.equal(await page.locator(".maplibregl-popup").count(), 0);
  await page.ctx.close();
});

test("Esc closes an open window first and the card stays; the second Esc closes the card", async () => {
  const page = await openSioni(1280, 800);
  await page.click("#btnVersion");
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden);
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => document.getElementById("infoModal").hidden);
  assert.equal(await page.locator(".maplibregl-popup").count(), 1, "the card was closed together with the window");
  await page.keyboard.press("Escape");
  assert.equal(await page.locator(".maplibregl-popup").count(), 0);
  await page.ctx.close();
});

test("events of the Isani palace (1184, 1210) have a pin at Metekhi with the place named as approximate", async () => {
  for (const [q, year] of [["Isani", 1210], ["Isani", 1184]]) {
    const page = await main();
    await search(page, q);
    const row = page.locator("#searchRes li").filter({ hasText: new RegExp(String(year)) }).first();
    assert.ok((await row.count()) > 0, `no search row for ${year}`);
    await row.click();
    const pin = page.locator(".evpinwrap");
    await pin.waitFor({ timeout: 15000 });
    assert.match(await pin.getAttribute("aria-label"), /Metekhi \(the Isani palace; the place is approximate\)/);
    await page.ctx.close();
  }
});

test("the address ?o=<id> opens the card of the object of the register", async () => {
  const page = await main("#1930", "&o=3049");
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 20000 });
  assert.match(await pop.innerText(), /Javakhishvili/);
  await page.ctx.close();
});

test("search finds a street by a former name and opens its card; a street without a line on the map has the card too", async () => {
  const page = await main("#1960");
  await search(page, "Kronshtadtskaya");
  const row = page.locator("#searchRes li").filter({ hasText: "Tsagareli" }).first();
  assert.ok((await row.count()) > 0, "the street is found by the former name");
  await row.click();
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  let body = await page.locator("#imBody").innerText();
  assert.match(body, /Archil Tsagareli Street/);
  assert.match(body, /1941–1991 · Kronshtadtskaya Street/, "the former name with the years");
  assert.match(body, /PDF p\. 194/, "the book with the page");
  await page.keyboard.press("Escape");
  await search(page, "Cholokashvili Avenue");               // the avenue has no line in OSM under this name: nogeom
  const row2 = page.locator("#searchRes li").filter({ hasText: /Ilia Chavchavadze|Chavchavadze/ }).first();
  assert.ok((await row2.count()) > 0, "the street without a line is found by a former name too");
  await row2.click();
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  body = await page.locator("#imBody").innerText();
  assert.match(body, /Earlier called \(the year is not named\)/, "the names without a year are in the card");
  await page.ctx.close();
});

test("the list of the old street names shows the encyclopedia as text with the page where the street has no link", async () => {
  const page = await main("#1960");
  const txt = await page.locator("#stnames").textContent();
  assert.match(txt, /Kutuzov/, "the Kutuzov Street of 1960 is in the list");
  assert.match(txt, /\[Tbilisi\. Streets, avenues, squares[^\]]*PDF p\. 40\]/, "the book reference with the page stands as text");
  const hrefs = await page.locator("#stnames a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  assert.ok(hrefs.length > 0 && hrefs.every((h) => /^https?:/.test(h)), "the streets with a source have a real link");
  await page.ctx.close();
});

test("the card of an event from a textbook shows the book with the page as text, a Wikipedia source stays a link", async () => {
  for (const [q, year, bookOnly] of [["Primakov", 1997, true], ["Erivan Square", 1907, false]]) {
    const page = await main(`#${year}`);
    await search(page, q);
    const row = page.locator("#searchRes li").filter({ hasText: new RegExp(String(year)) }).first();
    assert.ok((await row.count()) > 0, `no search row for ${q}`);
    await row.click();
    await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
    const body = page.locator("#imBody");
    assert.match(await body.innerText(), /Muskhelishvili[^\n]*PDF p\. \d+/, "the book reference with the page is in the card");
    const links = await body.locator("a").evaluateAll((as) => as.map((a) => a.textContent));
    assert.ok(!links.some((t) => /Muskhelishvili/.test(t)), "the book is not a link");
    if (bookOnly) assert.equal(links.length, 0, "an event with a book source only has no link");
    else assert.ok(links.some((t) => /wikipedia/i.test(t)), "the Wikipedia source is still a link");
    await page.ctx.close();
  }
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
