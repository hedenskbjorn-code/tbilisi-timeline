// Pure piecewise-linear timeline math for slider <-> year mapping and zoom windows.

export function yearToSlider(year, knots) {
  for (let i = 1; i < knots.length; i++) {
    if (year <= knots[i][0]) {
      const [y0, v0] = knots[i - 1], [y1, v1] = knots[i];
      return v0 + ((year - y0) / (y1 - y0)) * (v1 - v0);
    }
  }
  return 1000;
}

export function sliderToYear(value, knots, maxYear) {
  for (let i = 1; i < knots.length; i++) {
    if (value <= knots[i][1]) {
      const [y0, v0] = knots[i - 1], [y1, v1] = knots[i];
      return Math.round(y0 + ((value - v0) / (v1 - v0)) * (y1 - y0));
    }
  }
  return maxYear;
}

export function computeZoomWindow(lo, width, minYear, maxYear, fullKnots) {
  if (!width) return { lo: minYear, hi: maxYear, knots: fullKnots };
  let start = Math.round(lo);
  if (start < minYear) start = minYear;
  if (start + width > maxYear) start = maxYear - width;
  const hi = start + width;
  return { lo: start, hi, knots: [[start, 0], [hi, 1000]] };
}

export function centeredZoomWindow(year, width, minYear, maxYear) {
  return Math.min(Math.max(Math.round(year - width / 2), minYear), maxYear - width);
}
