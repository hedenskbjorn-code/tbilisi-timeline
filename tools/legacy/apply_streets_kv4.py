"""Release 1.8.4: name histories of 6 more streets and four additions to streets already on the map, all from the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008)
(idempotent; --dry-run only checks). Spec: tools/streets_kv4_spec.json. The text of the PDF (data/cache/nplg_pdfs, not committed) was read for every entry: the pages are in the spec.
The sources are the book itself: a street without a link carries "book": "<reference>, PDF p. N" (shown as plain text in the list of the names). The Georgian texts are Gemini's
(work/gemini/results/tbilisi_streets184.md), checked here: no Cyrillic, no the calque of the word "prospect", every ID present.
"""
import json, os, re, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPEC = os.path.join(R, "tools", "streets_kv4_spec.json")
RES = os.path.join(R, "work", "gemini", "results/tbilisi_streets184.md")
NAMES = os.path.join(R, "site", "data", "street_names.json")
VERIFIED = os.path.join(R, "data", "street_names_verified.json")
LIST = os.path.join(R, "data", "street_renamed_1987_1991.json")
CHANGELOG = os.path.join(R, "site", "data", "changelog.json")
DRY = "--dry-run" in sys.argv
CR, LF = chr(13), chr(10)
CYR = re.compile("[\u0400-\u04FF]")
CALQUE = "პროსპექტ"


def read(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write(p, obj, compact=False):
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
        if len(cells) >= 2 and re.match(r"^(S\d+_note|X\d+_note|CL184s)$", cells[0]):
            ka[cells[0]] = cells[1]
    return ka


def main():
    sp = read(SPEC)
    ka = parse_result()
    need = [s["id"] + "_note" for s in sp["spec"]] + [x["id"] + "_note" for x in sp["extend"]] + ["CL184s"]
    miss = [n for n in need if not ka.get(n)]
    assert not miss, "missing Georgian text: %s" % miss
    for n in need:
        assert not CYR.search(ka[n]) and CALQUE not in ka[n], "bad Georgian text in " + n
    for s in sp["spec"]:
        for i in s["iv"]:
            assert not CYR.search(i[2]["ka"]) and not CYR.search(s["now"]["ka"])

    d = read(NAMES)
    have = {x["now"]["en"]: x for x in d["streets"]}
    new = 0
    for s in sp["spec"]:
        if s["key"] in have:
            continue
        d["streets"].append({"now": s["now"], "iv": s["iv"], "note": {"ru": s["note"]["ru"], "en": s["note"]["en"], "ka": ka[s["id"] + "_note"]}, "book": s["book"]})
        new += 1
    ext = 0
    for x in sp["extend"]:
        st = have.get(x["key"])
        assert st, "no street to extend: " + x["key"]
        if x["op"] == "set":                                   # [old from, old to, new from, new to]: the dates of one interval are corrected
            of, ot, nf, nt = x["arg"]
            for iv in st["iv"]:
                if iv[0] == of and iv[1] == ot:
                    iv[0], iv[1] = nf, nt
                    ext += 1
        else:
            for iv in x["arg"]:
                if not any(a[0] == iv[0] and a[1] == iv[1] for a in st["iv"]):
                    st["iv"].append(iv)
                    st["iv"].sort(key=lambda a: a[0])
                    ext += 1
        for l, add in (("ru", x["note_add"]["ru"]), ("en", x["note_add"]["en"]), ("ka", ka[x["id"] + "_note"])):
            if add not in st["note"][l]:
                st["note"][l] = (st["note"][l].rstrip() + " " + add).strip()
                ext += 1
    write(NAMES, d, compact=True)

    v = read(VERIFIED)
    add = v.setdefault("additions_2026_11_22_encyclopedia", {"note": "Release 1.8.4: from the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008); the pages are the PDF pages of the file read.", "streets": []})
    seen = {y["street_en"] for y in add["streets"]}
    add["streets"].extend({"street_en": s["key"], "names": [{"name": i[2]["ru"], "from": i[0], "to": i[1], "from_kind": s["from_kinds"][j]} for j, i in enumerate(s["iv"])], "book": s["book"], "district": s["district"]}
                          for s in sp["spec"] if s["key"] not in seen)
    write(VERIFIED, v)

    rel = read(CHANGELOG)
    if rel[0]["version"] != "1.8.4":
        rel.insert(0, {"version": "1.8.4", "date": "2026-11-22", "items": []})
    item = {"t": "new", "ru": sp["CL"][0], "en": sp["CL"][1], "ka": ka["CL184s"]}
    if not any(i["ru"] == item["ru"] for i in rel[0]["items"]):
        rel[0]["items"].append(item)
    write(CHANGELOG, rel)
    print("streets added: %d, changes to old streets: %d; %s" % (new, ext, "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
