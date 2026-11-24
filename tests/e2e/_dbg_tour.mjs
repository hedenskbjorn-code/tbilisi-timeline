import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(), browser = await launch();
const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#2026`, { width: 390, height: 844 });
await waitReady(page);
if (await page.evaluate(() => document.getElementById("side").hidden || document.getElementById("side").getBoundingClientRect().height < 20)) await page.click("#btnInfo"); await page.click("#btnTour"); await page.waitForSelector("#tourHole");
for (let i = 0; i < 2; i++) {
  await page.waitForTimeout(500);
  const o = await page.evaluate(() => {
    const r = (id) => { const b = document.getElementById(id).getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.right), Math.round(b.bottom)]; };
    const h = document.getElementById("tourHole").getBoundingClientRect();
    return { title: document.getElementById("tourTitle").textContent, hole: [h.left, h.top, h.right, h.bottom].map(Math.round), timebar: r("timebar"), slider: r("slider"), bottom: r("bottom"), side: document.getElementById("side").hidden, map: r("map") };
  });
  console.log(JSON.stringify(o)); await page.waitForTimeout(500);
  await page.click("#tourCard button.chip.primary");
}
await page.ctx.close(); await browser.close(); server.srv.close();
