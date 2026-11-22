// The guided tour (loaded only when it is asked for: the welcome window or the button "?" / the menu; so it does not weigh on the first screen).
// Five steps from data/tour.json; each lights the real elements of the page (the rest is dimmed) and shows a card with the text, "Back / Next / Skip" and a counter.
// A step whose elements are not on the screen is left out (a phone, a folded scale); the panels are NOT opened: the buttons are lit and the card says what is inside.
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
let data = null;

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
    const m = document.getElementById("map").getBoundingClientRect();
    const w = Math.min(520, m.width * 0.7), h = Math.min(300, m.height * 0.36);
    return { left: m.left + (m.width - w) / 2, top: m.top + (m.height - h) / 2 + 24, right: m.left + (m.width + w) / 2, bottom: m.top + (m.height + h) / 2 + 24 };
  }
  const rs = (step.ids || []).map((id) => visible(document.getElementById(id))).filter(Boolean);
  if (!rs.length) return null;
  return { left: Math.min(...rs.map((r) => r.left)), top: Math.min(...rs.map((r) => r.top)), right: Math.max(...rs.map((r) => r.right)), bottom: Math.max(...rs.map((r) => r.bottom)) };
}

export async function startTour({ lang, onClose }) {
  if (document.getElementById("tour")) return;
  try { if (!data) data = await (await fetch("data/tour.json")).json(); } catch (e) { return; }
  const T = (o) => (o && (o[lang] || o.en)) || "";
  const steps = data.steps.filter((s) => rectOf(s));
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
  const close = () => {
    document.removeEventListener("keydown", onKey, true);
    removeEventListener("resize", place);
    root.remove();
    try { localStorage.setItem("tour", "1"); } catch (e) {}
    if (before && before.focus) { try { before.focus(); } catch (e) {} }
    if (onClose) onClose();
  };
  const go = (d) => { const n = i + d; if (n < 0) return; if (n >= steps.length) { close(); return; } i = n; place(); next.focus(); };
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
  place();
  next.focus();
}
