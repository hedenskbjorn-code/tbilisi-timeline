// Tbilisi Plan Aligner + boundary tracer.
// Overlay an old plan on a modern map, align it (4 corners), and trace boundary polygons on top.
const statusEl = document.getElementById('status');
const say = (t) => { statusEl.textContent = t; };

const map = new maplibregl.Map({
  container: 'map',
  center: [44.81, 41.697],
  zoom: 12.5,
  style: {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        maxzoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }
    },
    layers: [{ id: 'osm', type: 'raster', source: 'osm' }]
  }
});
map.addControl(new maplibregl.NavigationControl());

let plans = [];
let cur = null;          // current plan config
let corners = [];        // [[lng,lat] x4]  TL,TR,BR,BL
let markers = [];        // plan corner handles
let center = null;       // plan centre handle
let ready = false;

// boundary state
let polys = [];          // {type, confidence, ring:[[lng,lat]...]}
let active = -1;
let drawing = false;
let vtx = [];            // vertex markers of the active polygon

const selEl = document.getElementById('plan');
const opEl = document.getElementById('op');
const opv = document.getElementById('opv');
const typeEl = document.getElementById('btype');
const confEl = document.getElementById('bconf');
const handlesEl = document.getElementById('handles');
const cpEl = document.getElementById('cpmode');
const useWarpEl = document.getElementById('usewarp');
const gcpListEl = document.getElementById('gcplist');
const warpInfoEl = document.getElementById('warpinfo');

// ---------- control points (GCPs) ----------
let gcps = [];           // {px:[x,y] in plan pixels, lnglat:[lng,lat] true position}
let pendingPx = null;    // first click of a pair
let warpInfo = null;

const mercOf = (c) => { const m = maplibregl.MercatorCoordinate.fromLngLat({ lng: c[0], lat: c[1] }); return [m.x, m.y]; };
const lngLatOf = (xy) => { const ll = new maplibregl.MercatorCoordinate(xy[0], xy[1], 0).toLngLat(); return [ll.lng, ll.lat]; };

// Heckbert unit-square -> quad (projective), the same family of mapping MapLibre uses for image sources.
function quadCoeffs() {
  const q = corners.map(mercOf);
  const [p0, p1, p2, p3] = q;
  const dx1 = p1[0] - p2[0], dx2 = p3[0] - p2[0], dy1 = p1[1] - p2[1], dy2 = p3[1] - p2[1];
  const sx = p0[0] - p1[0] + p2[0] - p3[0], sy = p0[1] - p1[1] + p2[1] - p3[1];
  let g = 0, h = 0;
  if (Math.abs(sx) > 1e-18 || Math.abs(sy) > 1e-18) {
    const den = dx1 * dy2 - dx2 * dy1;
    g = (sx * dy2 - dx2 * sy) / den;
    h = (dx1 * sy - sx * dy1) / den;
  }
  return { a: p1[0] - p0[0] + g * p1[0], b: p3[0] - p0[0] + h * p3[0], c: p0[0],
           d: p1[1] - p0[1] + g * p1[1], e: p3[1] - p0[1] + h * p3[1], f: p0[1], g, h };
}
function pxToLngLat(px) {
  const k = quadCoeffs(), u = px[0] / cur.width, v = px[1] / cur.height;
  const w = k.g * u + k.h * v + 1;
  return lngLatOf([(k.a * u + k.b * v + k.c) / w, (k.d * u + k.e * v + k.f) / w]);
}
function lngLatToPx(ll) {
  const k = quadCoeffs(), [X, Y] = mercOf(ll);
  const a11 = k.a - X * k.g, a12 = k.b - X * k.h, a21 = k.d - Y * k.g, a22 = k.e - Y * k.h;
  const r1 = X - k.c, r2 = Y - k.f, det = a11 * a22 - a12 * a21;
  const u = (r1 * a22 - a12 * r2) / det, v = (a11 * r2 - r1 * a21) / det;
  return [u * cur.width, v * cur.height];
}

