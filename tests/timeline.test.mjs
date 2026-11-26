import test from "node:test";
import assert from "node:assert/strict";
import { yearToSlider, sliderToYear, computeZoomWindow, centeredZoomWindow } from "../site/js/timeline.js";

const MIN = 100, MAX = 2026;
const FULL_KNOTS = [[100, 0], [1000, 150], [1700, 350], [2026, 1000]];

test("timeline piecewise-linear mapping hits exact knots and round-trips", () => {
  assert.equal(yearToSlider(100, FULL_KNOTS), 0);
  assert.equal(yearToSlider(1000, FULL_KNOTS), 150);
  assert.equal(yearToSlider(1700, FULL_KNOTS), 350);
  assert.equal(yearToSlider(2026, FULL_KNOTS), 1000);
  assert.equal(sliderToYear(0, FULL_KNOTS, MAX), 100);
  assert.equal(sliderToYear(150, FULL_KNOTS, MAX), 1000);
  assert.equal(sliderToYear(350, FULL_KNOTS, MAX), 1700);
  assert.equal(sliderToYear(1000, FULL_KNOTS, MAX), 2026);
  assert.equal(sliderToYear(Math.round(yearToSlider(1887, FULL_KNOTS)), FULL_KNOTS, MAX), 1887);
});

test("timeline zoom window clamps to [MIN, MAX] and centers around target year", () => {
  const full = computeZoomWindow(500, 0, MIN, MAX, FULL_KNOTS);
  assert.equal(full.lo, MIN);
  assert.equal(full.hi, MAX);
  assert.deepEqual(full.knots, FULL_KNOTS);

  const clampedLow = computeZoomWindow(20, 330, MIN, MAX, FULL_KNOTS);
  assert.equal(clampedLow.lo, 100);
  assert.equal(clampedLow.hi, 430);

  const clampedHigh = computeZoomWindow(1950, 330, MIN, MAX, FULL_KNOTS);
  assert.equal(clampedHigh.lo, 1696);
  assert.equal(clampedHigh.hi, 2026);

  assert.equal(centeredZoomWindow(1900, 150, MIN, MAX), 1825);
  assert.equal(centeredZoomWindow(110, 150, MIN, MAX), 100);
});
