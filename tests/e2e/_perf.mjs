import { startServer, launch, openPage } from "./helpers.mjs";
const server = await startServer(); const browser = await launch();
for (const [name, cpu] of [["desktop", 1], ["phone-like (CPU x4)", 4]]) {
  const page = await openPage(browser, "about:blank");
  const cdp = await page.ctx.newCDPSession(page);
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: cpu });
  await page.addInitScript(() => { window.__lt = []; new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__lt.push([Math.round(e.startTime), Math.round(e.duration)]))).observe({ entryTypes: ["longtask"] }); });
  const t0 = Date.now(); const bytes = {};
  page.on("response", async (r) => { try { const b = await r.body(); bytes[r.url().replace(server.url, "")] = b.length; } catch {} });
  await page.goto(`${server.url}/?e2e=1&nostats=1&lang=en#1990`);
  await page.waitForFunction(() => window.TT_E2E && window.TT_E2E.map && window.TT_E2E.map.loaded(), null, { timeout: 120000 }).catch(() => {});
  const ready = Date.now() - t0;
  await page.waitForTimeout(2500);
  const m = await page.evaluate(() => ({ lt: window.__lt, nav: performance.getEntriesByType("navigation")[0].toJSON(), paint: performance.getEntriesByType("paint").map((p) => [p.name, Math.round(p.startTime)]) }));
  const tbt = m.lt.reduce((a, [, d]) => a + Math.max(0, d - 50), 0);
  const tot = Object.values(bytes).reduce((a, b) => a + b, 0);
  console.log(name, "| map ready ms:", ready, "| DOMContentLoaded:", Math.round(m.nav.domContentLoadedEventEnd), "| load:", Math.round(m.nav.loadEventEnd), "| paint:", JSON.stringify(m.paint), "| long tasks:", m.lt.length, "| TBT ms:", tbt, "| bytes (uncompressed bodies):", Math.round(tot / 1024), "KB in", Object.keys(bytes).length, "requests");
  console.log("  biggest:", Object.entries(bytes).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([u, b]) => u.slice(0, 40) + " " + Math.round(b / 1024) + "KB").join("; "));
  console.log("  longest tasks [start,dur]:", JSON.stringify(m.lt.sort((a, b) => b[1] - a[1]).slice(0, 6)));
  await page.ctx.close();
}
await browser.close(); server.srv.close();
