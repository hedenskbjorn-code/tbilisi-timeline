// The form "send a photo of this object" (the receiving side is worker/submit.js, the check is done by the owner in worker/admin.js). Open for every visitor when config.js says
// photoOpen: true; the link with ?club=0 hides it in this browser, ?club=1 shows it again (and is the only way to see it while photoOpen is false). The picture is re-encoded here (about 1600 px, JPEG): this removes the metadata (position, camera),
// the position of the shot is read before that and is sent only as a hint for the check.
(function () {
  "use strict";
  const cfg = window.TT_CONFIG || {};
  const LS = "ttClub";
  try {
    const q = new URLSearchParams(location.search).get("club");
    if (q === "1") localStorage.setItem(LS, "1");
    if (q === "0") localStorage.setItem(LS, "0");
  } catch (e) { /* no storage: the form stays off */ }
  const enabled = () => {
    if (!cfg.photoEndpoint) return false;
    try { const v = localStorage.getItem(LS); if (v === "0") return false; if (v === "1") return true; } catch (e) { /* no storage: the default */ }
    return !!cfg.photoOpen;
  };

  const T = {
    ru: {
      link: "📷 Прислать фото этого объекта", need: "Фото этого объекта пока нет. Если вы рядом, пришлите своё.", noPhotoL: "Объекты без фото (оранжевое кольцо): куда сходить с камерой", nearBtn: "Объекты без фото рядом со мной", nearTitle: "Объекты без фото рядом", nearHint: "Расстояние по прямой от вашего положения. Положение используется только в вашем браузере и никуда не отправляется.", nearNone: "Объектов без фото рядом не нашлось.", nearDenied: "Не удалось определить положение (разрешите доступ к геолокации в браузере).", locExifOk: (d) => "✓ Координаты в фото найдены: до объекта " + d + " м.", locExifFar: (d) => "⚠ Фото снято далеко от объекта (" + d + " м). Это точно тот объект?", locExifNone: "Координат в фото нет. Если вы рядом с объектом, добавьте геолокацию: так заявку проверить проще.", btnGeo: "📍 Добавить мою геолокацию (я рядом с объектом)", geoOk: (d, a) => "✓ Геолокация добавлена: до объекта " + d + " м (±" + a + " м).", geoFar: (d) => "⚠ По геолокации вы далеко от объекта (" + d + " м).", geoFail: "Не удалось определить положение (разрешите доступ к геолокации в браузере).", btnCam: "📷 Снять камерой", btnShot: "Снять", camFail: "Камера недоступна: выберите готовый снимок из файлов.", privGeo: "Положение (из снимка или ваше) хранится только в закрытой очереди для проверки и не публикуется.", title: "Фото объекта", object: "Объект",
      hint: "Снимайте здание снаружи, целиком, при хорошем свете; без людей и номеров машин. Фото должно быть вашим. Присланное сначала проверяет владелец сайта и может быть не опубликовано.",
      file: "Фотография (JPEG, PNG или WebP)", name: "Ваше имя или ник (будет подписано под фото)", note: "Заметка (необязательно)",
      consent: "Я автор этой фотографии и разрешаю использовать её на этом сайте на условиях CC BY-SA 4.0 с указанием моего имени.",
      privacy: "Хранятся только фото, имя и заметка (и положение снимка, если телефон его записал: оно нужно для проверки). Почта не собирается. Удалить фото: обращение на GitHub.",
      send: "Отправить", cancel: "Закрыть", sending: "Отправка…", ok: "Спасибо! Фото получено и будет проверено владельцем сайта.", dup: "Это фото уже было прислано.",
      err: { origin: "Страница не может отправить фото (адрес сайта).", closed: "Приём фото сейчас закрыт.", size: "Файл слишком большой.", form: "Не удалось прочитать форму.", time: "Слишком быстро: подождите несколько секунд и отправьте снова.",
        object: "Неизвестный объект.", consent: "Нужны имя и согласие.", links: "В имени и заметке нельзя оставлять ссылки.", image: "Нужна фотография JPEG, PNG или WebP не меньше 800 px по длинной стороне.",
        captcha: "Проверка «я не робот» не пройдена, попробуйте ещё раз.", limit: "Слишком много фото с этого устройства за сутки.", busy: "Сегодня принято слишком много фото, попробуйте завтра.", net: "Нет связи с сервером.",
        read: "Не удалось прочитать фото (возможно, формат HEIC: сделайте снимок в JPEG)." },
    },
    en: {
      link: "📷 Send a photo of this object", need: "There is no photo of this object yet. If you are nearby, send yours.", noPhotoL: "Objects without a photo (orange ring): where to go with a camera", nearBtn: "Objects without a photo near me", nearTitle: "Objects without a photo nearby", nearHint: "The distance is in a straight line from your position. The position is used only in your browser and is sent nowhere.", nearNone: "No objects without a photo were found nearby.", nearDenied: "The position could not be found (allow the access to the location in the browser).", locExifOk: (d) => "✓ The position is found in the photo: " + d + " m from the object.", locExifFar: (d) => "⚠ The photo was taken far from the object (" + d + " m). Is it really that object?", locExifNone: "There is no position in the photo. If you are near the object, add your location: it makes the check easier.", btnGeo: "📍 Add my location (I am near the object)", geoOk: (d, a) => "✓ Location added: " + d + " m from the object (±" + a + " m).", geoFar: (d) => "⚠ By your location you are far from the object (" + d + " m).", geoFail: "The position could not be found (allow the access to the location in the browser).", btnCam: "📷 Take a photo with the camera", btnShot: "Take", camFail: "The camera is not available: choose a ready photo from the files.", privGeo: "The position (from the photo or yours) is kept only in the closed queue for the check and is not published.", title: "Photo of the object", object: "Object",
      hint: "Photograph the building from outside, the whole of it, in good light; no people and no car plates. The photo must be your own. What you send is first checked by the owner of the site and may not be published.",
      file: "Photograph (JPEG, PNG or WebP)", name: "Your name or nickname (it will be signed under the photo)", note: "Note (optional)",
      consent: "I am the author of this photograph and allow its use on this site under CC BY-SA 4.0, with my name given.",
      privacy: "Only the photo, the name and the note are kept (and the position of the shot, if the phone recorded it: it is needed for the check). No e-mail is collected. To have a photo removed: an issue on GitHub.",
      send: "Send", cancel: "Close", sending: "Sending…", ok: "Thank you! The photo is received and will be checked by the owner of the site.", dup: "This photo has been sent already.",
      err: { origin: "The page cannot send the photo (address of the site).", closed: "Receiving photos is closed now.", size: "The file is too large.", form: "The form could not be read.", time: "Too fast: wait a few seconds and send again.",
        object: "Unknown object.", consent: "The name and the consent are needed.", links: "No links in the name and the note, please.", image: "A JPEG, PNG or WebP photograph of at least 800 px on the long side is needed.",
        captcha: "The \"I am not a robot\" check failed, try again.", limit: "Too many photos from this device today.", busy: "Too many photos were received today, try tomorrow.", net: "No connection with the server.",
        read: "The photo could not be read (maybe the HEIC format: take the picture as JPEG)." },
    },
    ka: {
      link: "📷 ამ ობიექტის ფოტოს გამოგზავნა", need: "ამ ობიექტის ფოტო ჯერ არ არის. თუ ახლოს ხართ, გამოგვიგზავნეთ თქვენი.", noPhotoL: "ობიექტები ფოტოს გარეშე (ნარინჯისფერი რგოლი): სად წახვიდეთ კამერით", nearBtn: "ფოტოს გარეშე ობიექტები ჩემ გვერდით", nearTitle: "ფოტოს გარეშე ობიექტები ახლოს", nearHint: "მანძილი წრფივია თქვენი მდებარეობიდან. მდებარეობა გამოიყენება მხოლოდ თქვენს ბრაუზერში და არსად იგზავნება.", nearNone: "ახლოს ფოტოს გარეშე ობიექტები ვერ მოიძებნა.", nearDenied: "მდებარეობის დადგენა ვერ მოხერხდა (ბრაუზერში მიეცით ამ საიტს გეოლოკაციაზე წვდომის ნება).", locExifOk: (d) => "✓ ფოტოში მდებარეობა ნაპოვნია: ობიექტამდე " + d + " მ.", locExifFar: (d) => "⚠ ფოტო ობიექტიდან შორს არის გადაღებული (" + d + " მ). ნამდვილად ეს ობიექტია?", locExifNone: "ფოტოში მდებარეობა არ არის. თუ ობიექტთან ახლოს ხართ, დაამატეთ თქვენი მდებარეობა: ასე შემოწმება უფრო ადვილია.", btnGeo: "📍 ჩემი მდებარეობის დამატება (ობიექტთან ახლოს ვარ)", geoOk: (d, a) => "✓ მდებარეობა დამატებულია: ობიექტამდე " + d + " მ (±" + a + " მ).", geoFar: (d) => "⚠ თქვენი მდებარეობით ობიექტიდან შორს ხართ (" + d + " მ).", geoFail: "მდებარეობის დადგენა ვერ მოხერხდა (ბრაუზერში მიეცით ამ საიტს გეოლოკაციაზე წვდომის ნება).", btnCam: "📷 კამერით გადაღება", btnShot: "გადაღება", camFail: "კამერა მიუწვდომელია: აირჩიეთ მზა ფოტო ფაილებიდან.", privGeo: "მდებარეობა (ფოტოდან ან თქვენი) ინახება მხოლოდ დახურულ რიგში შემოწმებისთვის და არ ქვეყნდება.", title: "ობიექტის ფოტო", object: "ობიექტი",
      hint: "გადაუღეთ შენობა გარედან, მთლიანად, კარგ განათებაზე; ადამიანებისა და მანქანის ნომრების გარეშე. ფოტო თქვენი უნდა იყოს. გამოგზავნილს ჯერ საიტის მფლობელი შეამოწმებს და შეიძლება არ გამოქვეყნდეს.",
      file: "ფოტო (JPEG, PNG ან WebP)", name: "თქვენი სახელი ან მეტსახელი (ფოტოს ქვეშ მიეწერება)", note: "შენიშვნა (სურვილისამებრ)",
      consent: "ვარ ამ ფოტოს ავტორი და ვაძლევ ნებართვას გამოვიყენოთ ეს საიტზე CC BY-SA 4.0-ის პირობებით, ჩემი სახელის მითითებით.",
      privacy: "ინახება მხოლოდ ფოტო, სახელი და შენიშვნა (და კადრის ადგილი, თუ ტელეფონმა ჩაწერა: ის შემოწმებისთვის გვჭირდება). ელფოსტა არ გროვდება. ფოტოს წასაშლელად: GitHub-ზე მიმართვა.",
      send: "გაგზავნა", cancel: "დახურვა", sending: "იგზავნება…", ok: "გმადლობთ! ფოტო მიღებულია და საიტის მფლობელი შეამოწმებს.", dup: "ეს ფოტო უკვე გამოგზავნილია.",
      err: { origin: "გვერდს ფოტოს გაგზავნა არ შეუძლია (საიტის მისამართი).", closed: "ფოტოების მიღება ახლა დახურულია.", size: "ფაილი ძალიან დიდია.", form: "ფორმის წაკითხვა ვერ მოხერხდა.", time: "ძალიან სწრაფად: მოიცადეთ რამდენიმე წამი და ხელახლა გაგზავნეთ.",
        object: "უცნობი ობიექტი.", consent: "საჭიროა სახელი და თანხმობა.", links: "სახელსა და შენიშვნაში ბმულები არ შეიძლება.", image: "საჭიროა JPEG, PNG ან WebP ფოტო, გრძელ მხარეზე მინიმუმ 800 პიქსელი.",
        captcha: "შემოწმება „მე არ ვარ რობოტი“ ვერ გაიარა, სცადეთ ხელახლა.", limit: "ამ მოწყობილობიდან დღეს ძალიან ბევრი ფოტო გამოიგზავნა.", busy: "დღეს ძალიან ბევრი ფოტო მიიღეს, სცადეთ ხვალ.", net: "სერვერთან კავშირი არ არის.",
        read: "ფოტოს წაკითხვა ვერ მოხერხდა (შესაძლოა HEIC ფორმატია: გადაიღეთ JPEG-ში)." },
    },
  };

  // the position of the shot from the EXIF of a JPEG: {lat, lon} or null
  function exifGps(buf) {
    const dv = new DataView(buf);
    if (dv.byteLength < 12 || dv.getUint16(0) !== 0xffd8) return null;
    let o = 2;
    while (o + 4 < dv.byteLength) {
      const m = dv.getUint16(o), len = dv.getUint16(o + 2);
      if (m === 0xffe1 && dv.getUint32(o + 4) === 0x45786966) return readTiff(dv, o + 10);
      if ((m & 0xff00) !== 0xff00 || len < 2) return null;
      o += 2 + len;
    }
    return null;
  }
  function readTiff(dv, base) {
    const le = dv.getUint16(base) === 0x4949, u16 = (p) => dv.getUint16(base + p, le), u32 = (p) => dv.getUint32(base + p, le);
    const ifd = (p) => { const n = u16(p), out = {}; for (let i = 0; i < n; i++) { const e = p + 2 + i * 12; out[u16(e)] = { type: u16(e + 2), count: u32(e + 4), at: e + 8 }; } return out; };
    const i0 = ifd(u32(4));
    if (!i0[0x8825]) return null;
    const g = ifd(u32(i0[0x8825].at));
    const rat = (t) => { if (!t) return null; const p = u32(t.at), v = []; for (let i = 0; i < 3; i++) v.push(u32(p + i * 8) / (u32(p + i * 8 + 4) || 1)); return v[0] + v[1] / 60 + v[2] / 3600; };
    const ref = (t) => (t ? String.fromCharCode(dv.getUint8(base + t.at)) : "");
    const la = rat(g[2]), lo = rat(g[4]);
    if (la === null || lo === null || !isFinite(la) || !isFinite(lo)) return null;
    return { lat: ref(g[1]) === "S" ? -la : la, lon: ref(g[3]) === "W" ? -lo : lo };
  }

  let modal = null, state = null, tsId = null, tsToken = "";
  function loadTurnstile() {
    return new Promise((res) => {
      if (window.turnstile) return res();
      const s = document.createElement("script");
      s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      s.async = true; s.onload = () => res(); s.onerror = () => res();
      document.head.appendChild(s);
    });
  }
  const mk = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };

  function build() {
    const m = mk("div", "modal"), f = mk("form", "modalbox");
    m.hidden = true; f.autocomplete = "off"; f.id = "phForm";
    m.setAttribute("role", "dialog"); m.setAttribute("aria-modal", "true"); m.setAttribute("aria-labelledby", "phTitle");
    f.innerHTML = '<h2 id="phTitle"></h2><div class="small" id="phObj"></div><p class="small" id="phHint"></p>' +
      '<label><span id="phFileL"></span><input id="phFile" type="file" accept="image/jpeg,image/png,image/webp"></label>' +
      '<div class="modalbtns" style="justify-content:flex-start;gap:8px;margin-top:8px"><button type="button" id="phCam" class="chip"></button><button type="button" id="phGeo" class="chip"></button></div>' +
      '<video id="phVid" playsinline muted hidden style="width:100%;max-height:260px;margin-top:6px;border-radius:6px;background:#000"></video><button type="button" id="phShot" class="chip primary" hidden></button>' +
      '<img id="phPrev" alt="" hidden style="max-width:100%;max-height:200px;margin-top:6px;border-radius:6px"><div class="small" id="phLoc" aria-live="polite"></div>' +
      '<label><span id="phNameL"></span><input id="phName" type="text" maxlength="60" required></label>' +
      '<label><span id="phNoteL"></span><input id="phNote" type="text" maxlength="300"></label>' +
      '<label style="display:flex;gap:8px;align-items:flex-start;color:inherit"><input id="phCons" type="checkbox" required style="margin-top:3px"><span id="phConsT"></span></label>' +
      '<input id="phHp" type="text" tabindex="-1" autocomplete="off" aria-hidden="true" class="trap"><div id="phTs" style="margin-top:8px"></div>' +
      '<p class="small" id="phPriv"></p><div class="modalbtns"><button type="button" id="phCancel" class="chip"></button><button type="submit" id="phSend" class="chip primary"></button></div><p id="phStatus" class="small" aria-live="polite"></p>';
    document.body.appendChild(m);
    m.addEventListener("click", (e) => { if (e.target === m) close(); });
    f.querySelector("#phCancel").addEventListener("click", close);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !m.hidden) close(); });
    f.querySelector("#phFile").addEventListener("change", onFile);
    f.querySelector("#phGeo").addEventListener("click", addGeo);
    f.querySelector("#phCam").addEventListener("click", openCamera);
    f.querySelector("#phShot").addEventListener("click", shoot);
    f.addEventListener("submit", send);
    m.appendChild(f);
    return m;
  }
  const q = (id) => modal.querySelector("#" + id);
  function labels() {
    const L = T[state.lang] || T.en;
    q("phTitle").textContent = L.title; q("phObj").textContent = L.object + ": " + state.name; q("phHint").textContent = L.hint;
    q("phFileL").textContent = L.file; q("phNameL").textContent = L.name; q("phNoteL").textContent = L.note; q("phConsT").textContent = L.consent;
    q("phCancel").textContent = L.cancel; q("phSend").textContent = L.send; q("phCam").textContent = L.btnCam; q("phGeo").textContent = L.btnGeo; q("phShot").textContent = L.btnShot;
    q("phCam").hidden = !(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    const p = q("phPriv"); p.textContent = L.privacy + " " + L.privGeo + " ";
    const a = mk("a", "", "GitHub"); a.href = "https://github.com/" + (cfg.repo || "") + "/issues"; a.target = "_blank"; a.rel = "noopener"; p.appendChild(a);
  }
  async function open(o) {
    if (!enabled()) return;
    state = { obj: o.obj, name: o.name || o.obj, lang: o.lang || "en", opened: Date.now(), blob: null, gps: null, geo: null, oc: isFinite(o.lat) && isFinite(o.lon) ? { lat: +o.lat, lon: +o.lon } : null };
    if (!modal) modal = build();
    stopCamera(); modal.querySelector("#phForm").reset(); q("phPrev").hidden = true; q("phStatus").textContent = ""; q("phLoc").textContent = ""; q("phSend").disabled = false;
    labels(); modal.hidden = false; tsToken = "";
    if (o.file) processFile(o.file);                                               // a photo shared from the phone arrives already chosen
    await loadTurnstile();
    if (window.turnstile && cfg.turnstileSitekey) {
      if (tsId !== null) { try { window.turnstile.remove(tsId); } catch (e) {} }
      q("phTs").textContent = "";
      tsId = window.turnstile.render(q("phTs"), { sitekey: cfg.turnstileSitekey, theme: "auto", callback: (t) => { tsToken = t; }, "expired-callback": () => { tsToken = ""; }, "error-callback": () => { tsToken = ""; } });
    }
  }
  function close() { stopCamera(); if (prevUrl) { URL.revokeObjectURL(prevUrl); prevUrl = null; } if (modal) modal.hidden = true; }

  // the distance in metres from the position to the object (null when the position of the object is not known)
  const dist = (la, lo) => { if (!state.oc) return null; const k = Math.cos(la * Math.PI / 180); return Math.round(Math.hypot((lo - state.oc.lon) * k * 111320, (la - state.oc.lat) * 111320)); };
  function showLoc() {
    const L = T[state.lang] || T.en, box = q("phLoc");
    box.textContent = "";
    const line = (txt, bad) => { const d = mk("div", "", txt); d.style.color = bad ? "#f76707" : "#2b8a3e"; d.style.marginTop = "4px"; box.appendChild(d); };
    if (state.blob || state.gps) {
      if (state.gps) { const d = dist(state.gps.lat, state.gps.lon); if (d === null) line("✓ " + L.locExifNone.slice(0, 0) + "GPS", false); else line(d <= 150 ? L.locExifOk(d) : L.locExifFar(d), d > 150); }
      else if (!state.geo) { const d = mk("div", "", L.locExifNone); d.style.marginTop = "4px"; box.appendChild(d); }
    }
    if (state.geo) { const d = dist(state.geo.lat, state.geo.lon); line(d === null ? "✓" : d <= 150 ? L.geoOk(d, Math.round(state.geo.acc || 0)) : L.geoFar(d), d !== null && d > 150); }
  }
  function getPosition() {
    return new Promise((res) => {
      if (!navigator.geolocation) return res(null);
      navigator.geolocation.getCurrentPosition((g) => res({ lat: g.coords.latitude, lon: g.coords.longitude, acc: g.coords.accuracy }), () => res(null), { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 });
    });
  }
  async function addGeo() {
    const L = T[state.lang] || T.en;
    q("phStatus").textContent = "";
    const g = await getPosition();
    if (!g) { q("phStatus").textContent = L.geoFail; return; }
    state.geo = g; showLoc();
  }

  // a photograph taken with the camera inside the form: the position is asked at the same moment, so it does not depend on what the phone writes into the file
  let stream = null, camPos = null;
  function stopCamera() { if (stream) { stream.getTracks().forEach((t) => t.stop()); stream = null; } if (modal) { q("phVid").hidden = true; q("phShot").hidden = true; } }
  async function openCamera() {
    const L = T[state.lang] || T.en;
    q("phStatus").textContent = "";
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 } }, audio: false });
    } catch (e) { q("phStatus").textContent = L.camFail; return; }
    const v = q("phVid"); v.srcObject = stream; v.hidden = false; q("phShot").hidden = false; await v.play().catch(() => {});
    getPosition().then((g) => { camPos = g; });                                  // asked while the camera is open
  }
  async function shoot() {
    const L = T[state.lang] || T.en, v = q("phVid");
    if (!v.videoWidth) return;
    const k = Math.min(1, 1600 / Math.max(v.videoWidth, v.videoHeight)), w = Math.round(v.videoWidth * k), h = Math.round(v.videoHeight * k);
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    c.getContext("2d").drawImage(v, 0, 0, w, h);
    const blob = await new Promise((r) => c.toBlob(r, "image/jpeg", 0.85));
    stopCamera();
    if (!blob || Math.max(w, h) < 800) { q("phStatus").textContent = L.err.image; return; }
    state.blob = blob; state.gps = null;
    showPrev(blob);
    const g = camPos || (await getPosition());
    if (g) state.geo = g;
    showLoc();
  }

  let prevUrl = null;
  function showPrev(blob) { if (prevUrl) URL.revokeObjectURL(prevUrl); prevUrl = URL.createObjectURL(blob); q("phPrev").src = prevUrl; q("phPrev").hidden = false; }
  const onFile = (e) => processFile(e.target.files && e.target.files[0]);
  async function processFile(file) {
    const L = T[state.lang] || T.en, st = q("phStatus");
    state.blob = null; state.gps = null; q("phPrev").hidden = true; st.textContent = "";
    if (!file) return;
    try {
      const buf = await file.arrayBuffer();
      try { state.gps = exifGps(buf); } catch (e) { state.gps = null; }        // read before the re-encoding removes it
      const bmp = await createImageBitmap(new Blob([buf], { type: file.type }), { imageOrientation: "from-image" });
      const k = Math.min(1, 1600 / Math.max(bmp.width, bmp.height)), w = Math.round(bmp.width * k), h = Math.round(bmp.height * k);
      if (Math.max(w, h) < 800) { st.textContent = L.err.image; return; }
      const c = document.createElement("canvas"); c.width = w; c.height = h;
      c.getContext("2d").drawImage(bmp, 0, 0, w, h);
      const blob = await new Promise((r) => c.toBlob(r, "image/jpeg", 0.85));
      if (!blob || blob.size > 3 * 1024 * 1024) { st.textContent = L.err.size; return; }
      state.blob = blob;
      showPrev(blob);
      showLoc();
    } catch (err) { st.textContent = L.err.read; }
  }

  async function send(e) {
    e.preventDefault();
    const L = T[state.lang] || T.en, st = q("phStatus"), btn = q("phSend");
    if (!state.blob) { st.textContent = L.err.read; return; }               // (the file field is no longer required: a photograph can also come from the camera)
    if (!tsToken) { st.textContent = L.err.captcha; return; }
    const fd = new FormData();
    fd.append("obj", state.obj); fd.append("name", q("phName").value); fd.append("note", q("phNote").value); fd.append("consent", q("phCons").checked ? "1" : "");
    fd.append("t", String(state.opened)); fd.append("hp", q("phHp").value); fd.append("cf-turnstile-response", tsToken);
    if (state.gps) { fd.append("lat", String(state.gps.lat)); fd.append("lon", String(state.gps.lon)); }
    if (state.geo) { fd.append("glat", String(state.geo.lat)); fd.append("glon", String(state.geo.lon)); fd.append("gacc", String(Math.round(state.geo.acc || 0))); }
    fd.append("photo", state.blob, "photo.jpg");
    btn.disabled = true; st.textContent = L.sending;
    try {
      const r = await fetch(cfg.photoEndpoint, { method: "POST", body: fd }), j = await r.json().catch(() => ({}));
      if (j.ok) { st.textContent = j.dup ? L.dup : L.ok; q("phForm").reset(); q("phPrev").hidden = true; state.blob = null; return; }
      st.textContent = (L.err[j.error] || L.err.net); btn.disabled = false;
      if (window.turnstile && tsId !== null) { try { window.turnstile.reset(tsId); } catch (x) {} tsToken = ""; }
    } catch (err) { st.textContent = L.err.net; btn.disabled = false; }
  }

  window.TT_PHOTO = { enabled, open, text: (lang) => (T[lang] || T.en).link, s: (lang) => T[lang] || T.en, _exifGps: exifGps, _state: () => state };           // _ : for the tests
})();
