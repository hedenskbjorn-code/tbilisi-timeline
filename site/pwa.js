// The installable application: registers the service worker, offers "Install" and takes a photo shared from the phone's share menu:
// the photo waits in the cache of the service worker; the visitor taps the object on the map and the form opens with the photo already in it.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const TXT = {
    ru: { install: "📲 Установить приложение", pick: "Фото получено. Нажмите на объект на карте, к которому оно относится.", cancel: "Отмена" },
    en: { install: "📲 Install the app", pick: "The photo is received. Tap the object on the map that it belongs to.", cancel: "Cancel" },
    ka: { install: "📲 აპლიკაციის დაყენება", pick: "ფოტო მიღებულია. დააწკაპუნეთ რუკაზე ობიექტზე, რომელსაც ეკუთვნის.", cancel: "გაუქმება" },
  };
  const lang = () => { const l = (document.documentElement.lang || "en").slice(0, 2); return TXT[l] ? l : "en"; };
  const S = () => TXT[lang()];

  if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(() => {}));      // works on https and on localhost only

  // "Install" button: shown in the filters panel only when the browser says the site can be installed
  let deferred = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault(); deferred = e;
    const b = $("btnInstall"), row = $("rowInstall");
    if (b && row) { b.textContent = S().install; row.hidden = false; }
  });
  window.addEventListener("appinstalled", () => { deferred = null; const row = $("rowInstall"); if (row) row.hidden = true; });
  window.TT_PWA = { install: async () => { if (!deferred) return; deferred.prompt(); try { await deferred.userChoice; } catch (e) {} deferred = null; const row = $("rowInstall"); if (row) row.hidden = true; }, retext: () => { const b = $("btnInstall"); if (b) b.textContent = S().install; } };
  document.addEventListener("DOMContentLoaded", () => { const b = $("btnInstall"); if (b) b.addEventListener("click", () => window.TT_PWA.install()); });

  // a photo shared from the phone: ?share=1
  async function takeShared() {
    try {
      const c = await caches.open("tt-share"), key = new URL("shared-photo", document.baseURI).href, r = await c.match(key);
      if (!r) return null;
      await c.delete(key);
      const blob = await r.blob();
      return new File([blob], decodeURIComponent(r.headers.get("X-Name") || "photo.jpg"), { type: blob.type || "image/jpeg" });
    } catch (e) { return null; }
  }
  async function startShare() {
    history.replaceState(null, "", location.pathname + location.hash);              // the address without ?share=1
    const file = await takeShared();
    if (!file || !window.TT_PHOTO || !window.TT_PHOTO.enabled() || !window.TT_APP) return;
    const bar = document.createElement("div");
    bar.style.cssText = "position:fixed;left:8px;right:8px;top:8px;z-index:60;background:#1c2b4a;color:#fff;padding:10px 12px;border-radius:8px;display:flex;gap:10px;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,.4)";
    const t = document.createElement("span"); t.style.flex = "1"; t.textContent = S().pick;
    const x = document.createElement("button"); x.type = "button"; x.className = "chip"; x.textContent = S().cancel;
    bar.appendChild(t); bar.appendChild(x); document.body.appendChild(bar);
    const done = () => { bar.remove(); window.TT_APP.pickObject(null); };
    x.addEventListener("click", done);
    window.TT_APP.pickObject((o) => { bar.remove(); window.TT_PHOTO.open({ obj: o.obj, name: o.name, lang: o.lang, lat: o.lat, lon: o.lon, file }); });
  }
  if (new URLSearchParams(location.search).get("share") === "1") window.addEventListener("load", () => setTimeout(startShare, 1500));
})();
