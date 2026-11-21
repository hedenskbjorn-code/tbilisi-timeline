"""Make data/religious_register.json: the worship buildings of the heritage register of Georgia that the curated layer 'Religious buildings' does not hold.
tools/build_religious.py puts these entries after the curated ones in site/data/religious.json.

Choice (the owner's decisions of 2026-11-21): every object of the register whose initial function is religious and that is a building of worship
(church, monastery, mosque, synagogue, chapel, shrine, basilica, bell tower, ruins of a church); not taken: burial grounds, kurgans, dolmens, settlements,
museums, and two exhibits moved to the open-air museum (41534, 41565). An object within 60 m of a curated building is the same building and is skipped.
Undated objects are kept with the mark "date unknown" (field undated). Parts of a complex stay separate points.
Denomination: only from the register itself (the name, the description, the subtype of the function), never guessed; without it the new category 'christian'
(church, denomination not given in the register) is used. The date on the timeline is the end of the range of the register (as for all objects of the register).
Names in English and Russian: the module of the site (tools/translit_names.mjs), the Georgian name is that of the register.

Usage: python -X utf8 -P tools/add_register_religious.py
"""
import json
import math
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCLUDE = {41534, 41565}          # a cult structure and a wooden church brought from villages to the open-air museum
KEEP_COMPLEX = {17828, 24768, 38177, 5072}   # Kukia church complex, remains of Surb Sarkis, Kaben monastery complex, Tkhinvali palace and churches

BURIAL = re.compile(r"სამაროვან|ყორღან|სარკოფაგ|სამარხ|საფლავ|სასაფლაო|პანთეონ|აკლდამა|ნამოსახლარ|ნასოფლარ|კოლექცი|ნაქულბაქ|ქვაჯვარა")
WORSHIP = re.compile(r"ეკლესია|ტაძარი|მონასტერი|მეჩეთი|სინაგოგა|სამლოცველო|ბაზილიკა|სამრეკლო|საყდარი|სალოცავი|ნაეკლესიარ|ნანგრევ|ეკლესი")
RUIN = re.compile(r"ნაეკლესიარ|ნანგრევ|ნაშთ")
DEN = [("armenian", r"სომხ|ეჩმიაძინ|შამქარეც|გრიგორიანულ|ვანქ"), ("catholic", r"კათოლიკ"),
       ("russian", r"რუსული მართლმადიდებლური|რუსული, მართლმადიდებლური|რუსეთის მართლმადიდებლ|რუსული ეკლესია"),
       ("lutheran", r"ლუთერ|ევანგელისტ"), ("jewish", r"ებრაულ|სინაგოგ"), ("muslim", r"მეჩეთ"), ("yazidi", r"ეზიდ"),
       ("orthodox", r"ქართული მართლმადიდებლ|საქართველოს სამოციქულო")]
APPROX = {"century", "era", "mixed", "middle", "quarter", "half", "decade"}


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 83000, (a[1] - b[1]) * 111000)


def note(lang, d, approx, frm, undated, den_known):
    if lang == "ru":
        s = "Объект реестра культурного наследия Грузии. "
        s += "Дата в реестре не указана. " if undated else "Дата по реестру: %s%s. " % (d, ("; на шкале взят конец диапазона (%d)" % frm) if approx else "")
        return s + ("Конфессия определена по названию или описанию объекта в реестре." if den_known else "Конфессия в реестре не указана.")
    if lang == "en":
        s = "An object of the register of immovable cultural heritage of Georgia. "
        s += "The date is not given in the register. " if undated else "Date by the register: %s%s. " % (d, ("; the end of the range (%d) is used on the timeline" % frm) if approx else "")
        return s + ("The denomination is taken from the name or the description of the object in the register." if den_known else "The denomination is not given in the register.")
    s = "საქართველოს კულტურული მემკვიდრეობის უძრავ ძეგლთა რეესტრის ობიექტი. "
    s += "რეესტრში თარიღი მითითებული არ არის. " if undated else "თარიღი რეესტრის მიხედვით: %s%s. " % (d, ("; დროის სკალაზე აღებულია დიაპაზონის ბოლო (%d)" % frm) if approx else "")
    return s + ("კონფესია განსაზღვრულია რეესტრში ობიექტის სახელწოდების ან აღწერის მიხედვით." if den_known else "რეესტრში კონფესია მითითებული არ არის.")