function renderGcps() {
  const feats = [];
  gcps.forEach((g, i) => {
    const from = pxToLngLat(g.px);
    feats.push({ type: 'Feature', properties: { i }, geometry: { type: 'LineString', coordinates: [from, g.lnglat] } });
    feats.push({ type: 'Feature', properties: { kind: 'from', i }, geometry: { type: 'Point', coordinates: from } });
    feats.push({ type: 'Feature', properties: { kind: 'to', i }, geometry: { type: 'Point', coordinates: g.lnglat } });
  });
  if (pendingPx) feats.push({ type: 'Feature', properties: { kind: 'from' }, geometry: { type: 'Point', coordinates: pxToLngLat(pendingPx) } });
  const src = map.getSource('gcp');
  if (src) src.setData({ type: 'FeatureCollection', features: feats });
  gcpListEl.innerHTML = '';
  gcps.forEach((g, i) => {
    const row = document.createElement('div');
    row.textContent = `${i + 1}: (${Math.round(g.px[0])}, ${Math.round(g.px[1])}) → ${g.lnglat[1].toFixed(5)}, ${g.lnglat[0].toFixed(5)} `;
    const x = document.createElement('a');
    x.textContent = '✕'; x.href = '#'; x.style.color = 'var(--accent)';
    x.onclick = (ev) => { ev.preventDefault(); gcps.splice(i, 1); renderGcps(); };
    row.appendChild(x);
    gcpListEl.appendChild(row);
  });
}

function handleCpClick(e) {
  if (useWarpEl.checked) { say('Untick "Show warped plan" first: points are placed on the unwarped overlay.'); return; }
  const ll = [e.lngLat.lng, e.lngLat.lat];
  if (!pendingPx) {
    const px = lngLatToPx(ll);
    if (px[0] < 0 || px[1] < 0 || px[0] > cur.width || px[1] > cur.height) { say('That spot is outside the plan.'); return; }
    pendingPx = px;
    say('Now click the SAME feature on the modern base map (Esc cancels).');
  } else {
    gcps.push({ px: pendingPx, lnglat: ll });
    pendingPx = null;
    say(`Point ${gcps.length} added. Pick another feature on the plan. 6-10 well spread points work best.`);
  }
  renderGcps();
}

async function loadGcps(p) {
  gcps = []; pendingPx = null;
  const j = await loadJson(`/data/georef/${p.id}_gcp.json`);
  if (j && j.gcps) gcps = j.gcps.map(g => ({ px: g.px, lnglat: g.lnglat }));
  renderGcps();
}

function removeWarped() {
  if (map.getLayer('warped')) map.removeLayer('warped');
  if (map.getSource('warped')) map.removeSource('warped');
  warpInfo = null;
}
function applyWarpVisibility() {
  const has = !!map.getLayer('warped');
  const on = has && useWarpEl.checked;
  if (has) map.setLayoutProperty('warped', 'visibility', on ? 'visible' : 'none');
  if (map.getLayer('plan')) map.setLayoutProperty('plan', 'visibility', on ? 'none' : 'visible');
  if (on) setHandlesVisible(false); else setHandlesVisible(handlesEl.checked);
}
async function loadWarped(p) {
  removeWarped();
  const info = await loadJson(`/data/warped/${p.id}.json`);
  if (!info || !info.ok) { warpInfoEl.textContent = ''; applyWarpVisibility(); return; }
  warpInfo = info;
  map.addSource('warped', { type: 'image', url: info.image + '?t=' + Date.now(), coordinates: info.corners });
  map.addLayer({ id: 'warped', type: 'raster', source: 'warped',
    paint: { 'raster-opacity': +opEl.value / 100, 'raster-fade-duration': 0 }, layout: { visibility: 'none' } }, 'bnd-fill');
  warpInfoEl.textContent = describeWarp(info);
  applyWarpVisibility();
}
function describeWarp(i) {
  const loo = i.loo_rms_m == null ? 'n/a (need 4+ points)' : `${Math.round(i.loo_rms_m)} m`;
  return `${i.model}, ${i.points} points. In-sample RMS ${Math.round(i.in_sample_rms_m)} m (max ${Math.round(i.in_sample_max_m)}). Leave-one-out RMS ${loo}.`;
}

// ---------- plan overlay ----------
async function loadJson(url) {
  try {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) return null;
    return await r.json();
  } catch (e) { return null; }
}

const centroid = () => [0, 1].map(i => corners.reduce((s, c) => s + c[i], 0) / 4);

function applyCorners() {
  const src = map.getSource('plan');
  if (src) src.setCoordinates(corners);
  if (center) center.setLngLat(centroid());
}

