// The pages open without errors in the three languages; the main page finishes loading.
import test from "node:test";
import assert from "node:assert/strict";
import { startServer, launch, openPage, waitReady, realErrors, LANGS } from "./helpers.mjs";

let server, browser;
test.before(async () => { server = await startServer(); browser = await launch(); });
test.after(async () => { await browser.close(); server.srv.close(); });

for (const lang of LANGS) {
  test(`main page, ${lang}: loads, no errors, language set`, async () => {
    const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=${lang}#1887`);
    await waitReady(page);
    assert.equal(await page.evaluate(() => document.documentElement.lang), lang);
    assert.ok((await page.textContent("#title")).trim().length > 3, "title is empty");
    assert.equal(await page.evaluate(() => window.TT_E2E.year), 1887);
    assert.deepEqual(realErrors(page), []);
    await page.ctx.close();
  });
  for (const sub of ["run", "entrances", "museums", "lost"]) {
    test(`page /${sub}/, ${lang}: loads, no errors, text and sections list`, async () => {
      const page = await openPage(browser, `${server.url}/${sub}/?nostats=1&lang=${lang}`);
      await page.waitForFunction(() => document.getElementById("title") && document.getElementById("title").textContent.length > 3, null, { timeout: 30000 });
      assert.equal(await page.evaluate(() => document.documentElement.lang), lang);
      assert.equal(await page.locator("#pagesSel option").count(), 5);
      assert.deepEqual(realErrors(page), []);
      await page.ctx.close();
    });
  }
}
