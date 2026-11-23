// The mail to the owner (worker/submit.js, notify): a letter for a new message of the form and a new photograph, only after the defences, at most ten a day, a kill switch, no link and no address of a
// visitor in it, a failure of the mail never breaks the answer to the visitor, one letter an hour for an error of the Worker. Offline: a fake KV, a fake send_email binding, a fake Turnstile.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

class FakeEmail { constructor(from, to, raw) { this.from = from; this.to = to; this.raw = raw; } }
globalThis.EmailMessageForTests = FakeEmail;
const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "ttw-")), "submit.mjs");
fs.writeFileSync(tmp, fs.readFileSync(new URL("../worker/submit.js", import.meta.url), "utf8").replace('import { EmailMessage } from "cloudflare:email";', "const EmailMessage = globalThis.EmailMessageForTests;"));      // the class of the runtime of Cloudflare is not in Node
const worker = (await import(pathToFileURL(tmp).href)).default;
const ORIGIN = "https://hedenskbjorn-code.github.io", SITE = ORIGIN + "/tbilisi-timeline/";

const realFetch = globalThis.fetch;
globalThis.fetch = async (u) => {
  if (String(u).includes("turnstile")) return new Response(JSON.stringify({ success: true }));
  if (String(u).endsWith("data/monuments.json")) return new Response(JSON.stringify({ features: [{ properties: { id: "77" }, geometry: { coordinates: [44.8, 41.7] } }] }));
  return realFetch(u);
};

function kv() {
  const m = new Map();
  return { m, get: async (k) => (m.has(k) ? m.get(k) : null), put: async (k, v) => { m.set(k, typeof v === "string" ? v : "[bytes]"); } };
}
function env(over = {}) {
  const sent = [];
  return { sent, PHOTOS: kv(), TURNSTILE_SECRET: "s", HASH_SALT: "salt", EMAIL_FROM: "alerts@example.org", EMAIL_TO: "owner@example.net", ADMIN_URL: "https://admin.example/", MAIL: { send: async (m) => { sent.push(m); } }, ...over };
}
const decode = (raw) => Buffer.from(raw.split("\r\n\r\n")[1].replace(/\r\n/g, ""), "base64").toString("utf8");
let counter = 0;
async function report(e, message = "The monument is gone, see http://evil.example/x and www.evil.example", ip = "203.0.113.9") {
  const pending = [], ctx = { waitUntil: (p) => pending.push(p) };
  const body = JSON.stringify({ hp: "", t: Date.now() - 6000, kind: "data", message: message + " #" + ++counter, contact: "", context: "mon:77", page: SITE + "?a=1", "cf-turnstile-response": "tok" });
  const req = new Request("https://w.example/feedback", { method: "POST", headers: { Origin: ORIGIN, "Content-Length": String(Buffer.byteLength(body)), "CF-Connecting-IP": ip }, body });
  const res = await worker.fetch(req, e, ctx);
  await Promise.all(pending);
  return res;
}

