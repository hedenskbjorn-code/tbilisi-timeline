// Unit tests for tools/verify_enrichment.py anti-hallucination verifier.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1")), "..");
const VERIFY = path.join(ROOT, "tools", "verify_enrichment.py");
const PY = process.platform === "win32" ? "python" : "python3";

function runVerifier(bundleObj) {
  const tmp = path.join(os.tmpdir(), `ve_${Date.now()}_${Math.random().toString(36).slice(2)}.json`);
  fs.writeFileSync(tmp, JSON.stringify(bundleObj), "utf8");
  try {
    const out = execFileSync(PY, ["-P", VERIFY, tmp], { cwd: ROOT, encoding: "utf8" });
    return { ok: true, out };
  } catch (e) {
    return { ok: false, out: (e.stdout || "") + (e.stderr || "") };
  } finally {
    fs.rmSync(tmp, { force: true });
  }
}

test("verify_enrichment passes a clean grounded place card", () => {
  const res = runVerifier({
    items: [{
      id: "park-w104122415",
      kind: "place",
      fetched_text: "The Tbilisi Zoological Park is the oldest and largest zoo in Georgia. Founded in 1927, it is located in the Vere River valley in central Tbilisi.",
      aq: "Founded in 1927, it is located in the Vere River valley in central Tbilisi.",
      texts: {
        ru: "Тбилисский зоологический парк основан в 1927 году в долине реки Вера.",
        en: "The Tbilisi Zoological Park was founded in 1927 in the Vere River valley.",
        ka: "თბილისის ზოოლოგიური პარკი დაარსდა 1927 წელს, მდინარე ვერეს ხეობაში.",
      },
    }],
  });
  assert.equal(res.ok, true, res.out);
});

test("verify_enrichment rejects non-verbatim aq, ungrounded years, cross-language mismatch, script leaks and glossary errors", () => {
  const res = runVerifier({
    items: [
      {
        id: "bad-aq-and-year",
        kind: "place",
        fetched_text: "Vaso Godziashvili was a Georgian theatre actor.",
        aq: "Vaso Godziashvili — famous Soviet actor.",
        texts: {
          ru: "Парк имени Васо Годзиашвили (1905–1976).",
          en: "Park named after Vaso Godziashvili (1905).",
          ka: "ბაღი ატარებს ვასო გოძიაშვილის სახელს.",
        },
      },
      {
        id: "bad-scripts-and-glossary",
        kind: "phase",
        reg_id: "3016",
        fetched_text: "Art Palace on Kargareteli street, Tbilisi.",
        texts: {
          ru: "Особняк начала XIX в. (ул. Каргаретели, 6).",
          en: "Early 19th c. mansion in Dinamо-Arena.",
          ka: "XIX ს. დასაწყისის სასახლე რუსთაველის პროსპექტზე, მდინარე ყურას ნაპირას مزين μετατράπησε yakınında.",
        },
      },
    ],
  });
  assert.equal(res.ok, false);
  assert.match(res.out, /NOT a verbatim substring/);
  assert.match(res.out, /ungrounded year '1905'/);
  assert.match(res.out, /cross-language year mismatch/);
  assert.match(res.out, /contains Cyrillic characters \(possible homoglyph\)/);
  assert.match(res.out, /contains Greek characters/);
  assert.match(res.out, /contains Arabic characters/);
  assert.match(res.out, /contains Turkish diacritics/);
  assert.match(res.out, /use 'გამზირი' instead of 'პროსპექტ'/);
  assert.match(res.out, /use 'მტკვარი'/);
  assert.match(res.out, /chronology contradiction: text claims early 19th c\. but register y0\.\.y1 is 1895\.\.1895/);
});

test("verify_enrichment allows explicitly owner_approved facts", () => {
  const res = runVerifier({
    items: [{
      id: "park-w62668395",
      kind: "place",
      fetched_text: "Сквер имени Гейдара Алиева — сквер в городе Тбилиси.",
      owner_approved_facts: "на правом берегу Куры (район Абанотубани)",
      aq: "Сквер имени Гейдара Алиева — сквер в городе Тбилиси.",
      texts: {
        ru: "Сквер имени Гейдара Алиева — сквер в Тбилиси на правом берегу Куры (район Абанотубани).",
        en: "Heydar Aliyev Park is a garden in Tbilisi on the right bank of the Kura River (Abanotubani).",
        ka: "ჰეიდარ ალიევის სახელობის სკვერი — პარკი თბილისში, მტკვრის მარჯვენა სანაპიროზე (აბანოთუბანი).",
      },
    }],
  });
  assert.equal(res.ok, true, res.out);
});

test("verify_enrichment rejects empty bundle, phase without source, and ungrounded 337 CE year", () => {
  const empty = runVerifier({ items: [] });
  assert.equal(empty.ok, false);
  assert.match(empty.out, /bundle has no items/);

  const noSrc = runVerifier({
    items: [
      {
        id: "phase-no-src",
        kind: "phase",
        texts: {
          ru: "Храм построен в 337 году.",
          en: "Church built in 337.",
          ka: "ტაძარი აიგო 337 წელს.",
        },
      },
      {
        id: "ungrounded-337",
        kind: "phase",
        fetched_text: "Ancient church rebuilt in the Middle Ages.",
        texts: {
          ru: "Храм основан в 337 году.",
          en: "Church founded in 337.",
          ka: "ტაძარი დაარსდა 337 წელს.",
        },
      },
    ],
  });
  assert.equal(noSrc.ok, false);
  assert.match(noSrc.out, /missing 'fetched_text' or 'owner_approved_facts'/);
  assert.match(noSrc.out, /ungrounded year '337'/);
});

test("verify_enrichment --check-repo passes on current repository data", () => {
  const out = execFileSync(PY, ["-P", VERIFY, "--check-repo"], { cwd: ROOT, encoding: "utf8" });
  assert.match(out, /verify_enrichment --check-repo: OK/);
});
