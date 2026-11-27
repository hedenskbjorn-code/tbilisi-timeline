// The panel "Filters and layers": four collapsible blocks (maps, boundaries, buildings and heritage, history and transport) with counters (the state is remembered, a phone opens one block), the modes "swipe" and
// "what was here" are buttons on the map, legends follow their layers (and are really hidden), the religious legend shows the denominations of the year,
// check boxes stand at the first line of a label, the register objects follow the layers (no list of the register), "Reset filters".
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, realErrors, DATA } from "./helpers.mjs";

let server, browser, page;
const URL_ = (extra = "", hash = "#1887") => `${server.url}/?e2e=1&base=off&nostats=1&lang=en${extra}${hash}`;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, URL_());
  await waitReady(page);
  if (await page.evaluate(() => document.getElementById("filters").hidden)) await page.click("#btnFilters");
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const ev = (fn, arg) => page.evaluate(fn, arg);
const hidden = (id) => ev((i) => document.getElementById(i).hidden, id);
const checked = (id) => ev((i) => document.getElementById(i).checked, id);
const shown = (id) => ev((i) => { const e = document.getElementById(i); return !!e && getComputedStyle(e).display !== "none" && e.offsetParent !== null; }, id);   // really on the screen, not only the attribute
const openAll = () => ev(() => document.querySelectorAll("#filters details.fsec").forEach((d) => { d.open = true; }));
const secs = () => ev(() => Object.fromEntries([...document.querySelectorAll("#filters details.fsec")].map((d) => [d.dataset.sec, d.open])));
const counter = (sid) => ev((s) => document.querySelector(`#filters details.fsec[data-sec="${s}"] .cnt`).textContent, sid);

test("two blocks: base map and more options; every block has a counter", async () => {
  assert.deepEqual(await secs(), { "f-base": true, "f-adv": true });
  for (const s of ["f-base", "f-adv"]) assert.match(await counter(s), /^\d+\/\d+$/, s);
  assert.equal(await ev(() => document.querySelector("#secCity > summary").textContent), "The city in this year", "the title of the left panel keeps its own key");
  await openAll();
});

test("a phone opens base map and keeps more options closed for visitors", async () => {
  const p2 = await openPage(browser, URL_("&groups=1"), { width: 390, height: 844 });
  await waitReady(p2);
  const st = await p2.evaluate(() => Object.fromEntries([...document.querySelectorAll("#filters details.fsec")].map((d) => [d.dataset.sec, d.open])));
  assert.deepEqual(st, { "f-base": true, "f-adv": false });
  const cnt = await p2.evaluate(() => [...document.querySelectorAll("#filters details.fsec .cnt")].map((c) => c.textContent));
  assert.equal(cnt.length, 2);
  for (const c of cnt) assert.match(c, /^[1-9]\d*\/\d+$/, "a counter of a closed panel: " + c);
  await p2.ctx.close();
});

test("the counter follows the check boxes, and lost preset hides districts/places", async () => {
  const [on0, all0] = (await counter("f-adv")).split("/").map(Number);
  await page.setChecked("#showBnd", false);
  assert.equal(await counter("f-adv"), `${on0 - 1}/${all0}`);
  await page.setChecked("#showBnd", true);
  assert.equal(await counter("f-adv"), `${on0}/${all0}`);
  const [e0] = (await counter("f-adv")).split("/").map(Number);
  await ev(() => { document.getElementById("showEdu").checked = true; document.getElementById("showEdu").dispatchEvent(new Event("change", { bubbles: true })); });
  assert.equal((await counter("f-adv")).split("/").map(Number)[0], e0 + 1);
  await page.click('#fpresets button[data-preset="arch"]');
  assert.equal(await checked("showResid"), true);
  await page.click('#fpresets button[data-preset="lost"]');
  assert.equal(await checked("showLost"), true);
  assert.equal(await checked("showGhost"), true);
  assert.equal(await checked("showDistricts"), false, "lost preset hides districts");
  assert.equal(await checked("showPlaces"), false, "lost preset hides places");
  assert.equal(await checked("showResid"), false);
  await page.click('#fpresets button[data-preset="hist"]');
  assert.equal(await checked("showResid"), false);
  assert.equal(await checked("showEdu"), false);

  // Regression: 0% opacity is restored on lost preset; active swipe is turned off when switching presets
  await ev(() => { const o = document.getElementById("op"); o.value = "0"; o.dispatchEvent(new Event("input", { bubbles: true })); });
  await page.click('#fpresets button[data-preset="lost"]');
  assert.ok(+(await ev(() => document.getElementById("op").value)) > 0, "lost preset restores non-zero plan opacity");
  await page.click("#thenBtn");
  assert.equal(await checked("showSwipe"), true);
  await page.click('#fpresets button[data-preset="trans"]');
  assert.equal(await checked("showSwipe"), false, "switching preset turns off active swipe");
  await page.click("#filtersReset");
});