test("a message of the form sends one plain letter without a link and without the address of the visitor", async () => {
  const e = env();
  const res = await report(e);
  assert.equal((await res.json()).ok, true);
  assert.equal(e.sent.length, 1);
  const m = e.sent[0];
  assert.equal(m.from, "alerts@example.org"); assert.equal(m.to, "owner@example.net");
  assert.match(m.raw, /^Subject: \[tbilisi-timeline\] new problem report$/m);
  assert.match(m.raw, /Content-Type: text\/plain; charset=UTF-8/);
  const body = decode(m.raw);
  assert.match(body, /Kind: data/); assert.match(body, /Queue id: /); assert.match(body, /https:\/\/admin\.example\//);
  assert.ok(!/evil\.example/.test(body), "the link of the visitor is removed");
  assert.ok(!/203\.0\.113\.9/.test(m.raw + body), "no address of the visitor");
});

test("at most ten letters a day, the eleventh message is kept in the queue without a letter", async () => {
  const e = env();
  for (let i = 0; i < 12; i++) await report(e, "message number " + i, "198.51.100." + i);
  assert.equal(e.sent.length, 10);
  assert.equal([...e.PHOTOS.m.keys()].filter((k) => k.startsWith("fb:")).length, 12, "all the twelve are in the queue");
});

test("the kill switch cfg:notify=0 stops the mail, a missing binding changes nothing for the visitor", async () => {
  const e1 = env(); e1.PHOTOS.m.set("cfg:notify", "0");
  assert.equal((await (await report(e1)).json()).ok, true); assert.equal(e1.sent.length, 0);
  const e2 = env({ MAIL: undefined });
  assert.equal((await (await report(e2)).json()).ok, true);
});

test("a failure of the mail does not break the answer and the message is in the queue", async () => {
  const e = env({ MAIL: { send: async () => { throw new Error("mail down"); } } });
  const res = await report(e);
  assert.equal((await res.json()).ok, true);
  assert.equal([...e.PHOTOS.m.keys()].filter((k) => k.startsWith("fb:")).length, 1);
});

test("an error of the Worker: the visitor gets a plain answer and the owner one letter an hour", async () => {
  const e = env();
  const get = e.PHOTOS.get;
  e.PHOTOS.get = async (k) => { if (k === "cfg:fb_open") throw new Error("kv down"); return get(k); };
  const r1 = await report(e), r2 = await report(e);
  assert.equal(r1.status, 500); assert.equal((await r2.json()).error, "server");
  assert.equal(e.sent.length, 1);
  assert.match(e.sent[0].raw, /^Subject: \[tbilisi-timeline\] error in the worker$/m);
});

// a photograph: a crafted JPEG header of 900x900 (the Worker reads the size from the file), a register object that exists
function jpeg() { return Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xff, 0xc0, 0x00, 0x11, 0x08, 0x03, 0x84, 0x03, 0x84, 0x03, 0x01, 0x11, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01, 0xff, 0xd9, 0x00, 0x00, 0x00, 0x00]); }
test("a photograph sends one letter with the object and the size, no picture inside", async () => {
  const e = env(), pending = [], ctx = { waitUntil: (p) => pending.push(p) };
  const fd = new FormData();
  fd.set("hp", ""); fd.set("t", String(Date.now() - 6000)); fd.set("obj", "mon:77"); fd.set("name", "A visitor"); fd.set("note", "front"); fd.set("consent", "1"); fd.set("cf-turnstile-response", "tok");
  fd.set("photo", new Blob([jpeg()], { type: "image/jpeg" }), "p.jpg");
  const packed = new Response(fd), buf = Buffer.from(await packed.arrayBuffer());                    // the browser sends the length of the form: here it is counted
  const res = await worker.fetch(new Request("https://w.example/submit", { method: "POST", headers: { Origin: ORIGIN, "CF-Connecting-IP": "203.0.113.7", "Content-Type": packed.headers.get("content-type"), "Content-Length": String(buf.length) }, body: buf }), e, ctx);
  await Promise.all(pending);
  assert.equal((await res.json()).ok, true);
  assert.equal(e.sent.length, 1);
  assert.match(e.sent[0].raw, /^Subject: \[tbilisi-timeline\] new photo$/m);
  const body = decode(e.sent[0].raw);
  assert.match(body, /Object: mon:77/); assert.match(body, /900x900/);
  assert.ok(!/203\.0\.113\.7|A visitor/.test(body), "no address and no name of the visitor");
});

test("a failure of the mail leaves the reason for the owner with the addresses masked, a success leaves a mark of time", async () => {
  const e1 = env({ MAIL: { send: async () => { throw new Error("destination owner@example.net is not verified"); } } });
  await report(e1);
  const dbg = JSON.parse(e1.PHOTOS.m.get("dbg:notify"));
  assert.match(dbg.message, /destination \[address\] is not verified/);
  assert.ok(!/owner@example\.net/.test(JSON.stringify(dbg)));
  const e2 = env();
  await report(e2);
  assert.ok(e2.PHOTOS.m.get("dbg:notify_ok") > 0);
});
