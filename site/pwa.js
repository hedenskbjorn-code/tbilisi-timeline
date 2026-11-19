// The installable application: registers the service worker, offers "Install" and takes a photo shared from the phone's share menu:
// the photo waits in the cache of the service worker; the visitor taps the object on the map and the form opens with the photo already in it.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const TXT = {
    ru: { install: "📲 Установить приложение", pick: "Фото получено. Нажмите на объект на карте, к которому оно относится.", cancel: "Отмена", iosTitle: "Установка на iPhone", ios: ["1. Откройте сайт в Safari.", "2. Нажмите «Поделиться» (квадрат со стрелкой вверх).", "3. Выберите «На экран Домой».", "Приём фото из меню «Поделиться» на iPhone недоступен: фото можно снять или выбрать в самой форме."] },
    en: { install: "📲 Install the app", pick: "The photo is received. Tap the object on the map that it belongs to.", cancel: "Cancel", iosTitle: "Installing on iPhone", ios: ["1. Open the site in Safari.", "2. Tap \"Share\" (the square with an arrow up).", "3. Choose \"Add to Home Screen\".", "Receiving a photo from the Share menu is not available on iPhone: take a photo or choose one in the form itself."] },
    ka: { install: "📲 აპლიკაციის დაყენება", pick: "ფოტო მიღებულია. დააწკაპუნეთ რუკაზე ობიექტზე, რომელსაც ეკუთვნის.", cancel: "გაუქმება", iosTitle: "iPhone-ზე დაყენება", ios: ["1. გახსენით საიტი Safari-ში.", "2. დააჭირეთ „გაზიარება“ (კვადრატი ისრით ზემოთ).", "3. აირჩიეთ „საწყის ეკრანზე დამატება“.", "iPhone-ზე ფოტოს მიღება მენიუდან „გაზიარება“ მიუწვდომელია: ფოტო გადაიღეთ ან აირჩიეთ თვით ფორმაში."] },
  };
  const lang = () => { const l = (document.documentElement.lang || "en").slice(0, 2); return TXT[l] ? l : "en"; };
  const S = () => TXT[lang()];

  if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(() => {}));      // works on https and on localhost only

  // "Install" button: shown in the filters panel only when the browser says the site can be installed
  let deferred = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault(); deferred = e;
    const b = $("btnInstall");
    if (b) { b.title = S().install; b.setAttribute("aria-label", S().install); b.hidden = false; }
  });
  window.addEventListener("appinstalled", () => { deferred = null; const b = $("btnInstall"); if (b) b.hidden = true; });
  // iPhone and iPad: Safari has no install prompt (no "beforeinstallprompt"), so the same button shows the steps of "Add to Home Screen"
  const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const standalone = navigator.standalone === true || (window.matchMedia && matchMedia("(display-mode: standalone)").matches);
  function showIosHint() {
    if (!window.TT_APP || !window.TT_APP.info) return;
    window.TT_APP.info(S().iosTitle, S().ios);
  }
  document.addEventListener("DOMContentLoaded", () => {
    const b = $("btnInstall");
    if (b && isIos && !standalone) { b.title = S().iosTitle; b.setAttribute("aria-label", S().iosTitle); b.hidden = false; }
  });
  window.TT_PWA = { install: async () => { if (!deferred) { if (isIos && !standalone) showIosHint(); return; } deferred.prompt(); try { await deferred.userChoice; } catch (e) {} deferred = null; const b = $("btnInstall"); if (b) b.hidden = true; }, retext: () => { const b = $("btnInstall"); if (b) { const x = deferred || !(isIos && !standalone) ? S().install : S().iosTitle; b.title = x; b.setAttribute("aria-label", x); } } };
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
  else if (window.caches) caches.delete("tt-share").catch(() => {});                  // a shared photo nobody picked up is not kept
})();
