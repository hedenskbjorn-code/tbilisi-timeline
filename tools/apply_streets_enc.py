"""Release 1.8.4: the streets of the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008) (idempotent; --dry-run only checks).
Spec: tools/streets_enc1_spec.json (made by tools/build_enc_spec.py from the answers of Gemini that tools/verify_enc_batches.py and tools/verify_enc4.py accepted: every quote is a verbatim part
of the text of the entry, the chain of the years is continuous, the Georgian note equals the template). The entry of a street (site/data/street_names.json): now, geom (the key of the geometry when it
differs from now.en), iv (the intervals with names), undated (the names without a year), book (the reference with the PDF page), nogeom (no line on the map: the card and the search only).
The note of a street is in site/data/street_notes.json under the key (geom or now.en): the app loads that file when a card is opened. A street with names without a year only has no interval.
After it run: tools/build_street_labels.py (the geometry) and node tests/check_data.mjs.
"""
import json
import os
import re
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPEC = os.path.join(R, "tools", "streets_enc1_spec.json")
NAMES = os.path.join(R, "site", "data", "street_names.json")
NOTES = os.path.join(R, "site", "data", "street_notes.json")
VERIFIED = os.path.join(R, "data", "street_names_verified.json")
DRY = "--dry-run" in sys.argv
CR, LF = chr(13), chr(10)
CYR = re.compile("[Ѐ-ӿ]")


def read(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write(p, obj, compact=False):
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(obj, ensure_ascii=False, indent=1)
    if os.path.exists(p):
        with open(p, "rb") as f:
            crlf = (CR + LF).encode() in f.read()
        if crlf:
            data = data.replace(LF, CR + LF)
    b = data.encode("utf-8")  # encode first: a failure must not truncate the file
    if not DRY:
        with open(p, "wb") as f:
            f.write(b)


def norm(s):
    return re.sub(r"\s+", "", re.sub(r"\([^)]*\)", "", s))


def key_of(st):
    return st.get("geom") or st["now"]["en"]


def main():
    spec = read(SPEC)
    sp = spec["spec"]
    d = read(NAMES)
    notes = read(NOTES)["notes"] if os.path.exists(NOTES) else {}
    have = {key_of(x) for x in d["streets"]}
    new = 0
    for s in sp:
        assert not CYR.search(s["now"]["ka"] + s["note"]["ka"] + "".join(i[2]["ka"] for i in s["iv"])), "Cyrillic in the Georgian text of " + s["id"]
        key = s["geom"]
        if key in have:
            continue
        e = {"now": s["now"]}
        if s["geom"] != s["now"]["en"]:
            e["geom"] = s["geom"]
        e["iv"] = s["iv"]
        if s["undated"]:
            e["undated"] = s["undated"]
        e["book"] = s["book"]
        if s.get("nogeom"):
            e["nogeom"] = True
        d["streets"].append(e)
        notes[key] = s["note"]
        new += 1
    # the streets that are already on the map: the intervals that do not overlap an existing one, the names without a year, the note and the book are added
    by = {norm(x["now"]["ka"]): x for x in d["streets"]}
    by_en = {x["now"]["en"]: x for x in d["streets"] if not x.get("geom")}
    merged = 0
    for m in spec.get("merge", []):
        st = by_en.get(m["target_en"]) or by[norm(m["target_ka"])]
        for iv in m["add_iv"]:
            assert not CYR.search(iv[2]["ka"])
            if not any(iv[0] < b and a < iv[1] for a, b, _ in st["iv"]):
                st["iv"].append(iv)
                merged += 1
        st["iv"].sort(key=lambda a: a[0])
        for u in m["undated"]:
            if not any(x["ka"] == u["ka"] for x in st.get("undated", [])):
                st.setdefault("undated", []).append(u)
                merged += 1
        nt = notes.setdefault(key_of(st), {"ru": "", "en": "", "ka": ""})
        for l in ("ru", "en", "ka"):
            if m["note"][l] not in nt[l]:
                nt[l] = (nt[l].rstrip() + " " + m["note"][l]).strip()
                merged += 1
        if "book" not in st:
            st["book"] = m["book"]
    write(NAMES, d, compact=True)
    write(NOTES, {"notes": notes}, compact=True)
    v = read(VERIFIED)
    add = v.setdefault("additions_2026_11_22_encyclopedia_full", {"note": "Release 1.8.4: every street of the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008) with a former name; the intervals are the ones the answers of Gemini gave and the programs checked against the text (verbatim quotes); the pages are the PDF pages.", "streets": []})
    seen = {x["id"] for x in add["streets"]}
    add["streets"].extend({"id": s["id"], "street_en": s["geom"], "names": [{"name": i[2]["ru"], "from": i[0], "to": i[1], "from_kind": s["from_kinds"][j]} for j, i in enumerate(s["iv"])],
                           "undated": [u["ru"] for u in s["undated"]], "book": s["book"], "district": s["district"]} for s in sp if s["id"] not in seen)
    write(VERIFIED, v)
    print("streets added: %d (already there: %d), changes in the streets that were on the map: %d; %s" % (new, len(sp) - new, merged, "dry run, nothing written" if DRY else "written"))


if __name__ == "__main__":
    main()
