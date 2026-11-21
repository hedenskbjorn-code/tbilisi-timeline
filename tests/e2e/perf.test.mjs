// Budgets of the first screen: the weight of what the page loads from its own site, and the time on a slow network (1.6 Mbit/s, 150 ms).
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, waitReady, HERE } from "./helpers.mjs";

const budget = JSON.parse(fs.readFileSync(path.join(HERE, "budget.json"), "utf8"));
let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

async function measure(throttle) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, serviceWorkers: "block" });
  await ctx.route((u) => !/^(127\.0\.0\.1|localhost)$/.test(u.hostname), (r) => r.abort());
  const page = await ctx.newPage();
  let bytes = 0;
  const pend = [];
  page.on("response", (r) => pend.push(r.request().sizes().then((s) => { bytes += s.responseBodySize + s.responseHeadersSize; }, () => {})));
  if (throttle) {
    const cdp = await ctx.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: 200 * 1024, uploadThroughput: 100 * 1024 });
  }
  const t0 = Date.now();
  await page.goto(`${server.url}/?base=off&nostats=1&lang=en#1887`, { waitUntil: "domcontentloaded" });
  await waitReady(page, 120000);
  const secs = (Date.now() - t0) / 1000;
  await Promise.all(pend);
  await ctx.close();
  return { secs, kb: Math.round(bytes / 1024) };
}

test("the first screen stays within the budget of weight", async () => {
  const r = await measure(false);
  console.log(`first screen: ${r.kb} KB (budget ${budget.firstLoadKB} KB)`);
  assert.ok(r.kb <= budget.firstLoadKB, `${r.kb} KB > ${budget.firstLoadKB} KB`);
});

test("the first screen on a slow network stays within the budget of time", async () => {
  const r = await measure(true);
  console.log(`slow network: ${r.secs.toFixed(1)} s (budget ${budget.throttledSeconds} s), ${r.kb} KB`);
  assert.ok(r.secs <= budget.throttledSeconds, `${r.secs.toFixed(1)} s > ${budget.throttledSeconds} s`);
});
