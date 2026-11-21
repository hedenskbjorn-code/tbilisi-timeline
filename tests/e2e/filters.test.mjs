// The panel "Filters and layers": four collapsible blocks with counters (the state is remembered, a phone opens one block), the modes "swipe" and
// "what was here" are buttons on the map, legends follow their layers (and are really hidden), the religious legend shows the denominations of the year,
// check boxes stand at the first line of a label, "All / Clear all" for the types, the hint for an empty choice, "Reset filters".
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
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const ev = (fn, arg) => page.evaluate(fn, arg);
const hidden = (id) => ev((i) => document.getElementById(i).hidden, id);
const checked = (id) => ev((i) => document.getElementById(i).checked, id);
const shown = (id) => ev((i) => { const e = document.getElementById(i); return !!e && getComputedStyle(e).display !== "none" && e.offsetParent !== null; }, id);   // really on the screen, not only the attribute
const openAll = () => ev(() => document.querySelectorAll("#filters details.fsec").forEach((d) => { d.open = true; }));
const secs = () => ev(() => Object.fromEntries([...document.querySelectorAll("#filters details.fsec")].map((d) => [d.dataset.sec, d.open])));
const counter = (sid) => ev((s) => document.querySelector(`#filters details.fsec[data-sec="${s}"] .cnt`).textContent, sid);

test("four blocks: only the layers by year are open (a wide screen and a phone alike), the rest closed; every block has a counter", async () => {
  assert.deepEqual(await secs(), { "f-base": false, "f-city": false, "f-layers": true, "f-reg": false });
  for (const s of ["f-base", "f-city", "f-layers", "f-reg"]) assert.match(await counter(s), /^\d+\/\d+$/, s);
  assert.equal(await ev(() => document.querySelector("#secCity > summary").textContent), "The city in this year", "the title of the left panel keeps its own key");
  await openAll();
});

test("a phone opens one block (layers by year)", async () => {
  const p2 = await openPage(browser, URL_(), { width: 390, height: 844 });
  await waitReady(p2);
  const st = await p2.evaluate(() => Object.fromEntries([...document.querySelectorAll("#filters details.fsec")].map((d) => [d.dataset.sec, d.open])));
  assert.deepEqual(st, { "f-base": false, "f-city": false, "f-layers": true, "f-reg": false });
  const cnt = await p2.evaluate(() => [...document.querySelectorAll("#filters details.fsec .cnt")].map((c) => c.textContent));   // the panel itself is closed on a phone, the counters still count
  assert.equal(cnt.length, 4);
  for (const c of cnt) assert.match(c, /^[1-9]\d*\/\d+$/, "a counter of a closed panel: " + c);
  await p2.ctx.close();
});

test("the counter follows the check boxes, also when a layer is switched on by itself", async () => {
  const [on0, all0] = (await counter("f-city")).split("/").map(Number);
  await page.setChecked("#showBnd", false);
  assert.equal(await counter("f-city"), `${on0 - 1}/${all0}`);
  await page.setChecked("#showBnd", true);
  assert.equal(await counter("f-city"), `${on0}/${all0}`);
  const [e0] = (await counter("f-layers")).split("/").map(Number);
  await ev(() => { document.getElementById("showEdu").checked = true; document.getElementById("showEdu").dispatchEvent(new Event("change", { bubbles: true })); });
  assert.equal((await counter("f-layers")).split("/").map(Number)[0], e0 + 1);
  await page.setChecked("#showEdu", false);
});

