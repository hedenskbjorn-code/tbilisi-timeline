"""Build site/data/run_trc2026.json: the route "TRC City Run 2026" (a GPX file of a Strava route) and the architectural sights near it, in the order of the route.
Only the geometry of the route is kept (no author, no link to a person); the sights come from the data of the site: the register objects that are of national
significance, have a Wikipedia article or are churches, fortresses and city walls, bridges, theatres and museums, plus a few picked by hand, and the religious buildings
of data/religious.json that still stand. "Near" means the distance from the point of the object to the track (up to 150 m); the distance is given for every sight.
Usage: python -X utf8 -P tools/build_run_route.py "<path to the .gpx>"
"""
import json
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAX_D = 150
HAND = {26522, 3725, 16937, 3616, 3937, 3827, 17828, 3757, 3397}      # Kukia Fortress, the old city wall, Gabriadze clock tower, Narikala, the synagogue, the mosque, Kukia church, Surb Gevorg, the Armenian church
EXCLUDE = {3835, 3317, 26449, 4920, 17121, 4209, 4381}                    # a shrine, a convent, a stone cross, a former church, the metro station, a house: not sights on their own
NAMES = {                                                                  # names fixed by hand where the register or the Wikipedia title is too general or wrong
    2765: ("Тбилисский театральный университет (второе здание, пр. Агмашенебели)", "Shota Rustaveli Theatre and Film University (second building, Aghmashenebeli Avenue)", "შოთა რუსთაველის თეატრისა და კინოს უნივერსიტეტი (მეორე შენობა, აღმაშენებლის გამზ.)"),
    3827: ("Мечеть Джума", "Juma Mosque", "ჯუმა მეჩეთი"),
    3937: ("Большая синагога", "Great Synagogue", "დიდი სინაგოგა"),
    18545: ("Церковь Сорока Мучеников", "Church of the Forty Martyrs", "ორმოც მოწამეთა ეკლესია"),
    16051: ("Фрагменты старой городской стены у улицы Пушкина", "Fragments of the old city wall near Pushkin Street", "ძველი ქალაქის გალავნის ფრაგმენტები პუშკინის ქუჩასთან"),
    3908: ("Тбилисская духовная семинария", "Tbilisi Theological Seminary", "თბილისის სასულიერო სემინარია"),
    3725: ("Старая городская стена у улицы Бараташвили", "The old city wall by Baratashvili Street", "ძველი ქალაქის გალავანი ბარათაშვილის ქუჩასთან"),
    3616: ("Крепость Нарикала", "Narikala Fortress", "ნარიყალა"),
    4893: ("Мост Галактиона Табидзе", "Galaktion Tabidze Bridge", "გალაკტიონ ტაბიძის ხიდი"),
    3433: ("Собор Сиони", "Sioni Cathedral", "სიონის ტაძარი"), 3864: ("Собор Сиони", "Sioni Cathedral", "სიონის ტაძარი"), 3447: ("Собор Сиони", "Sioni Cathedral", "სიონის ტაძარი"),
    3787: ("Базилика Анчисхати", "Anchiskhati Basilica", "ანჩისხატის ბაზილიკა"), 3914: ("Базилика Анчисхати", "Anchiskhati Basilica", "ანჩისხატის ბაზილიკა"),
}


def read_gpx(path):
    t = open(path, encoding="utf-8").read()
    return [(float(a), float(b), float(c)) for a, b, c in re.findall(r'<trkpt lat="([^"]+)" lon="([^"]+)">\s*<ele>([^<]+)</ele>', t)]


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def seg_dist(p, a, b):
    k = math.cos(math.radians(p[0]))
    ax, ay = (a[1] - p[1]) * k * 111320, (a[0] - p[0]) * 111320
    bx, by = (b[1] - p[1]) * k * 111320, (b[0] - p[0]) * 111320
    dx, dy = bx - ax, by - ay
    d2 = dx * dx + dy * dy
    t = 0 if d2 == 0 else max(0, min(1, -(ax * dx + ay * dy) / d2))
    return math.hypot(ax + t * dx, ay + t * dy), t


def title(s):
    return re.sub(r"\s*\((?:Тбилиси|Tbilisi|თბილისი)[^)]*\)", "", s or "").strip()


