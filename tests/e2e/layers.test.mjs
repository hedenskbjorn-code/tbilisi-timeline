// Layers of the map: they exist, hold all the data, obey the check boxes and the year.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, realErrors } from "./helpers.mjs";
import { DATA } from "./helpers.mjs";

const count = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8")).length;
let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1887`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const ev = (fn, arg) => page.evaluate(fn, arg);

test("the layers of the map exist", async () => {
  const missing = await ev(() => ["rel-pt", "sci-pt", "edu-pt", "urban-fill", "urban-line-approx", "mon", "tr-line"].filter((i) => !window.TT_E2E.map.getLayer(i)));
  assert.deepEqual(missing, []);
});

test("the layers of religion, science and education hold all the objects of the data", async () => {
  const n = await ev(() => Object.fromEntries(["rel", "sci", "edu"].map((s) => [s, window.TT_E2E.map.getSource(s).serialize().data.features.length])));
  assert.deepEqual(n, { rel: count("religious.json"), sci: count("science.json"), edu: count("education.json") });
});

test("the check boxes: religion and science are on, education is off by default", async () => {
  const v = await ev(() => Object.fromEntries(["rel-pt", "sci-pt", "edu-pt"].map((i) => [i, window.TT_E2E.map.getLayoutProperty(i, "visibility")])));
  assert.deepEqual(v, { "rel-pt": "visible", "sci-pt": "visible", "edu-pt": "none" });
});

test("the check box Education turns the layer on and off", async () => {
  await page.check("#showEdu");
  assert.equal(await ev(() => window.TT_E2E.map.getLayoutProperty("edu-pt", "visibility")), "visible");
  await page.uncheck("#showEdu");
  assert.equal(await ev(() => window.TT_E2E.map.getLayoutProperty("edu-pt", "visibility")), "none");
});

test("the year changes the filters of the layers (religion 1000, outline of 1924 for 1930)", async () => {
  await ev(() => { location.hash = "#1000"; });
  await page.waitForFunction(() => window.TT_E2E.year === 1000);
  assert.match(await ev(() => JSON.stringify(window.TT_E2E.map.getFilter("rel-pt"))), /1000/);
  await ev(() => { location.hash = "#1930"; });
  await page.waitForFunction(() => window.TT_E2E.year === 1930);
  assert.match(await ev(() => JSON.stringify(window.TT_E2E.map.getFilter("urban-fill"))), /1924/);
});

test("the plan of the year is on the map (1887)", async () => {
  await ev(() => { location.hash = "#1887"; });
  await page.waitForFunction(() => window.TT_E2E.year === 1887);
  const plans = JSON.parse(fs.readFileSync(path.join(DATA, "plans.json"), "utf8"));
  const p = plans.find((x) => x.year === 1887);
  await page.waitForFunction((id) => window.TT_E2E.map.getLayer("plan-" + id), p.id, { timeout: 15000 });
  assert.equal(await ev((id) => window.TT_E2E.map.getLayoutProperty("plan-" + id, "visibility"), p.id), "visible");
});

test("no errors in the console after all of this", async () => {
  assert.deepEqual(realErrors(page), []);
});
