"""Make data/science_register.json (more institutions for the layer 'Science and culture') and data/education_register.json (the new layer 'Education')
from the heritage register of Georgia. tools/build_science.py and tools/build_education.py put them into site/data.

Choice (the owner's decisions of 2026-11-21), by the name of the object:
  science    universities, institutes, academies, observatories, laboratories, libraries
  culture    museums (also house-museums), theatres, cinemas, concert halls, galleries, circus, conservatory
  education  schools, gymnasiums, lyceums, vocational schools, colleges, kindergartens (the new layer)
Not taken: stations and power plants, residential houses that only have a gallery in the name, gardens, destroyed objects, palaces and clubs, objects within 80 m of a
curated institution of the layer (the same institution). A generic name (just "theatre", "museum", "laboratory") is kept only with an address.
Undated objects are kept with the mark "date unknown" (field undated). The register gives the date of the building only, not the year the institution was founded: the note says so.
Names in English and Russian: the module of the site (tools/translit_names.mjs); the Georgian name is that of the register.

Usage: python -X utf8 -P tools/add_register_layers.py
"""
import collections
import html
import json
import math
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATION = re.compile(r"სადგურ|საბაგირ|ფუნიკულიორ|ჰიდროელექტრო|ავტოსადგურ")
SCIENCE = re.compile(r"უნივერსიტეტ|ინსტიტუტ|აკადემი|ობსერვატორ|ლაბორატორია|ბიბლიოთეკ")
CULTURE = re.compile(r"მუზეუმ|თეატრ|კინოთეატრ|საკონცერტო|ფილარმონი|ცირკ|ოპერ|კონსერვატორ|გალერე")
EDU = re.compile(r"სკოლა|გიმნაზი|ლიცეუმ|სასწავლებელ|კოლეჯ|საბავშვო ბაღ")
GENERIC = {"თეატრი", "მუზეუმი", "სახლ-მუზეუმი", "სახლ_მუზეუმი", "ლაბორატორია", "კინოთეატრი", "სკოლა", "საბავშვო ბაღი", "საბავშვო ბაღი,"}
SKIP_IDS = {2952}                  # the Philharmonic garden: a garden
APPROX = {"century", "era", "mixed", "middle", "quarter", "half", "decade"}


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"&#x?[0-9A-Fa-f]+;", " ", s or ""))).strip()


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 83000, (a[1] - b[1]) * 111000)


def note(lang, d, approx, frm, undated, generic):
    if lang == "ru":
        s = "Здание: объект реестра культурного наследия Грузии. "
        s += "Дата здания в реестре не указана. " if undated else "Дата здания по реестру: %s%s. " % (d, ("; на шкале взят конец диапазона (%d)" % frm) if approx else "")
        s += "Год основания учреждения реестр не указывает."
        return s + (" В реестре название общее, объект определяется по адресу." if generic else "")
    if lang == "en":
        s = "The building is an object of the register of immovable cultural heritage of Georgia. "
        s += "The date of the building is not given in the register. " if undated else "Date of the building by the register: %s%s. " % (d, ("; the end of the range (%d) is used on the timeline" % frm) if approx else "")
        s += "The register does not give the year the institution was founded."
        return s + (" The name in the register is general; the object is identified by its address." if generic else "")
    s = "შენობა საქართველოს კულტურული მემკვიდრეობის უძრავ ძეგლთა რეესტრის ობიექტია. "
    s += "რეესტრში შენობის თარიღი მითითებული არ არის. " if undated else "შენობის თარიღი რეესტრის მიხედვით: %s%s. " % (d, ("; დროის სკალაზე აღებულია დიაპაზონის ბოლო (%d)" % frm) if approx else "")
    s += "რეესტრი დაწესებულების დაარსების წელს არ ასახელებს."
    return s + (" რეესტრში სახელწოდება ზოგადია, ობიექტი მისამართით იდენტიფიცირდება." if generic else "")


