// The guided tour after the welcome window: six concise steps (step 3 opens the layers panel and restores it), welcome quick-start scenarios, modal focus trap, Esc/Back.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA, tick } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

const url = (extra = "") => `${server.url}/?e2e=1&base=off&nostats=1&lang=en${extra}#1887`;
const hole = async (page) => { await page.waitForTimeout(450); return page.evaluate(() => { const r = document.getElementById("tourHole").getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; }); };
const card = async (page) => { await page.waitForTimeout(300); return page.evaluate(() => { const r = document.getElementById("tourCard").getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: innerWidth, h: innerHeight, txt: document.getElementById("tourCard").innerText }; }); };
const center = (page, id) => page.evaluate((i) => { const r = document.getElementById(i).getBoundingClientRect(); return { x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 }; }, id);
const inside = (h, p) => p.x >= h.l && p.x <= h.r && p.y >= h.t && p.y <= h.b;

test("the welcome window offers 4 scenarios and the 6-step tour; modal keeps focus inside", async () => {
  const page = await openPage(browser, url("&welcome=1"));
  await waitReady(page);
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  assert.equal(await page.locator("#imBody .wel-sc button").count(), 4, "4 starter scenarios");
  assert.equal(await page.evaluate(() => !!document.activeElement.closest("#infoModal")), true, "focus moved into infoModal");
  await page.locator("#imBody button", { hasText: "Quick tour" }).click();
  await page.waitForSelector("#tourHole", { timeout: 10000 });
  assert.equal(await page.evaluate(() => document.getElementById("infoModal").hidden), true, "the welcome window is closed");

  let c = await card(page);
  assert.match(c.txt, /1 of 6/);
  assert.ok(inside(await hole(page), await center(page, "timebar")), "step 1 lights the time scale");

  await page.click("#tourCard button.chip.primary");
  c = await card(page);
  assert.match(c.txt, /2 of 6/);
  assert.ok(inside(await hole(page), await center(page, "btnSearch")), "step 2 lights Search");

  await page.click("#tourCard button.chip.primary");
  c = await card(page);
  assert.match(c.txt, /3 of 6/);
  assert.match(c.txt, /Map modes/);
  await page.waitForTimeout(500);
  const ok3 = await page.evaluate(() => {
    const h = document.getElementById("tourHole").getBoundingClientRect(), el = document.querySelector("#fpresets"), r = el && el.getBoundingClientRect(), f = document.getElementById("filters");
    return { open: !f.hidden && f.getBoundingClientRect().height > 20, lit: !!r && r.width > 0 && (r.left + r.right) / 2 >= h.left && (r.left + r.right) / 2 <= h.right && (r.top + r.bottom) / 2 >= h.top && (r.top + r.bottom) / 2 <= h.bottom };
  });
  assert.equal(ok3.open, true, "step 3 opens filters panel");
  assert.equal(ok3.lit, true, "step 3 lights presets");

  await page.click("#tourCard button.chip.primary");
  c = await card(page);
  assert.match(c.txt, /4 of 6/);
  const h4 = await hole(page);
  for (const id of ["thenBtn", "hereBtn", "linkBtn"]) assert.ok(inside(h4, await center(page, id)), "step 4 lights " + id);

  await page.click("#tourCard button.chip.primary");
  c = await card(page);
  assert.match(c.txt, /5 of 6/);
  assert.match(c.txt, /Rulers and biography/);
  assert.ok(inside(await hole(page), await center(page, "rbShow")), "step 5 lights Rulers button");

  await page.click("#tourCard button.chip.primary");
  c = await card(page);
  assert.match(c.txt, /6 of 6/);
  assert.match(c.txt, /Other site pages/);
  assert.ok(inside(await hole(page), await center(page, "pagesSel")), "step 6 lights pages selector");
  assert.match(await page.locator("#tourCard button.chip.primary").innerText(), /Done/);

  await page.click("#tourCard button.chip.primary");
  assert.equal(await page.locator("#tour").count(), 0, "the tour is gone");
  await page.ctx.close();
});

test("welcome quick-start scenario opens multi-phase Ateshgah card in 1 click", async () => {
  const page = await openPage(browser, url("&welcome=1"));
  await waitReady(page);
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  await page.locator("#imBody .wel-sc button").nth(2).click();
  await page.locator(".maplibregl-popup .pop .catphases").waitFor({ timeout: 15000 });
  assert.match(await page.locator(".maplibregl-popup .pop").innerText(), /Atashgah|Ateshgah/i);
  await page.ctx.close();
});

