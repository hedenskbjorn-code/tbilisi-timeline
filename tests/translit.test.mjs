// Unit tests of site/translit.js (the English and Russian forms of Georgian names, addresses and dates of the register).
// Run: node --test tests/
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const G = require("../site/translit.js");
G.setDict({ names: { "თბილისი": { en: "Tbilisi", ru: "Тбилиси" } }, streets: { "გამზ.": { en: "Ave.", ru: "пр." }, "ქუჩა": { en: "St.", ru: "ул." } } });

test("nameInfo: the Georgian original stays for ka and for unknown names", () => {
  assert.deepEqual(G.nameInfo("თბილისი", "ka", null), { text: "თბილისი", src: "orig" });
  assert.deepEqual(G.nameInfo("უცნობი", "en", null), { text: "უცნობი", src: "orig" });
});
test("nameInfo: the dictionary and the title of the Wikipedia article", () => {
  assert.deepEqual(G.nameInfo("თბილისი", "en", null), { text: "Tbilisi", src: "ai" });
  assert.deepEqual(G.nameInfo("რაღაც", "en", "en:The Place (Tbilisi)|ru:Место"), { text: "The Place", src: "wiki" });   // the brackets of the title are cut
  assert.deepEqual(G.nameInfo("რაღაც", "ru", "en:The Place|ru:Место (Тбилиси)"), { text: "Место", src: "wiki" });
});
test("address: the street words are translated, the number stays", () => {
  assert.equal(G.address("რუსთაველის გამზ. 12", "en"), "Rustaveli Ave. 12");
  assert.equal(G.address("რუსთაველის გამზ. 12", "ru"), "Руставели пр. 12");
  assert.equal(G.address("ბარათაშვილის ქუჩა 5", "en"), "Baratashvili St. 5");
});
test("address: ka, empty and null are returned as they are", () => {
  assert.equal(G.address("რუსთაველის გამზ. 12", "ka"), "რუსთაველის გამზ. 12");
  assert.equal(G.address("", "en"), "");
  assert.equal(G.address(null, "en"), null);
});
test("date: a century with a part of it", () => {
  assert.equal(G.date("მე-19 საუკუნის დასაწყისი", "en"), "beginning of the 19th century");
  assert.equal(G.date("მე-19 საუკუნის დასაწყისი", "ru"), "начало XIX века");
  assert.equal(G.date("19-ე საუკუნის მეორე ნახევარი", "en"), "second half of the 19th century");
  assert.equal(G.date("19-ე საუკუნის მეორე ნახევარი", "ru"), "вторая половина XIX века");
});
test("date: decades and years", () => {
  assert.equal(G.date("1850-იანი წლები", "en"), "1850s");
  assert.equal(G.date("1850-იანი წლები", "ru"), "1850-е годы");
  assert.equal(G.date("1887 წ.; 19-ე საუკუნე", "en"), "1887; 19th century");
});
test("date: a range of centuries is a range (regression: only the last century was shown)", () => {
  assert.equal(G.date("მე-17-18 საუკუნეები", "en"), "17th-18th centuries");
  assert.equal(G.date("მე-17-18 საუკუნეები", "ru"), "XVII-XVIII века");
  assert.equal(G.date("18-19 საუკუნეები", "en"), "18th-19th centuries");
});
test("date: a range with a part of the century or a year stays as the register text", () => {
  assert.equal(G.date("მე-16-20 საუკუნის შუახანი", "en"), "მე-16-20 საუკუნის შუახანი");
  assert.equal(G.date("მე-17-18 საუკუნეები (1735 წლამდე)", "ru"), "მე-17-18 საუკუნეები (1735 წლამდე)");
});
test("date: ka, plain numbers and unknown texts are returned as they are", () => {
  assert.equal(G.date("მე-19 საუკუნის დასაწყისი", "ka"), "მე-19 საუკუნის დასაწყისი");
  assert.equal(G.date("1887", "en"), "1887");
  assert.equal(G.date("უცნობი", "en"), "უცნობი");
});
