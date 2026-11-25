// The layers "Monuments and sculptures" and "Memorial plaques": lazy files, off by default, a year filter, a sub box for the objects without a year, a label of an object without a name,
// a card with the photo and the licence, clusters.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { startServer, launch, openPage, waitReady } from "./helpers.mjs";
import { DATA } from "./helpers.mjs";

let server, browser, page, reqs;
test.before(async () => {
  server = await startServer();
  browser = await launch();
  page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=en#1990`);
  reqs = [];
  page.on("request", (r) => reqs.push(r.url()));
  await waitReady(page);
});
test.after(async () => { await page.ctx.close(); await browser.close(); server.srv.close(); });

const MON = JSON.parse(fs.readFileSync(path.join(DATA, "sculptures.json"), "utf8"));
const PLQ = JSON.parse(fs.readFileSync(path.join(DATA, "plaques.json"), "utf8"));
const feats = (src) => page.evaluate((s) => window.TT_E2E.map.getSource(s).serialize().data.features.length, src);

test("the files are lazy and both layers are off", async () => {
  assert.ok(!reqs.some((u) => /sculptures\.json|plaques\.json/.test(u)));
  assert.equal(await page.isChecked("#showMon"), false);
  assert.equal(await page.isChecked("#showPlq"), false);
});

test("the monuments of the year: the layer shows the dated objects up to the year, the sub box adds the undated ones", async () => {
  await page.check("#showMon");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("mons"), null, { timeout: 20000 });
  const dated = MON.items.filter((c) => c.y != null && c.y <= 1990).length;
  assert.equal(await feats("mons"), dated);
  assert.ok(dated > 20 && dated < MON.items.length);
  assert.equal(await page.locator("#showMonUndated").isVisible(), true);
  await page.check("#showMonUndated");
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("mons").serialize().data.features.length === n, dated + MON.items.filter((c) => c.y == null).length, { timeout: 10000 });
  await page.uncheck("#showMonUndated");
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("mons").serialize().data.features.length === n, dated, { timeout: 10000 });
});

async function openCard(key, c, zoom = 18) {
  await page.evaluate(() => document.querySelectorAll(".maplibregl-popup-close-button").forEach((b) => b.click()));
  const pt = await page.evaluate(([c, z]) => { const m = window.TT_E2E.map; m.jumpTo({ center: [c.lon, c.lat], zoom: z }); return new Promise((r) => m.once("idle", () => r(m.project([c.lon, c.lat])))); }, [c, zoom]);
  const box = await page.locator("#map canvas").first().boundingBox();
  await page.mouse.click(box.x + pt.x, box.y + pt.y);
  const pop = page.locator(".maplibregl-popup .pop");
  await pop.waitFor({ timeout: 15000 });
  return pop;
}

test("the card of a monument: the type, the year, the street and the photo with its author and licence", async () => {
  const c = MON.items.find((x) => x.y != null && x.y <= 1990 && x.ph && MON.photos[x.ph] && x.st && (x.n.en || x.n.ru || x.n.ka));
  assert.ok(c, "an object with everything");
  const pop = await openCard("mon", c);
  const txt = await pop.innerText();
  assert.ok(txt.includes(MON.ui["k_" + c.k].en), txt);
  assert.match(txt, new RegExp("Installed: " + c.y));
  assert.match(txt, /Location: /);
  assert.match(txt, /Photo: Wikimedia Commons/);
  assert.ok(await pop.locator("figure img").count() >= 1, "the photo");
});

test("an object without a name is labelled by its type and the nearest street", async () => {
  const c = MON.items.find((x) => !x.n.ka && !x.n.ru && !x.n.en && x.y == null && x.st);
  assert.ok(c, "an undated object without a name that has a street");
  await page.check("#showMonUndated");
  await page.waitForFunction((n) => window.TT_E2E.map.getSource("mons").serialize().data.features.length >= n, 1, { timeout: 10000 });
  const pop = await openCard("mon", c);
  const h = await pop.locator("h3").innerText();
  const st = MON.streets[c.st];
  assert.equal(h, MON.ui["k_" + c.k].en + ", " + st.en);
});

test("the plaques: dated by the first year of the life of the inscription, a card with the inscription", async () => {
  await page.check("#showPlq");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("plqs"), null, { timeout: 20000 });
  const dated = PLQ.items.filter((c) => c.y != null && c.y <= 1990).length;
  assert.equal(await feats("plqs"), dated);
  const c = PLQ.items.find((x) => x.y != null && x.y <= 1990 && x.ins && x.ph && PLQ.photos[x.ph]);
  const pop = await openCard("plq", c);
  const txt = await pop.innerText();
  assert.match(txt, new RegExp("Linked to the house since " + c.y));
  assert.match(txt, /Inscription: /);
  assert.match(txt, /Memorial plaque/);
});

test("the year of the plaque is never the year of the life: no plaque is dated by a year that its inscription does not name first", async () => {
  for (const c of PLQ.items) if (c.y != null) assert.ok(c.ins.includes(String(c.y)), `${c.id}: the year ${c.y} is not in the inscription`);
});