test("the open state of a block is remembered after a reload; 'Reset filters' does not touch it", async () => {
  await page.click('#filters details.fsec[data-sec="f-base"] > summary');
  assert.equal((await secs())["f-base"], false, "was open, now closed");
  await page.reload();
  await waitReady(page);
  if (await ev(() => document.getElementById("filters").hidden)) await page.click("#btnFilters");
  assert.equal((await secs())["f-base"], false, "stays closed after the reload");
  await page.click('#filters details.fsec[data-sec="f-base"] > summary');
  await openAll();
  assert.equal(await ev(() => document.querySelector('#filters details.fsec[data-sec="f-base"]').open), true);
});

test("the modes are not in the panel: the boxes are hidden, the buttons are on the map", async () => {
  for (const id of ["showSwipe", "showHere"]) assert.equal(await shown(id), false, id + " is not on the screen");
  assert.equal(await shown("hereBtn"), true);
  assert.equal(await shown("thenBtn"), true);
  assert.equal(await ev(() => document.getElementById("hereBtn").getAttribute("aria-pressed")), "false");
  await page.click("#hereBtn");
  assert.equal(await checked("showHere"), true);
  assert.equal(await ev(() => document.getElementById("hereBtn").getAttribute("aria-pressed")), "true");
  assert.equal(await ev(() => document.getElementById("map").classList.contains("here")), true);
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), false, "a changed mode wakes the reset button");
  await page.click("#filtersReset");
  assert.equal(await checked("showHere"), false);
  assert.equal(await ev(() => document.getElementById("hereBtn").getAttribute("aria-pressed")), "false");
  assert.equal(await ev(() => document.getElementById("map").classList.contains("here")), false);
});

test("the legend of a layer stands in f-layers and is really hidden while the layer is off", async () => {
  for (const [chk, leg] of [["showRel", "relLegend"], ["showSci", "sciLegend"], ["showEdu", "eduLegend"]]) {
    await page.setChecked("#" + chk, true);
    assert.equal(await shown(leg), true, leg + " is on the screen with the layer on");
    await page.setChecked("#" + chk, false);
    assert.equal(await shown(leg), false, leg + " is off the screen with the layer off");
  }
  await page.setChecked("#showRel", true);
  await page.setChecked("#showSci", true);
});

test("the religious legend: a strip of dots with the denominations of the year, opens into the names", async () => {
  const ro = JSON.parse(fs.readFileSync(path.join(DATA, "religious_osm.json"), "utf8")).items;                                   // the buildings of OpenStreetMap join the layer after the first screen
  const rel = JSON.parse(fs.readFileSync(path.join(DATA, "religious.json"), "utf8")).concat(ro);
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("rel").serialize().data.features.length === n, rel.length, { timeout: 20000 });
  const expected = (y) => new Set(rel.filter((r) => (!r.undated || y >= 2026) && r.from <= y && (r.to === undefined || r.to > y)).map((r) => r.rel)).size;
  const dots = () => ev(() => document.querySelectorAll("#relLegend i.rdot").length);
  assert.equal(await dots(), expected(1887));
  assert.equal(await ev(() => document.querySelector("#relLegend details").open), false, "closed: one line instead of ten");
  assert.equal(await ev(() => !!document.querySelector("#relLegend summary").getAttribute("aria-label")), true, "the strip has a name for a screen reader");
  await page.click("#relLegend summary");
  assert.equal(await ev(() => document.querySelectorAll("#relLegend .rlist span").length), expected(1887), "the names are in the list");
  await ev(() => { location.hash = "#1000"; });
  await page.waitForFunction(() => window.TT_E2E.year === 1000);
  assert.equal(await dots(), expected(1000));
  assert.ok(expected(1000) < expected(2020), "an early year shows fewer denominations than today");
  await ev(() => { location.hash = "#1887"; });
  await page.waitForFunction(() => window.TT_E2E.year === 1887);
});

