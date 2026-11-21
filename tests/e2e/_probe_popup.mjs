// A probe, not a test (the name starts with _): does the open card of an object close with Esc, and can its close button be clicked
// (is it not covered by the time bar), at several sizes of the window and for several kinds of cards.
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";

const server = await startServer();
const browser = await launch();
const CASES = [["Sioni", "⛪"], ["Great Synagogue", "⛪"], ["Narikala", null], ["Cycling School", "🏫"]];
for (const [w, h] of [[1280, 720], [1280, 800], [1024, 768], [390, 844]]) {
  for (const [q, emoji] of CASES) {
    const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1887`, { width: w, height: h });
    await waitReady(page);
    await page.click("#btnSearch").catch(() => page.click("#btnMore").then(() => page.click("#btnSearch")));
    await page.fill("#searchQ", q);
    await page.waitForSelector("#searchRes li");
    const row = emoji ? page.locator("#searchRes li", { hasText: emoji }).first() : page.locator("#searchRes li").first();
    await row.click();
    try { await page.locator(".maplibregl-popup .pop").waitFor({ timeout: 8000 }); } catch (e) { console.log(`${w}x${h} ${q}: no popup`); await page.ctx.close(); continue; }
    await page.waitForTimeout(1800);                                   // the camera flies to the object
    const info = await page.evaluate(() => {
      const b = document.querySelector(".maplibregl-popup-close-button");
      const r = b ? b.getBoundingClientRect() : null;
      const hit = r ? document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) : null;
      const pr = document.querySelector(".maplibregl-popup").getBoundingClientRect();
      return { closeBtn: !!b, covered: !!(hit && hit !== b && !b.contains(hit)), coveredBy: hit ? (hit.id || hit.className || hit.tagName) : null, popupTop: Math.round(pr.top), popupBottom: Math.round(pr.bottom), vh: window.innerHeight,
               timebarBottom: Math.round(document.getElementById("timebar").getBoundingClientRect().bottom) };
    });
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);
    const stillOpen = await page.locator(".maplibregl-popup").count();
    console.log(`${w}x${h} ${q}: ${JSON.stringify(info)}  after Esc popups: ${stillOpen}`);
    await page.ctx.close();
  }
}
await browser.close();
server.srv.close();
