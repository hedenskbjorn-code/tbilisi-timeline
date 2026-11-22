"""Build the spec of the streets of the encyclopedia (2008) from the checked answers of Gemini: data/cache/enc2008_verified.json (strict passes) and data/cache/enc2008_verified4.json (full pass),
and the OSM ways (data/raw/osm_transport/street_labels_enc.json): tools/streets_enc1_spec.json. The streets already on the map and the ones without a line in OSM or with namesakes in
several places are not in the spec; they are listed in data/cache/enc2008_pending.json for a separate decision. The Russian and English notes are made from the template
(the Georgian note is the checked one of Gemini). A street with names without a year only (no interval) is in the spec too: it has no label on the map, only the card.
Usage: python -P tools/build_enc_spec.py
"""
import collections
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_street_labels import join  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VER1 = os.path.join(ROOT, "data", "cache", "enc2008_verified.json")
VER4 = os.path.join(ROOT, "data", "cache", "enc2008_verified4.json")
OSM = os.path.join(ROOT, "data", "raw", "osm_transport", "street_labels_enc.json")
NAMES = os.path.join(ROOT, "site", "data", "street_names.json")
OUT = os.path.join(ROOT, "tools", "streets_enc1_spec.json")
PEND = os.path.join(ROOT, "data", "cache", "enc2008_pending.json")
H_RU = "Энциклопедия «Тбилиси. Улицы, проспекты, площади» (2008): "
H_EN = "Encyclopedia 'Tbilisi. Streets, avenues, squares' (2008): "
LAB_RU = {"exact": "%d", "plan": "%d (год плана или списка)", "dec": "%d-е годы (точный год не назван, на карте условно с %d)", "after": "после %d (год не назван, на карте условно с %d)",
          "origin": "с возникновения улицы (на карте условно с %d)"}
LAB_EN = {"exact": "%d", "plan": "%d (the year of a plan or list)", "dec": "the %ds (the exact year is not named, on the map conventionally from %d)",
          "after": "after %d (the year is not named, on the map conventionally from %d)", "origin": "from the origin of the street (on the map conventionally from %d)"}


def lab(tpl, y):
    return tpl % ((y, y) if tpl.count("%d") == 2 else (y,))


def norm_name(s):
    return re.sub(r"\s+", "", re.sub(r"\([^)]*\)", "", s))


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", "", s)).strip()


def name_forms(s):
    """The name without the parentheses, and with the nickname in the place of the word before it: 'გიორგი (გიგო) ზაზიაშვილის ქუჩა' -> 'გიგო ზაზიაშვილის ქუჩა'."""
    forms = [clean(s)]
    m = re.search(r"(\S+) \(([^)]+)\)", s)
    if m:
        forms.append(clean(s.replace(m.group(0), m.group(2))))
    return forms


def groups(chains, gap=700):
    gs = []
    for c in chains:
        la = sum(p[1] for p in c) / len(c)
        lo = sum(p[0] for p in c) / len(c)
        for g in gs:
            if any(math.hypot((lo - x[0]) * 83000, (la - x[1]) * 111000) < gap for x in g):
                g.append((lo, la))
                break
        else:
            gs.append([(lo, la)])
    return gs


SOV = {"ძველი თბილისის": {"Mtatsminda", "Krtsanisi", "Chugureti", "Isani"}, "ვაკე-საბურთალოს": {"Vake", "Saburtalo"}, "დიდუბე-ჩუღურეთის": {"Didube", "Chugureti"},
       "გლდანი-ნაძალადევის": {"Gldani", "Nadzaladevi"}, "ისანი-სამგორის": {"Isani", "Samgori"}}
ALLNAMES = os.path.join(ROOT, "data", "raw", "osm_transport", "tbilisi_all_street_names.json")
FUZZY = os.path.join(ROOT, "data", "cache", "enc2008_fuzzy_names.json")


def polygons():
    out = collections.defaultdict(list)
    for f in json.load(open(os.path.join(ROOT, "site", "data", "districts.json"), encoding="utf-8"))["features"]:
        if f["geometry"]["type"] == "MultiPolygon":
            for poly in f["geometry"]["coordinates"]:
                out[f["properties"]["name_en"]].append(poly[0])
    return out


