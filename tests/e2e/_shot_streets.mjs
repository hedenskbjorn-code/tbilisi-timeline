// one-off: a screenshot of the street names (not a test)
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(); const browser = await launch();
const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=ru&c=44.8035,41.6935,15.6#1960`);
await waitReady(page);
await page.waitForTimeout(2500);
await page.screenshot({ path: "F:/TEMP/claude/f22f922f413ad417/f8a4c083-bf60-42ff-8d8a-a918c3c934cc/scratchpad/streets_1960.png" });
await page.ctx.close(); await browser.close(); server.srv.close();
console.log("done");
