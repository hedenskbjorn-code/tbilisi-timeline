// Worker "tbilisi-photos-admin": the page where the owner looks at the photographs that visitors sent and reads their messages (queues in the KV of worker/submit.js).
// It is closed twice: Cloudflare Access (the policy allows only the owner) and, as a second lock, this Worker checks the signed header of Access itself (signature, issuer,
// audience, expiry, the e-mail), so that a mistake in the settings of Access cannot open the page. Settings: binding PHOTOS (KV), variables TEAM_DOMAIN, POLICY_AUD, secret ADMIN_EMAILS
// (e-mails of the moderators, comma separated).
const SITE = "https://hedenskbjorn-code.github.io/tbilisi-timeline/";
const b64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
const json = (o, st = 200) => new Response(JSON.stringify(o), { status: st, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });

let jwks = null, jwksAt = 0;
async function keys(env) {
  if (jwks && Date.now() - jwksAt < 3600e3) return jwks;
  const r = await fetch("https://" + env.TEAM_DOMAIN + "/cdn-cgi/access/certs");
  jwks = await r.json(); jwksAt = Date.now();
  return jwks;
}
async function who(req, env) {
  const jwt = req.headers.get("Cf-Access-Jwt-Assertion");
  if (!jwt) return null;
  try {
    const [h, p, s] = jwt.split(".");
    const header = JSON.parse(new TextDecoder().decode(b64u(h))), pl = JSON.parse(new TextDecoder().decode(b64u(p))), now = Date.now() / 1000;
    if (header.alg !== "RS256" || !(pl.exp > now) || (pl.nbf && pl.nbf > now + 60) || pl.iss !== "https://" + env.TEAM_DOMAIN) return null;
    if (!(Array.isArray(pl.aud) ? pl.aud : [pl.aud]).includes(env.POLICY_AUD)) return null;
    const jwk = (await keys(env)).keys.find((k) => k.kid === header.kid);
    if (!jwk) return null;
    const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    if (!(await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64u(s), new TextEncoder().encode(h + "." + p)))) return null;
    const mail = String(pl.email || "").toLowerCase();
    return String(env.ADMIN_EMAILS || "").toLowerCase().split(",").map((x) => x.trim()).includes(mail) ? mail : null;
  } catch (e) { return null; }
}

async function listAll(env) {
  const out = [];
  let cursor;
  do {
    const r = await env.PHOTOS.list({ prefix: "meta:", cursor, limit: 1000 });
    for (const k of r.keys) out.push({ id: k.name.slice(5), ...(k.metadata || {}) });
    cursor = r.list_complete ? null : r.cursor;
  } while (cursor);
  return out.sort((a, b) => (b.v || 0) - (a.v || 0) || (b.t || 0) - (a.t || 0));          // the photographs with a confirmed position come first
}

async function act(env, body, mail) {
  if (!body || typeof body !== "object") return json({ error: "json" }, 400);
  const id = String(body.id || "");
  if (!/^[a-z0-9]{6,20}$/.test(id)) return json({ error: "id" }, 400);
  const raw = await env.PHOTOS.get("meta:" + id);
  if (!raw) return json({ error: "gone" }, 404);
  const m = JSON.parse(raw);
  const small = (s) => ({ s, o: m.obj, t: m.ts, w: m.w, h: m.h, n: (m.name || "").slice(0, 30), v: m.v || 0 });
  if (body.action === "approve") {
    const img = await env.PHOTOS.get("img:" + id, { type: "arrayBuffer" });
    if (!img) return json({ error: "no image" }, 404);
    m.status = "approved"; m.by = mail; m.at = Date.now();
    delete m.lat; delete m.lon; delete m.glat; delete m.glon; delete m.ipH;       // after the check the exact positions and the hash of the address are not needed: the distances and the flag stay
    await env.PHOTOS.put("img:" + id, img);                                       // without an expiry: it stays until it is imported into the site
    await env.PHOTOS.put("h:" + m.hash, id);
    await env.PHOTOS.put("meta:" + id, JSON.stringify(m), { metadata: small("approved") });
  } else if (body.action === "reject") {
    m.status = "rejected"; m.reason = String(body.reason || "").slice(0, 80); m.by = mail; m.at = Date.now();
    await env.PHOTOS.delete("img:" + id);
    if (m.hash) await env.PHOTOS.delete("h:" + m.hash);
    await env.PHOTOS.put("meta:" + id, JSON.stringify(m), { expirationTtl: 30 * 86400, metadata: small("rejected") });
  } else if (body.action === "reassign") {
    const o = String(body.obj || "");
    if (!/^[a-z]{1,8}:[A-Za-z0-9_.\-]{1,40}$/.test(o)) return json({ error: "object" }, 400);
    m.obj = o; m.reassigned = true;
    await env.PHOTOS.put("meta:" + id, JSON.stringify(m), { expirationTtl: 60 * 86400, metadata: small(m.status) });
  } else return json({ error: "action" }, 400);
  return json({ ok: true });
}

