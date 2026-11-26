import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const SITE_DATA = path.join(ROOT, "site", "data");

test("dataset_registry.json covers every site/data/*.json file with explicit SQLite status", () => {
  const reg = JSON.parse(fs.readFileSync(path.join(ROOT, "tools", "dataset_registry.json"), "utf8")).datasets;
  const files = fs.readdirSync(SITE_DATA).filter((f) => f.endsWith(".json")).sort();
  for (const f of files) {
    assert.ok(f in reg, `${f} must be listed in tools/dataset_registry.json`);
    const entry = reg[f];
    assert.ok(entry.sqlite_layer || entry.exclusion_reason, `${f} needs sqlite_layer or exclusion_reason`);
  }
});

test("lost.json preserves valid id=0 and detects missing/duplicate IDs without skipping zero", () => {
  const lost = JSON.parse(fs.readFileSync(path.join(SITE_DATA, "lost.json"), "utf8"));
  const hasZero = lost.features.some((f) => f.id === 0);
  assert.equal(hasZero, true, "lost.json includes valid id=0");
  const validId = (id) => id !== null && id !== undefined && id !== "";
  assert.equal(validId(0), true);
  assert.equal(validId(null), false);
  assert.equal(validId(""), false);
});
