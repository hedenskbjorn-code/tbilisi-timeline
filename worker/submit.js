// Worker "tbilisi-photos": receives photographs of objects from visitors of the site. Nothing sent here is public: every file waits in a private queue (KV) until the owner looks
// at it in the admin page (worker/admin.js). Defences, in the order they are applied:
//   origin of the page, kill switch, size, honeypot and the time the form was open, Cloudflare Turnstile, per-visitor and total daily limits, the content of the file
//   (magic bytes and the real width and height, no other types, no SVG), a text filter, a duplicate check by the hash of the file.
// Settings: binding PHOTOS (KV), secrets TURNSTILE_SECRET and HASH_SALT. KV key "cfg:open" = "0" closes the form.
const ORIGIN = "https://hedenskbjorn-code.github.io";
const MAX_BYTES = 3 * 1024 * 1024;          // the page re-encodes the picture to about 1600 px (a few hundred KB), so this is generous
const MIN_SIDE = 800, MAX_SIDE = 8000;
const PER_IP_DAY = 5, GLOBAL_DAY = 40;
const MIN_FORM_MS = 4000, MAX_FORM_MS = 3 * 3600 * 1000;
const PENDING_TTL = 60 * 86400;             // a picture nobody looked at is removed after 60 days
const OBJ_RE = /^[a-z]{1,8}:[A-Za-z0-9_.\-]{1,40}$/;
const BBOX = { lat: [41.55, 41.90], lon: [44.60, 45.05] };          // Tbilisi: a coordinate outside is dropped

const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
const sha256 = async (data) => hex(await crypto.subtle.digest("SHA-256", data));
const clean = (s, n) => String(s || "").replace(/[\u0000-\u001f\u007f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, n);

function cors(origin) {
  return { "Access-Control-Allow-Origin": origin === ORIGIN ? ORIGIN : "null", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400", Vary: "Origin" };
}
function reply(body, status, origin) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...cors(origin) } });
}

// type and size of a picture from the file itself (JPEG, PNG, WebP); null when it is not one of them
function imageInfo(u8) {
  if (u8.length > 30 && u8[0] === 0xff && u8[1] === 0xd8 && u8[2] === 0xff) {
    let i = 2;
    while (i < u8.length - 9) {
      if (u8[i] !== 0xff) { i++; continue; }
      const m = u8[i + 1];
      if (m === 0xff) { i++; continue; }
      if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) return { type: "image/jpeg", h: (u8[i + 5] << 8) | u8[i + 6], w: (u8[i + 7] << 8) | u8[i + 8] };
      i += 2 + ((u8[i + 2] << 8) | u8[i + 3]);
    }
    return null;
  }
  if (u8.length > 30 && u8[0] === 0x89 && u8[1] === 0x50 && u8[2] === 0x4e && u8[3] === 0x47) {
    const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
    return { type: "image/png", w: dv.getUint32(16), h: dv.getUint32(20) };
  }
  const tag = (o, s) => String.fromCharCode(u8[o], u8[o + 1], u8[o + 2], u8[o + 3]) === s;
  if (u8.length > 40 && tag(0, "RIFF") && tag(8, "WEBP")) {
    if (tag(12, "VP8 ")) return { type: "image/webp", w: (u8[26] | (u8[27] << 8)) & 0x3fff, h: (u8[28] | (u8[29] << 8)) & 0x3fff };
    if (tag(12, "VP8L")) return { type: "image/webp", w: 1 + (((u8[22] & 0x3f) << 8) | u8[21]), h: 1 + (((u8[24] & 0x0f) << 10) | (u8[23] << 2) | ((u8[22] & 0xc0) >> 6)) };
    if (tag(12, "VP8X")) return { type: "image/webp", w: 1 + (u8[24] | (u8[25] << 8) | (u8[26] << 16)), h: 1 + (u8[27] | (u8[28] << 8) | (u8[29] << 16)) };
  }
  return null;
}

async function turnstileOk(env, token, ip) {
  if (!token) return false;
  const body = new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: String(token).slice(0, 2048) });
  if (ip) body.set("remoteip", ip);
  try {
    const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body });
    return (await r.json()).success === true;
  } catch (e) { return false; }
}

async function bump(env, key, limit) {
  const cur = parseInt(await env.PHOTOS.get(key), 10) || 0;
  if (cur >= limit) return false;
  await env.PHOTOS.put(key, String(cur + 1), { expirationTtl: 172800 });
  return true;
}

