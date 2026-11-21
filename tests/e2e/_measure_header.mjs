// A measurement, not a test (the name starts with _): how wide the header is at different widths of the window, in three languages.
import { startServer, launch, openPage, waitReady, LANGS } from "./helpers.mjs";

const server = await startServer();
const browser = await launch();
const widths = [641, 700, 768, 800, 900, 1000, 1024, 1100, 1200, 1280];
for (const lang of LANGS) {
  const row = [];
  for (const w of widths) {
    const page = await openPage(browser, `${server.url}/?e2e=1&base=off&nostats=1&lang=${lang}#1887`, { width: w, height: 800 });
    await waitReady(page);
    const m = await page.evaluate(() => {
      const top = document.getElementById("top");
      const tr = document.getElementById("topRight");
      const r = tr ? tr.getBoundingClientRect() : null;
      return { need: top.scrollWidth, have: top.clientWidth, out: r ? Math.round(r.right - window.innerWidth) : null };
    });
    row.push(`${w}:${m.need > m.have ? "OVER+" + (m.need - m.have) : "ok"}`);
    await page.ctx.close();
  }
  console.log(lang, row.join("  "));
}
await browser.close();
server.srv.close();
