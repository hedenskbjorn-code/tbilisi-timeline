"""Release 1.8.3: name histories of 5 more streets of the blog list of the toponyms renamed in 1987-1991 (idempotent; --dry-run only checks).

Each name, year and quote was checked against the text of the ka.wikipedia page (tools/streets_kv2_spec.json; Tamar Mepe Avenue: ru.wikipedia for the year 1989 and ka.wikipedia for 1935).
The Georgian notes are Gemini's (work/gemini/results/tbilisi_kvamli_notes2.md), checked here: no Cyrillic, no the calque of the word "prospect", every ID present.
"""
import json, os, re, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPEC = os.path.join(R, "tools", "streets_kv2_spec.json")
RES = os.path.join(R, "work", "gemini", "results/tbilisi_kvamli_notes2.md")
NAMES = os.path.join(R, "site", "data", "street_names.json")
VERIFIED = os.path.join(R, "data", "street_names_verified.json")
LIST = os.path.join(R, "data", "street_renamed_1987_1991.json")
CHANGELOG = os.path.join(R, "site", "data", "changelog.json")
DRY = "--dry-run" in sys.argv
CALQUE = "პროსპექტ"
CR, LF = chr(13), chr(10)


def read(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write(p, obj, compact=False):
    # each file keeps the form it has: street_names.json is compact, the others use an indent of one space; no final newline; the line endings stay
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(obj, ensure_ascii=False, indent=1)
    with open(p, "rb") as f:
        crlf = (CR + LF).encode() in f.read()
    if crlf:
        data = data.replace(LF, CR + LF)
    b = data.encode("utf-8")  # encode first: a failure must not truncate the file
    if not DRY:
        with open(p, "wb") as f:
            f.write(b)


def parse_result():
    ka = {}
    for line in open(RES, encoding="utf-8").read().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.match(r"^(K\d+_note|CL183)$", cells[0]):
            ka[cells[0]] = cells[1]
    return ka


def main():
    sp = read(SPEC)
    ka = parse_result()
    entries, verified = [], []
    for s in sp["spec"]:
        k = "K%s_note" % s["n"]
        assert ka.get(k), "missing Georgian note " + k
        assert not re.search(r"[Ѐ-ӿ]", ka[k]) and CALQUE not in ka[k], "bad Georgian text in " + k
        entries.append({"now": s["now"], "iv": s["iv"], "note": {"ru": s["note"]["ru"], "en": s["note"]["en"], "ka": ka[k]}, "src": s["src"]})
        verified.append({"street_en": s["key"], "names": [{"name": i[2]["ru"], "from": i[0], "to": i[1]} for i in s["iv"]], "src": s["src"], "district": s["district"]})
    assert ka.get("CL183") and not re.search(r"[Ѐ-ӿ]", ka["CL183"]) and CALQUE not in ka["CL183"]

    d = read(NAMES)
    have = {x["now"]["en"] for x in d["streets"]}
    new = [e for e in entries if e["now"]["en"] not in have]
    d["streets"].extend(new)
    write(NAMES, d, compact=True)

    v = read(VERIFIED)
    add = v.setdefault("additions_2026_11_22_renamed_1988_1991_part2", {"note": "Release 1.8.3: the years found by the second round (see data/street_renamed_1987_1991.json); each quote compared with the page text.", "streets": []})
    seen = {x["street_en"] for x in add["streets"]}
    add["streets"].extend(x for x in verified if x["street_en"] not in seen)
    write(VERIFIED, v)

    lst = read(LIST)
    added = {int(s["n"]) for s in sp["spec"]}
    for s in lst["streets"]:
        if s["n"] in added:
            s["status"] = "done"
    write(LIST, lst)

    rel = read(CHANGELOG)
    if rel[0]["version"] != "1.8.3":
        rel.insert(0, {"version": "1.8.3", "date": "2026-11-22", "items": [{"t": "new", "ru": sp["CL"][0], "en": sp["CL"][1], "ka": ka["CL183"]}]})
    write(CHANGELOG, rel)
    print("streets added: %d (already there: %d); %s" % (len(new), len(entries) - len(new), "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
