import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { selectPlan, territoryPlans } from "../site/js/plans.js";

const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "site", "data");
const PLANS = JSON.parse(fs.readFileSync(path.join(DATA, "plans.json"), "utf8"));
const TBILISI_CENTER = { lng: 44.8085, lat: 41.6955 };
const BAGINETI_CENTER = { lng: 44.715, lat: 41.833 };
const MTSKHETA_CENTER = { lng: 44.72, lat: 41.84 };

test("adding a Mtskheta/Bagineti archaeological plan does not shift Tbilisi 1913 or Tbilisi auto-topo", () => {
  const withBagineti = [
    ...PLANS,
    {
      id: "bagineti_1963",
      year: 1963,
      pub_year: 1963,
      depicted_from: -200,
      depicted_to: 300,
      territory: "mtskheta",
      kind: "archaeological_plan",
      bounds: [44.70, 41.82, 44.73, 41.84],
    },
  ];
  assert.equal(selectPlan(withBagineti, 1913, TBILISI_CENTER)?.id, "tbilisi_1913");
  assert.equal(selectPlan(withBagineti, 1927, TBILISI_CENTER)?.id, "tbilisi_1913");
  assert.equal(selectPlan(withBagineti, 1928, TBILISI_CENTER), null);
  assert.equal(selectPlan(withBagineti, 1950, TBILISI_CENTER), null, "Tbilisi auto-topo stays enabled in 1950");
  assert.equal(territoryPlans(withBagineti, "tbilisi").length, PLANS.length);
});

test("Mtskheta/Bagineti local plan is selected by its own territory and depicted period", () => {
  const withBagineti = [
    ...PLANS,
    {
      id: "bagineti_1963",
      year: 1963,
      pub_year: 1963,
      depicted_from: -200,
      depicted_to: 300,
      territory: "mtskheta",
      kind: "archaeological_plan",
      bounds: [44.70, 41.82, 44.73, 41.84],
    },
  ];
  assert.equal(selectPlan(withBagineti, 200, BAGINETI_CENTER)?.id, "bagineti_1963");
  assert.equal(selectPlan(withBagineti, 200, TBILISI_CENTER), null);
  assert.equal(selectPlan(withBagineti, 1963, BAGINETI_CENTER), null, "outside depicted period in Bagineti");
  assert.equal(selectPlan(withBagineti, 1887, MTSKHETA_CENTER), null, "Tbilisi 1887 plan does not leak into Mtskheta");
});
