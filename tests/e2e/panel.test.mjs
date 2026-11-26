// The panel of the filters, second pass: transport is a group (a master box and five boxes that really filter the lines by kind), the two controls of the photographs stand in a strip under the head
// and not in a block, the layer of places is with the streets, and on a phone a click of the visitor opens one block and closes the others (the tour, which opens blocks itself, does not).
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
});
test.after(async () => { await browser.close(); server.srv.close(); });

const open = async (width = 1280) => {
  const p = await openPage(browser, `${server.url}/?e2e=1&groups=1&base=off&nostats=1&lang=en#1990`, { width, height: width < 700 ? 800 : 800 });
  await waitReady(p);
  await p.waitForFunction(() => window.TT_E2E && window.TT_E2E.map.getLayer("tr-line"), null, { timeout: 30000 });
  if (await p.evaluate(() => document.getElementById("filters").hidden)) await p.click("#btnFilters");
  return p;
};

test("transport is a group: the master box and five boxes filter the lines by kind", async () => {
  page = await open();
  const ev = (f, a) => page.evaluate(f, a);
  const st = () => ev(() => { const g = document.querySelector(".gm[data-gm=tr]"), m = g.querySelector(".gmaster"); return { kids: [...g.querySelectorAll(".gmkids input")].map((c) => c.id + ":" + c.checked), master: m.checked, half: m.indeterminate, inHist: !!g.closest("details[data-sec=f-adv]") }; });
  const s0 = await st();
  assert.equal(s0.inHist, true, "the group is in the fine-tuning section");
  assert.deepEqual(s0.kids, ["showTrMetro:true", "showTrTram:true", "showTrRail:true", "showTrRoad:true", "showTrCable:true"]);
  assert.equal(s0.master, true);
  assert.equal(await ev(() => document.getElementById("showTransport")), null, "the old single box is gone");
  const flt = (id) => ev((i) => JSON.stringify(window.TT_E2E.map.getFilter(i)), id);
  const vis = (id) => ev((i) => window.TT_E2E.map.getLayoutProperty(i, "visibility"), id);
  assert.match(await flt("tr-line"), /"tram"/);
  await ev(() => { const c = document.getElementById("showTrTram"); c.checked = false; c.dispatchEvent(new Event("change", { bubbles: true })); });
  const f = await flt("tr-line");
  assert.ok(!f.includes('"tram"') && f.includes('"railway"') && f.includes('"metro_line"'), "the tram is out of the filter, the rest stays: " + f.slice(0, 200));
  assert.equal(await vis("tr-line"), "visible");
  assert.equal((await st()).half, true, "the master box is half-ticked");
  // the master box switches all the five off: no line is drawn; and on again
  await ev(() => { const m = document.querySelector(".gm[data-gm=tr] .gmaster"); m.checked = false; m.dispatchEvent(new Event("change", { bubbles: true })); });
  assert.equal(await vis("tr-line"), "none");
  assert.equal(await vis("tr-pt"), "none");
  await ev(() => { const m = document.querySelector(".gm[data-gm=tr] .gmaster"); m.checked = true; m.dispatchEvent(new Event("change", { bubbles: true })); });
  assert.equal(await vis("tr-line"), "visible");
  assert.match(await flt("tr-line"), /"tram"/);
  assert.deepEqual((await st()).kids.every((k) => k.endsWith("true")), true);
  await page.ctx.close();
});

