"""Release 1.8.3, part three: name histories of 23 more streets of the blog list of the toponyms renamed in 1987-1991 (idempotent; --dry-run only checks).

The names and years are from the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008): the quotes of the report of Gemini were compared with the text of its PDF (data/street_renamed_1987_1991.json, field enc2008;
the PDF itself is in data/cache/nplg_pdfs, not committed). The source link of an entry is a Wikipedia page about the street or the person, the note names the book.
The Georgian notes are Gemini's (for_gemini/from_desktop/tbilisi_kvamli_notes3_result.md), checked here: no Cyrillic, no the calque of the word "prospect", every ID present.
Also: the old name Ordzhonikidze is added to Tevdore Mghvdeli Street (the street was divided in 1990), the item of the changelog of 1.8.3 gets the new count.
"""
import json, os, re, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPEC = os.path.join(R, "tools", "streets_kv3_spec.json")
RES = os.path.join(R, "for_gemini", "from_desktop", "tbilisi_kvamli_notes3_result.md")
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
        if len(cells) >= 2 and re.match(r"^(K\d+_note|CL183b)$", cells[0]):
            ka[cells[0]] = cells[1]
    return ka


def main():
    sp = read(SPEC)
    ka = parse_result()
    # Gemini counted the 23 numbers of its table; the item of the changelog speaks of the 28 streets of the whole release (5 + 23): the number is set here
    ka["CL183b"] = ka["CL183b"].replace("კიდევ 23", "კიდევ %d" % (len(sp["spec"]) + 5))
    entries, verified = [], []
    for s in sp["spec"]:
        k = "K%s_note" % s["n"]
        assert ka.get(k), "missing Georgian note " + k
        assert not re.search(r"[Ѐ-ӿ]", ka[k]) and CALQUE not in ka[k], "bad Georgian text in " + k
        for i in s["iv"]:
            assert not re.search(r"[Ѐ-ӿ]", i[2]["ka"]) and not re.search(r"[Ѐ-ӿ]", s["now"]["ka"])
        assert s["src"] and s["src"].startswith("https://")
        entries.append({"now": s["now"], "iv": s["iv"], "note": {"ru": s["note"]["ru"], "en": s["note"]["en"], "ka": ka[k]}, "src": s["src"]})
        verified.append({"street_en": s["key"], "names": [{"name": i[2]["ru"], "from": i[0], "to": i[1], "from_kind": s["from_kinds"][j]} for j, i in enumerate(s["iv"])], "src": s["src"], "district": s["district"], "enc2008_pdf_page": s["pdf_page"]})
    assert ka.get("CL183b") and not re.search(r"[Ѐ-ӿ]", ka["CL183b"]) and CALQUE not in ka["CL183b"]

    d = read(NAMES)
    have = {x["now"]["en"]: x for x in d["streets"]}
    new = [e for e in entries if e["now"]["en"] not in have]
    d["streets"].extend(new)
    ext = 0
    for e in sp["extend"]:
        st = have.get(e["key"])
        assert st, "no street to extend: " + e["key"]
        for iv in e["iv"]:
            if not any(x[0] == iv[0] and x[1] == iv[1] for x in st["iv"]):
                st["iv"].append(iv)
                ext += 1
    write(NAMES, d, compact=True)

    v = read(VERIFIED)
    add = v.setdefault("additions_2026_11_22_renamed_1988_1991_part3", {"note": "Release 1.8.3: from the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008); the quotes were compared with the text of the PDF (see data/street_renamed_1987_1991.json, field enc2008).", "streets": []})
    seen = {x["street_en"] for x in add["streets"]}
    add["streets"].extend(x for x in verified if x["street_en"] not in seen)
    write(VERIFIED, v)

    lst = read(LIST)
    added = {int(s["n"]) for s in sp["spec"]} | {e["n"] for e in sp["extend"]}
    for s in lst["streets"]:
        if s["n"] in added:
            s["status"] = "done"
    write(LIST, lst)

    rel = read(CHANGELOG)
    assert rel[0]["version"] == "1.8.3"
    rel[0]["items"][0] = {"t": "new", "ru": sp["CL"][0], "en": sp["CL"][1], "ka": ka["CL183b"]}
    write(CHANGELOG, rel)
    print("streets added: %d (already there: %d), intervals added to old streets: %d; %s" % (len(new), len(entries) - len(new), ext, "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
