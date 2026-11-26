"""Release 1.8.2: street name histories of eight more streets (idempotent; --dry-run only checks).

The names and years come from the Wikipedia pages named in the spec (ru or ka); only what a page states.
The Georgian texts are Gemini's (work/gemini/results/tbilisi_streets190_ka.md), checked here:
no Cyrillic, no the calque of the word "prospect", every ID present.
Spec: the SPEC dict below (names, years, notes, sources); geometry is in site/data/street_geom.json (tools/build_street_labels.py).
"""
import json, os, re, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(R, "work", "gemini", "results/tbilisi_streets190_ka.md")
SPEC = os.path.join(R, "work", "gemini", "..", "..", "tools", "streets182_spec.json")
NAMES = os.path.join(R, "site", "data", "street_names.json")
VERIFIED = os.path.join(R, "data", "street_names_verified.json")
CHANGELOG = os.path.join(R, "site", "data", "changelog.json")
DRY = "--dry-run" in sys.argv
CALQUE = "პროსპექტ"
# the Georgian forms that the checked page gives differently from Gemini's first answer
KA_OVERRIDE = {"S2_n0": "ლორის-მელიქოვის ქუჩა"}  # ka.wikipedia 'ლადო გუდიაშვილის ქუჩა': "1877 წელს ქუჩას დაერქვა ლორის-მელიქოვის სახელი"


def read(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write(p, obj, compact=False, indent=1):
    # each file keeps the form it has: street_names.json is compact, the others use an indent of one space; no final newline
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(obj, ensure_ascii=False, indent=indent)
    with open(p, "rb") as f:
        crlf = b"\x0d\x0a" in f.read()  # keep the line endings the file already has
    if crlf:
        data = data.replace(chr(10), chr(13) + chr(10))
    b = data.encode("utf-8")  # encode first: a failure must not truncate the file
    if not DRY:
        with open(p, "wb") as f:
            f.write(b)


def parse_result():
    ka = {}
    for line in open(RES, encoding="utf-8").read().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.match(r"^(S\d+_(now|n\d+|note)|CL190)$", cells[0]):
            ka[cells[0]] = cells[1]
    ka.update(KA_OVERRIDE)
    return ka


def main():
    spec = read(SPEC)
    ST, CLOG = spec["ST"], spec["CLOG"]
    ka = parse_result()
    entries, verified = [], []
    for i, (key, now, iv, nru, nen, src) in enumerate(ST):
        need = ["S%d_now" % i, "S%d_note" % i] + ["S%d_n%d" % (i, j) for j in range(len(iv))]
        miss = [n for n in need if not ka.get(n)]
        assert not miss, "missing Georgian text: %s" % miss
        for n in need:
            assert not re.search(r"[Ѐ-ӿ]", ka[n]), "Cyrillic in %s" % n
            assert CALQUE not in ka[n], "calque in %s" % n
        entries.append({
            "now": {"ru": now[0], "en": now[1], "ka": ka["S%d_now" % i]},
            "iv": [[a, b, {"ru": ru, "en": en, "ka": ka["S%d_n%d" % (i, j)]}] for j, (a, b, ru, en) in enumerate(iv)],
            "note": {"ru": nru, "en": nen, "ka": ka["S%d_note" % i]},
            "src": src,
        })
        verified.append({"street_en": key, "names": [{"name": ru, "from": a, "to": b} for a, b, ru, en in iv], "note": nru, "src": src})
    assert not re.search(r"[Ѐ-ӿ]", ka["CL190"]) and CALQUE not in ka["CL190"]

    d = read(NAMES)
    have = {s["now"]["en"] for s in d["streets"]}
    new = [e for e in entries if e["now"]["en"] not in have]
    d["streets"].extend(new)
    d["note"] = "from data/street_names_verified.json: only names with years stated by the cited Wikipedia pages"
    write(NAMES, d, compact=True)

    v = read(VERIFIED)
    add = v.setdefault("additions_2026_11_22", {"note": "Release 1.8.2: names and years as stated by the cited ru/ka Wikipedia pages (read through the API on 2026-11-22).", "streets": []})
    seen = {s["street_en"] for s in add["streets"]}
    add["streets"].extend(s for s in verified if s["street_en"] not in seen)
    write(VERIFIED, v)

    rel = read(CHANGELOG)
    if rel[0]["version"] != "1.8.2":
        rel.insert(0, {"version": "1.8.2", "date": "2026-11-22", "items": [
            {"t": "new", "ru": CLOG[0], "en": CLOG[1], "ka": ka["CL190"]},
            {"t": "fix", "ru": "В грузинских текстах слово «проспект» (калька с русского) заменено на `გამზირი` во всех формах.".replace("`", ""),
             "en": "In the Georgian texts the word for 'prospect' (a calque of the Russian) is replaced by the Georgian word for 'avenue' in all its forms.",
             "ka": "ქართულ ტექსტებში რუსულიდან გადმოკოპირებული სიტყვა „პროსპექტი“ ყველა ფორმით შეიცვალა სიტყვით „გამზირი“."}]})
    write(CHANGELOG, rel)
    print("streets added: %d (already there: %d); %s" % (len(new), len(entries) - len(new), "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