test("Esc closes the tour; the button starts it again; Back goes one step back", async () => {
  const page = await openPage(browser, url());
  await waitReady(page);
  await page.evaluate(() => document.getElementById("btnTour").click());
  await page.waitForSelector("#tourHole", { timeout: 10000 });
  await page.click("#tourCard button.chip.primary");
  await page.click("#tourCard button.chip:not(.primary)");
  assert.match((await card(page)).txt, /1 of 6/, "Back");
  await page.keyboard.press("Escape");
  assert.equal(await page.locator("#tour").count(), 0, "Esc");
  await page.ctx.close();
});

test("on a phone the card stays inside the screen at every step and the panel of the filters is put back as it was", async () => {
  const page = await openPage(browser, url("&welcome=1"), { width: 390, height: 844 });
  await waitReady(page);
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  const filtersOpen = () => page.evaluate(() => document.body.classList.contains("filters-open") || getComputedStyle(document.getElementById("filters")).display !== "none" && document.getElementById("filters").getBoundingClientRect().right <= innerWidth && document.getElementById("filters").getBoundingClientRect().width > 0 && document.getElementById("filters").getBoundingClientRect().left >= 0);
  const f0 = await filtersOpen();
  await page.locator("#imBody button", { hasText: "Quick tour" }).click();
  await page.waitForSelector("#tourHole", { timeout: 10000 });
  let n = 0;
  for (;;) {
    const c = await card(page);
    n++;
    assert.ok(c.l >= 0 && c.t >= 0 && c.r <= c.w && c.b <= c.h, `step ${n}: the card is inside the screen ${JSON.stringify([c.l, c.t, c.r, c.b, c.w, c.h])}`);
    const done = /Done/.test(await page.locator("#tourCard button.chip.primary").innerText());
    await page.click("#tourCard button.chip.primary");
    if (done) break;
    assert.ok(n < 8, "no endless loop");
  }
  assert.equal(n, 6, "all 6 steps shown on phone");
  assert.equal(await filtersOpen(), f0, "the panel of the filters is as it was before the tour");
  await page.ctx.close();
});

test("the button of the tour is the first control of the panel City; the button of the version is in the panel", async () => {
  const page = await openPage(browser, url());
  await waitReady(page);
  const o = await page.evaluate(() => {
    const side = document.getElementById("side"), first = [...side.querySelectorAll("button:not(.pclose)")][0];
    const tb = document.getElementById("btnTour").getBoundingClientRect(), sb = side.getBoundingClientRect();
    return { first: first && first.id, tourTop: tb.top - sb.top, inTop: !!document.querySelector("#top #btnVersion"), inSide: !!document.querySelector("#side #btnVersion") };
  });
  assert.equal(o.first, "btnTour", "the first button of the panel");
  assert.ok(o.tourTop < 160, "it is seen without scrolling: " + o.tourTop);
  assert.equal(o.inTop, false, "no version button in the top bar");
  assert.equal(o.inSide, true);
  await page.ctx.close();
});

test("on a phone the tour started from the panel City closes the panel", async () => {
  const page = await openPage(browser, url(), { width: 390, height: 844 });
  await waitReady(page);
  const side = () => page.evaluate(() => { const s = document.getElementById("side"); return !s.hidden && s.getBoundingClientRect().height > 20; });
  if (!(await side())) await page.click("#btnInfo");
  assert.equal(await side(), true, "the panel City is open before the tour");
  await page.click("#btnTour");
  await page.waitForSelector("#tourHole", { timeout: 10000 });
  assert.equal(await side(), false, "the panel City is closed when the tour starts");
  await page.keyboard.press("Escape");
  await page.ctx.close();
});

test("clicking the ruler photo in #rulerCard opens the biography modal", async () => {
  const page = await openPage(browser, url());
  await waitReady(page);
  await page.click("#rbShow");
  await page.waitForSelector("#rulerCard .rc-media.clickable", { timeout: 15000 });
  await page.click("#rulerCard .rc-media.clickable");
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 10000 });
  const bodyTxt = await page.locator("#imBody").innerText();
  assert.ok(bodyTxt.length > 20, "ruler biography modal opened");
  await page.ctx.close();
});

test("clicking the second ruler portrait (viceroy) opens the viceroy card, not the emperor", async () => {
  const page = await openPage(browser, url());
  await waitReady(page);
  await page.click("#rbShow");
  await page.waitForFunction(() => document.querySelectorAll("#rulerCard .rc-port.clickable").length >= 2, null, { timeout: 15000 });
  await page.locator("#rulerCard .rc-port.clickable").nth(1).click();
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 10000 });
  const bodyTxt = await page.locator("#imBody").innerText();
  assert.ok(/Viceroy|Наместник|Дондуков|Dondukov|დონდუკოვ/i.test(bodyTxt), "expected viceroy card, got: " + bodyTxt.slice(0, 120));
  await page.ctx.close();
});

