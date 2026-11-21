// The panel "Filters and layers": legends follow their check boxes, check boxes stand at the first line of a label, "All / Clear all" for the types,
// a hint for an empty choice, the button "Reset filters" (active only when something differs from the defaults), the legend is collapsed.
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady, realErrors } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1887`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const ev = (fn, arg) => page.evaluate(fn, arg);
const hidden = (id) => ev((i) => document.getElementById(i).hidden, id);
const checked = (id) => ev((i) => document.getElementById(i).checked, id);

test("the legend of a layer stands under its check box and is hidden while the layer is off", async () => {
  for (const [chk, leg] of [["showRel", "relLegend"], ["showSci", "sciLegend"], ["showEdu", "eduLegend"], ["showRun", "runLegend"]]) {
    assert.equal(await ev(([c, l]) => document.getElementById(c).closest("label").nextElementSibling.id === l, [chk, leg]), true, leg + " follows " + chk);
    await page.setChecked("#" + chk, true);
    assert.equal(await hidden(leg), false, leg + " is shown with the layer on");
    await page.setChecked("#" + chk, false);
    assert.equal(await hidden(leg), true, leg + " is hidden with the layer off");
  }
  await page.setChecked("#showRel", true);
  await page.setChecked("#showSci", true);
  await page.setChecked("#showEdu", false);
  await page.setChecked("#showRun", false);
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
  assert.equal(await ev(() => JSON.stringify(window.TT_E2E.map.getFilter("mon")).includes('"literal",[]')), true, "the map filter holds an empty set of types");
  await page.click("#typesAll");
  assert.equal((await types()).every(Boolean), true);
  assert.equal(await hidden("emptyObjects"), true);
});

test("the hint also shows when all three statuses are unchecked", async () => {
  for (const id of ["showNat", "showMon", "showObj"]) await page.setChecked("#" + id, false);
  assert.equal(await hidden("emptyObjects"), false);
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

test("no errors on the page after all this", () => {
  assert.deepEqual(realErrors(page), []);
});