async function listFb(env) {
  const out = [];
  let cursor;
  do {
    const r = await env.PHOTOS.list({ prefix: "fb:", cursor, limit: 1000 });
    for (const k of r.keys) out.push({ id: k.name.slice(3), ...(k.metadata || {}) });
    cursor = r.list_complete ? null : r.cursor;
  } while (cursor);
  return out.sort((a, b) => (b.t || 0) - (a.t || 0));
}

async function fbAct(env, body, mail) {
  if (!body || typeof body !== "object") return json({ error: "json" }, 400);
  const id = String(body.id || "");
  if (!/^[a-z0-9]{6,20}$/.test(id)) return json({ error: "id" }, 400);
  const raw = await env.PHOTOS.get("fb:" + id);
  if (!raw) return json({ error: "gone" }, 404);
  const m = JSON.parse(raw);
  const small = (s) => ({ s, k: m.kind, t: m.ts, n: (m.message || "").slice(0, 80) });
  if (body.action === "done") {
    m.status = "done"; m.by = mail; m.at = Date.now(); delete m.ipH;                      // the hash of the address is not needed after the owner has read the message
    await env.PHOTOS.put("fb:" + id, JSON.stringify(m), { expirationTtl: 90 * 86400, metadata: small("done") });
  } else if (body.action === "reopen") {
    m.status = "new"; delete m.by; delete m.at;
    await env.PHOTOS.put("fb:" + id, JSON.stringify(m), { expirationTtl: 180 * 86400, metadata: small("new") });
  } else if (body.action === "delete") {
    await env.PHOTOS.delete("fb:" + id);
  } else return json({ error: "action" }, 400);
  return json({ ok: true });
}

export default {
  async fetch(req, env) {
    const mail = await who(req, env);
    if (!mail) return new Response("Forbidden", { status: 403 });
    const url = new URL(req.url);
    if (url.pathname === "/api/list") return json(await listAll(env));
    if (url.pathname === "/api/fb/list") return json(await listFb(env));
    if (url.pathname.startsWith("/api/fb/get/")) {
      const r = await env.PHOTOS.get("fb:" + url.pathname.slice(12));
      if (!r) return json({ error: "gone" }, 404);
      const o = JSON.parse(r);
      delete o.ipH;                                                                              // the page of the owner never shows the hash of the address
      return json(o);
    }
    if (url.pathname === "/api/fb/act" && req.method === "POST" && req.headers.get("X-Admin") === "1") return fbAct(env, await req.json().catch(() => null), mail);
    if (url.pathname.startsWith("/api/meta/")) { const r = await env.PHOTOS.get("meta:" + url.pathname.slice(10)); return r ? new Response(r, { headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } }) : json({ error: "gone" }, 404); }
    if (url.pathname.startsWith("/api/img/")) {
      const id = url.pathname.slice(9), raw = await env.PHOTOS.get("meta:" + id), img = raw && (await env.PHOTOS.get("img:" + id, { type: "arrayBuffer" }));
      if (!img) return new Response("gone", { status: 404 });
      return new Response(img, { headers: { "Content-Type": JSON.parse(raw).mime, "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" } });
    }
    if (url.pathname === "/api/act" && req.method === "POST" && req.headers.get("X-Admin") === "1") return act(env, await req.json().catch(() => null), mail);
    if (url.pathname === "/api/open" && req.method === "POST" && req.headers.get("X-Admin") === "1") {              // the switch of the form: {open: true|false}
      const b = await req.json().catch(() => null);
      if (!b) return json({ error: "json" }, 400);
      await env.PHOTOS.put("cfg:open", b.open ? "1" : "0");
      return json({ ok: true, open: !!b.open });
    }
    if (url.pathname === "/api/open") return json({ open: (await env.PHOTOS.get("cfg:open")) !== "0" });
    if (url.pathname !== "/") return new Response("Not found", { status: 404 });
    const nonce = btoa(String.fromCharCode(...crypto.getRandomValues(new Uint8Array(12))));
    return new Response(PAGE.replaceAll("__NONCE__", nonce).replace("__SITE__", SITE).replace("__MAIL__", mail), { headers: {
      "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
      "Content-Security-Policy": "default-src 'none'; img-src 'self' https://thumb.wikimedia.org https://upload.wikimedia.org https://hedenskbjorn-code.github.io; script-src 'nonce-" + nonce + "'; style-src 'nonce-" + nonce + "'; connect-src 'self' https://hedenskbjorn-code.github.io; base-uri 'none'; form-action 'none'; frame-ancestors 'none'" } });
  },
};

