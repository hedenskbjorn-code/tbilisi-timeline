// "Support the project": a heart button in the header opens a small window with a link to the payment page of the owner's bank and its QR code.
// The link lives in data/support.json (fetched only when the window is opened); the site itself takes no payments and stores nothing.
(function () {
  "use strict";
  const TXT = {
    ru: { btn: "Поддержать проект", title: "Поддержать проект", lead: "Проект некоммерческий, без рекламы и подписок. Если карта вам полезна, можно поддержать её развитие переводом. Это добровольно: сайт остаётся открытым для всех.", go: "Перейти к оплате (TBC)", qr: "Или отсканируйте QR в приложении банка", how: "Платёж в лари (GEL), сумму вы вводите сами. Среди способов на странице TBC: Google Pay или перевод из Банка Грузии, Liberty, Credo.", note: "Оплата происходит на странице банка: сайт не получает и не хранит данные платежа.", close: "Закрыть", fail: "Не удалось загрузить ссылку на оплату. Попробуйте позже." },
    en: { btn: "Support the project", title: "Support the project", lead: "The project is non-commercial, with no ads and no subscriptions. If the map is useful to you, you can support its development with a transfer. It is voluntary: the site stays open to everyone.", go: "Go to the payment page (TBC)", qr: "Or scan the QR in your bank app", how: "The payment is in lari (GEL); you enter the amount yourself. Among the options on the TBC page: Google Pay, or a transfer from Bank of Georgia, Liberty or Credo.", note: "The payment is made on the bank's page: this site neither receives nor stores any payment data.", close: "Close", fail: "Could not load the payment link. Please try later." },
    ka: { btn: "პროექტის მხარდაჭერა", title: "პროექტის მხარდაჭერა", lead: "პროექტი არაკომერციულია, რეკლამისა და გამოწერის გარეშე. თუ რუკა თქვენთვის სასარგებლოა, შეგიძლიათ მხარი დაუჭიროთ მის განვითარებას გადარიცხვით. ეს ნებაყოფლობითია: საიტი ყველასთვის ღია რჩება.", go: "გადახდის გვერდზე გადასვლა (TBC)", qr: "ან დაასკანირეთ QR ბანკის აპლიკაციაში", how: "გადახდა ლარშია (GEL), თანხას თავად შეიყვანთ. TBC-ის გვერდზე ხელმისაწვდომ ვარიანტებს შორისაა Google Pay და გადარიცხვა საქართველოს ბანკიდან, ლიბერთი ბანკიდან ან კრედო ბანკიდან.", note: "გადახდა ხდება ბანკის გვერდზე: საიტი არ იღებს და არ ინახავს გადახდის მონაცემებს.", close: "დახურვა", fail: "გადახდის ბმულის ჩატვირთვა ვერ მოხერხდა. სცადეთ მოგვიანებით." },
  };
  const $ = (id) => document.getElementById(id);
  const lang = () => { const l = (document.documentElement.lang || "en").slice(0, 2); return TXT[l] ? l : "en"; };
  const S = () => TXT[lang()];
  let cfg = null, modal = null, lastFocus = null;

  function retext() {
    const b = $("btnSupport"); if (b) { b.title = S().btn; b.setAttribute("aria-label", S().btn); }
    const s = $("btnSupportSide"); if (s) s.textContent = "❤ " + S().btn;
    if (modal && !modal.hidden) fill();
  }
  async function loadCfg() {
    if (cfg) return cfg;
    try {
      const r = await fetch("data/support.json");
      const j = await r.json();
      if (typeof j.url === "string" && /^https:\/\/transfer\.tbcbank\.ge\//.test(j.url)) cfg = j;     // only the bank's own address is ever used as the link
    } catch (e) {}
    return cfg;
  }
  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function fill() {
    const box = modal.firstChild; box.textContent = "";
    const L = S();
    const h = el("h2", "", L.title); h.id = "spTitle";
    box.appendChild(h);
    box.appendChild(el("p", "", L.lead));
    if (!cfg) { box.appendChild(el("p", "small", L.fail)); }
    else {
      const a = el("a", "chip primary spgo", L.go); a.href = cfg.url; a.target = "_blank"; a.rel = "noopener noreferrer";
      box.appendChild(a);
      const fig = el("div", "spqr");
      const img = el("img"); img.src = "img/support-qr.png"; img.width = 180; img.height = 180; img.alt = "QR"; fig.appendChild(img);
      fig.appendChild(el("div", "small", L.qr));
      box.appendChild(fig);
      box.appendChild(el("p", "small", L.how));
      box.appendChild(el("p", "small", L.note));
    }
    const row = el("div", "modalbtns"), x = el("button", "chip", L.close); x.type = "button"; x.addEventListener("click", close);
    row.appendChild(x); box.appendChild(row);
  }
  function close() { if (modal) modal.hidden = true; if (lastFocus && lastFocus.focus) lastFocus.focus(); }
  async function open() {
    lastFocus = document.activeElement;
    if (!modal) {
      modal = el("div", "modal"); modal.hidden = true; modal.setAttribute("role", "dialog"); modal.setAttribute("aria-modal", "true"); modal.setAttribute("aria-labelledby", "spTitle");
      modal.appendChild(el("div", "modalbox"));
      modal.addEventListener("click", (e) => { if (e.target === modal) close(); });
      document.addEventListener("keydown", (e) => { if (e.key === "Escape" && modal && !modal.hidden) close(); });
      document.body.appendChild(modal);
    }
    await loadCfg();
    fill(); modal.hidden = false;
    const f = modal.querySelector("a,button"); if (f) f.focus();
  }
  document.addEventListener("DOMContentLoaded", () => {
    for (const id of ["btnSupport", "btnSupportSide"]) { const b = $(id); if (b) b.addEventListener("click", open); }
    retext();
    new MutationObserver(retext).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  });
})();
