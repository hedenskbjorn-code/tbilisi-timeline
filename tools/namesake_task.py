"""The task for Gemini: in whose honour (or after what) a street, an avenue, a square, a bridge, a school or a museum is named. Makes for_gemini/from_desktop/namesake_batch_NN.md:
the entries of the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008; ids E0001..., the text of the entry, the PDF page) in packs of 100 and a pack of the objects whose name has "named after"
(სახელობის / სახ.: the register of the monuments and the layers of science and education). The answer is checked by tools/verify_namesakes.py.
Usage: python -P tools/namesake_task.py
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "site", "data")
ENT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
OUTD = os.path.join(ROOT, "for_gemini", "from_desktop")
PACK = 100
NAMED = re.compile(r"სახელობის|სახ\.")


def objects():
    rows = []
    for f in json.load(open(os.path.join(D, "monuments.json"), encoding="utf-8"))["features"]:
        p = f["properties"]
        if NAMED.search(p["name"]) and not p.get("dup"):
            rows.append(("M%s" % p["id"], p["name"], p.get("address", "")))
    for fn in ("science", "education"):
        for x in json.load(open(os.path.join(D, fn + ".json"), encoding="utf-8")):
            nm = x["name"].get("ka", "") if isinstance(x["name"], dict) else x["name"]
            if NAMED.search(nm):
                ad = x.get("addr", "")
                rows.append(("%s:%s" % (fn[:3].upper(), x["id"]), nm, (ad.get("ka") or ad.get("en") or "") if isinstance(ad, dict) else ad))
    return rows


def main():
    ents = json.load(open(ENT, encoding="utf-8"))
    n = 0
    for k in range(0, len(ents), PACK):
        n += 1
        lines = ["# Пакет %02d: статьи энциклопедии (в честь кого или чего названо)" % n, ""]
        for e in ents[k:k + PACK]:
            t = (e.get("text_long") or e["text"]).replace("\n", " ")[:3000]
            lines += ["## %s | PDF стр. %s" % (e["id"], e["page"]), "", t, ""]
        open(os.path.join(OUTD, "namesake_batch_%02d.md" % n), "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
    rows = objects()
    lines = ["# Пакет объектов (школы, музеи, институты «имени …»): в честь кого назван объект", "", "| id | название | адрес |", "|---|---|---|"]
    lines += ["| %s | %s | %s |" % (i, nm.replace("|", "/"), a.replace("|", "/")) for i, nm, a in rows]
    open(os.path.join(OUTD, "namesake_objects.md"), "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
    print("batches:", n, "| objects:", len(rows))


if __name__ == "__main__":
    main()