const num = (v, lo, hi) => { const x = parseFloat(v); return Number.isFinite(x) && x >= lo && x <= hi ? Math.round(x * 1e6) / 1e6 : null; };

export default {
  async fetch(req, env) {
    const url = new URL(req.url), origin = req.headers.get("Origin") || "";
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (url.pathname === "/health") return reply({ ok: true, open: (await env.PHOTOS.get("cfg:open")) !== "0" }, 200, origin);
    if (url.pathname !== "/submit" || req.method !== "POST") return reply({ ok: false, error: "not_found" }, 404, origin);
    if (origin !== ORIGIN) return reply({ ok: false, error: "origin" }, 403, origin);
    if ((await env.PHOTOS.get("cfg:open")) === "0") return reply({ ok: false, error: "closed" }, 503, origin);
    const len = parseInt(req.headers.get("Content-Length") || "0", 10);
    if (!len || len > MAX_BYTES + 60000) return reply({ ok: false, error: "size" }, 413, origin);
    let fd;
    try { fd = await req.formData(); } catch (e) { return reply({ ok: false, error: "form" }, 400, origin); }
    if (String(fd.get("hp") || "")) return reply({ ok: true, id: "x" }, 200, origin);              // a bot filled the hidden field: it is told "ok" and nothing is kept
    const open = parseInt(fd.get("t"), 10), spent = Date.now() - open;
    if (!(spent >= MIN_FORM_MS && spent <= MAX_FORM_MS)) return reply({ ok: false, error: "time" }, 400, origin);
    const obj = String(fd.get("obj") || "");
    if (!OBJ_RE.test(obj)) return reply({ ok: false, error: "object" }, 400, origin);
    const name = clean(fd.get("name"), 60), note = clean(fd.get("note"), 300);
    if (!name || fd.get("consent") !== "1") return reply({ ok: false, error: "consent" }, 400, origin);
    if (/https?:|www\.|@[a-z0-9]/i.test(name + " " + note)) return reply({ ok: false, error: "links" }, 400, origin);
    const file = fd.get("photo");
    if (!file || typeof file === "string" || !file.size || file.size > MAX_BYTES) return reply({ ok: false, error: "size" }, 413, origin);
    const bytes = new Uint8Array(await file.arrayBuffer());
    const info = imageInfo(bytes);
    if (!info || !info.w || !info.h || Math.max(info.w, info.h) < MIN_SIDE || Math.max(info.w, info.h) > MAX_SIDE) return reply({ ok: false, error: "image" }, 400, origin);
    const ip = req.headers.get("CF-Connecting-IP") || "";
    if (!(await turnstileOk(env, fd.get("cf-turnstile-response"), ip))) return reply({ ok: false, error: "captcha" }, 403, origin);
    const day = new Date().toISOString().slice(0, 10);
    const ipH = (await sha256(new TextEncoder().encode(env.HASH_SALT + "|" + ip))).slice(0, 16);
    if (!(await bump(env, "rl:" + day + ":" + ipH, PER_IP_DAY))) return reply({ ok: false, error: "limit" }, 429, origin);
    if (!(await bump(env, "rl:" + day + ":all", GLOBAL_DAY))) return reply({ ok: false, error: "busy" }, 429, origin);
    const hash = await sha256(bytes);
    if (await env.PHOTOS.get("h:" + hash)) return reply({ ok: true, dup: true }, 200, origin);
    const ts = Date.now(), rnd = hex(crypto.getRandomValues(new Uint8Array(3))), id = ts.toString(36) + rnd;
    const lat = num(fd.get("lat"), BBOX.lat[0], BBOX.lat[1]), lon = num(fd.get("lon"), BBOX.lon[0], BBOX.lon[1]);
    const meta = { id, obj, name, note, lat: lat !== null && lon !== null ? lat : null, lon: lat !== null && lon !== null ? lon : null, ts, mime: info.type, w: info.w, h: info.h, size: bytes.length, hash, ipH, status: "pending", license: "CC BY-SA 4.0" };
    await env.PHOTOS.put("img:" + id, bytes, { expirationTtl: PENDING_TTL });
    await env.PHOTOS.put("h:" + hash, id, { expirationTtl: PENDING_TTL });
    await env.PHOTOS.put("meta:" + id, JSON.stringify(meta), { expirationTtl: PENDING_TTL, metadata: { s: "pending", o: obj, t: ts, w: info.w, h: info.h, n: name.slice(0, 30) } });
    return reply({ ok: true, id }, 200, origin);
  },
};