def main():
    pts = read_gpx(sys.argv[1])
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + hav(a, b))

    def locate(lat, lon):
        best = (1e9, 0)
        for i in range(len(pts) - 1):
            d, t = seg_dist((lat, lon), pts[i], pts[i + 1])
            if d < best[0]:
                best = (d, (cum[i] + t * (cum[i + 1] - cum[i])) / 1000)
        return best

    feats = json.load(open(os.path.join(ROOT, "site", "data", "monuments.json"), encoding="utf-8"))["features"]
    tr = json.load(open(os.path.join(ROOT, "site", "data", "names_i18n.json"), encoding="utf-8"))["names"]
    cand = []
    for f in feats:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        d, km = locate(lat, lon)
        if d > MAX_D:
            continue
        wp = dict(x.split(":", 1) for x in (p.get("wp") or "").split("|") if ":" in x)
        if p["id"] in EXCLUDE:
            continue
        pick = p["id"] in HAND or p.get("national") or (wp and p.get("fn") != "residential") or (wp and p.get("fn") == "residential" and "Palace" in wp.get("en", "")) \
            or (p.get("fn") == "religious")
        if not pick:
            continue
        ka = title(wp.get("ka")) or (p.get("name") or "").strip()
        en = title(wp.get("en")) or (tr.get(p.get("name") or "", {}).get("en") or "")
        ru = title(wp.get("ru")) or (tr.get(p.get("name") or "", {}).get("ru") or "")
        if p["id"] in NAMES:
            ru, en, ka = NAMES[p["id"]]
        cand.append({"id": p["id"], "lat": lat, "lon": lon, "d": d, "km": km, "fn": p.get("fn"), "ye": p.get("ye"), "name": {"ru": ru or en or ka, "en": en or ru or ka, "ka": ka},
                     "wp": {k: v for k, v in wp.items() if k in ("en", "ru", "ka")}, "key": (wp.get("en") or wp.get("ru") or wp.get("ka") or "").lower()})
    # one sight per building: the register has several entries for one building (Sioni, Anchiskhati, the opera...): the same Wikipedia title, or the same name within 45 m
    cand.sort(key=lambda c: c["d"])
    kept = []
    for c in cand:
        dup = False
        for k in kept:
            near = hav((c["lat"], c["lon"]), (k["lat"], k["lon"])) < 45
            if (c["key"] and c["key"] == k["key"] and hav((c["lat"], c["lon"]), (k["lat"], k["lon"])) < 250) or (near and c["name"]["en"] == k["name"]["en"]):
                dup = True
                break
        if not dup:
            kept.append(c)
    # religious buildings of the layer that still stand and are not yet there
    rel = json.load(open(os.path.join(ROOT, "site", "data", "religious.json"), encoding="utf-8"))
    for r in rel:
        if "to" in r:
            continue
        d, km = locate(r["lat"], r["lon"])
        if d > MAX_D:
            continue
        if any(hav((r["lat"], r["lon"]), (k["lat"], k["lon"])) < 60 for k in kept):
            continue
        kept.append({"id": "rel:" + r["id"], "lat": r["lat"], "lon": r["lon"], "d": d, "km": km, "fn": "religious", "ye": r["from"], "name": r["name"], "wp": {}, "key": ""})
    kept.sort(key=lambda c: c["km"])
    sights = []
    for i, c in enumerate(kept, 1):
        sights.append({"n": i, "km": round(c["km"], 2), "d": round(c["d"]), "lat": round(c["lat"], 6), "lon": round(c["lon"], 6), "fn": c["fn"], "year": c["ye"],
                       "name": c["name"], "wp": c["wp"]})
    out = {"note": "Built by tools/build_run_route.py on 2026-11-19 from the GPX of the route TRC City Run 2026 (Strava route 3539586152726489518) and the data of this site.",
           "route": {"name": "TRC City Run 2026", "length_km": round(cum[-1] / 1000, 2), "ele_min": round(min(p[2] for p in pts)), "ele_max": round(max(p[2] for p in pts)),
                     "coords": [[round(p[1], 6), round(p[0], 6)] for p in pts], "src": "https://www.strava.com/routes/3539586152726489518"},
           "sights": sights}
    p = os.path.join(ROOT, "site", "data", "run_trc2026.json")
    open(p, "wb").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print("route km:", out["route"]["length_km"], "| sights:", len(sights))
    for s in sights:
        print(s["n"], s["km"], s["d"], s["fn"], s["name"]["en"][:48], "|", s["name"]["ru"][:36])


if __name__ == "__main__":
    main()
