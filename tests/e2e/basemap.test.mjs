// One basemap "the old map of the chosen year": the plan of the year, from 1953 to 2005 (no plan) the topographic map, a list "map source" for the experienced; one opacity slider; no separate
// "topographic map on top" box.
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&nostats=1&lang=en#1990`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const state = () => page.evaluate(() => {
  const m = window.TT_E2E.map;
  const plans = m.getStyle().layers.filter((l) => l.id.startsWith("plan-") && m.getLayoutProperty(l.id, "visibility") === "visible").map((l) => l.id);
  return { topo: !!m.getLayer("topo"), topoOpacity: m.getLayer("topo") ? m.getPaintProperty("topo", "raster-opacity") : null, plans, line: document.getElementById("planline").textContent, year: window.TT_E2E.year };
});
const setSel = (v) => page.locator("#topoSel").evaluate((e, v) => { e.value = v; e.dispatchEvent(new Event("input", { bubbles: true })); e.dispatchEvent(new Event("change", { bubbles: true })); }, v);   // the panel may be closed: no click
const setBox = (on) => page.locator("#showPlan").evaluate((e, on) => { e.checked = on; e.dispatchEvent(new Event("change", { bubbles: true })); }, on);
const setYear = async (y) => { await page.evaluate((y) => { location.hash = String(y); }, y); await page.waitForFunction((y) => window.TT_E2E.year === y && !document.body.classList.contains("stale"), y, { timeout: 10000 }); };

test("the controls: one checkbox, one slider, one list of sources; the old boxes are gone", async () => {
  for (const id of ["showTopo", "autoTopo", "topoOp"]) assert.equal(await page.locator("#" + id).count(), 0, id + " is gone");
  assert.equal(await page.locator("#showPlan").count(), 1);
  assert.equal(await page.locator("#op").count(), 1);
  const opts = await page.locator("#topoSel option").evaluateAll((o) => o.map((x) => x.value));
  assert.deepEqual(opts, ["auto", "plan", "t2", "t10", "t25", "t50", "t100"]);
  assert.equal(await page.locator("#topoSel").inputValue(), "auto");
  assert.match(await page.locator("#showPlan").evaluate((e) => e.closest("label").textContent), /Old map of the chosen year/);
});

test("by the year: the topographic map where the years of topographic maps are and there is no plan, the plan where there is one", async () => {
  await setYear(1990);
  let s = await state();
  assert.equal(s.topo, true, "1990: the topographic map");
  assert.deepEqual(s.plans, []);
  assert.match(s.line, /topographic map/i);
  await setYear(1887);
  s = await state();
  assert.equal(s.topo, false, "1887: no topographic map");
  assert.equal(s.plans.length, 1, "1887: one plan");
  assert.match(s.line, /1887/);
});

test("a chosen scale of the topographic map takes the place of the plan in every year; 'plan only' never shows it", async () => {
  await setYear(1887);
  await setSel("t10");
  await page.waitForTimeout(500);
  let s = await state();
  assert.equal(s.topo, true, "a scale is chosen: the map is shown in 1887");
  assert.deepEqual(s.plans, [], "the plan is hidden under it");
  assert.match(s.line, /1:10 000/);
  await setYear(1990);
  await setSel("plan");
  await page.waitForTimeout(500);
  s = await state();
  assert.equal(s.topo, false, "plan only: no topographic map in 1990");
  await setSel("auto");
  await page.waitForTimeout(500);
  assert.equal((await state()).topo, true, "automatic again: the map of 1990");
});

test("one slider sets the opacity of both, and the box switches the whole basemap", async () => {
  await setYear(1990);
  await page.locator("#op").evaluate((e) => { e.value = "40"; e.dispatchEvent(new Event("input", { bubbles: true })); });
  await page.waitForTimeout(300);
  assert.equal((await state()).topoOpacity, 0.4);
  await setBox(false);
  await page.waitForTimeout(500);
  const s = await state();
  assert.equal(s.topo, false, "the box is off: no old map at all");
  assert.equal(await page.locator("#topobox").evaluate((e) => e.hidden), true, "and the list of sources is hidden");
  await setBox(true);
});
