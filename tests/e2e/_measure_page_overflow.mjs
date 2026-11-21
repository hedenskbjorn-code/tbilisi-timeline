// A measurement, not a test (the name starts with _): what makes the page wider than the window on a phone, and whether it can really be scrolled sideways.
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";

const server = await startServer();
const browser = await launch();
for (const [lang, w] of [["ka", 360], ["ru", 320], ["en", 390]]) {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=${lang}#1887`, { width: w, height: 800 });
  await waitReady(page);
  const r = await page.evaluate(() => {
    window.scrollTo(200, 0);
    const sx = window.scrollX;
    const offenders = [...document.querySelectorAll("body *")].map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter((o) => o.r.right > window.innerWidth + 1 && o.r.width > 0 && getComputedStyle(o.e).position !== "fixed")
      .map((o) => `${o.e.tagName.toLowerCase()}#${o.e.id || ""}.${String(o.e.className).slice(0, 30)} right=${Math.round(o.r.right)} vis=${getComputedStyle(o.e).visibility} disp=${getComputedStyle(o.e).display}`)
      .slice(0, 8);
    return { scrollX: sx, htmlOverflowX: getComputedStyle(document.documentElement).overflowX, bodyOverflowX: getComputedStyle(document.body).overflowX, docW: document.documentElement.scrollWidth, inner: window.innerWidth, offenders };
  });
  console.log(lang, w, JSON.stringify(r, null, 1));
  await page.ctx.close();
}
await browser.close();
server.srv.close();
