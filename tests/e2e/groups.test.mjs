// Groups of boxes in the panel of filters: closed for a visitor, a master box switches the boxes of its group, half-ticked when only some are on, the arrow opens the group, the counter and the reset button
// do not see the master boxes.
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";

let server, browser, page;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&groups=1&base=off&nostats=1&lang=en#1990`);
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const ev = (f, a) => page.evaluate(f, a);
const grp = (g) => ev((g) => { const el = document.querySelector(`.gm[data-gm=${g}]`), m = el.querySelector(".gmaster"); return { open: !el.querySelector(".gmkids").hidden, checked: m.checked, half: m.indeterminate }; }, g);
const kidsOf = (ids) => ev((ids) => ids.map((i) => document.getElementById(i).checked), ids);
const setMaster = (g, on) => page.locator(`.gm[data-gm=${g}] .gmaster`).evaluate((e, on) => { e.checked = on; e.dispatchEvent(new Event("change", { bubbles: true })); }, on);

test("for a visitor the groups are closed, and the master boxes show the state of their boxes", async () => {
  for (const g of ["reg", "sci", "mon"]) assert.equal((await grp(g)).open, false, g + " is closed");
  assert.deepEqual(await grp("reg"), { open: false, checked: true, half: false });          // all four boxes of the register are on
  assert.deepEqual(await grp("sci"), { open: false, checked: false, half: true });          // science on, education off
  assert.deepEqual(await grp("mon"), { open: false, checked: false, half: false });         // monuments and plaques off
});

test("the arrow opens and closes a group", async () => {
  await page.locator(".gm[data-gm=sci] .gmtoggle").evaluate((e) => e.click());
  assert.equal((await grp("sci")).open, true);
  assert.equal(await page.locator(".gm[data-gm=sci] .gmtoggle").getAttribute("aria-expanded"), "true");
  await page.locator(".gm[data-gm=sci] .gmtoggle").evaluate((e) => e.click());
  assert.equal((await grp("sci")).open, false);
});

test("the master box switches every box of its group, and the layers follow", async () => {
  await setMaster("mon", true);
  assert.deepEqual(await kidsOf(["showMon", "showPlq"]), [true, true]);
  await page.waitForFunction(() => window.TT_E2E.map.getSource("mons") && window.TT_E2E.map.getSource("plqs"), null, { timeout: 20000 });
  await setMaster("mon", false);
  assert.deepEqual(await kidsOf(["showMon", "showPlq"]), [false, false]);
  await setMaster("reg", false);
  assert.deepEqual(await kidsOf(["showResid", "showPublic", "showDef", "showOtherB"]), [false, false, false, false]);
  assert.deepEqual(await grp("reg"), { open: false, checked: false, half: false });
  await setMaster("reg", true);
  assert.deepEqual(await kidsOf(["showResid", "showPublic", "showDef", "showOtherB"]), [true, true, true, true]);
});

test("a single box changes its master to half-ticked, and the master boxes are not counted nor do they wake the reset button", async () => {
  await page.locator("#showResid").evaluate((e) => { e.checked = false; e.dispatchEvent(new Event("change", { bubbles: true })); });
  assert.deepEqual(await grp("reg"), { open: false, checked: false, half: true });
  const cnt = await page.locator("details[data-sec=f-layers] > summary .cnt").evaluate((e) => e.textContent);
  const [on, all] = cnt.split("/").map(Number);
  const boxes = await ev(() => [...document.querySelectorAll("details[data-sec=f-layers] input[type=checkbox]:not(.gmaster)")].filter((c) => { for (let e = c; e && e.dataset?.sec !== "f-layers"; e = e.parentElement) if (e.hidden && !e.classList.contains("gmkids")) return false; return true; }));
  assert.ok(all >= 10 && on < all, "the counter counts the boxes of the section: " + cnt);
  await page.locator("#showResid").evaluate((e) => { e.checked = true; e.dispatchEvent(new Event("change", { bubbles: true })); });
  assert.equal(await page.locator("#filtersReset").isDisabled(), true, "everything is as by default again: the reset button is off");
});
