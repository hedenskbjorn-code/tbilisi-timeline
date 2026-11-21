// The top bar of the main page fits at every width of the window and in every language (a header that runs out of the screen hid the language selector on tablets).
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady, LANGS } from "./helpers.mjs";

const WIDTHS = [320, 360, 390, 641, 768, 800, 1000, 1099, 1100, 1280];
let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

const measure = (page) => page.evaluate(() => {
  const top = document.getElementById("top");
  const out = [...top.querySelectorAll(":scope > *")].filter((e) => e.offsetParent !== null && e.getBoundingClientRect().right > window.innerWidth + 1).map((e) => e.id || e.tagName);
  return { over: top.scrollWidth - top.clientWidth, out, page: document.documentElement.scrollWidth - window.innerWidth };
});

for (const lang of LANGS) {
  test(`the top bar and the page fit at ${WIDTHS.length} widths of the window (every width a fresh page), ${lang}`, async () => {
    const bad = [];
    for (const w of WIDTHS) {
      const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=${lang}#1887`, { width: w, height: 800 });
      await waitReady(page);
      const m = await measure(page);
      if (m.over > 1 || m.out.length || m.page > 1) bad.push(`${w}px: bar over ${m.over}, outside [${m.out}], page wider by ${m.page}`);
      await page.ctx.close();
    }
    assert.deepEqual(bad, []);
  });
}

test("the window is resized (a tablet is turned): the group of buttons goes into the menu and comes back, the bar always fits", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=ka#1887`, { width: 1280, height: 800 });
  await waitReady(page);
  assert.equal(await page.locator("#top > #topRight").count(), 1);
  for (const w of [1024, 800, 1024, 1280]) {
    await page.setViewportSize({ width: w, height: 800 });
    await page.waitForTimeout(300);
    const m = await measure(page);
    assert.ok(m.over <= 1 && m.out.length === 0, `${w}px: bar over ${m.over}, outside [${m.out}]`);
    assert.equal(await page.locator("#top > #topRight").count(), w < 1100 ? 0 : 1, `${w}px: the group is in a wrong place`);
  }
  await page.ctx.close();
});

test("on a tablet the language, version and sections are in the menu (...) and the menu opens", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1887`, { width: 800, height: 900 });
  await waitReady(page);
  assert.equal(await page.locator("#top > #topRight").count(), 0, "the group is still in the bar");
  await page.click("#btnMore");
  await page.waitForSelector("#moreMenu:not([hidden])");
  assert.equal(await page.locator("#moreMenu #lang").count(), 1);
  assert.equal(await page.locator("#moreMenu #pagesSel").count(), 1);
  assert.equal(await page.locator("#moreMenu #btnVersion").count(), 1);
  // the menu is on top: the element at its centre belongs to the menu (not to the time bar or to a panel), and every item can be reached
  const topmost = await page.evaluate(() => {
    const r = document.getElementById("moreMenu").getBoundingClientRect();
    const hit = (x, y) => { const e = document.elementFromPoint(x, y); return !!(e && e.closest("#moreMenu")); };
    return { centre: hit(r.left + r.width / 2, r.top + 20), bottom: hit(r.left + r.width / 2, r.bottom - 10) };
  });
  assert.deepEqual(topmost, { centre: true, bottom: true });
  await page.keyboard.press("Escape");
  await page.ctx.close();
});

test("on a wide screen the group stays in the bar and there is no menu button", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=ka#1887`, { width: 1280, height: 800 });
  await waitReady(page);
  assert.equal(await page.locator("#top > #topRight").count(), 1);
  assert.equal(await page.locator("#btnMore").isVisible(), false);
  await page.ctx.close();
});