function makeMarker(lngLat, cls, onDrag) {
  const el = document.createElement('div');
  el.className = 'handle ' + cls;
  const m = new maplibregl.Marker({ element: el, draggable: true }).setLngLat(lngLat).addTo(map);
  m.on('drag', () => onDrag(m.getLngLat()));
  return m;
}

function setHandlesVisible(v) {
  [...markers, center].forEach(m => { if (m) m.getElement().style.display = v ? '' : 'none'; });
}

function clearPlanMarkers() {
  markers.forEach(m => m.remove());
  markers = [];
  if (center) { center.remove(); center = null; }
}

async function showPlan(p) {
  cur = p;
  clearPlanMarkers();
  if (map.getLayer('plan')) map.removeLayer('plan');
  if (map.getSource('plan')) map.removeSource('plan');
  removeWarped();
  const saved = await loadJson(`/data/georef/${p.id}.json`);
  corners = ((saved && saved.corners) || p.initialCorners).map(c => c.slice());
  map.addSource('plan', { type: 'image', url: p.image, coordinates: corners });
  map.addLayer({ id: 'plan', type: 'raster', source: 'plan',
    paint: { 'raster-opacity': +opEl.value / 100, 'raster-fade-duration': 0 } }, 'bnd-fill');
  corners.forEach((c, i) => {
    markers.push(makeMarker(c, '', (ll) => { corners[i] = [ll.lng, ll.lat]; applyCorners(); }));
  });
  let last = null;
  center = makeMarker(centroid(), 'center', (ll) => {
    if (!last) last = centroid();
    const dx = ll.lng - last[0], dy = ll.lat - last[1];
    corners = corners.map(c => [c[0] + dx, c[1] + dy]);
    markers.forEach((m, i) => m.setLngLat(corners[i]));
    const src = map.getSource('plan'); if (src) src.setCoordinates(corners);
    last = [ll.lng, ll.lat];
  });
  center.on('dragend', () => { last = null; });
  setHandlesVisible(handlesEl.checked);
  await loadBoundaries(p);
  await loadGcps(p);
  await loadWarped(p);
  say(saved ? `Loaded saved alignment for ${p.year}.` : 'No saved alignment: using initial guess. Tick "Plan handles" to adjust, then Save.');
}

