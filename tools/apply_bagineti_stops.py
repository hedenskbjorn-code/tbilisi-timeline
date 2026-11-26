"""Add Bagineti sub-objects (Queen's Bath, King's Bath, Six-Apsed Temple, Wine Cellar, Bath, Six-Column Hall)
to site/data/mtskheta_tour.json (armazi part) and their Commons photos to site/data/photos.json.
Connect the Armazi fortress stop along the mapped hiking trail and back.

Idempotent: running twice produces byte-identical output. Supports --dry-run.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOUR_PATH = ROOT / "site" / "data" / "mtskheta_tour.json"
BAK_TOUR_PATH = ROOT / "data" / "curated" / "mtskheta_tour_base.json"
PHOTOS_PATH = ROOT / "site" / "data" / "photos.json"
OSRM_TAIL_PATH = ROOT / "data" / "curated" / "bagineti_tail_osrm.json"
FORTRESS_TRAIL_PATH = Path(__file__).with_name("armazi_fortress_trail.json")

NEW_PHOTOS = {
    "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 04.jpg": {
        "thumb": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/02/Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_04.jpg/960px-Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_04.jpg",
        "page": "https://commons.wikimedia.org/wiki/File:Armaztsikhe_archaeological_site_open-air_museum,_Mtskheta,_Georgia_04.jpg",
        "author": "Kober",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
        "w": 640,
        "h": 480,
    },
    "File:2010 – Conservation of Armaztsikhe Archaeological Site in Mtskheta - 14040204886.jpg": {
        "thumb": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ac/2010_%E2%80%93_Conservation_of_Armaztsikhe_Archaeological_Site_in_Mtskheta_-_14040204886.jpg/960px-2010_%E2%80%93_Conservation_of_Armaztsikhe_Archaeological_Site_in_Mtskheta_-_14040204886.jpg",
        "page": "https://commons.wikimedia.org/wiki/File:2010_%E2%80%93_Conservation_of_Armaztsikhe_Archaeological_Site_in_Mtskheta_-_14040204886.jpg",
        "author": "USEmbassyTbilisi",
        "license": "Public domain",
        "license_url": None,
        "w": 640,
        "h": 480,
    },
    "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 10.jpg": {
        "thumb": "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e9/Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_10.jpg/960px-Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_10.jpg",
        "page": "https://commons.wikimedia.org/wiki/File:Armaztsikhe_archaeological_site_open-air_museum,_Mtskheta,_Georgia_10.jpg",
        "author": "Kober",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
        "w": 640,
        "h": 480,
    },
    "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 11.jpg": {
        "thumb": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/06/Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_11.jpg/960px-Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_11.jpg",
        "page": "https://commons.wikimedia.org/wiki/File:Armaztsikhe_archaeological_site_open-air_museum,_Mtskheta,_Georgia_11.jpg",
        "author": "Kober",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
        "w": 640,
        "h": 480,
    },
    "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 18.jpg": {
        "thumb": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4a/Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_18.jpg/960px-Armaztsikhe_archaeological_site_open-air_museum%2C_Mtskheta%2C_Georgia_18.jpg",
        "page": "https://commons.wikimedia.org/wiki/File:Armaztsikhe_archaeological_site_open-air_museum,_Mtskheta,_Georgia_18.jpg",
        "author": "Kober",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
        "w": 640,
        "h": 480,
    },
}

SUB_STOPS = [
    {
        "id": "bagineti_queens_bath",
        "rid": 11900,
        "lat": 41.83828,
        "lon": 44.721127,
        "kind": "bath",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 04.jpg",
        "name": {
            "ru": "Армазцихе — Багинети: Баня царицы",
            "en": "Armaztsikhe–Bagineti: Queen’s Bath",
            "ka": "არმაზციხე/ბაგინეთი: დედოფლის აბანო",
        },
        "address": {
            "ru": "Гора Багинети, археологический комплекс Армазцихе",
            "en": "Mount Bagineti, Armaztsikhe archaeological site",
            "ka": "ბაგინეთის მთა, არმაზციხის არქეოლოგიური კომპლექსი",
        },
        "year": {
            "ru": "I–III вв. н. э.",
            "en": "1st–3rd c. CE",
            "ka": "I–III სს.",
        },
        "desc": {
            "ru": "Античная баня из рваного камня на известковом растворе с черепичной кровлей. Состоит из трёх отделений (холодного с раздевальней и бассейном, тёплого и горячего с двумя полукруглыми и одной прямоугольной ваннами, облицованными кирпичом и гидравлическим раствором).",
            "en": "Roman-style bathhouse built of rubble stone with lime mortar and a tiled roof. Comprises three sections: cold (changing room and pool), warm, and hot (two semicircular and one rectangular brick tubs lined with hydraulic mortar).",
            "ka": "ფლეთილი ქვით კირის ხსნარზე ნაგები კრამიტით გადახურული ანტიკური აბანო. შედგება სამი განყოფილებისგან: ცივი (გასახდელი და აუზი), თბილი და ცხელი (ორი ნახევარწრიული და ერთი ოთხკუთხა აბაზანით).",
        },
        "src": ["https://memkvidreoba.gov.ge/objects/immovable/immovableObject?id=11900"],
    },
    {
        "id": "bagineti_kings_bath",
        "rid": 11901,
        "lat": 41.837534,
        "lon": 44.72132,
        "kind": "bath",
        "ph": "File:2010 – Conservation of Armaztsikhe Archaeological Site in Mtskheta - 14040204886.jpg",
        "name": {
            "ru": "Армазцихе — Багинети: Царская баня",
            "en": "Armaztsikhe–Bagineti: King’s Bath",
            "ka": "არმაზციხე/ბაგინეთი: სამეფო აბანო",
        },
        "address": {
            "ru": "II терраса горы Багинети, Армазцихе",
            "en": "2nd terrace of Mount Bagineti, Armaztsikhe",
            "ka": "ბაგინეთის მთის II ტერასა, არმაზციხე",
        },
        "year": {
            "ru": "I–III вв. н. э.",
            "en": "1st–3rd c. CE",
            "ka": "I–III სს.",
        },
        "desc": {
            "ru": "Античная баня анфиладного типа (Der Reihentyp) на II террасе с пятью отделениями (аподитерий, фригидарий, тепидарий, кальдарий, префурний) и палестрой (50 кв. м) к западу. Отапливалась гипокаустом со столбиками высотой 61 см и толстым слоем opus signinum.",
            "en": "Enfilade Roman-type bathhouse on the 2nd terrace with five rooms (apoditerium, frigidarium, tepidarium, caldarium, praefurnium) and a 50 m² palaestra to the west. Heated by a 61 cm hypocaust and lined with thick opus signinum.",
            "ka": "II ტერასაზე მდებარე ანფილადური ტიპის აბანო ხუთი განყოფილებით (გასახდელი, ცივი, თბილი, ცხელი და საცეცხლე) და 50 მ² პალესტრით. ჰიპოკაუსტის სვეტები 61 სმ სიმაღლისაა, შელესილია opus signinum-ით.",
        },
        "src": ["https://memkvidreoba.gov.ge/objects/immovable/immovableObject?id=11901"],
    },
    {
        "id": "bagineti_six_apsed_temple",
        "rid": 11902,
        "lat": 41.837368,
        "lon": 44.721849,
        "kind": "temple",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 10.jpg",
        "name": {
            "ru": "Армазцихе — Багинети: Шестиапсидный храм",
            "en": "Armaztsikhe–Bagineti: Six-Apsed Temple",
            "ka": "არმაზციხე/ბაგინეთი: ექვსაფსიდიანი ტაძარი",
        },
        "address": {
            "ru": "I терраса горы Багинети, Армазцихе",
            "en": "1st terrace of Mount Bagineti, Armaztsikhe",
            "ka": "ბაგინეთის მთის I ტერასა, არმაზციხე",
        },
        "year": {
            "ru": "III–I вв. до н. э. – III в. н. э.",
            "en": "3rd–1st c. BCE – 3rd c. CE",
            "ka": "ძვ. წ. III–I – ახ. წ. III სს.",
        },
        "desc": {
            "ru": "Уникальный языческий храм на I террасе: прямоугольный центральный зал (200 кв. м) из сырца на песчаниковом цоколе с 6 апсидами (по две с запада и востока, по одной с юга и севера) и резной шестигранной базой центральной колонны шириной 1,27 м.",
            "en": "Unique pagan temple on the 1st terrace: a 200 m² rectangular mudbrick hall on sandstone ashlar plinths with six apses (two east, two west, one south, one north) and a carved 1.27 m hexagonal central column base.",
            "ka": "I ტერასაზე მდებარე ოთხკუთხა წარმართული ტაძარი (200 მ²) ექვსი აფსიდით (დასავლეთით და აღმოსავლეთით ორ-ორი, სამხრეთით და ჩრდილოეთით თითო-თითო) და ცენტრში 1,27 მ სიგანის ექვსკუთხა მოჩუქურთმებული ბაზით.",
        },
        "src": ["https://memkvidreoba.gov.ge/objects/immovable/immovableObject?id=11902"],
    },
    {
        "id": "bagineti_wine_cellar",
        "rid": 19878,
        "lat": 41.837326,
        "lon": 44.721677,
        "kind": "cellar",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 11.jpg",
        "name": {
            "ru": "Армазцихе — Багинети: Винный погреб (марани)",
            "en": "Armaztsikhe–Bagineti: Wine Cellar (Marani)",
            "ka": "არმაზციხე/ბაგინეთი: მარანი",
        },
        "address": {
            "ru": "I терраса горы Багинети, у Шестиапсидного храма",
            "en": "1st terrace of Mount Bagineti, by the Six-Apsed Temple",
            "ka": "ბაგინეთის მთის I ტერასა, ექვსაფსიდიან ტაძართან",
        },
        "year": {
            "ru": "I–III вв. н. э.",
            "en": "1st–3rd c. CE",
            "ka": "I–III სს.",
        },
        "desc": {
            "ru": "Храмовый винный погреб при Шестиапсидном храме: в пол вкопаны 16 крупных глиняных квеври, выстроенных в два ряда, общей вместимостью свыше 20 тонн жертвенного вина.",
            "en": "Temple wine cellar belonging to the Six-Apsed Temple: 16 large clay qvevri buried in two rows in the floor, with a combined capacity exceeding 20 tons of ritual wine.",
            "ka": "ექვსაფსიდიანი ტაძრის მარანი: იატაკში ორ რიგად ჩადგმულია 16 დიდი ქვევრი, რომელთა საერთო ტევადობა 20 ტონაზე მეტია საზედაშე ღვინისთვის.",
        },
        "src": ["https://memkvidreoba.gov.ge/objects/immovable/immovableObject?id=19878"],
    },
    {
        "id": "bagineti_bath",
        "rid": 20207,
        "lat": 41.837093,
        "lon": 44.721271,
        "kind": "bath",
        "name": {
            "ru": "Армазцихе — Багинети: Малая баня",
            "en": "Armaztsikhe–Bagineti: Bath",
            "ka": "არმაზციხე/ბაგინეთი: აბანო",
        },
        "address": {
            "ru": "К северо-западу от Шестиколонного зала, Багинети",
            "en": "Northwest of the Six-Column Hall, Mount Bagineti",
            "ka": "სვეტებიანი დარბაზის ჩრდილო-დასავლეთით, ბაგინეთი",
        },
        "year": {
            "ru": "I–III вв. н. э. (раскопки 1946 г.)",
            "en": "1st–3rd c. CE (excavated 1946)",
            "ka": "I–III სს. (გათხრილია 1946 წ.)",
        },
        "desc": {
            "ru": "Компактная баня слоя Армазцихе III (7 × 4,7 м, ~35 кв. м), раскопанная в 1946 г. на краю обрыва для стока воды. Сохранились два ряда круглых и квадратных кирпичных столбиков гипокауста, керамические плиты пола, оштукатуренная ванна и следы бассейна-резервуара.",
            "en": "Compact Armaztsikhe III bathhouse (7 × 4.7 m, ~35 m²) excavated in 1946 on the cliff edge for drainage. Retains two rows of round and square brick hypocaust piers, ceramic floor tiles, a plastered tub, and reservoir remains.",
            "ka": "1946 წ. გათხრილი არმაზციხე III-ის მცირე აბანო (7 × 4,7 მ), მოწყობილი ფლატეზე წყლის გასასვლელად. შემორჩენილია ჰიპოკაუსტის ორრიგა აგურის სვეტები, კერამიკული ფილები, შელესილი აბაზანა და აუზის ნაშთები.",
        },
        "src": ["https://memkvidreoba.gov.ge/objects/immovable/immovableObject?id=20207"],
    },
    {
        "id": "bagineti_six_column_hall",
        "rid": 11904,
        "lat": 41.836841,
        "lon": 44.721663,
        "kind": "palace",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 18.jpg",
        "name": {
            "ru": "Армазцихе — Багинети: Шестиколонный зал",
            "en": "Armaztsikhe–Bagineti: Six-Column Hall",
            "ka": "არმაზციხე/ბაგინეთი: სვეტებიანი დარბაზი",
        },
        "address": {
            "ru": "Юго-восточная часть I террасы, Багинети",
            "en": "Southeastern part of the 1st terrace, Mount Bagineti",
            "ka": "I ტერასის სამხრეთ-აღმოსავლეთი ნაწილი, ბაგინეთი",
        },
        "year": {
            "ru": "IV–III вв. до н. э.",
            "en": "4th–3rd c. BCE",
            "ka": "ძვ. წ. IV–III სს.",
        },
        "desc": {
            "ru": "Монументальное прямоугольное здание (20,82 × 8,87 м, ~185 кв. м) слоя Армазцихе I на I террасе: стены толщиной 1,45–1,70 м из песчаниковых квадров (до 3,3 м) и сырца, 6 баз и капителей вдоль оси под деревянные колонны и двускатная черепичная кровля. Предположительно царский дворец.",
            "en": "Monumental Armaztsikhe I rectangular hall (20.82 × 8.87 m, ~185 m²) on the 1st terrace: 1.45–1.70 m walls of sandstone ashlar (up to 3.3 m) and mudbrick, six axial column bases and capitals supporting wooden pillars, and a pitched tiled roof. Likely a royal palace.",
            "ka": "არმაზციხე I-ის მონუმენტური მართკუთხა დარბაზი (20,82 × 8,87 მ, ~185 მ²) I ტერასაზე: 1,45–1,70 მ სისქის ქვათლილისა და ალიზის კედლები, გრძივ ღერძზე განლაგებული 6 ბაზისი და კაპიტელი ხის სვეტებისთვის, ორფერდა კრამიტის სახურავი.",
        },
        "src": ["https://memkvidreoba.gov.ge/objects/immovable/immovableObject?id=11904"],
    },
]


def haversine_km(c1, c2) -> float:
    r = math.pi / 180.0
    dlat = (c2[1] - c1[1]) * r
    dlon = (c2[0] - c1[0]) * r
    a = math.sin(dlat / 2) ** 2 + math.cos(c1[1] * r) * math.cos(c2[1] * r) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for req in (PHOTOS_PATH, BAK_TOUR_PATH, TOUR_PATH, OSRM_TAIL_PATH, FORTRESS_TRAIL_PATH):
        if not req.is_file():
            raise FileNotFoundError(f"Missing required input file: {req}")

    photos = json.loads(PHOTOS_PATH.read_text(encoding="utf-8"))
    added_ph = 0
    for k, v in NEW_PHOTOS.items():
        if k not in photos:
            photos[k] = v
            added_ph += 1

    bak_tour = json.loads(BAK_TOUR_PATH.read_text(encoding="utf-8"))
    bak_armazi = next(p for p in bak_tour["parts"] if p["id"] == "armazi")
    bak_idx_bag = next(i for i, s in enumerate(bak_armazi["stops"]) if s["id"] == "bagineti")
    prefix_stops = [dict(s) for s in bak_armazi["stops"][: bak_idx_bag + 1]]
    bak_coords = bak_armazi["route"]["coords"]
    bag_pt = (prefix_stops[-1]["lon"], prefix_stops[-1]["lat"])
    cut_i = min(range(len(bak_coords)), key=lambda i: (bak_coords[i][0] - bag_pt[0]) ** 2 + (bak_coords[i][1] - bag_pt[1]) ** 2)
    prefix_coords = bak_coords[: cut_i + 1]

    trail = json.loads(FORTRESS_TRAIL_PATH.read_text(encoding="utf-8"))
    trail_coords = trail["coords"]
    if len(trail_coords) < 2:
        raise ValueError("Armazi fortress trail must contain at least two points")
    fortress_ix = next(i for i, s in enumerate(prefix_stops) if s["id"] == "armazi_fortress")
    fortress = prefix_stops[fortress_ix]
    junction = min(range(len(prefix_coords)), key=lambda i: haversine_km(prefix_coords[i], trail_coords[0]))
    if haversine_km(prefix_coords[junction], trail_coords[0]) > 0.002:
        raise ValueError("Armazi fortress trail does not join the base route within 2 m")
    if haversine_km(trail_coords[-1], (fortress["lon"], fortress["lat"])) > 0.020:
        raise ValueError("Armazi fortress trail does not reach the stop within 20 m")
    # Replace the rounded router vertex with the OSM trail junction. The return follows the same path.
    prefix_coords[junction:junction + 1] = trail_coords + trail_coords[-2::-1]
    trail_m = round(sum(haversine_km(a, b) for a, b in zip(trail_coords, trail_coords[1:])) * 1000)
    for s in prefix_stops[fortress_ix:fortress_ix + 2]:
        s["leg_m"] += trail_m
        s["leg_min"] = max(1, round(s["leg_m"] / 70))
    if trail["source"] not in fortress["src"]:
        fortress["src"] = [*fortress["src"], trail["source"]]

    original_tour = TOUR_PATH.read_text(encoding="utf-8")
    tour = json.loads(original_tour)
    osrm_tail = json.loads(OSRM_TAIL_PATH.read_text(encoding="utf-8"))
    tail_coords = osrm_tail["geometry"]["coordinates"]
    tail_legs = [round(l["distance"]) for l in osrm_tail["legs"]]

    armazi = next(p for p in tour["parts"] if p["id"] == "armazi")
    tail_stops = [dict(s) for s in SUB_STOPS] + [dict(next(s for s in bak_armazi["stops"] if s["id"] == "jvari"))]

    new_stops = prefix_stops + tail_stops
    for i in range(len(prefix_stops), len(new_stops)):
        prev_s, cur_s = new_stops[i - 1], new_stops[i]
        direct_m = round(haversine_km((prev_s["lon"], prev_s["lat"]), (cur_s["lon"], cur_s["lat"])) * 1000)
        leg_m = max(direct_m, tail_legs[i - len(prefix_stops)])
        cur_s["leg_m"] = leg_m
        cur_s["leg_min"] = max(1, round(leg_m / 70))
    for i, s in enumerate(new_stops):
        s["n"] = i + 1

    coords = prefix_coords + tail_coords[1:]
    total_km = round(sum(haversine_km(coords[i], coords[i + 1]) for i in range(len(coords) - 1)), 1)
    armazi["stops"] = new_stops
    armazi["route"] = {
        "length_km": total_km,
        "walk_min": round(total_km / 4.2 * 60),
        "coords": coords,
    }

    new_tour = json.dumps(tour, ensure_ascii=False, indent=2) + "\n"
    tour_changed = new_tour != original_tour
    if not args.dry_run:
        if added_ph:
            PHOTOS_PATH.write_text(json.dumps(photos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        if tour_changed:
            TOUR_PATH.write_text(new_tour, encoding="utf-8", newline="\n")
    action = "would update" if args.dry_run else "updated"
    print(f"{action}: {int(tour_changed)} tour files, {added_ph} new photos; "
          f"armazi stops={len(new_stops)}, length_km={total_km}, coords={len(coords)}, fortress trail={trail_m} m each way")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
