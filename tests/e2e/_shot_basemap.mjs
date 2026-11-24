import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(); const browser = await launch();
for (const [name, vp] of [["desk", { width: 1280, height: 800 }], ["phone", { width: 390, height: 780 }]]) {
  const ctx = await browser.newContext({ viewport: vp, locale: "ru-RU" });
  const page = await ctx.newPage();
  await page.goto(`${server.url}/?e2e=1&nostats=1&lang=ru#1990`);
  await waitReady(page);
  await page.evaluate(() => document.getElementById("btnFilters").click());
  await page.waitForTimeout(700);
  console.log(name, "filters visible:", await page.evaluate(() => { const f = document.getElementById("filters"); const r = f.getBoundingClientRect(); return !f.hidden && r.width > 0 && getComputedStyle(f).visibility; }));
  await page.evaluate(() => { document.querySelector("details[data-sec=f-layers]").open = true; });
  await page.waitForTimeout(400);
  await page.evaluate(() => document.querySelector("details[data-sec=f-base]").open = false);
  await page.evaluate(() => document.querySelector("details[data-sec=f-layers]").scrollIntoView());
  await page.waitForTimeout(300);
  await page.screenshot({ path: `F:/TEMP/claude/f22f922f413ad417/f8a4c083-bf60-42ff-8d8a-a918c3c934cc/scratchpad/groups_${name}.png` });
  await ctx.close();
}
await browser.close(); server.srv.close();
