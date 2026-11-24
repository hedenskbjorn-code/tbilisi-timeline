// Audit (read only): errors of the console, failed requests, and basic accessibility of the page in three languages with all the layers on, at several years.
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(), browser = await launch();
const out = { errors: [], failed: [], a11y: {}, timing: {} };
for (const lang of ["ru", "en", "ka"]) {
  const page = await openPage(browser, `${server.url}/?e2e=1&nostats=1&lang=${lang}#2026`);
  const tag = (s) => `[${lang}] ${s}`;
  page.on("pageerror", (e) => out.errors.push(tag("pageerror: " + e.message)));
  page.on("console", (m) => { if (m.type() === "error") { const t = m.text(); if (!/Failed to load resource|net::ERR|tiles|openfreemap|ERR_/.test(t)) out.errors.push(tag("console: " + t.slice(0, 200))); } });
  page.on("requestfailed", (r) => { const u = r.url(); if (u.startsWith(server.url)) out.failed.push(tag(u + " " + (r.failure() || {}).errorText)); });
  page.on("response", (r) => { if (r.url().startsWith(server.url) && r.status() >= 400) out.failed.push(tag(r.status() + " " + r.url())); });
  const t0 = Date.now();
  await waitReady(page);
  out.timing[lang] = Date.now() - t0;
  for (const id of ["showPlaces", "showMon", "showPlq", "showEdu", "showSci", "showRel", "showLost", "showStLabels"]) { try { await page.check("#" + id, { timeout: 3000 }); } catch (e) { out.errors.push(tag("cannot check #" + id)); } }
  await page.waitForTimeout(2500);
  for (const y of [1800, 1913, 1960, 2026]) {
    await page.evaluate((y) => { location.hash = "#" + y; window.dispatchEvent(new HashChangeEvent("hashchange")); }, y);
    await page.waitForTimeout(700);
  }
  // open the search and a card of every layer through the search
  for (const q of ["Mushtaidi", "Rustaveli", "Samgori", "Pushkin", "Dighomi", "Abashidze"]) {
    try { await page.click("#btnSearch"); await page.fill("#searchQ", q); await page.waitForTimeout(500); const li = page.locator("#searchRes li[data-i]").first(); if (await li.count()) { await li.click(); await page.waitForTimeout(900); } await page.keyboard.press("Escape"); await page.keyboard.press("Escape"); await page.waitForTimeout(300); } catch (e) { out.errors.push(tag("search " + q + ": " + e.message.slice(0, 80))); }
  }
  // basic accessibility
  out.a11y[lang] = await page.evaluate(() => {
    const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
    const name = (e) => (e.getAttribute("aria-label") || e.getAttribute("title") || e.textContent || "").trim();
    return {
      buttonsWithoutName: [...document.querySelectorAll("button, [role=button]")].filter((b) => vis(b) && !name(b)).map((b) => b.id || b.className).slice(0, 10),
      imgsWithoutAlt: [...document.querySelectorAll("img")].filter((i) => !i.hasAttribute("alt")).map((i) => (i.src || "").slice(-50)).slice(0, 10),
      inputsWithoutLabel: [...document.querySelectorAll("input, select, textarea")].filter((i) => vis(i) && i.type !== "hidden" && !i.getAttribute("aria-label") && !(i.id && document.querySelector(`label[for="${i.id}"]`)) && !i.closest("label")).map((i) => i.id || i.name || i.type).slice(0, 10),
      linksWithoutText: [...document.querySelectorAll("a")].filter((a) => vis(a) && !name(a) && !a.querySelector("img[alt]")).map((a) => a.href.slice(0, 50)).slice(0, 10),
      htmlLang: document.documentElement.lang, title: document.title, h1: document.querySelectorAll("h1").length,
      focusableCount: document.querySelectorAll("a[href], button, input, select, textarea, [tabindex]").length,
      tabindexPositive: [...document.querySelectorAll("[tabindex]")].filter((e) => +e.getAttribute("tabindex") > 0).length,
    };
  });
  await page.ctx.close();
}
console.log(JSON.stringify(out, null, 1));
await browser.close(); server.srv.close();
