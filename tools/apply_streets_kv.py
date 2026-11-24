"""Release 1.8.2, part two: name histories of 26 streets renamed in 1988-1991 (idempotent; --dry-run only checks).

The list of renamed streets is from a blog post; every name, year and quote was checked against the text of the ka.wikipedia page (see tools/streets_kv_spec.json: only what a page states;
a decade ("30s") or a year of a plan or directory is marked as such in the note). The Georgian notes are Gemini's (work/gemini/results/tbilisi_kvamli_notes.md), checked here:
no Cyrillic, no the calque of the word "prospect", every ID present.
"""
import json, os, re, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPEC = os.path.join(R, "tools", "streets_kv_spec.json")
RES = os.path.join(R, "work", "gemini", "results/tbilisi_kvamli_notes.md")
NAMES = os.path.join(R, "site", "data", "street_names.json")
VERIFIED = os.path.join(R, "data", "street_names_verified.json")
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
        if len(cells) >= 2 and re.match(r"^(K\d+_note|CL182b)$", cells[0]):
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
        entries.append({
            "now": s["now"],
            "iv": [[s["from"], s["to"], s["old"]]],
            "note": {"ru": s["note"]["ru"], "en": s["note"]["en"], "ka": ka[k]},
            "src": s["src"],
        })
        verified.append({"street_en": s["key"], "names": [{"name": s["old"]["ru"], "from": s["from"], "to": s["to"], "from_kind": s["from_kind"]}], "src": s["src"], "district": s["district"]})
    assert ka.get("CL182b") and not re.search(r"[Ѐ-ӿ]", ka["CL182b"]) and CALQUE not in ka["CL182b"]

    d = read(NAMES)
    have = {x["now"]["en"] for x in d["streets"]}
    new = [e for e in entries if e["now"]["en"] not in have]
    d["streets"].extend(new)
    write(NAMES, d, compact=True)

    v = read(VERIFIED)
    add = v.setdefault("additions_2026_11_22_renamed_1988_1991", {"note": "From a blog list of the toponyms renamed in 1987-1991; each name, year and quote checked against the ka.wikipedia page (2026-11-22). Not added (no page year, or the year of the old name unknown): about 40 streets of the list, Archil Tsagareli Street (formerly Kronshtadtskaya) among them.", "streets": []})
    seen = {x["street_en"] for x in add["streets"]}
    add["streets"].extend(x for x in verified if x["street_en"] not in seen)
    write(VERIFIED, v)

    rel = read(CHANGELOG)
    r0 = rel[0]
    assert r0["version"] == "1.8.2"
    if not any(i["ru"] == sp["CL"][0] for i in r0["items"]):
        r0["items"].insert(1, {"t": "new", "ru": sp["CL"][0], "en": sp["CL"][1], "ka": ka["CL182b"]})
    write(CHANGELOG, rel)
    print("streets added: %d (already there: %d); %s" % (len(new), len(entries) - len(new), "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