// ---------- boundary tracing ----------
function ensureBoundaryLayers() {
  map.addSource('bnd', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  map.addLayer({ id: 'bnd-fill', type: 'fill', source: 'bnd', filter: ['==', ['geometry-type'], 'Polygon'],
    paint: { 'fill-color': ['match', ['get', 'type'], 'city_limit', '#1a8a3a', '#d4381c'],
             'fill-opacity': ['case', ['get', 'active'], 0.3, 0.16] } });
  map.addSource('gcp', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  map.addLayer({ id: 'gcp-line', type: 'line', source: 'gcp', filter: ['==', ['geometry-type'], 'LineString'],
    paint: { 'line-color': '#e0a000', 'line-width': 2 } });
  map.addLayer({ id: 'gcp-pt', type: 'circle', source: 'gcp', filter: ['==', ['geometry-type'], 'Point'],
    paint: { 'circle-radius': 5, 'circle-color': ['match', ['get', 'kind'], 'from', '#d22', '#1a9a3a'],
             'circle-stroke-width': 1.5, 'circle-stroke-color': '#fff' } });
  const lineColor = ['match', ['get', 'type'], 'city_limit', '#1a8a3a', '#d4381c'];
  const lineWidth = ['case', ['get', 'active'], 4, 2.5];
  // (line-dasharray cannot be data-driven in MapLibre, so approximate boundaries get their own dashed layer)
  map.addLayer({ id: 'bnd-line', type: 'line', source: 'bnd', filter: ['!=', ['get', 'confidence'], 'approximate'],
    paint: { 'line-color': lineColor, 'line-width': lineWidth } });
  map.addLayer({ id: 'bnd-line-approx', type: 'line', source: 'bnd', filter: ['==', ['get', 'confidence'], 'approximate'],
    paint: { 'line-color': lineColor, 'line-width': lineWidth, 'line-dasharray': [3, 2] } });
}

function render() {
  const feats = polys.map((p, i) => {
    const props = { idx: i, type: p.type, confidence: p.confidence, active: i === active };
    if (p.ring.length >= 3) {
      return { type: 'Feature', properties: props,
        geometry: { type: 'Polygon', coordinates: [[...p.ring, p.ring[0]]] } };
    }
    if (p.ring.length === 2) {
      return { type: 'Feature', properties: props, geometry: { type: 'LineString', coordinates: p.ring } };
    }
    return null;
  }).filter(Boolean);
  const src = map.getSource('bnd');
  if (src) src.setData({ type: 'FeatureCollection', features: feats });
}

function rebuildVertexMarkers() {
  vtx.forEach(m => m.remove());
  vtx = [];
  if (active < 0 || !polys[active]) return;
  polys[active].ring.forEach((c, i) => {
    const el = document.createElement('div');
    el.className = 'vtx';
    el.title = 'Drag to move, right-click to delete';
    const m = new maplibregl.Marker({ element: el, draggable: true }).setLngLat(c).addTo(map);
    m.on('drag', () => { const ll = m.getLngLat(); polys[active].ring[i] = [ll.lng, ll.lat]; render(); });
    el.addEventListener('contextmenu', (e) => {
      e.preventDefault(); e.stopPropagation();
      polys[active].ring.splice(i, 1);
      rebuildVertexMarkers(); render();
    });
    vtx.push(m);
  });
}

function setActive(i) {
  active = i;
  if (i >= 0) { typeEl.value = polys[i].type; confEl.value = polys[i].confidence; }
  rebuildVertexMarkers(); render();
}

function setDrawing(v) {
  drawing = v;
  map.getCanvas().style.cursor = v ? 'crosshair' : '';
}

async function loadBoundaries(p) {
  polys = []; active = -1; setDrawing(false); rebuildVertexMarkers();
  const gj = await loadJson(`/data/boundaries/${p.id}.geojson`);
  if (gj && gj.features) {
    gj.features.forEach(f => {
      const ring = f.geometry.coordinates[0].slice(0, -1);
      polys.push({ type: f.properties.type || 'city_limit', confidence: f.properties.confidence || 'approximate', ring });
    });
  }
  render();
}

document.getElementById('newpoly').addEventListener('click', () => {
  polys.push({ type: typeEl.value, confidence: confEl.value, ring: [] });
  setActive(polys.length - 1);
  setDrawing(true);
  say('Click on the map to add vertices. Enter or "Finish" to close the polygon.');
});
function finish() {
  if (!drawing) return;
  setDrawing(false);
  if (active >= 0 && polys[active].ring.length < 3) {
    polys.splice(active, 1); active = -1; rebuildVertexMarkers();
    say('Polygon needs at least 3 vertices; discarded.');
  } else say('Polygon closed. Drag vertices to adjust (right-click deletes one). Save boundary when done.');
  render();
}
document.getElementById('finish').addEventListener('click', finish);
document.addEventListener('keydown', (e) => { if (e.key === 'Enter') finish(); });
document.getElementById('undo').addEventListener('click', () => {
  if (active < 0) return;
  polys[active].ring.pop(); rebuildVertexMarkers(); render();
});
document.getElementById('delpoly').addEventListener('click', () => {
  if (active < 0) return;
  polys.splice(active, 1); setDrawing(false); setActive(-1);
  say('Polygon removed (not saved to disk until you press Save boundary).');
});
typeEl.addEventListener('change', () => { if (active >= 0) { polys[active].type = typeEl.value; render(); } });
confEl.addEventListener('change', () => { if (active >= 0) { polys[active].confidence = confEl.value; render(); } });

map.on('click', (e) => {
  if (cpEl.checked) { handleCpClick(e); return; }
  if (drawing && active >= 0) {
    polys[active].ring.push([e.lngLat.lng, e.lngLat.lat]);
    rebuildVertexMarkers(); render();
    return;
  }
  const hit = map.queryRenderedFeatures(e.point, { layers: ['bnd-fill'] })[0];
  if (hit) setActive(hit.properties.idx);
});

document.getElementById('savebnd').addEventListener('click', async () => {
  if (!cur) return;
  const features = polys.filter(p => p.ring.length >= 3).map(p => ({
    type: 'Feature',
    properties: { year: cur.year, plan_id: cur.id, type: p.type, confidence: p.confidence,
                  source: 'traced on ' + cur.title },
    geometry: { type: 'Polygon', coordinates: [[...p.ring, p.ring[0]]] }
  }));
  try {
    const r = await fetch(`/save_boundary/${cur.id}`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ features }) });
    say(r.ok ? `Saved ${features.length} polygon(s) to data/boundaries/${cur.id}.geojson` : `Save failed (${r.status})`);
  } catch (e) { say('Save failed: ' + e.message); }
});

