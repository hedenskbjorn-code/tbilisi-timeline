// Audit: what happens when the lazy file of a layer fails to load once (a dropped connection)? Does the layer load on the next switch on?
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(), browser = await launch();
const page = await openPage(browser, `${server.url}/?e2e=1&nostats=1&lang=en#2000`);
let n = 0;
await page.route("**/data/places.json*", (route) => { n++; if (n <= 1) route.abort("failed"); else route.continue(); });
await waitReady(page);
await page.check("#showPlaces");
await page.waitForTimeout(3000);
console.log("requests after the first switch on:", n, "| source exists:", await page.evaluate(() => !!window.TT_E2E.map.getSource("places")));
await page.uncheck("#showPlaces"); await page.check("#showPlaces");
await page.waitForTimeout(3000);
console.log("requests after switching off and on:", n, "| source exists:", await page.evaluate(() => !!window.TT_E2E.map.getSource("places")));
await page.ctx.close(); await browser.close(); server.srv.close();
