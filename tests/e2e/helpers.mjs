// Helpers of the browser tests (node:test + playwright-core, the installed Chrome is used: nothing is downloaded).
// The site is served from site/ by a small static server with gzip (as GitHub Pages does), the service worker is blocked, and ?base=off
// makes the base map the plain offline background, so the tests do not depend on the network (tiles.openfreemap.org).
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

export const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..", "..");
const SITE = path.join(ROOT, "site");
export const DATA = path.join(SITE, "data");
const MIME = { ".html": "text/html;charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".css": "text/css", ".webp": "image/webp",
  ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".webmanifest": "application/manifest+json", ".pbf": "application/x-protobuf", ".geojson": "application/json" };
const ZIP = new Set([".html", ".js", ".mjs", ".json", ".css", ".svg", ".geojson", ".webmanifest"]);
const GZ_CACHE = new Map();

export function startServer(port = 0, host = "127.0.0.1") {
  const srv = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split("?")[0]);
    if (p.endsWith("/")) p += "index.html";
    let f = path.join(SITE, p);
    if (!f.startsWith(SITE)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) { res.writeHead(301, { location: p + "/" }); return res.end(); }
    fs.readFile(f, (e, d) => {
      if (e) { res.writeHead(404); return res.end("not found"); }
      const ext = path.extname(f);
      const h = { "content-type": MIME[ext] || "application/octet-stream", "cache-control": "no-store" };
      if (ZIP.has(ext)) { let z = GZ_CACHE.get(f); if (!z) { z = zlib.gzipSync(d, { level: 6 }); GZ_CACHE.set(f, z); } d = z; h["content-encoding"] = "gzip"; }
      res.writeHead(200, h);
      res.end(d);
    });
  });
  return new Promise((resolve) => srv.listen(port, host, () => resolve({ srv, url: "http://127.0.0.1:" + srv.address().port })));
}

export async function launch() {
  const opts = { headless: true };
  if (process.env.CHROME_PATH) opts.executablePath = process.env.CHROME_PATH; else opts.channel = "chrome";
  return chromium.launch(opts);
}

// a page with the collected errors of the console and of the page: page.errors
export async function openPage(browser, url, { width = 1280, height = 800, throttle = null, dpr = 1 } = {}) {
  const ctx = await browser.newContext({ viewport: { width, height }, serviceWorkers: "block", locale: "en-US", deviceScaleFactor: dpr });
  // hermetic: nothing but the local server is reachable (the tests must not depend on third-party hosts)
  await ctx.route((u) => !/^(127\.0\.0\.1|localhost)$/.test(u.hostname), (r) => r.abort());
  const page = await ctx.newPage();
  page.errors = [];
  page.on("pageerror", (e) => page.errors.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") page.errors.push("console.error: " + m.text().slice(0, 200)); });
  if (throttle) {
    const cdp = await ctx.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: throttle.latency, downloadThroughput: throttle.down, uploadThroughput: throttle.up });
  }
  page.ctx = ctx;
  await page.goto(url, { waitUntil: "domcontentloaded" });
  return page;
}

// the main page is ready when the plank "loading" is gone
export async function waitReady(page, ms = 45000) {
  await page.waitForFunction(() => { const l = document.getElementById("loading"); return !!l && l.hidden; }, null, { timeout: ms });
}

// errors that come from the network of the test machine and not from the site are not counted (blocked third-party scripts, the basemap)
export function realErrors(page) {
  return page.errors.filter((e) => !/Failed to load resource|net::ERR|AJAXError|Failed to fetch|NetworkError|cloudflareinsights|openfreemap|challenges\.cloudflare|wikimedia|workers\.dev/i.test(e));
}

export const LANGS = ["ru", "en", "ka"];

// switch a box of the panel of the filters: its block (<details>) is opened first (the blocks are closed by default except one, and a closed block hides its boxes)
export async function tick(page, sel, on = true) {
  await page.evaluate((s) => { const d = document.querySelector(s)?.closest("details"); if (d) d.open = true; }, sel);
  await (on ? page.check(sel) : page.uncheck(sel));
}
