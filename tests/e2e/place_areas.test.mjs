// The outlines of quarters and squares of the layer "Local names" have a box of their own (off by default, shown only while the layer is on); every outline has its own colour of a palette so that
// neighbouring districts are told apart; the outline of the former hippodrome goes with the layer; the note about the hippodrome stands on its card only.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady, DATA, tick } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1990`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const PL = JSON.parse(fs.readFileSync(path.join(DATA, "places.json"), "utf8"));
const ev = (f, a) => page.evaluate(f, a);

async function openCard(c, zoom = 18) {
  await ev(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await ev(([c, z]) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: z }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, [c, zoom]);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  return pop;
}

test("the box of the outlines: off by default, hidden while the layer of places is off, shown with it", async () => {
  assert.equal(await ev(() => document.getElementById("showPlaceAreas").checked), false);
  assert.equal(await ev(() => document.getElementById("rowPlaceAreas").hidden), true, "hidden while the layer is off");
  assert.equal(await ev(() => getComputedStyle(document.getElementById("rowPlaceAreas")).display), "none");
  await ev(() => { if (document.getElementById("filters").hidden) document.getElementById("btnFilters").click(); document.querySelector('#filters details[data-sec="f-adv"]').open = true; });
  await tick(page, "#showPlaces", true);
  await page.waitForFunction(() => window.TT_E2E.map.getLayer("places-area-fill"), null, { timeout: 20000 });
  assert.equal(await ev(() => document.getElementById("rowPlaceAreas").hidden), false, "shown with the layer");
  assert.equal(await ev(() => !!document.getElementById("rowPlaceAreas").closest("details[data-sec=f-adv]")), true, "in the fine-tuning section");
});

test("the outlines of quarters and squares are drawn only when the box is on; the outline of the hippodrome always goes with the layer", async () => {
  const flt = () => ev(() => JSON.stringify(window.TT_E2E.map.getFilter("places-area-fill")));
  const fltLine = () => ev(() => JSON.stringify(window.TT_E2E.map.getFilter("places-area-line")));
  assert.equal(await flt(), JSON.stringify(["==", ["get", "kind"], "area"]), "only the areas of the past while the box is off");
  assert.equal(await fltLine(), await flt());
  await page.check("#showPlaceAreas");
  assert.ok([null, undefined, "null", undefined].includes(await ev(() => window.TT_E2E.map.getFilter("places-area-fill") ?? null)) || (await flt()) === "null", "every outline when the box is on");
  const kinds = await ev(() => window.TT_E2E.map.getSource("places-area").serialize().data.features.map((f) => f.properties.kind));
  const n = (k) => kinds.filter((x) => x === k).length;
  assert.ok(n("district") >= 40 && n("square") >= 15 && n("area") >= 1, `outlines: ${n("district")} quarters, ${n("square")} squares, ${n("area")} areas`);
  await page.uncheck("#showPlaceAreas");
  assert.equal(await flt(), JSON.stringify(["==", ["get", "kind"], "area"]));
});

test("every outline has a colour of the palette and the neighbouring districts differ", async () => {
  const cols = await ev(() => window.TT_E2E.map.getSource("places-area").serialize().data.features.filter((f) => f.properties.kind !== "area").map((f) => f.properties.col));
  assert.ok(new Set(cols).size >= 8, "colours: " + new Set(cols).size);
  let same = 0;
  for (let i = 1; i < cols.length; i++) if (cols[i] === cols[i - 1]) same++;
  assert.equal(same, 0, "two outlines in a row never share a colour");
});

test("the note about the hippodrome stands on the card of the hippodrome only", async () => {
  const note = PL.ui.area_note.en.slice(0, 40);
  const quarter = PL.items.find((c) => c.id === "district-r2073134");                   // Abanotubani: a quarter with an outline
  assert.ok(quarter && quarter.g, "a quarter with an outline");
  let txt = await (await openCard(quarter)).innerText();
  assert.ok(txt.includes("Abanotubani"), txt);
  assert.ok(!txt.includes(note) && !/hippodrome/i.test(txt), "no note about the hippodrome on the card of a quarter: " + txt.slice(0, 200));
  const hip = PL.items.find((c) => c.id === "area-saburtalo-hippodrome");
  txt = await (await openCard(hip, 15.5)).innerText();
  assert.ok(txt.includes(note), "the note stands on the card of the hippodrome");
});

test("Reset filters puts the box of the outlines off again", async () => {
  await page.check("#showPlaceAreas");
  await page.click("#filtersReset", { force: true });
  assert.equal(await ev(() => document.getElementById("showPlaceAreas").checked), false);
});
