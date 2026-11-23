// The guided tour after the welcome window: five steps, the lit element is the real one, the card stays on the screen (a phone too), no panel is opened by the tour,
// the button "?" of the menu starts it, Esc closes it.
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

const url = (extra = "") => `${server.url}/?e2e=1&base=off&nostats=1&lang=en${extra}#1887`;
const hole = async (page) => { await page.waitForTimeout(450); return page.evaluate(() => { const r = document.getElementById("tourHole").getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; }); };
const card = (page) => page.evaluate(() => { const r = document.getElementById("tourCard").getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: innerWidth, h: innerHeight, txt: document.getElementById("tourCard").innerText }; });
const center = (page, id) => page.evaluate((i) => { const r = document.getElementById(i).getBoundingClientRect(); return { x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 }; }, id);
const inside = (h, p) => p.x >= h.l && p.x <= h.r && p.y >= h.t && p.y <= h.b;

test("the welcome window offers the tour; the tour lights the real elements, step by step, and ends with 'Done'", async () => {
  const page = await openPage(browser, url("&welcome=1"));
  await waitReady(page);
  await page.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  await page.locator("#imBody button", { hasText: "Quick tour" }).click();
  await page.waitForSelector("#tourHole", { timeout: 10000 });
  assert.equal(await page.evaluate(() => document.getElementById("infoModal").hidden), true, "the welcome window is closed");
  let c = await card(page);
  assert.match(c.txt, /1 of 6/);
  assert.ok(inside(await hole(page), await center(page, "timebar")), "step 1 lights the time scale");
  await page.click("#tourCard button.chip.primary");
  assert.match((await card(page)).txt, /2 of 6/);
  assert.match((await card(page)).txt, /Wikimedia Commons/, "the photo of a card leads to Commons");
  await page.click("#tourCard button.chip.primary");
  c = await card(page);
  assert.match(c.txt, /3 of 6/);
  const h3 = await hole(page);
  assert.ok(inside(h3, await center(page, "btnFilters")) && inside(h3, await center(page, "btnSearch")), "step 3 lights both buttons");
  await page.click("#tourCard button.chip.primary");
  c = await card(page);
  assert.match(c.txt, /4 of 6/);
  assert.match(c.txt, /Views and photos/, "the step of the views");
  assert.match(c.txt, /flip through/, "the flipping of the pictures is explained");
  assert.ok(inside(await hole(page), await center(page, "btnViews")), "step 4 lights the button Views");
  await page.click("#tourCard button.chip.primary");
  const h4 = await hole(page);
  for (const id of ["thenBtn", "hereBtn", "linkBtn"]) assert.ok(inside(h4, await center(page, id)), "step 5 lights " + id);
  assert.match((await card(page)).txt, /plan of 1735–1913/, "the swipe is said to need an old plan");
  await page.click("#tourCard button.chip.primary");
  assert.match((await card(page)).txt, /6 of 6/);
  assert.match(await page.locator("#tourCard button.chip.primary").innerText(), /Done/);
  await page.click("#tourCard button.chip.primary");
  assert.equal(await page.locator("#tour").count(), 0, "the tour is gone");
  await page.ctx.close();
});

test("Esc closes the tour; the button '?' starts it again; Back goes one step back", async () => {
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

test("on a phone the card stays inside the screen at every step and the tour opens no panel", async () => {
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
  assert.ok(n >= 3, "at least three steps on a phone: " + n);
  assert.equal(await filtersOpen(), f0, "the tour did not open the panel of the filters");
  await page.ctx.close();
});

test("the button of the tour is the first control of the panel Info (not in the footer); the button of the version is in the panel, not in the top bar", async () => {
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

test("on a phone the tour started from the panel Info closes the panel, and at every step the lit place is the thing the card speaks about", async () => {
  const page = await openPage(browser, url(), { width: 390, height: 844 });
  await waitReady(page);
  const side = () => page.evaluate(() => { const s = document.getElementById("side"); return !s.hidden && s.getBoundingClientRect().height > 20; });
  if (!(await side())) await page.click("#btnInfo");                                   // the panel Info is open: the button of the tour is inside it
  assert.equal(await side(), true, "the panel Info is open before the tour");
  await page.click("#btnTour");
  await page.waitForSelector("#tourHole", { timeout: 10000 });
  assert.equal(await side(), false, "the panel Info is closed when the tour starts (it covered the map)");
  let n = 0;
  for (;;) {
    n++;
    await page.waitForTimeout(450);                                                    // the lit place moves with a short animation
    const o = await page.evaluate(() => {
      const h = document.getElementById("tourHole").getBoundingClientRect(), title = document.getElementById("tourTitle").textContent;
      const x = h.left + h.width / 2, y = h.top + h.height / 2, stack = document.elementsFromPoint(x, y).filter((e) => !e.closest("#tour"));      // what lies under the lit place (the layer of the tour itself is left out)
      const top = stack[0], under = (top && top.closest("[id]") && top.closest("[id]").id) || "";
      return { title, under, inMap: !!(top && top.closest("#map")), inSide: !!(top && top.closest("#side")) };
    });
    assert.equal(o.inSide, false, `step ${n} "${o.title}": the lit place is not the panel Info`);
    if (o.title === "Map") assert.equal(o.inMap, true, `step "Map": the lit place is on the map (under it: #${o.under})`);
    const done = /Done/.test(await page.locator("#tourCard button.chip.primary").innerText());
    await page.click("#tourCard button.chip.primary");
    if (done) break;
    assert.ok(n < 8);
  }
  await page.ctx.close();
});
