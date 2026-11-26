// Spatial and temporal selection of georeferenced historical plans and archaeological overlays.

export function planBounds(p) {
  if (Array.isArray(p?.bounds) && p.bounds.length === 4) return p.bounds;
  if (!Array.isArray(p?.corners) || p.corners.length < 4) return null;
  let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity;
  for (const [lon, lat] of p.corners) {
    if (lon < minLon) minLon = lon;
    if (lat < minLat) minLat = lat;
    if (lon > maxLon) maxLon = lon;
    if (lat > maxLat) maxLat = lat;
  }
  return [minLon, minLat, maxLon, maxLat];
}

export function inBounds(center, b) {
  if (!center || !b) return false;
  const lon = Array.isArray(center) ? center[0] : center.lng;
  const lat = Array.isArray(center) ? center[1] : center.lat;
  return Number.isFinite(lon) && Number.isFinite(lat) && lon >= b[0] && lon <= b[2] && lat >= b[1] && lat <= b[3];
}

export function territoryPlans(plans, territory = "tbilisi") {
  return (plans || []).filter((p) => (p.territory || "tbilisi") === territory);
}

const TBILISI_BOUNDS = [44.68, 41.60, 44.96, 41.80];

/**
 * Select the active plan for (year, center) without letting local/regional plans
 * stretch Tbilisi's chronological plan window or disable Tbilisi auto-topo.
 */
export function selectPlan(plans, year, center, planAfter = 15) {
  if (!Array.isArray(plans) || !plans.length) return null;
  // 1. Check non-Tbilisi local/regional plans whose bounds cover the map center and depicted period.
  const local = plans.filter((p) => {
    const terr = p.territory || "tbilisi";
    if (terr === "tbilisi") return false;
    if (!inBounds(center, planBounds(p))) return false;
    const from = Number.isFinite(p.depicted_from) ? p.depicted_from : p.year;
    const to = Number.isFinite(p.depicted_to) ? p.depicted_to : p.year;
    return year >= from && year <= to;
  });
  if (local.length) return local[local.length - 1];

  // 2. Chronological Tbilisi plans (only within Tbilisi bounds; never leak into Mtskheta).
  if (center && !inBounds(center, TBILISI_BOUNDS)) return null;
  const tb = territoryPlans(plans, "tbilisi");
  let p = null, next = null;
  for (let i = 0; i < tb.length; i++) {
    if (tb[i].year <= year) {
      p = tb[i];
      next = tb[i + 1] || null;
    }
  }
  if (!p) return null;
  const until = next ? next.year : p.year + planAfter;
  return year < until ? p : null;
}
