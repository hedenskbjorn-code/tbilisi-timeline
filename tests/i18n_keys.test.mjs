// A key of the interface that is written twice in one language block does not fail anywhere: the later one silently replaces the earlier one
// (it happened: the new title of a block of the right panel took the key of a title of the left panel). Every key used by data-i in index.html
// must stand exactly three times in site/i18n.js: once for ru, once for en, once for ka.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SITE = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "site");
const html = fs.readFileSync(path.join(SITE, "index.html"), "utf8");
const js = fs.readFileSync(path.join(SITE, "i18n.js"), "utf8");

test("every data-i key of index.html stands exactly three times in i18n.js (no silent override)", () => {
  const keys = [...new Set([...html.matchAll(/data-i="([^"]+)"/g)].map((m) => m[1]))];
  assert.ok(keys.length > 50);
  const bad = {};
  for (const k of keys) {
    const n = [...js.matchAll(new RegExp("(?<![\\w.])" + k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ":\\s", "g"))].length;
    if (n !== 3) bad[k] = n;
  }
  assert.deepEqual(bad, {});
});
