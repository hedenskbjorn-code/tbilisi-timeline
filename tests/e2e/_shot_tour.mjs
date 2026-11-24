import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(); const browser = await launch();
const S = "F:/TEMP/claude/f22f922f413ad417/f8a4c083-bf60-42ff-8d8a-a918c3c934cc/scratchpad/";
for (const [name, vp] of [["phone", { width: 390, height: 780 }], ["desk", { width: 1280, height: 800 }]]) {
  const page = await openPage(browser, `${server.url}/?e2e=1&nostats=1&lang=en#1990`, vp);
  await waitReady(page);
  await page.evaluate(() => document.getElementById("btnTour").click());
  await page.waitForSelector("#tourHole", { timeout: 10000 });
  for (let n = 1; n <= 8; n++) {
    await page.waitForTimeout(700);
    if (n >= 4 && n <= 8 && (name === "phone" ? [4, 5, 6, 8].includes(n) : [5, 6].includes(n))) await page.screenshot({ path: `${S}tour_${name}_${n}.png` });
    await page.click("#tourCard button.chip.primary");
  }
  await page.ctx.close();
}
await browser.close(); server.srv.close();
