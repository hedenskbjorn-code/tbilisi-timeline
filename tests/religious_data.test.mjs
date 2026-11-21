// Patch 1.8.1: the Alexander Nevsky church of Chugureti is entered in the register twice (objects 3049 and 7998): one card stays, the duplicate is gone;
// the eight events from the CyberLeninka articles stand in the timeline, each with a note that names the article and a source with an address.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "site", "data");
const load = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));

test("the religious layer holds one card of the Alexander Nevsky church (3049), not two", () => {
  const rel = load("religious.json");
  assert.equal(rel.some((r) => r.id === "reg7998"), false, "the duplicate reg7998 is gone");
  const c = rel.find((r) => r.id === "reg3049");
  assert.ok(c);
  assert.equal(c.from, 1864);
  assert.equal(c.rel, "russian");
  assert.match(c.note.ru, /7998/);
});

test("the eight events from the CyberLeninka articles stand in the timeline with a note and a source", () => {
  const ev = load("history_events.json").events;
  for (const d of ["05.04.1864", "19.02.1868", "22.06.1882", "1887-1888", "30.12.1909", "1924", "07.02.1930", "1931-1932"]) {
    const e = ev.find((x) => x.date === d && /cyberleninka|doi\.org/.test(JSON.stringify(x.src)));
    assert.ok(e, "event " + d);
    assert.ok(e.note.ru && e.note.en && e.note.ka, "note of " + d);
    assert.match(typeof e.src[0] === "string" ? e.src[0] : e.src[0].url, /^https:\/\//);
  }
});

test("the Art Palace and the Dry Bridge have the dates of their Wikipedia pages on the map layer", () => {
  const f = load("monuments.json").features;
  const get = (id) => f.find((x) => x.properties.id === id).properties;
  assert.equal(get(3016).ye, 1895);
  assert.equal(get(4866).y0, 1848);
  assert.equal(get(4866).y1, 1851);
  const sci = load("science.json").find((x) => x.id === "reg3016");
  assert.equal(sci.from, 1895);
});
