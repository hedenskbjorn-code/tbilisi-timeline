// The guided tour (loaded only when it is asked for: the welcome window or the button "?" / the menu; so it does not weigh on the first screen).
// Five steps from data/tour.json; each lights the real elements of the page (the rest is dimmed) and shows a card with the text, "Back / Next / Skip" and a counter.
// A step whose elements are not on the screen is left out (a phone, a folded scale). The panels are not opened by the steps about the buttons (the buttons are lit and the card says what is inside); the steps about
// the FILTERS open the panel (step.open = "filters") and a block of it (step.section), light elements inside it (step.sel: CSS selectors) and put everything back as it was when the tour moves on or ends.
const CSS = `
#tour{position:fixed;inset:0;z-index:40}
#tourHole{position:fixed;border-radius:10px;border:2px solid #fff;box-shadow:0 0 0 100vmax rgba(0,0,0,.6);pointer-events:none;transition:left .25s,top .25s,width .25s,height .25s}
#tourHole::after{content:"";position:absolute;inset:-6px;border-radius:14px;border:2px solid #fff;opacity:.7;animation:tourPulse 1.6s ease-out infinite}
@keyframes tourPulse{0%{transform:scale(.97);opacity:.8}100%{transform:scale(1.08);opacity:0}}
@media (prefers-reduced-motion:reduce){#tourHole{transition:none}#tourHole::after{animation:none}}
#tourCard{position:fixed;box-sizing:border-box;width:min(340px,calc(100vw - 16px));background:var(--panel,#fff);color:var(--fg,#222);border-radius:12px;padding:14px 16px;box-shadow:0 6px 28px #0006;font-size:14px;line-height:1.4}
#tourCard h3{margin:0 0 6px;font-size:16px}
#tourCard p{margin:0 0 12px}
#tourCard .tf{display:flex;align-items:center;gap:8px}
#tourCard .tc{flex:1;color:var(--muted,#666);font-size:12px}
#tourCard button.skip{border:0;background:none;color:var(--muted,#666);cursor:pointer;font:inherit;padding:6px 4px}
`;
let data = null, FREE = null;

const visible = (el) => {
  if (!el) return null;
  const r = el.getBoundingClientRect();
  if (r.width < 1 || r.height < 1 || r.bottom <= 0 || r.right <= 0 || r.top >= innerHeight || r.left >= innerWidth) return null;
  if (getComputedStyle(el).visibility === "hidden") return null;
  return r;
};

// the rectangle of a step: the union of the visible elements (or the middle of the map)
function rectOf(step) {
  if (step.rect === "map") {
    const f = FREE && FREE(), mm = document.getElementById("map").getBoundingClientRect();
    const m = f && f.right - f.left > 80 && f.bottom - f.top > 80 ? { left: f.left, top: f.top, width: f.right - f.left, height: f.bottom - f.top } : mm;        // the part of the map that no panel covers
    const w = Math.min(520, m.width * 0.7), h = Math.min(300, m.height * 0.36);
    return { left: m.left + (m.width - w) / 2, top: m.top + (m.height - h) / 2 + 24, right: m.left + (m.width + w) / 2, bottom: m.top + (m.height + h) / 2 + 24 };
  }
  const rs = [...(step.ids || []).map((id) => document.getElementById(id)), ...(step.sel || []).flatMap((q) => [...document.querySelectorAll(q)])].map(visible).filter(Boolean);
  if (!rs.length) return null;
  return { left: Math.min(...rs.map((r) => r.left)), top: Math.min(...rs.map((r) => r.top)), right: Math.max(...rs.map((r) => r.right)), bottom: Math.max(...rs.map((r) => r.bottom)) };
}

