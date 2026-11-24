import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
const server = await startServer(), browser = await launch();
const page = await openPage(browser, `${server.url}/?e2e=1&groups=1&base=off&nostats=1&lang=en#1990`);
await waitReady(page);
console.log(JSON.stringify(await page.evaluate(() => ["rowNear", "rowNoPhoto"].map((i) => { const e = document.getElementById(i); return [i, e.hidden, getComputedStyle(e).display]; }).concat([...document.querySelectorAll(".sub2")].map((e) => ["sub2", e.hidden, getComputedStyle(e).display])))));
await page.ctx.close(); await browser.close(); server.srv.close();
