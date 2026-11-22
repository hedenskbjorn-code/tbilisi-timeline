"""Release 1.8.4: 38 events from the textbooks of the history of Georgia (idempotent; --dry-run only checks).

Every event was found in the text of a textbook (the pages are the PDF pages of the files read: data/cache/ocr/*.txt) and compared with it claim by claim;
the sources are the books themselves ({"label": "<reference>, PDF p. N", "book": true}, no link: the books are not published), a Wikipedia page is added only where the page states the event.
Two old events get a more exact date (853 and 1918). The Georgian texts are Gemini's (for_gemini/from_desktop/tbilisi_textbook_events_result.md), checked here:
no Cyrillic, no the calque of the word "prospect", every ID present. Spec: tools/textbook_events_spec.json.
After it run: tools/build_bibliography.py
"""
import bisect
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPEC = os.path.join(ROOT, "tools", "textbook_events_spec.json")
RES = os.path.join(ROOT, "for_gemini", "from_desktop", "tbilisi_textbook_events_result.md")
EVP = os.path.join(ROOT, "site", "data", "history_events.json")
CHANGELOG = os.path.join(ROOT, "site", "data", "changelog.json")
DRY = "--dry-run" in sys.argv
CYR = re.compile("[Ѐ-ӿ]")
CALQUE = "პროსპექტ"


def load_checked(path):
    raw = open(path, encoding="utf-8", newline="").read()
    doc = json.loads(raw)
    assert json.dumps(doc, ensure_ascii=False, indent=1) == raw, "the file layout changed, refusing to rewrite " + path
    return doc, ("\r\n" in raw)


def write(path, doc, crlf):
    s = json.dumps(doc, ensure_ascii=False, indent=1)
    if crlf:
        s = s.replace("\n", "\r\n")
    b = s.encode("utf-8")  # encode first: a failure must not truncate the file
    if not DRY:
        open(path, "wb").write(b)


def parse_result():
    ka = {}
    for line in open(RES, encoding="utf-8").read().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.match(r"^(T\d+_(text|note)|U\d+_note|CL184)$", cells[0]):
            ka[cells[0]] = cells[1]
    return ka


def main():
    spec = json.load(open(SPEC, encoding="utf-8"))
    ka = parse_result()
    need = []
    for e in spec["events"]:
        need.append(e["id"] + "_text")
        if e["note"]["ru"]:
            need.append(e["id"] + "_note")
    need += [u["id"] + "_note" for u in spec["updates"]] + ["CL184"]
    miss = [n for n in need if not ka.get(n)]
    assert not miss, "missing Georgian text: %s" % miss
    for n in need:
        assert not CYR.search(ka[n]) and CALQUE not in ka[n], "bad Georgian text in " + n

    doc, crlf = load_checked(EVP)
    events = doc["events"]
    have = {(x["year"], x["date"], x["ru"]) for x in events}
    added = 0
    for e in spec["events"]:
        if (e["year"], e["date"], e["ru"]) in have:
            continue
        ev = {"year": e["year"], "date": e["date"], "cat": e["cat"], "src": e["src"], "ru": e["ru"], "en": e["en"], "ka": ka[e["id"] + "_text"]}
        if e["note"]["ru"]:
            ev["note"] = {"ru": e["note"]["ru"], "en": e["note"]["en"], "ka": ka[e["id"] + "_note"]}
        events.insert(bisect.bisect_right([x["year"] for x in events], e["year"]), ev)
        added += 1
    upd = 0
    marks = {853: "Буга", 1918: "Основан Тбилисский государственный университет"}
    for u in spec["updates"]:
        tgt = [x for x in events if x["year"] == u["year"] and marks[u["year"]] in x["ru"]]
        assert len(tgt) == 1, "the event to update is not found or not unique: %s" % u["id"]
        x = tgt[0]
        if x["date"] != u["date"]:
            x["date"] = u["date"]
            upd += 1
        note = x.get("note") or {"ru": "", "en": "", "ka": ""}
        for l, add in (("ru", u["note"]["ru"]), ("en", u["note"]["en"]), ("ka", ka[u["id"] + "_note"])):
            if add not in note[l]:
                note[l] = (note[l].rstrip() + " " + add).strip()
                upd += 1
        x["note"] = note
        if not any(isinstance(s, dict) and s.get("label") == u["src"]["label"] for s in x["src"]):
            x["src"].append(u["src"])
            upd += 1
    write(EVP, doc, crlf)

    rel, rcrlf = None, False
    raw = open(CHANGELOG, encoding="utf-8", newline="").read()
    rel = json.loads(raw)
    rcrlf = "\r\n" in raw
    if rel[0]["version"] != "1.8.4":
        rel.insert(0, {"version": "1.8.4", "date": "2026-11-22", "items": []})
    item = {"t": "new", "ru": spec["CL"][0], "en": spec["CL"][1], "ka": ka["CL184"]}
    if not any(i["ru"] == item["ru"] for i in rel[0]["items"]):
        rel[0]["items"].insert(0, item)
    s = json.dumps(rel, ensure_ascii=False, indent=1)
    if rcrlf:
        s = s.replace("\n", "\r\n")
    if not DRY:
        open(CHANGELOG, "wb").write(s.encode("utf-8"))
    print("events added: %d, updates of old events: %d; %s" % (added, upd, "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