export async function startTour({ lang, onClose, free, panel }) {
  if (document.getElementById("tour")) return;
  FREE = free || null;
  try { if (!data) data = await (await fetch("data/tour.json")).json(); } catch (e) { return; }
  const T = (o) => (o && (o[lang] || o.en)) || "";
  const steps = data.steps.filter((s) => (s.open && panel) || rectOf(s));       // a step that opens a panel is kept: its elements are on the screen only after the panel is open
  if (!steps.length) return;
  if (!document.getElementById("tourCss")) { const st = document.createElement("style"); st.id = "tourCss"; st.textContent = CSS; document.head.appendChild(st); }
  const before = document.activeElement;
  const root = document.createElement("div"), hole = document.createElement("div"), card = document.createElement("div");
  root.id = "tour"; hole.id = "tourHole"; card.id = "tourCard";
  card.setAttribute("role", "dialog"); card.setAttribute("aria-modal", "true"); card.setAttribute("aria-labelledby", "tourTitle");
  root.append(hole, card);
  document.body.appendChild(root);
  let i = 0;
  const h3 = document.createElement("h3"), p = document.createElement("p"), tf = document.createElement("div"), tc = document.createElement("span");
  h3.id = "tourTitle";
  tf.className = "tf"; tc.className = "tc";
  const back = document.createElement("button"), skip = document.createElement("button"), next = document.createElement("button");
  for (const b of [back, skip, next]) b.type = "button";
  back.className = "chip"; next.className = "chip primary"; skip.className = "skip";
  back.textContent = T(data.ui.prev); skip.textContent = T(data.ui.skip);
  tf.append(tc, skip, back, next);
  card.append(h3, p, tf);
  const place = () => {
    const s = steps[i], r = rectOf(s);
    if (!r) return;
    const pad = 6, vw = innerWidth, vh = innerHeight;
    hole.style.left = r.left - pad + "px"; hole.style.top = r.top - pad + "px";
    hole.style.width = r.right - r.left + 2 * pad + "px"; hole.style.height = r.bottom - r.top + 2 * pad + "px";
    h3.textContent = T(s.title); p.textContent = T(s.text);
    tc.textContent = (i + 1) + " " + T(data.ui.of) + " " + steps.length;
    back.hidden = i === 0;
    next.textContent = T(i === steps.length - 1 ? data.ui.done : data.ui.next);
    card.style.left = card.style.top = card.style.bottom = "";
    const cw = card.offsetWidth, ch = card.offsetHeight, below = r.bottom + pad + 12, above = r.top - pad - 12 - ch;
    let top = below + ch <= vh - 8 ? below : above >= 8 ? above : Math.max(8, vh - ch - 8);
    let left = Math.min(Math.max(8, (r.left + r.right) / 2 - cw / 2), vw - cw - 8);
    card.style.left = left + "px"; card.style.top = top + "px";
  };
  // the panel and the blocks that the tour opened are closed again when it moves to a step that does not need them and when it ends
  const openedPanels = new Set(), openedSections = new Set();
  const settle = () => new Promise((r) => setTimeout(r, 120));
  const prep = async (s) => {
    if (panel) {
      for (const k of [...openedPanels]) if (k !== s.open) { panel.set(k, false); openedPanels.delete(k); }
      if (s.open && !panel.get(s.open)) { panel.set(s.open, true); openedPanels.add(s.open); }
    }
    for (const d of [...openedSections]) if (!s.section || d.dataset.sec !== s.section) { d.open = false; openedSections.delete(d); }
    const d = s.section && document.querySelector('details[data-sec="' + s.section + '"]');
    if (d && !d.open) { d.open = true; openedSections.add(d); }
    if (s.open || s.section) { await settle(); if (d && d.scrollIntoView) d.scrollIntoView({ block: "nearest" }); }
  };
  const close = () => {
    document.removeEventListener("keydown", onKey, true);
    for (const d of openedSections) d.open = false;
    if (panel) for (const k of openedPanels) panel.set(k, false);
    removeEventListener("resize", place);
    root.remove();
    try { localStorage.setItem("tour", "1"); } catch (e) {}
    if (before && before.focus) { try { before.focus(); } catch (e) {} }
    if (onClose) onClose();
  };
  let moving = false;
  const go = async (d) => {
    if (moving) return;
    let n = i + d;
    if (n < 0) return;
    if (n >= steps.length) { close(); return; }
    moving = true;
    for (;;) {                                                            // a step whose elements cannot be found even after its panel is open is passed over
      await prep(steps[n]);
      if (rectOf(steps[n])) break;
      n += d || 1;
      if (n < 0 || n >= steps.length) { n = Math.min(Math.max(n, 0), steps.length - 1); await prep(steps[n]); break; }
    }
    i = n; moving = false; place(); next.focus();
  };
  const onKey = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
    else if (e.key === "ArrowRight" || e.key === "Enter" && e.target !== skip && e.target !== back) { e.preventDefault(); go(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
    else if (e.key === "Tab") {                                           // the focus stays on the card
      const f = [back, skip, next].filter((b) => !b.hidden), k = f.indexOf(document.activeElement);
      e.preventDefault();
      f[(k + (e.shiftKey ? f.length - 1 : 1)) % f.length].focus();
    }
  };
  next.addEventListener("click", () => go(1));
  back.addEventListener("click", () => go(-1));
  skip.addEventListener("click", close);
  document.addEventListener("keydown", onKey, true);
  addEventListener("resize", place);
  prep(steps[0]).then(() => { place(); next.focus(); });
}