test("USSR dual-tier (#1950): #rulerCard shows 2 portraits and each opens its card with bio and Wikipedia link", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1950`);
  await waitReady(page);
  await page.click("#rbShow");
  await page.waitForFunction(() => document.querySelectorAll("#rulerCard .rc-port.clickable").length === 2, null, { timeout: 15000 });

  for (const [idx, nameRe, bioRe, wikiRe] of [
    [0, /Joseph Stalin/i, /General Secretary of the Communist Party/i, /en\.wikipedia\.org\/wiki\/Joseph_Stalin/],
    [1, /Charkviani/i, /First Secretary of the Communist Party of Georgia/i, /en\.wikipedia\.org\/wiki\/Kandid_Charkviani/],
  ]) {
    await page.locator("#rulerCard .rc-port.clickable").nth(idx).click();
    await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 10000 });
    const bodyTxt = await page.locator("#imBody").innerText();
    const wikiHrefs = await page.locator('#imBody a[href*="wikipedia.org"]').evaluateAll((els) => els.map((e) => e.getAttribute("href")));
    assert.match(bodyTxt, nameRe, `portrait ${idx} opened expected ruler`);
    assert.match(bodyTxt, bioRe, `portrait ${idx} shows bio`);
    assert.ok(wikiHrefs.some((h) => wikiRe.test(h || "")), `portrait ${idx} shows Wikipedia bio_src link: ${wikiHrefs.join(", ")}`);
    await page.click("#imClose");
    await page.waitForFunction(() => document.getElementById("infoModal").hidden, null, { timeout: 5000 });
  }
  await page.ctx.close();
});

test("#yearchip is visible below #timebar when #side is hidden", async () => {
  const page = await openPage(browser, url());
  await waitReady(page);
  await page.click("#side .pclose");
  await page.waitForFunction(() => document.getElementById("side").hidden, null, { timeout: 5000 });
  const m = await page.evaluate(() => {
    const yc = document.getElementById("yearchip"), tb = document.getElementById("timebar");
    const cs = getComputedStyle(yc), yr = yc.getBoundingClientRect(), tr = tb.getBoundingClientRect();
    return { display: cs.display, text: yc.textContent.trim(), w: yr.width, h: yr.height, top: yr.top, tbBottom: tr.bottom };
  });
  assert.notEqual(m.display, "none", "#yearchip is displayed when #side is hidden");
  assert.ok(m.w > 0 && m.h > 0, "#yearchip has non-zero size");
  assert.equal(m.text, "1887", "#yearchip shows active year");
  assert.ok(m.top >= m.tbBottom - 1, `#yearchip (${m.top}) sits below #timebar (${m.tbBottom})`);
  await page.ctx.close();
});

test("clicking a museum marker (showMus) opens a popup with #objShare link", async () => {
  const museums = JSON.parse(fs.readFileSync(path.join(DATA, "museums.json"), "utf8"));
  const science = JSON.parse(fs.readFileSync(path.join(DATA, "science.json"), "utf8"));
  const sciIds = new Set(science.map((s) => s.id));
  const mus = museums.find((m) => !sciIds.has(m.id) && m.from <= 2026) || museums[0];
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`);
  await waitReady(page);
  await tick(page, "#showMus", true);
  await tick(page, "#showSci", false);
  await tick(page, "#showRel", false);
  await page.waitForFunction(() => {
    const m = window.TT_E2E.map;
    return m.getLayer("mus-pt") && m.getLayoutProperty("mus-pt", "visibility") === "visible";
  }, null, { timeout: 15000 });
  const pt = await page.evaluate((c) => {
    const m = window.TT_E2E.map;
    m.jumpTo({ center: [c.lon, c.lat], zoom: 17 });
    return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat]))));
  }, mus);
  const box = await page.locator("#map").boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  assert.match(await pop.innerText(), new RegExp(mus.name.en.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").slice(0, 20)));
  assert.equal(await pop.locator("#objShare").count(), 1, "museum popup has #objShare");
  assert.equal(await page.evaluate(() => new URL(location.href).searchParams.get("o")), "mu:" + mus.id, "URL parameter ?o=mu:<id> is set");
  await page.ctx.close();
});
