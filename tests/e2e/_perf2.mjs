import { startServer, launch, openPage } from "./helpers.mjs";
const server = await startServer(); const browser = await launch();
for (const [name, cpu] of [["desktop", 1], ["phone-like (CPU x4)", 4]]) {
  const page = await openPage(browser, "about:blank");
  const cdp = await page.ctx.newCDPSession(page);
  await page.goto(`${server.url}/?e2e=1&nostats=1&lang=en#1990`);
  await page.waitForFunction(() => window.TT_E2E && window.TT_E2E.map && window.TT_E2E.map.loaded(), null, { timeout: 60000 });
  await page.waitForTimeout(2000);
  // all layers on
  await page.evaluate(() => { for (const id of ["showRel", "showSci", "showEdu", "showPlaces", "showMon", "showPlq", "showMod"]) { const e = document.getElementById(id); if (e && !e.checked) { e.checked = true; e.dispatchEvent(new Event("change", { bubbles: true })); } } });
  await page.waitForTimeout(6000);
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: cpu });
  const r = await page.evaluate(async () => {
    const sl = document.getElementById("slider"); const out = []; let longs = [];
    new PerformanceObserver((l) => l.getEntries().forEach((e) => longs.push(Math.round(e.duration)))).observe({ entryTypes: ["longtask"] });
    for (const v of [700, 760, 820, 880, 940, 880, 820, 760, 700, 640]) {
      const t = performance.now(); sl.value = v; sl.dispatchEvent(new Event("input", { bubbles: true }));
      await new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(res)));
      out.push(Math.round(performance.now() - t));
    }
    return { frames: out, longs };
  });
  const feats = await page.evaluate(() => { const m = window.TT_E2E.map; let n = 0; for (const s of Object.values(m.style.sourceCaches || {})) n++; return Object.keys(m.style.getSource ? m.style.stylesheet.sources : {}).length; });
  console.log(name, "| slider step to 2 frames ms:", JSON.stringify(r.frames), "| long tasks ms:", JSON.stringify(r.longs), "| sources:", feats);
  await page.ctx.close();
}
await browser.close(); server.srv.close();
