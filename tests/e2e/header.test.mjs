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

test("the window is resized (a phone vs wide): #pagesSel moves into the menu on phones and back on wider screens, #moreMenu holds secondary controls", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=ka#1887`, { width: 1280, height: 800 });
  await waitReady(page);
  assert.equal(await page.locator("#top > #pagesSel").count(), 1);
  assert.equal(await page.locator("#moreMenu #topRight").count(), 1);
  for (const w of [390, 640, 800, 1280]) {
    await page.setViewportSize({ width: w, height: 800 });
    await page.waitForTimeout(300);
    const m = await measure(page);
    assert.ok(m.over <= 1 && m.out.length === 0, `${w}px: bar over ${m.over}, outside [${m.out}]`);
    assert.equal(await page.locator("#top > #pagesSel").count(), w <= 820 ? 0 : 1, `${w}px: pagesSel placement`);
  }
  await page.ctx.close();
});

test("secondary controls (#lang, #fbOpen, #btnSupport) live in #moreMenu and the menu opens on top", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1887`, { width: 1280, height: 900 });
  await waitReady(page);
  assert.equal(await page.locator("#btnMore").isVisible(), true);
  await page.click("#btnMore");
  await page.waitForSelector("#moreMenu:not([hidden])");
  assert.equal(await page.locator("#moreMenu #lang").count(), 1);
  assert.equal(await page.locator("#moreMenu #fbOpen").count(), 1);
  assert.equal(await page.locator("#moreMenu #btnSupport").count(), 1);
  assert.equal(await page.locator("#moreMenu #btnVersion").count(), 0, "the version button lives in the panel City");
  assert.equal(await page.locator("#side #btnVersion").count(), 1);
  const topmost = await page.evaluate(() => {
    const r = document.getElementById("moreMenu").getBoundingClientRect();
    const hit = (x, y) => { const e = document.elementFromPoint(x, y); return !!(e && e.closest("#moreMenu")); };
    return { centre: hit(r.left + r.width / 2, r.top + 20), bottom: hit(r.left + r.width / 2, r.bottom - 10) };
  });
  assert.deepEqual(topmost, { centre: true, bottom: true });
  await page.keyboard.press("Escape");
  await page.ctx.close();
});

test("on a wide screen #pagesSel stays in the top bar while secondary controls stay in #moreMenu", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=ka#1887`, { width: 1280, height: 800 });
  await waitReady(page);
  assert.equal(await page.locator("#top > #pagesSel").count(), 1);
  assert.equal(await page.locator("#moreMenu:not([hidden])").count(), 0);
  await page.ctx.close();
});

test("menu more returns keyboard focus to #btnMore after language change and feedback close, and scrolls on low 700x240 viewport", async () => {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1887`, { width: 700, height: 240 });
  await waitReady(page);
  await page.click("#btnMore");
  await page.waitForSelector("#moreMenu:not([hidden])");
  const fit = await page.evaluate(() => {
    const m = document.getElementById("moreMenu"), r = m.getBoundingClientRect(), st = getComputedStyle(m);
    return { bottom: r.bottom <= window.innerHeight + 1, overflowY: st.overflowY, scroll: m.scrollHeight >= m.clientHeight };
  });
  assert.equal(fit.bottom, true, "menu stays within 240px height");
  assert.equal(fit.overflowY, "auto", "menu has own vertical scroll");

  await page.selectOption("#lang", "ru");
  assert.equal(await page.evaluate(() => document.activeElement?.id), "btnMore", "focus returns to btnMore after lang change");

  await page.click("#btnMore");
  await page.click("#fbOpen");
  await page.waitForSelector("#fbModal:not([hidden])");
  await page.click("#fbCancel");
  assert.equal(await page.evaluate(() => document.activeElement?.id), "btnMore", "focus returns to btnMore after closing feedback from menu");
  await page.ctx.close();
});