// ---------- general UI ----------
map.on('load', async () => {
  ensureBoundaryLayers();
  plans = await (await fetch('maps.json', { cache: 'no-store' })).json();
  plans.forEach(p => {
    const o = document.createElement('option');
    o.value = p.id; o.textContent = `${p.year} ${p.title}`;
    selEl.appendChild(o);
  });
  ready = true;
  const qid = new URLSearchParams(location.search).get('plan');
  const first = plans.find(p => p.id === qid) || plans[0];
  selEl.value = first.id;
  await showPlan(first);
  const b = corners.reduce((a, c) => [Math.min(a[0], c[0]), Math.min(a[1], c[1]), Math.max(a[2], c[0]), Math.max(a[3], c[1])],
    [180, 90, -180, -90]);
  map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 40, duration: 0 });
});

selEl.addEventListener('change', () => showPlan(plans.find(p => p.id === selEl.value)));
opEl.addEventListener('input', () => {
  opv.textContent = opEl.value;
  ['plan', 'warped'].forEach(id => { if (map.getLayer(id)) map.setPaintProperty(id, 'raster-opacity', +opEl.value / 100); });
});
cpEl.addEventListener('change', () => {
  if (cpEl.checked) { setDrawing(false); say('Control point mode: click a feature on the plan, then the same spot on the base map.'); }
  else { pendingPx = null; renderGcps(); say('Control point mode off.'); }
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && pendingPx) { pendingPx = null; renderGcps(); say('Cancelled.'); } });
useWarpEl.addEventListener('change', applyWarpVisibility);
document.getElementById('cleargcp').addEventListener('click', () => { gcps = []; pendingPx = null; renderGcps(); say('Points cleared (saved file untouched until Save points).'); });
document.getElementById('savegcp').addEventListener('click', async () => {
  if (!cur) return;
  try {
    const r = await fetch(`/save_gcp/${cur.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gcps: gcps.map(g => ({ px: g.px, lnglat: g.lnglat })) }) });
    say(r.ok ? `Saved ${gcps.length} points to data/georef/${cur.id}_gcp.json` : `Save failed (${r.status})`);
  } catch (e) { say('Save failed: ' + e.message); }
});
document.getElementById('warp').addEventListener('click', async () => {
  if (!cur) return;
  if (gcps.length < 3) { say('Need at least 3 points (6+ recommended).'); return; }
  say('Saving points and computing the warp...');
  try {
    await fetch(`/save_gcp/${cur.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gcps: gcps.map(g => ({ px: g.px, lnglat: g.lnglat })) }) });
    const r = await fetch(`/warp/${cur.id}`, { method: 'POST' });
    const j = await r.json();
    if (!j.ok) { say('Warp failed: ' + (j.error || r.status)); return; }
    await loadWarped(cur);
    useWarpEl.checked = true; applyWarpVisibility();
    say('Warp done. ' + describeWarp(j) + ' Per-point leave-one-out errors (m): ' + (j.loo_per_point_m || []).join(', '));
  } catch (e) { say('Warp failed: ' + e.message); }
});
handlesEl.addEventListener('change', () => setHandlesVisible(handlesEl.checked));
document.getElementById('toggle').addEventListener('click', (e) => {
  const vis = map.getLayoutProperty('plan', 'visibility') !== 'none';
  map.setLayoutProperty('plan', 'visibility', vis ? 'none' : 'visible');
  e.target.textContent = vis ? 'Show plan' : 'Hide plan';
});
document.getElementById('reset').addEventListener('click', () => {
  if (!cur) return;
  corners = cur.initialCorners.map(c => c.slice());
  markers.forEach((m, i) => m.setLngLat(corners[i]));
  applyCorners();
  say('Plan reset to the initial guess (saved file untouched until you press Save).');
});
document.getElementById('save').addEventListener('click', async () => {
  if (!cur) return;
  try {
    const r = await fetch(`/save/${cur.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corners }) });
    say(r.ok ? `Saved alignment to data/georef/${cur.id}.json` : `Save failed (${r.status})`);
  } catch (e) { say('Save failed: ' + e.message); }
});