test("a description taken from Wikipedia (dw): short, in the right script, without stress marks, with the link of the article; the card says where the text is from", async () => {
  const CY = /[А-Яа-яЁё]/, GE = /[ა-ჰ]/;
  for (const [file, D] of [["sculptures", MON], ["plaques", PLQ]]) {
    const wiki = D.items.filter((c) => c.dw);
    assert.ok(wiki.length > 100, file + ": the descriptions from Wikipedia are there: " + wiki.length);
    for (const c of wiki) {
      assert.ok(c.d && Object.values(c.d).some(Boolean), `${file} ${c.id}: dw without a description`);
      assert.ok(c.w && Object.keys(c.w).length, `${file} ${c.id}: no link of the article`);
      for (const [l, t] of Object.entries(c.d)) {
        if (!t) continue;
        assert.ok(t.length <= 330, `${file} ${c.id} ${l}: too long (${t.length})`);
        assert.ok(!t.includes("́"), `${file} ${c.id} ${l}: a stress mark`);
        if (l === "ka") assert.ok(GE.test(t) && !CY.test(t), `${file} ${c.id}: the Georgian text has Cyrillic or no Georgian letters`);
        if (l === "en") assert.ok(!CY.test(t), `${file} ${c.id}: the English text has Cyrillic letters`);        // the Georgian spelling of the name in brackets ("Georgian: ...") is how an English article writes it
      }
    }
    assert.ok(MON.ui.from_wiki && MON.ui.from_wiki_person && PLQ.ui.from_wiki && PLQ.ui.from_wiki_person, "the labels are in the ui of both files");
  }
  // the card of a plaque (in the year 1990 of this test): the label, the text, the link of the article
  const c = PLQ.items.find((x) => x.dw && x.d.en && x.y != null && x.y <= 1990 && x.w && x.w.en);
  assert.ok(c, "a dated plaque with an English description from Wikipedia");
  await page.check("#showPlq");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("plqs"), null, { timeout: 20000 });
  const pop = await openCard("plq", c);
  const txt = await pop.innerText();
  assert.ok(txt.includes("About the person (Wikipedia)"), "the label on the card");
  assert.ok(txt.includes(c.d.en.slice(0, 40)), "the description on the card");
  assert.ok((await pop.locator(`a[href="${c.w.en}"]`).count()) >= 1, "the link of the article on the card");
});

test("the layers turn off", async () => {
  await page.uncheck("#showMon");
  await page.uncheck("#showPlq");
  const v = await page.evaluate(() => ["mon-pt", "plq-pt", "mon-cl", "plq-cl"].map((i) => window.TT_E2E.map.getLayoutProperty(i, "visibility")));
  assert.deepEqual(v, ["none", "none", "none", "none"]);
});

test("a description found by a search: the card shows it (ru / en), the details give the quotation, the Georgian text is there too", async () => {
  const c = MON.items.find((x) => x.id === "KAW_032");                        // 1981: shown in the year 1990 of this test
  assert.ok(c && c.d && c.d.en && c.dq && c.dq.length, "the description with quotations exists in the data");
  assert.ok(c.d.ka && /[ა-ჰ]/.test(c.d.ka) && !/[А-Яа-яЁё]/.test(c.d.ka), "the Georgian description is there (checked: Georgian letters, no Cyrillic)");
  const noKa = MON.items.filter((x) => x.dq && x.d && !x.d.ka);                    // a description found by a search that has no Georgian text yet (a short OSM tag has only the language of the tag)
  assert.ok(noKa.every((x) => x.d.ru && x.d.en), "a description found by a search has ru and en: " + noKa.map((x) => x.id));
  await page.check("#showMon");
  await page.waitForFunction(() => window.TT_E2E.map.getSource("mons"), null, { timeout: 20000 });
  const pop = await openCard("mon", c);
  assert.ok((await pop.innerText()).includes(c.d.en), "the English description");
  await page.locator(".maplibregl-popup .actions a.fb").first().click();
  await page.waitForFunction(() => !document.getElementById("imBody").closest("#infoModal").hidden, null, { timeout: 15000 });
  const body = await page.locator("#imBody").innerText();
  assert.ok(body.includes(c.dq[0].q.slice(0, 40)), "the quotation in the details");
  await page.keyboard.press("Escape");
});

test("slider bounce 1900 -> 1990 -> 1900 -> pause -> 1990 updates cluster source without stale sig", async () => {
  const setSlider = (y) => page.evaluate((yr) => {
    const sl = document.getElementById("slider");
    sl.value = String(yr);
    sl.dispatchEvent(new Event("input", { bubbles: true }));
  }, y);
  await setSlider(1900);
  await page.waitForTimeout(240);
  await setSlider(1990);
  await page.waitForTimeout(40);
  await setSlider(1900);
  await page.waitForTimeout(240);
  await setSlider(1990);
  await page.waitForTimeout(240);
  const cnt = await page.evaluate(() => window.TT_E2E.map.getSource("mons")?._data?.features?.length || 0);
  assert.ok(cnt >= 100, `expected >= 100 sculptures in 1990 after bounce, got ${cnt}`);
});