def main():
    raw = {f["properties"]["id"]: f["properties"] for f in json.load(open(os.path.join(ROOT, "data", "tbilisi_monuments.geojson"), encoding="utf-8"))["features"]}
    mon = {f["properties"]["id"]: f for f in json.load(open(os.path.join(ROOT, "site", "data", "monuments.json"), encoding="utf-8"))["features"]}
    layer = [r for r in json.load(open(os.path.join(ROOT, "site", "data", "religious.json"), encoding="utf-8")) if "rid" not in r]
    picked = []
    for i, f in mon.items():
        p = f["properties"]
        if p["fn"] != "religious" or i in EXCLUDE:
            continue
        c = f["geometry"]["coordinates"]
        if any(dist(c, (r["lon"], r["lat"])) < 60 for r in layer):
            continue
        n = p["name"] or ""
        if BURIAL.search(n) or not (WORSHIP.search(n) or i in KEEP_COMPLEX):
            continue
        picked.append(i)
    picked.sort()
    cache = os.path.join(ROOT, "data", "cache")
    os.makedirs(cache, exist_ok=True)
    inp, outp = os.path.join(cache, "_translit_in.json"), os.path.join(cache, "_translit_out.json")
    json.dump([{"id": i, "name": mon[i]["properties"]["name"].strip(), "address": mon[i]["properties"]["address"] or "", "wp": mon[i]["properties"].get("wp", "")} for i in picked],
              open(inp, "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run(["node", os.path.join(ROOT, "tools", "translit_names.mjs"), inp, outp], check=True)
    tr = json.load(open(outp, encoding="utf-8"))
    out = []
    for i in picked:
        p = mon[i]["properties"]
        r = raw[i]
        c = mon[i]["geometry"]["coordinates"]
        text = (p["name"] or "") + " " + (r.get("description") or "")
        rel = next((k for k, rx in DEN if re.search(rx, text)), None)
        undated = not isinstance(p["ye"], (int, float))
        frm = 364 if undated else int(p["ye"])
        y0, y1 = r.get("year_from"), r.get("year_to")
        d = "" if undated else (str(y0) if y0 == y1 or not y0 else "%s–%s" % (y0, y1))
        approx = (not undated) and p["prec"] in APPROX
        ruin = bool(RUIN.search(p["name"] or ""))
        name_ka = re.sub(r"\s+", " ", p["name"]).strip()
        addr_ka = re.sub(r"\s+", " ", p["address"] or "").strip()
        e = {"id": "reg%d" % i, "rel": rel or "christian", "from": frm, "date": d, "lat": round(c[1], 6), "lon": round(c[0], 6),
             "name": {"ru": tr[str(i)]["ru"]["name"], "en": tr[str(i)]["en"]["name"], "ka": name_ka},
             "status": ({"ru": "руины или остатки (по реестру)", "en": "ruins or remains (per the register)", "ka": "ნანგრევები ან ნაშთები (რეესტრის მიხედვით)"} if ruin else
                        {"ru": "стоит (объект реестра)", "en": "stands (a register object)", "ka": "დგას (რეესტრის ობიექტი)"}),
             "note": {l: note(l, d, approx, frm, undated, rel is not None) for l in ("ru", "en", "ka")},
             "src": [], "regno": p.get("reg") or "", "rid": i}
        if undated:
            e["undated"] = True
        if approx:
            e["dapprox"] = True                  # the date is a range (the end of it is used); "approx" of the layers means that the point on the map is approximate
        if p.get("unc"):
            e["approx"] = True                   # the register itself marks the position as uncertain
        if addr_ka:
            e["addr"] = {"ru": tr[str(i)]["ru"]["address"], "en": tr[str(i)]["en"]["address"], "ka": addr_ka}
        if p.get("ph"):
            e["ph"] = p["ph"]
        out.append(e)
    path = os.path.join(ROOT, "data", "religious_register.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import collections
    print(len(out), "buildings ->", path, dict(collections.Counter(e["rel"] for e in out)),
          "undated:", sum(1 for e in out if e.get("undated")), "ruins:", sum(1 for e in out if "руины" in e["status"]["ru"]), "with photos:", sum(1 for e in out if "ph" in e))


if __name__ == "__main__":
    main()