test("the open state of a block is remembered after a reload; 'Reset filters' does not touch it", async () => {
  await page.click('#filters details.fsec[data-sec="f-city"] > summary');
  assert.equal((await secs())["f-city"], false, "was open, now closed");
  await page.reload();
  await waitReady(page);
  assert.equal((await secs())["f-city"], false, "stays closed after the reload");
  assert.equal((await secs())["f-layers"], true);
  await page.click('#filters details.fsec[data-sec="f-city"] > summary');
  await openAll();
  assert.equal(await ev(() => document.querySelector('#filters details.fsec[data-sec="f-city"]').open), true);
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

test("the legend of a layer stands under its check box and is really hidden while the layer is off", async () => {
  for (const [chk, leg] of [["showRel", "relLegend"], ["showSci", "sciLegend"], ["showEdu", "eduLegend"], ["showRun", "runLegend"]]) {
    assert.equal(await ev(([c, l]) => document.getElementById(c).closest("label").nextElementSibling.id === l, [chk, leg]), true, leg + " follows " + chk);
    await page.setChecked("#" + chk, true);
    if (leg !== "runLegend") assert.equal(await shown(leg), true, leg + " is on the screen with the layer on");      // the route legend is empty until its data come
    await page.setChecked("#" + chk, false);
    assert.equal(await shown(leg), false, leg + " is off the screen with the layer off");
  }
  await page.setChecked("#showRel", true);
  await page.setChecked("#showSci", true);
});

test("the religious legend: a strip of dots with the denominations of the year, opens into the names", async () => {
  const rel = JSON.parse(fs.readFileSync(path.join(DATA, "religious.json"), "utf8"));
  const expected = (y) => new Set(rel.filter((r) => r.from <= y && (r.to === undefined || r.to > y)).map((r) => r.rel)).size;
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

test("'Clear all' unchecks the nine types, shows the hint, 'All' brings them back", async () => {
  const types = () => ev(() => [...document.querySelectorAll("#typelist input[type=checkbox]")].map((c) => c.checked));
  assert.equal((await types()).length, 9);
  assert.equal(await hidden("emptyObjects"), true);
  await page.click("#typesNone");
  assert.deepEqual((await types()).filter(Boolean), []);
  assert.equal(await hidden("emptyObjects"), false);
  assert.equal(await shown("emptyObjects"), true);
  assert.equal(await ev(() => JSON.stringify(window.TT_E2E.map.getFilter("mon")).includes('"literal",[]')), true, "the map filter holds an empty set of types");
  await page.click("#typesAll");
  assert.equal((await types()).every(Boolean), true);
  assert.equal(await hidden("emptyObjects"), true);
});

test("the hint also shows when all three statuses are unchecked, and it is seen with the block closed", async () => {
  for (const id of ["showNat", "showMon", "showObj"]) await page.setChecked("#" + id, false);
  assert.equal(await hidden("emptyObjects"), false);
  await ev(() => { document.querySelector('#filters details.fsec[data-sec="f-reg"]').open = false; });
  assert.equal(await shown("emptyObjects"), true, "the hint is outside the blocks");
  await openAll();
  await page.setChecked("#showMon", true);
  assert.equal(await hidden("emptyObjects"), true);
  await page.setChecked("#showNat", true);
  await page.setChecked("#showObj", true);
});

test("'Reset filters' is off at the start, turns on with any change and brings back the defaults", async () => {
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), true, "off while everything is as by default");
  const wide = await ev(() => window.innerWidth > 900);
  await page.setChecked("#showBnd", false);                 // default on
  await page.setChecked("#showEdu", true);                  // default off
  await page.setChecked("#showRulers", !wide);              // the default depends on the width
  await ev(() => { const o = document.getElementById("op"); o.value = 20; o.dispatchEvent(new Event("input", { bubbles: true })); });
  await page.click("#typelist label:first-child input");    // one type off
  assert.equal(await ev(() => document.getElementById("filtersReset").disabled), false);
  await page.click("#filtersReset");
  assert.equal(await checked("showBnd"), true);
  assert.equal(await checked("showEdu"), false);
  assert.equal(await checked("showRulers"), wide);
  assert.equal(await ev(() => document.getElementById("op").value), "65");
  assert.equal(await ev(() => document.getElementById("opv").textContent), "65%");
  assert.equal(await ev(() => [...document.querySelectorAll("#typelist input")].every((c) => c.checked)), true);
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