test("the photograph controls are in #fquick inside fine-tuning, places legend is in f-layers", async () => {
  page = await open();
  const r = await page.evaluate(() => {
    const f = document.getElementById("filters"), q = document.getElementById("fquick");
    return {
      inAdv: !!q && !!q.closest("details[data-sec=f-adv]"),
      before: !!q && q.compareDocumentPosition(f.querySelector("details.fsec")) & Node.DOCUMENT_POSITION_FOLLOWING,
      kids: q ? [...q.querySelectorAll("[id]")].map((e) => e.id) : [],
      places: !!document.getElementById("showPlaces").closest("details[data-sec=f-adv]"),
      legend: !!document.getElementById("placesLegend").closest("details[data-sec=f-adv]"),
      shown: q ? getComputedStyle(q).display : null,
    };
  });
  assert.equal(r.inAdv, true, "the quick controls live inside fine-tuning");
  assert.ok(r.inAdv, "the quick controls live inside fine-tuning");
  assert.deepEqual(r.kids.sort(), ["btnNear", "noPhotoL", "rowNear", "rowNoPhoto", "showNoPhoto"].sort());
  assert.equal(r.places, true, "the places checkbox is in fine-tuning");
  assert.equal(r.legend, true, "and its legend stands under the unified city toggle");
  // a hidden row takes no room (the attribute is not beaten by display:flex of .row) and the strip is gone when both are hidden
  const g = await page.evaluate(() => {
    const q = document.getElementById("fquick"), a = document.getElementById("rowNear"), b = document.getElementById("rowNoPhoto"), was = [a.hidden, b.hidden];
    a.hidden = true; b.hidden = true;
    const both = [getComputedStyle(a).display, getComputedStyle(b).display, getComputedStyle(q).display, q.getBoundingClientRect().height];
    a.hidden = was[0]; b.hidden = was[1];
    return { both, undated: [...document.querySelectorAll(".sub2")].filter((e) => e.hidden).map((e) => getComputedStyle(e).display) };
  });
  assert.deepEqual(g.both.slice(0, 3), ["none", "none", "none"]);
  assert.equal(g.both[3], 0);
  assert.ok(g.undated.length >= 2 && g.undated.every((d) => d === "none"), "the hidden boxes 'without a year' take no room: " + g.undated);
  await page.ctx.close();
});

test("on a phone a click of the visitor opens one block and closes the others; opening by a script does not", async () => {
  page = await open(390);
  const secs = () => page.evaluate(() => Object.fromEntries([...document.querySelectorAll("#filters details.fsec")].map((d) => [d.dataset.sec, d.open])));
  const click = (s) => page.evaluate((s) => document.querySelector(`details[data-sec=${s}] > summary`).click(), s).then(() => page.waitForTimeout(80));
  assert.deepEqual(await secs(), { "f-base": true, "f-adv": false });
  await click("f-base");
  assert.deepEqual(await secs(), { "f-base": false, "f-adv": false });
  await click("f-adv");
  assert.deepEqual(await secs(), { "f-base": false, "f-adv": true });
  await click("f-adv");                                                   // closing the open one leaves none open
  assert.deepEqual(await secs(), { "f-base": false, "f-adv": false });
  // a script (the tour) opens a block: nothing else is closed
  await page.evaluate(() => { document.querySelector("details[data-sec=f-adv]").open = true; document.querySelector("details[data-sec=f-base]").open = true; });
  await page.waitForTimeout(150);
  assert.deepEqual(await secs(), { "f-base": true, "f-adv": true });
  // the counters stay in the titles of the closed blocks
  assert.match(await page.evaluate(() => document.querySelector("details[data-sec=f-adv] .cnt").textContent), /^\d+\/\d+$/);
  await page.ctx.close();
  // a wide screen keeps what it did: all the blocks may be open together
  page = await open(1280);
  await page.evaluate(() => document.querySelector("details[data-sec=f-adv] > summary").click());
  await page.waitForTimeout(80);
  assert.deepEqual(await secs(), { "f-base": true, "f-adv": true });
  await page.ctx.close();
});

test("the route of the run is not in the filters (it has its own page /run/)", async () => {
  page = await open();
  const r = await page.evaluate(() => ({ box: !!document.getElementById("showRun"), legend: !!document.getElementById("runLegend"), layers: window.TT_E2E.map.getStyle().layers.filter((l) => l.id.startsWith("run-")).length, src: !!window.TT_E2E.map.getSource("run") }));
  assert.deepEqual(r, { box: false, legend: false, layers: 0, src: false });
  assert.equal((await page.request.get(`${server.url}/run/`)).status(), 200, "the page of the run is still there");
  await page.ctx.close();
});
