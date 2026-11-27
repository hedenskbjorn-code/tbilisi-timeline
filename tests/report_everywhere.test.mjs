// A visitor must be able to report a problem on ANY card: every function of app.js that shows a card on the map (showPopup) adds the row of the card with the report link (actions),
// the window of details, the viewer of the views and the other pages of the site have a button or a link to the form. A new card without the link stops the deploy.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const read = (p) => fs.readFileSync(new URL("../site/" + p, import.meta.url), "utf8");
const app = read("app.js");

test("every function that shows a card on the map adds the report link", () => {
  const heads = [...app.matchAll(/^  (?:async )?function ([A-Za-z0-9_]+)\(/gm)];
  const bad = [];
  let n = 0;
  heads.forEach((m, i) => {
    const body = app.slice(m.index, i + 1 < heads.length ? heads[i + 1].index : app.length);
    if (m[1] !== "showPopup" && /\bshowPopup\(/.test(body)) {
      n++;
      if (!/\bactions\(el,/.test(body)) bad.push(m[1]);
    }
  });
  assert.ok(n >= 12, "the cards were found: " + n);
  assert.deepEqual(bad, [], "cards without the report link: " + bad.join(", "));
});

test("the window of details, the viewer and the other pages lead to the form", () => {
  const html = read("index.html");
  assert.match(html, /id="imReport"/);
  assert.match(html, /id="vmReport"/);
  assert.match(app, /\$\("imReport"\)\.addEventListener\("click"/);
  assert.match(app, /\$\("vmReport"\)\.addEventListener\("click"/);
  for (const [dir, file] of [["entrances", "entrances/entrances.js"], ["run", "run/run.js"], ["museums", "museums/museums.js"], ["mtskheta", "mtskheta/mtskheta.js"], ["lost", "lost/lost.js"]]) {
    const page = read(dir + "/index.html");
    assert.ok(page.includes('id="report"') && page.includes('href="../?report=' + dir + '"'), `${dir}/index.html: the link to the form is missing`);
    const js = read(file);
    for (const w of ["Сообщить об ошибке", "Report a problem", "შეცდომის შეტყობინება"]) assert.ok(js.includes(w), `${file}: the text "${w}" is missing`);
  }
  assert.match(app, /new URLSearchParams\(location\.search\)\.get\("report"\)/);
});