def inside(pt, ring):
    x, y = pt
    c = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi, xj, yj = ring[i][0], ring[i][1], ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def fuzzy_variant(name, names, taken=()):
    """A spelling variant of the name in OSM (an OCR or old spelling difference): the same number of words and a ratio of 0.93 or more, a single best candidate."""
    import difflib
    def ok(n):                                              # the same number of words; the single different word is not short; the candidate is not the exact name of another street of the book
        if len(n.split()) != len(name.split()) or n in taken:
            return False
        diff = [(a, b) for a, b in zip(name.split(), n.split()) if a != b]
        return len(diff) == 1 and len(diff[0][0]) > 6
    c = [n for n in difflib.get_close_matches(name, names, n=3, cutoff=0.93) if ok(n)]
    return c[0] if c and (len(c) == 1 or difflib.SequenceMatcher(None, name, c[0]).ratio() - difflib.SequenceMatcher(None, name, c[1]).ratio() > 0.03) else None


def rows():
    out = []
    if os.path.exists(VER1):
        for r in json.load(open(VER1, encoding="utf-8"))["ok"]:
            out.append({**r, "origin": None, "undated": []})
    if os.path.exists(VER4):
        out += json.load(open(VER4, encoding="utf-8"))["ok"]
    return out


def main():
    ok = rows()
    osm = json.load(open(OSM, encoding="utf-8"))
    by = collections.defaultdict(dict)
    for e in osm["elements"]:
        if e.get("geometry") and e["tags"].get("name"):
            by[e["tags"]["name"]][e["id"]] = [[round(p["lon"], 5), round(p["lat"], 5)] for p in e["geometry"]]
    site = json.load(open(NAMES, encoding="utf-8"))["streets"]
    # the spec must not depend on whether it was applied: the streets that the application added (they are listed in data/street_names_verified.json) are not the "streets on the map" of this run
    vn = os.path.join(ROOT, "data", "street_names_verified.json")
    added = {x["street_en"] for x in json.load(open(vn, encoding="utf-8")).get("additions_2026_11_22_encyclopedia_full", {}).get("streets", [])}
    site = [x for x in site if (x.get("geom") or x["now"]["en"]) not in added]
    site_ka = {norm_name(s["now"]["ka"]) for s in site}
    used_en = {s["now"]["en"] for s in site}
    spec, pend, seen_ka, merge = [], [], set(), []
    site_by = {norm_name(x["now"]["ka"]): x for x in site}
    site_by_en = {x["now"]["en"]: x for x in site}
    allnames = list(json.load(open(ALLNAMES, encoding="utf-8"))) if os.path.exists(ALLNAMES) else []
    taken_ka = {r["ka_now"] for r in ok} | {clean(r["ka_now"]) for r in ok} | {x["now"]["ka"] for x in site}
    poly = polygons()
    need = []
    for r in ok:
        why = None
        near = "all"
        target = next((site_by[norm_name(f)] for f in name_forms(r["ka_now"]) if norm_name(f) in site_by), None) or site_by_en.get(r["en_now"])      # the same street under another spelling of the Georgian name: the English name decides too
        if target is not None:                      # the street is on the map: the intervals that do not overlap an existing one are added, the rest goes into the note
            ex = target
            ranges = [(iv[0], iv[1]) for iv in ex["iv"]]
            new_iv = [i for i in r["intervals"] if not any(i["from"] < b and a < i["to"] for a, b in ranges)]
            same = [i for i in r["intervals"] if (i["from"], i["to"]) in ranges]
            iv, und = r["intervals"], r["undated"]
            pr = "; ".join("%s — %s" % (lab(LAB_RU[i["kind"]], i["from"]), i["ru"]) for i in iv)
            pe = "; ".join("%s — %s" % (lab(LAB_EN[i["kind"]], i["from"]), i["en"]) for i in iv)
            if iv:
                pr += "; %d — %s." % (iv[-1]["to"], r["ru_now"])
                pe += "; %d — %s." % (iv[-1]["to"], r["en_now"])
            if und:
                pr += (" " if iv else "") + "Ранее называлась (год не назван): " + "; ".join(u["ru"] for u in und) + "."
                pe += (" " if iv else "") + "Earlier called (the year is not named): " + "; ".join(u["en"] for u in und) + "."
            merge.append({"id": r["id"], "target_en": ex["now"]["en"], "target_ka": ex["now"]["ka"], "add_iv": [[i["from"], i["to"], {"ru": i["ru"], "en": i["en"], "ka": i["ka"]}] for i in new_iv],
                          "undated": [{"ru": u["ru"], "en": u["en"], "ka": u["ka"]} for u in und], "same_intervals": len(same), "pdf_page": r["page"],
                          "book": "Tbilisi. Streets, avenues, squares (თბილისი. ქუჩები, გამზირები, მოედნები), 2008, PDF p. %s" % r["page"],
                          "note": {"ru": H_RU + pr, "en": H_EN + pe, "ka": r["note_ka"]}})
            continue
        osm_ka = r["ka_now"] if r["ka_now"] in by else clean(r["ka_now"])
        if norm_name(r["ka_now"]) in site_ka:
            why = "already on the map"
        elif norm_name(r["ka_now"]) in seen_ka:
            why = "the same name twice in the encyclopedia"
        else:
            if osm_ka not in by and allnames:
                fv = fuzzy_variant(osm_ka, allnames, taken_ka)
                if fv:
                    if fv in by:
                        osm_ka = fv
                    else:
                        need.append(fv)
                        why = "the spelling variant %s has to be fetched from OSM" % fv
            if why:
                pass
            elif osm_ka not in by:
                why = "no way in OSM by this name"
            else:
                gs = groups(join(list(by[osm_ka].values())))
                if len(gs) > 1:
                    allowed = next((v for k, v in SOV.items() if r["district"].startswith(k)), set())
                    ins = [g for g in gs if any(inside(pt, ring) for pt in g[:1] + g[-1:] for d in allowed for ring in poly.get(d, []))]
                    if len(ins) == 1:
                        near = [round(sum(p[1] for p in ins[0]) / len(ins[0]), 5), round(sum(p[0] for p in ins[0]) / len(ins[0]), 5)]
                    else:
                        why = "namesakes in several places (%d in the district of the entry)" % len(ins)
        nogeom = bool(why)
        if why:                                                    # no usable line: the street is in the data (search, card) without a label on the map
            pend.append({"id": r["id"], "ka_now": r["ka_now"], "page": r["page"], "district": r["district"], "why": why})
            osm_ka, near = None, None
        seen_ka.add(norm_name(r["ka_now"]))
        en = r["en_now"]
        geom = en if en not in used_en else "%s [%s]" % (en, r["id"])
        used_en.add(en)
        iv = r["intervals"]
        und = r["undated"]
        pr = "; ".join("%s — %s" % (lab(LAB_RU[i["kind"]], i["from"]), i["ru"]) for i in iv)
        pe = "; ".join("%s — %s" % (lab(LAB_EN[i["kind"]], i["from"]), i["en"]) for i in iv)
        if iv:
            pr += "; %d — %s." % (iv[-1]["to"], r["ru_now"])
            pe += "; %d — %s." % (iv[-1]["to"], r["en_now"])
        if und:
            pr += (" " if iv else "") + "Ранее называлась (год не назван): " + "; ".join(u["ru"] for u in und) + "."
            pe += (" " if iv else "") + "Earlier called (the year is not named): " + "; ".join(u["en"] for u in und) + "."
        spec.append({"id": r["id"], "geom": geom, "osm_ka": osm_ka, "nogeom": nogeom, "district": r["district"], "near": near, "now": {"ru": r["ru_now"], "en": en, "ka": r["ka_now"]},
                     "iv": [[i["from"], i["to"], {"ru": i["ru"], "en": i["en"], "ka": i["ka"]}] for i in iv], "from_kinds": [i["kind"] for i in iv],
                     "origin": r["origin"]["from"] if r["origin"] else None,
                     "undated": [{"ru": u["ru"], "en": u["en"], "ka": u["ka"]} for u in und],
                     "book": "Tbilisi. Streets, avenues, squares (თბილისი. ქუჩები, გამზირები, მოედნები), 2008, PDF p. %s" % r["page"], "pdf_page": r["page"],
                     "note": {"ru": H_RU + pr, "en": H_EN + pe, "ka": r["note_ka"]}})
    json.dump(sorted(set(need)), open(FUZZY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"spec": spec, "merge": merge}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(pend, open(PEND, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c = collections.Counter(p["why"] for p in pend)
    print("merge into streets already on the map: %d (new intervals: %d)" % (len(merge), sum(len(m["add_iv"]) for m in merge)))
    print("accepted entries: %d | in the spec: %d (with intervals: %d, only undated names: %d) | to fetch: %d | pending: %s" % (
        len(ok), len(spec), sum(1 for s in spec if s["iv"]), sum(1 for s in spec if not s["iv"]), len(set(need)), dict(c)))


if __name__ == "__main__":
    main()
