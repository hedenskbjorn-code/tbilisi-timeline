import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(); const browser = await launch();
const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=ru#1887`);
await waitReady(page);
await page.waitForTimeout(1500);
await page.screenshot({ path: "F:/TEMP/claude/f22f922f413ad417/f8a4c083-bf60-42ff-8d8a-a918c3c934cc/scratchpad/side_top.png", clip: { x: 0, y: 0, width: 700, height: 420 } });
await page.ctx.close(); await browser.close(); server.srv.close();