const PAGE = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Фото от посетителей: проверка</title>
<style nonce="__NONCE__">
body{font:15px/1.45 system-ui,sans-serif;margin:0;background:#17181b;color:#ece8e1}header{display:flex;gap:12px;align-items:center;padding:10px 16px;background:#1d1f23;position:sticky;top:0;z-index:5;flex-wrap:wrap}
header b{font-size:16px}.sp{flex:1}button,select,input{font:inherit;padding:6px 10px;border-radius:8px;border:1px solid #fff3;background:#2a2c31;color:inherit;cursor:pointer}button.ok{background:#2b8a3e}button.no{background:#c92a2a}
.tab.on{outline:2px solid #e0735c}main{padding:14px 16px;display:flex;flex-direction:column;gap:14px;max-width:1100px;margin:0 auto}
.card{display:grid;grid-template-columns:minmax(260px,520px) 1fr;gap:14px;background:#1f2125;border:1px solid #fff2;border-radius:12px;padding:12px}.card img.big{width:100%;border-radius:8px;background:#000}
.old{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}.old img{height:70px;border-radius:6px}.fl{display:inline-block;padding:1px 8px;border-radius:6px;background:#fff2;margin:0 4px 4px 0;font-size:12.5px}.fl.bad{background:#c92a2a88}
.muted{color:#a39b90;font-size:13px}.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center}input[type=text]{min-width:200px}
@media(max-width:760px){.card{grid-template-columns:1fr}}
</style></head><body>
<header><b>Фото от посетителей</b><span class="muted" id="who">__MAIL__</span><button class="tab on" data-s="pending">Ждут</button><button class="tab" data-s="approved">Одобрены</button><button class="tab" data-s="rejected">Отклонены</button><button id="modeb">Сообщения</button><span class="sp"></span><span id="cnt" class="muted"></span><button id="sw"></button></header>
<main id="list"><div class="muted">Загрузка…</div></main>
<script nonce="__NONCE__">
const SITE="__SITE__";let items=[],status="pending",data={mon:{},rel:{},sci:{}},photos={};
const REASONS=["не то здание","случайное изображение","плохое качество","есть люди или номера машин","чужая фотография","дубль","другое"];
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!==undefined)e.textContent=x;return e};
const hav=(a,b,c,d)=>{const k=Math.cos(a*Math.PI/180);return Math.hypot((d-b)*k*111320,(c-a)*111320)};
async function jget(u){const r=await fetch(u,{cache:"no-store"});return r.json()}
async function post(u,b){const r=await fetch(u,{method:"POST",headers:{"Content-Type":"application/json","X-Admin":"1"},body:JSON.stringify(b)});return r.json()}
function objInfo(o){const [k,id]=o.split(":");if(k==="mon"){const f=data.mon[id];return f&&{name:f.properties.name,addr:f.properties.address,lon:f.geometry.coordinates[0],lat:f.geometry.coordinates[1],ph:(f.properties.ph||"").split("|").filter(Boolean)}}
 if(k==="rel"){const r=data.rel[id];return r&&{name:r.name.ru+" / "+r.name.en,addr:"",lon:r.lon,lat:r.lat,ph:[]}}
 if(k==="sci"){const r=data.sci[id];return r&&{name:r.name.ru+" / "+r.name.en,addr:"",lon:r.lon,lat:r.lat,ph:[]}}return null}
async function load(){
 const [mon,rel,sci,ph]=await Promise.all([jget(SITE+"data/monuments.json"),jget(SITE+"data/religious.json"),jget(SITE+"data/science.json"),jget(SITE+"data/photos.json")]);
 for(const f of mon.features)data.mon[f.properties.id]=f;for(const r of rel)data.rel[r.id]=r;for(const r of sci)data.sci[r.id]=r;photos=ph;
 await refresh();await refreshFb();setMode("photo");const o=await jget("/api/open");swBtn(o.open)}
function swBtn(open){const b=document.getElementById("sw");b.textContent=open?"Форма открыта (закрыть)":"Форма закрыта (открыть)";b.onclick=async()=>{const r=await post("/api/open",{open:!open});swBtn(r.open)}}
async function refresh(){items=await jget("/api/list");render()}
async function render(){
 const box=document.getElementById("list");box.textContent="";const sel=items.filter(x=>x.s===status);
 document.getElementById("cnt").textContent="ждут: "+items.filter(x=>x.s==="pending").length+" · одобрены: "+items.filter(x=>x.s==="approved").length;
 if(!sel.length){box.appendChild(el("div","muted","Пусто."));return}
 for(const it of sel){const m=await jget("/api/meta/"+it.id);if(m.error)continue;const o=objInfo(m.obj),c=el("div","card");
  const left=el("div");const im=el("img","big");im.src="/api/img/"+it.id;im.loading="lazy";left.appendChild(im);c.appendChild(left);
  const r=el("div");r.appendChild(el("b","",o?o.name:m.obj));if(o&&o.addr)r.appendChild(el("div","muted",o.addr));r.appendChild(el("div","muted","объект: "+m.obj+(m.reassigned?" (переназначено)":"")));
  const fl=el("div");const f=(t,bad)=>{fl.appendChild(el("span","fl"+(bad?" bad":""),t))};
  f(m.w+"×"+m.h+", "+Math.round(m.size/1024)+" КБ");if(Math.max(m.w,m.h)<1200)f("маленькое",1);
  const osm=(la,lo)=>"https://www.openstreetmap.org/?mlat="+la+"&mlon="+lo+"#map=19/"+la+"/"+lo;
  if(m.dEx!=null)f("координаты снимка: "+m.dEx+" м от объекта",m.dEx>150);else if(m.lat!=null&&o){const d=Math.round(hav(m.lat,m.lon,o.lat,o.lon));f("координаты снимка: "+d+" м от объекта",d>150)}else f("координат в снимке нет",1);
  if(m.dGeo!=null)f("геолокация при отправке: "+m.dGeo+" м"+(m.gacc?" (±"+Math.round(m.gacc)+" м)":""),m.dGeo>150);else f("геолокации при отправке нет",1);
  f(m.v?"положение подтверждено":"положение не подтверждено",!m.v);
  f("дата отправки: "+new Date(m.ts).toLocaleString("ru"));r.appendChild(fl);
  const lk=el("div","muted");const a=(t,u)=>{const x=el("a","",t);x.href=u;x.target="_blank";x.rel="noopener noreferrer";x.style.color="#8fb8e8";x.style.marginRight="12px";lk.appendChild(x)};
  if(o)a("объект на карте",osm(o.lat,o.lon));if(m.lat!=null)a("снимок на карте",osm(m.lat,m.lon));if(m.glat!=null)a("геолокация на карте",osm(m.glat,m.glon));r.appendChild(lk);
  r.appendChild(el("div","","Автор: "+m.name+(m.note?" · «"+m.note+"»":"")));
  if(o&&o.ph.length){r.appendChild(el("div","muted","Уже есть фото объекта:"));const old=el("div","old");for(const k of o.ph.slice(0,4)){const p=photos[k];if(p){const i=el("img");i.src=p.thumb;old.appendChild(i)}}r.appendChild(old)}
  if(m.status==="rejected")r.appendChild(el("div","muted","Причина: "+m.reason));
  if(m.status==="pending"){const row=el("div","row"),ok=el("button","ok","Одобрить"),no=el("button","no","Отклонить"),rs=el("select");REASONS.forEach(x=>rs.appendChild(el("option","",x)));
   ok.onclick=async()=>{ok.disabled=true;await post("/api/act",{id:it.id,action:"approve"});refresh()};no.onclick=async()=>{no.disabled=true;await post("/api/act",{id:it.id,action:"reject",reason:rs.value});refresh()};
   row.append(ok,rs,no);r.appendChild(row);
   const rr=el("div","row"),inp=el("input");inp.type="text";inp.placeholder="другой объект: часть названия или адреса";const out=el("div","muted");
   inp.oninput=()=>{out.textContent="";const q=inp.value.trim().toLowerCase();if(q.length<3)return;let n=0;for(const id in data.mon){const p=data.mon[id].properties;if(((p.name||"")+" "+(p.address||"")).toLowerCase().includes(q)&&n<6){n++;const b=el("button","",(p.name||"")+" · "+(p.address||"")+" ["+id+"]");b.onclick=async()=>{await post("/api/act",{id:it.id,action:"reassign",obj:"mon:"+id});refresh()};out.appendChild(b);out.appendChild(el("br"))}}};
   rr.append(inp);r.append(rr,out)}
  c.appendChild(r);box.appendChild(c)}}
document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{status=b.dataset.s;document.querySelectorAll(".tab").forEach(x=>x.classList.toggle("on",x===b));render()});
let mode="photo",fbs=[],fbStatus="new";
const KINDS={data:"Ошибка в данных объекта",georef:"Привязка старого плана",boundary:"Граница города",translation:"Перевод или название",rights:"Вопрос по правам",other:"Другое"};
async function refreshFb(){fbs=await jget("/api/fb/list")}
async function renderFb(){
 const box=document.getElementById("list");box.textContent="";
 const bar=el("div","row");for(const [s,t] of [["new","Новые"],["done","Сделаны"]]){const b=el("button","tab"+(fbStatus===s?" on":""),t+" ("+fbs.filter(x=>x.s===s).length+")");b.onclick=()=>{fbStatus=s;renderFb()};bar.appendChild(b)}
 box.appendChild(bar);
 const sel=fbs.filter(x=>x.s===fbStatus);if(!sel.length){box.appendChild(el("div","muted","Пусто."));return}
 for(const it of sel){const m=await jget("/api/fb/get/"+it.id);if(m.error)continue;
  const c=el("div","card");c.style.gridTemplateColumns="1fr";const r=el("div");
  r.appendChild(el("b","",(KINDS[m.kind]||m.kind)+" · "+new Date(m.ts).toLocaleString("ru")));
  const msg=el("div","",m.message);msg.style.whiteSpace="pre-wrap";msg.style.margin="6px 0";r.appendChild(msg);
  if(m.contact)r.appendChild(el("div","","Контакт: "+m.contact));
  if(m.context)r.appendChild(el("div","muted","Контекст: "+m.context));
  if(m.page&&m.page.startsWith(SITE)){const a=el("a","","страница, откуда отправлено");a.href=m.page;a.target="_blank";a.rel="noopener noreferrer";a.style.color="#8fb8e8";r.appendChild(a)}
  const row=el("div","row"),ok=el("button",m.status==="done"?"":"ok",m.status==="done"?"Вернуть в новые":"Готово"),del=el("button","no","Удалить");
  ok.onclick=async()=>{ok.disabled=true;await post("/api/fb/act",{id:it.id,action:m.status==="done"?"reopen":"done"});await refreshFb();setMode("fb")};
  del.onclick=async()=>{if(!confirm("Удалить сообщение насовсем?"))return;del.disabled=true;await post("/api/fb/act",{id:it.id,action:"delete"});await refreshFb();setMode("fb")};
  row.append(ok,del);r.appendChild(row);c.appendChild(r);box.appendChild(c)}}
function setMode(m){mode=m;document.getElementById("modeb").textContent=m==="photo"?"Сообщения ("+fbs.filter(x=>x.s==="new").length+")":"Фото";document.querySelectorAll(".tab[data-s]").forEach(x=>{x.style.display=m==="photo"?"":"none"});if(m==="photo")render();else renderFb()}
document.getElementById("modeb").onclick=()=>setMode(mode==="photo"?"fb":"photo");
load();
</script></body></html>`;
