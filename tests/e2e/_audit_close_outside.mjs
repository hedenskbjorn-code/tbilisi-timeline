// Audit (read only): on a phone, can every window be closed by a tap beside it?
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(), browser = await launch();
const res = [];
const vis = (page, sel) => page.evaluate((s) => { const e = document.querySelector(s); if (!e || e.hidden) return false; const r = e.getBoundingClientRect(); const st = getComputedStyle(e); return r.width > 2 && r.height > 2 && st.display !== "none" && st.visibility !== "hidden"; }, sel);
async function run(name, fn) {
  const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1960`, { width: 390, height: 844 });
  try { await waitReady(page); const ok = await fn(page); res.push([name, ok]); }
  catch (e) { res.push([name + " :: " + e.message.split("\n")[0].slice(0, 100), "ERR"]); }
  await page.ctx.close();
}
const tap = async (page, x, y) => { await page.mouse.click(x, y); await page.waitForTimeout(500); };

await run("info window (street card): tap in the corner", async (p) => {
  await p.click("#btnSearch"); await p.fill("#searchQ", "Kita Abashidze"); await p.locator("#searchRes li").filter({ hasText: "🛣" }).first().click();
  await p.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  await tap(p, 5, 5); return !(await vis(p, "#infoModal"));
});
await run("viewer of the views: tap in the corner", async (p) => {
  await p.click("#btnViews"); await p.check("#viewsAll"); await p.locator("#vgrid button").first().click();
  await p.waitForFunction(() => !document.getElementById("viewModal").hidden, null, { timeout: 5000 });
  await tap(p, 5, 5); return !(await vis(p, "#viewModal"));
});
await run("the list window Views: tap on the map below", async (p) => {
  await p.click("#btnViews"); await p.waitForTimeout(500);
  if (!(await vis(p, "#views"))) return "was not open";
  await tap(p, 195, 800); return !(await vis(p, "#views"));
});
await run("form 'report a problem': tap in the corner", async (p) => {
  await p.evaluate(() => document.getElementById("fbOpen").click());
  await p.waitForFunction(() => !document.getElementById("fbModal").hidden, null, { timeout: 5000 });
  await tap(p, 5, 5); return !(await vis(p, "#fbModal"));
});
await run("panel Filters: tap on the map", async (p) => {
  await p.click("#btnFilters"); await p.waitForTimeout(500);
  if (!(await vis(p, "#filters"))) return "was not open";
  await tap(p, 195, 834); return !(await vis(p, "#filters"));
});
await run("panel Info: tap on the map", async (p) => {
  if (!(await vis(p, "#side"))) await p.click("#btnInfo");
  await p.waitForTimeout(400);
  if (!(await vis(p, "#side"))) return "was not open";
  await tap(p, 195, 834); return !(await vis(p, "#side"));
});
await run("search window: tap on the map", async (p) => {
  await p.click("#btnSearch"); await p.waitForTimeout(400);
  if (!(await vis(p, "#search"))) return "was not open";
  await tap(p, 195, 800); return !(await vis(p, "#search"));
});
await run("menu more: tap on the map", async (p) => {
  if (!(await vis(p, "#btnMore"))) return "no button";
  await p.click("#btnMore"); await p.waitForTimeout(400);
  if (!(await vis(p, "#moreMenu"))) return "was not open";
  await tap(p, 195, 800); return !(await vis(p, "#moreMenu"));
});
await run("card on the map (popup): tap on the map beside it", async (p) => {
  await p.click("#btnSearch"); await p.fill("#searchQ", "Mushtaidi"); await p.locator("#searchRes li").first().click();
  await p.waitForSelector(".maplibregl-popup", { timeout: 15000 }); await p.waitForTimeout(1800);
  const box = await p.locator(".maplibregl-popup").boundingBox();
  await tap(p, 195, box.y > 300 ? 150 : 800); return (await p.locator(".maplibregl-popup").count()) === 0;
});
await run("welcome window: tap in the corner", async (p) => {
  await p.goto(`${server.url}/?e2e=1&base=off&nostats=1&lang=en&welcome=1#1960`); await waitReady(p);
  await p.waitForFunction(() => !document.getElementById("infoModal").hidden, null, { timeout: 15000 });
  await tap(p, 5, 5); return !(await vis(p, "#infoModal"));
});
for (const [n, ok] of res) console.log(ok === true ? "OK   " : ok === "ERR" ? "ERR  " : "??   (" + String(ok) + ") ", n);
await browser.close(); server.srv.close();
