// Service worker of the site: (1) the application shell works without network (the last seen data too), (2) accepts a photo shared to the site from the share menu of the phone
// (Web Share Target: POST ./share-target) and leaves it for the page to pick up. Heavy things (tiles, photos, topographic maps) are never cached here.
const VERSION = "tt-v1";
const SHARE_CACHE = "tt-share";
const BASE = self.registration.scope;                                  // ends with "/"
const SHELL = ["./", "index.html", "app.js", "photo.js", "pwa.js", "config.js", "style.css", "translit.js", "vendor/maplibre-gl.js", "vendor/maplibre-gl.css", "manifest.webmanifest", "img/pwa/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => Promise.all(SHELL.map((u) => c.add(new Request(new URL(u, BASE), { cache: "reload" })).catch(() => {})))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION && k !== SHARE_CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
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

async function networkFirst(req) {
  const c = await caches.open(VERSION);
  try {
    const r = await fetch(req);
    if (r && r.ok && r.type === "basic") c.put(req, r.clone());
    return r;
  } catch (err) {
    const hit = (await c.match(req, { ignoreSearch: req.mode === "navigate" })) || (req.mode === "navigate" ? await c.match(new URL("./", BASE).href) : null);
    if (hit) return hit;
    throw err;
  }
}

self.addEventListener("fetch", (e) => {
  const req = e.request, url = new URL(req.url);
  if (req.method === "POST" && url.href === new URL("share-target", BASE).href) { e.respondWith(takeShare(req)); return; }
  if (req.method !== "GET" || url.origin !== self.location.origin || !url.href.startsWith(BASE)) return;     // tiles, Wikimedia, the Workers: the browser itself
  const rel = url.href.slice(BASE.length);
  if (rel.startsWith("img/") && !rel.startsWith("img/pwa/")) return;                                       // photos and previews: not cached here
  if (rel.startsWith("topo/")) return;
  e.respondWith(networkFirst(req));
});