def main():
    mon = {f["properties"]["id"]: f for f in json.load(open(os.path.join(ROOT, "site", "data", "monuments.json"), encoding="utf-8"))["features"]}
    cur = [x for x in json.load(open(os.path.join(ROOT, "site", "data", "science.json"), encoding="utf-8")) if "rid" not in x]
    picked = []
    for i, f in mon.items():
        p = f["properties"]
        n = (p["name"] or "").strip()
        c = f["geometry"]["coordinates"]
        if i in SKIP_IDS or "საცხოვრებელი სახლი" in n:
            continue
        if p["fn"] == "residential" and not re.search(r"მუზეუმ|თეატრ", n):
            continue
        if STATION.search(n) and not SCIENCE.search(n):
            continue
        if re.search(r"დანგრეული|სასაფლაო|პარლამენტის", n) and not re.search("ბიბლიოთეკ", n):
            continue
        kind = None
        if EDU.search(n) and not re.search(r"უნივერსიტეტ|ინსტიტუტ|აკადემი", n):
            kind = "edu"
        elif SCIENCE.search(n):
            kind = "science"
        elif CULTURE.search(n):
            kind = "culture"
        if not kind:
            continue
        if kind != "edu" and any(dist(c, (x["lon"], x["lat"])) < 80 for x in cur):
            continue
        if n in GENERIC and not p["address"]:
            continue
        picked.append((i, kind))
    picked.sort()
    cache = os.path.join(ROOT, "data", "cache")
    os.makedirs(cache, exist_ok=True)
    inp, outp = os.path.join(cache, "_translit_in.json"), os.path.join(cache, "_translit_out.json")
    json.dump([{"id": i, "name": clean(mon[i]["properties"]["name"]), "address": clean(mon[i]["properties"]["address"]), "wp": mon[i]["properties"].get("wp", "")} for i, _ in picked],
              open(inp, "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run(["node", os.path.join(ROOT, "tools", "translit_names.mjs"), inp, outp], check=True)
    tr = json.load(open(outp, encoding="utf-8"))
    sci, edu = [], []
    for i, kind in picked:
        p = mon[i]["properties"]
        c = mon[i]["geometry"]["coordinates"]
        n = clean(p["name"])
        undated = not isinstance(p["ye"], (int, float))
        frm = 364 if undated else int(p["ye"])
        y0, y1 = p.get("y0"), p.get("y1")
        d = "" if undated else (str(y0) if (not y0 or y0 == y1) else "%s–%s" % (y0, y1))
        approx = (not undated) and p["prec"] in APPROX
        generic = n in GENERIC
        e = {"id": "reg%d" % i, "kind": kind, "from": frm, "lat": round(c[1], 6), "lon": round(c[0], 6),
             "name": {"ru": tr[str(i)]["ru"]["name"], "en": tr[str(i)]["en"]["name"], "ka": n},
             "note": {l: note(l, d, approx, frm, undated, generic) for l in ("ru", "en", "ka")},
             "src": [], "regno": p.get("reg") or "", "rid": i}
        if kind == "edu":
            e["kind"] = "kindergarten" if "საბავშვო ბაღ" in n else "school"
        if d:
            e["built"] = d
        if undated:
            e["undated"] = True
        if approx:
            e["dapprox"] = True                  # the date is a range (the end of it is used); "approx" of the layers means that the point on the map is approximate
        if p.get("unc"):
            e["approx"] = True                   # the register itself marks the position as uncertain
        a = clean(p["address"])
        if a:
            e["addr"] = {"ru": tr[str(i)]["ru"]["address"], "en": tr[str(i)]["en"]["address"], "ka": a}
        if p.get("ph"):
            e["ph"] = p["ph"]
        (edu if kind == "edu" else sci).append(e)
    for name, data in (("science_register.json", sci), ("education_register.json", edu)):
        json.dump(data, open(os.path.join(ROOT, "data", name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, len(data), dict(collections.Counter(x["kind"] for x in data)), "undated:", sum(1 for x in data if x.get("undated")), "with photos:", sum(1 for x in data if "ph" in x))


if __name__ == "__main__":
    main()