test("a check box stands at the first line of its label (within 1 px), also for labels of several lines", async () => {
  const bad = await ev(() => {
    const out = [];
    for (const lab of document.querySelectorAll("#filters label.row")) {
      const cb = lab.querySelector("input[type=checkbox]"), sp = lab.querySelector("span");
      if (!cb || !sp || !cb.offsetParent) continue;
      const r = document.createRange(); r.selectNodeContents(sp);
      const first = [...r.getClientRects()].find((x) => x.width > 0);
      if (!first) continue;
      const c = cb.getBoundingClientRect();
      const dy = (c.top + c.height / 2) - (first.top + first.height / 2);
      if (Math.abs(dy) > 1) out.push(cb.id + ":" + dy.toFixed(1));
    }
    return out;
  });
  assert.deepEqual(bad, []);
});

test("the legend box is collapsed by default", async () => {
  assert.equal(await ev(() => document.getElementById("legendbox").open), false);
});

test("the register objects follow the check boxes of the layers: no list of the register, the duplicates of the layers are not drawn", async () => {
  assert.equal(await ev(() => document.getElementById("typelist")), null, "the list of the types of the register is gone");
  const flt = () => ev(() => JSON.stringify(window.TT_E2E.map.getFilter("mon")));
  const f0 = await flt();
  assert.ok(f0.includes('"dup"'), "the objects that a layer already shows are left out");
  assert.ok(f0.includes("religious") && !f0.includes("residential") && !f0.includes("culture"), "register building types are off by default while religious is on");
  await page.setChecked("#showResid", true);
  assert.ok((await flt()).includes("residential"), "the residential layer turns on");
  await page.setChecked("#showResid", false);
  await page.setChecked("#showPublic", true);
  const fPub = await flt();
  assert.ok(fPub.includes("public") && fPub.includes("culture"), "the public layer brings public and culture register objects");
  await page.setChecked("#showPublic", false);
  await page.setChecked("#showDef", true);
  await page.setChecked("#showOtherB", true);
  assert.ok((await flt()).includes("memorial") && (await flt()).includes("defense"));
  await page.setChecked("#showOtherB", false);
  const f1 = await flt();
  assert.ok(!f1.includes("memorial") && !f1.includes("rural") && !f1.includes("transport") && f1.includes("defense"), "the group of the other structures is off, the defence stays");
  await page.setChecked("#showDef", false);
  assert.equal(await ev(() => document.getElementById("showNatOnly")), null, "no box for the national significance: the colour of the point shows it");
  await page.setChecked("#showRel", false);
  assert.ok(!(await flt()).includes("religious"), "the layer of religious buildings switches its register objects too");
  await page.setChecked("#showRel", true);
});

test("'Reset filters' is off at the start, turns on with any change and brings back the defaults", async () => {
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), true, "off while everything is as by default");
  await page.setChecked("#showBnd", false);                 // default on
  await page.setChecked("#showEdu", true);                  // default off
  await page.setChecked("#showRulers", true);               // default off on all widths
  await ev(() => { const o = document.getElementById("op"); o.value = 20; o.dispatchEvent(new Event("input", { bubbles: true })); });
  await page.setChecked("#showResid", true);                // register group on (default off)
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), false);
  await page.click("#filtersReset");
  assert.equal(await checked("showBnd"), true);
  assert.equal(await checked("showEdu"), false);
  assert.equal(await checked("showRulers"), false);
  assert.equal(await ev(() => document.getElementById("op").value), "65");
  assert.equal(await ev(() => document.getElementById("opv").textContent), "65%");
  assert.equal(await checked("showResid"), false);
  assert.equal(await ev(() => window.TT_E2E.map.getLayoutProperty("edu-pt", "visibility")), "none");
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), true, "off again");
});

test("a layer switched on by the code (a school found by the search) wakes the reset button", async () => {
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), true);
  await page.click("#btnSearch");
  await page.fill("#searchQ", "Cycling School");
  await page.waitForSelector("#searchRes li");
  await page.locator("#searchRes li", { hasText: "🏫" }).first().click();
  await page.locator(".maplibregl-popup .pop").waitFor({ timeout: 15000 });
  assert.equal(await checked("showEdu"), true);
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), false, "the layer was switched on by the code, the reset button must know");
  await page.click("#filtersReset");
  assert.equal(await checked("showEdu"), false);
});

test("no errors on the page after all this", () => {
  assert.deepEqual(realErrors(page), []);
});
