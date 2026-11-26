// Service worker of the site: (1) the application shell works without network (the last seen data too), (2) accepts a photo shared to the site from the share menu of the phone
// (Web Share Target: POST ./share-target) and leaves it for the page to pick up. Heavy things (tiles, photos, topographic maps) are never cached here.
const VERSION = "tt-af15e4ef";
const SHARE_CACHE = "tt-share";
const BASE = self.registration.scope;                                  // ends with "/"
const SHELL = ["index.html", "app.js?v=8c4fb7fe", "js/net.js?v=46b6ac82", "js/plans.js?v=2282229a", "js/timeline.js?v=54a1da95", "js/tour.js?v=90324d2c", "i18n.js?v=c73a8dc8", "photo.js?v=4335926d", "pwa.js?v=4f2c4857", "support.js?v=0d64cfb5", "stats.js?v=d4621ad4", "config.js?v=36f6eee6", "style.css?v=f7002b0c", "translit.js?v=1f0144e5", "vendor/maplibre-gl.js?v=e877fe22", "vendor/maplibre-gl.css?v=576b085f", "manifest.webmanifest", "img/pwa/icon-192.png", "data/manifest.json"];
const CORE_DATA = ["data/plans.json", "data/monuments.json", "data/tour.json"];
const BASE_PATH = new URL(BASE).pathname;
const INDEX = new URL("index.html", BASE);
const MANIFEST = new URL("data/manifest.json", BASE);
const SHELL_URLS = new Set(SHELL.map((path) => new URL(path, BASE).href));
let manifestPromise;

function readManifest(cache) {
  return manifestPromise ||= cache.match(MANIFEST.href).then(async (response) => {
    const manifest = await response?.json();
    if (!manifest?.f || `tt-${manifest.v}` !== VERSION) throw new Error("Offline manifest version mismatch");
    return manifest.f;
  });
}

async function checkHash(response, expected, path) {
  if (!response?.ok || !expected) throw new Error(`Missing offline resource: ${path}`);
  let bytes = new Uint8Array(await response.arrayBuffer());
  // The generator hashes LF bytes regardless of the line endings in the checkout.
  if (bytes.includes(13)) {
    let length = 0;
    for (let i = 0; i < bytes.length; i++) {
      if (bytes[i] !== 13 || bytes[i + 1] !== 10) bytes[length++] = bytes[i];
    }
    bytes = bytes.subarray(0, length);
  }
  const bytesHash = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  const actual = Array.from(bytesHash.slice(0, 4), (byte) => byte.toString(16).padStart(2, "0")).join("");
  if (actual !== expected) throw new Error(`Offline resource version mismatch: ${path}`);
}

function addAll(cache, urls) {
  return cache.addAll([...urls].map((url) => new Request(url, { cache: "reload" })));
}

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(VERSION);
    try {
      await addAll(cache, SHELL_URLS);
      const files = await readManifest(cache);
      const core = CORE_DATA.map((path) => new URL(`${path}?v=${files[path]}`, BASE).href);
      await addAll(cache, core);
      await Promise.all([...SHELL_URLS, ...core].filter((href) => href !== MANIFEST.href).map(async (href) => {
        const url = new URL(href), path = url.pathname.slice(BASE_PATH.length);
        await checkHash(await cache.match(href), url.searchParams.get("v") || files[path], path);
      }));
    } catch (error) {
      await caches.delete(VERSION);
      throw error;
    }
    // The browser activates the new version once tabs using the previous version are closed.
  })());
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith("tt-") && k !== VERSION && k !== SHARE_CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

async function takeShare(req) {
  try {
    const fd = await req.formData();
    const f = fd.get("photo");
    if (f && f.size && f.size <= 25 * 1024 * 1024 && /^image\//.test(f.type || "")) {
      const c = await caches.open(SHARE_CACHE);
      await c.put(new URL("shared-photo", BASE).href, new Response(f, { headers: { "Content-Type": f.type || "image/jpeg", "X-Name": encodeURIComponent(f.name || "photo.jpg") } }));
    }
  } catch (e) { /* the page will simply find nothing */ }
  return Response.redirect(new URL("./?share=1", BASE).href, 303);
}

async function networkFirst(req, cache) {
  try {
    const r = await fetch(req);
    if (r.status === 200 && r.type === "basic") await cache.put(req, r.clone()).catch(() => {});
    return r;
  } catch (err) {
    const hit = await cache.match(req);
    if (hit) return hit;
    throw err;
  }
}

async function respond(req, url, path) {
  const cache = await caches.open(VERSION);
  if (req.mode === "navigate" && (url.pathname === BASE_PATH || url.pathname === INDEX.pathname)) {
    return (await cache.match(INDEX.href)) || Response.error();
  }
  if (SHELL_URLS.has(url.href)) return (await cache.match(url.href)) || Response.error();

  if (path.startsWith("data/") || path === "vendor/minisearch.js") {
    const files = await readManifest(cache), version = files[path];
    if (version) {
      const requested = url.searchParams.get("v");
      if (requested !== null && requested !== version) return Response.error();
      // Normalize direct JSON fetches (e.g. the tour) to the active manifest's URL.
      url.searchParams.set("v", version);
      const hit = await cache.match(url.href);
      if (hit) return hit;
      const response = await fetch(url.href, { cache: "no-cache" });
      if (response.status === 200 && response.type === "basic") {
        await checkHash(response.clone(), version, path);
        await cache.put(url.href, response.clone()).catch(() => {});
      }
      return response;
    }
  }
  return networkFirst(req, cache);
}

self.addEventListener("fetch", (e) => {
  const req = e.request, url = new URL(req.url);
  if (req.method === "POST" && url.href === new URL("share-target", BASE).href) { e.respondWith(takeShare(req)); return; }
  if (req.method !== "GET" || req.headers.has("range") || url.origin !== self.location.origin || !url.href.startsWith(BASE)) return;     // tiles, Wikimedia, Range requests, Workers: browser itself
  const rel = url.pathname.slice(BASE_PATH.length);
  if (rel.startsWith("img/") && !rel.startsWith("img/pwa/")) return;                                       // photos and previews: not cached here
  if (rel.startsWith("topo/")) return;
  e.respondWith(respond(req, url, rel));
});
