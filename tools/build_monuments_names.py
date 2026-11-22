"""The second step of the layer of monuments and plaques: the names and the street of every object. Reads data/cache/monuments_clean.json (tools/build_monuments.py), data/cache/monument_labels.json
(tools/fetch_monument_labels.py), site/data/street_geom.json + street_names.json. Makes data/cache/monuments_named.json:
- the name in a language that is empty is taken from the Wikidata label of the subject when the object has ONE subject (a person) and the label exists;
- "st": the nearest street of the site within 150 m (the key of street_geom.json) for every object: it makes the label of an object without a name ("Bust, Rustaveli Avenue");
- "need": the names that are still empty in some language while another language has the name: the table for Gemini (for_gemini/from_desktop/monuments_names_batch_01.md, id | ka | ru | en | kind).
Usage: python -P tools/build_monuments_names.py
"""
import json
import math
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAT = {"ბრინჯაო": "bronze", "bronze": "bronze", "metal": "metal", "ქვა": "stone", "stone": "stone", "სპილენძი": "copper", "ბეტონი": "concrete", "concrete": "concrete", "marble": "marble", "თუჯი": "cast_iron",
       "stainless_steel": "steel", "steel": "steel", "ბაზალტი": "basalt", "თაბაშირი": "plaster", "wood": "wood", "aluminium": "aluminium"}      # the values of the table -> the keys of the strings of the card
KM = (83000.0, 111000.0)


def script_ok(lg, v):
    cyr, geo = len(re.findall("[А-Яа-яЁё]", v)), len(re.findall("[ა-ჿ]", v))
    return (geo > 0 and cyr == 0) if lg == "ka" else (cyr == 0) if lg == "en" else (cyr > 0)


def seg_dist(p, a, b):
    ax, ay = (a[0] - p[0]) * KM[0], (a[1] - p[1]) * KM[1]
    bx, by = (b[0] - p[0]) * KM[0], (b[1] - p[1]) * KM[1]
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
    return math.hypot(ax + t * dx, ay + t * dy)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "data", "cache", "monuments_clean.json"), encoding="utf-8"))
    L = json.load(open(os.path.join(R, "data", "cache", "monument_labels.json"), encoding="utf-8"))
    sg = json.load(open(os.path.join(R, "site", "data", "street_geom.json"), encoding="utf-8"))
    lines = []
    for k, g in sg.items():
        if g.get("type") in ("LineString", "MultiLineString"):
            parts = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
            lines.append((k, parts))

    def nearest(la, lo):
        best = (150.0, None)
        for k, parts in lines:
            for pl in parts:
                for a, b in zip(pl, pl[1:]):
                    if abs(a[1] - la) > 0.004 and abs(b[1] - la) > 0.004:
                        continue
                    dd = seg_dist((lo, la), a, b)
                    if dd < best[0]:
                        best = (dd, k)
        return best[1]

    need = []
    for key in ("monuments", "plaques"):
        for x in d[key]:
            qs = [q for q in x["qid"].split(";") if q.startswith("Q")]
            if len(qs) == 1 and qs[0] in L:
                for lg in ("ka", "ru", "en"):
                    if not x["n"][lg] and L[qs[0]][lg]:
                        x["n"][lg] = L[qs[0]][lg]
            x["st"] = nearest(x["lat"], x["lon"])
            if key == "monuments":
                x["mat"] = MAT.get(x["material"].strip().lower() if x["material"].isascii() else x["material"].strip(), "")
                for f in ("sculptor", "architect"):                       # given as in the source (mostly Georgian initials: the full names are unknown, a translation would be a guess); a value without a letter is not a name
                    if not re.search(r"[^\W\d_]", x[f]) or x[f].strip() in ("-", "—"):
                        x[f] = ""
            have = [lg for lg in ("ka", "ru", "en") if x["n"][lg]]
            wrong = [lg for lg in have if not script_ok(lg, x["n"][lg])]               # a name that stands in a field of the wrong script (a Latin text in ka, a Cyrillic one in en) is given again
            if have and (len(have) < 3 or wrong):
                need.append((key[0] + ":" + x["id"], x))
    json.dump(d, open(os.path.join(R, "data", "cache", "monuments_named.json"), "w", encoding="utf-8"), ensure_ascii=False)
    rows = ["# Имена памятников и мемориальных досок Тбилиси: заполнить недостающие языки", "", "| id | ka | ru | en | что это |", "|---|---|---|---|---|"]
    kinds = {"m": "памятник", "p": "мемориальная доска"}
    for i, x in need:
        rows.append("| %s | %s | %s | %s | %s |" % (i, x["n"]["ka"], x["n"]["ru"], x["n"]["en"], x.get("kind") or "plaque"))
    open(os.path.join(R, "for_gemini", "from_desktop", "monuments_names_batch_01.md"), "wb").write(("\n".join(rows) + "\n").encode("utf-8"))
    nm = lambda x: any(x["n"].values())  # noqa: E731
    for key in ("monuments", "plaques"):
        xs = d[key]
        print(key, len(xs), "| all three names:", sum(1 for x in xs if all(x["n"].values())), "| partial (to Gemini):", sum(1 for x in xs if nm(x) and not all(x["n"].values())), "| no name:", sum(1 for x in xs if not nm(x)),
              "| with a street:", sum(1 for x in xs if x["st"]), "| unnamed without a street:", sum(1 for x in xs if not nm(x) and not x["st"]))
    print("rows for Gemini:", len(need))


if __name__ == "__main__":
    main()
