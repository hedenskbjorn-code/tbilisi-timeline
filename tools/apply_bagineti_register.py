"""Add Armaztsikhe-Bagineti (#6581) and its 6 excavated sub-objects to site/data/monuments.json
and their ru/en names to site/data/names_i18n.json.

Idempotent: running twice produces no changes. Supports --dry-run.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MON_PATH = ROOT / "site" / "data" / "monuments.json"
I18N_PATH = ROOT / "site" / "data" / "names_i18n.json"

BAGINETI_MONUMENTS = [
    {
        "id": 6581,
        "name": "არმაზციხე/ბაგინეთი",
        "lon": 44.72146,
        "lat": 41.83775,
        "cls": "archaeology",
        "fn": "defense",
        "monument": True,
        "national": True,
        "reg": "6525",
        "raw_date": "ძვ. წ. IV - ახ. წ. VI სს.",
        "y0": -399,
        "y1": 600,
        "ye": 600,
        "ym": 100,
        "prec": "period",
        "ph": "File:Armazi Palace.jpg",
        "ru": "Армазцихе — Багинети (городище)",
        "en": "Armaztsikhe–Bagineti Archaeological Site",
    },
    {
        "id": 11900,
        "name": "არმაზციხე/ბაგინეთი. დედოფლის აბანო",
        "lon": 44.721127,
        "lat": 41.83828,
        "cls": "archaeology",
        "fn": "public",
        "monument": True,
        "national": False,
        "raw_date": "ახ. წ. I-III სს.",
        "y0": 1,
        "y1": 300,
        "ye": 300,
        "ym": 150,
        "prec": "period",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 04.jpg",
        "ru": "Армазцихе — Багинети: Баня царицы",
        "en": "Armaztsikhe–Bagineti: Queen’s Bath",
    },
    {
        "id": 11901,
        "name": "არმაზციხე/ბაგინეთი. სამეფო აბანო",
        "lon": 44.72132,
        "lat": 41.837534,
        "cls": "archaeology",
        "fn": "public",
        "monument": True,
        "national": False,
        "raw_date": "ახ. წ. I-III სს.",
        "y0": 1,
        "y1": 300,
        "ye": 300,
        "ym": 150,
        "prec": "period",
        "ph": "File:2010 – Conservation of Armaztsikhe Archaeological Site in Mtskheta - 14040204886.jpg",
        "ru": "Армазцихе — Багинети: Царская баня",
        "en": "Armaztsikhe–Bagineti: King’s Bath",
    },
    {
        "id": 11902,
        "name": "არმაზციხე/ბაგინეთი. ექვსაფსიდიანი ტაძარი",
        "lon": 44.721849,
        "lat": 41.837368,
        "cls": "archaeology",
        "fn": "religious",
        "monument": True,
        "national": False,
        "raw_date": "ძვ. წ. III - ახ. წ. III სს.",
        "y0": -299,
        "y1": 300,
        "ye": 300,
        "ym": 1,
        "prec": "period",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 10.jpg",
        "ru": "Армазцихе — Багинети: Шестиапсидный храм",
        "en": "Armaztsikhe–Bagineti: Six-Apsed Temple",
    },
    {
        "id": 19878,
        "name": "არმაზციხე/ბაგინეთი. მარანი",
        "lon": 44.721677,
        "lat": 41.837326,
        "cls": "archaeology",
        "fn": "other",
        "monument": True,
        "national": False,
        "raw_date": "ახ. წ. I-III სს.",
        "y0": 1,
        "y1": 300,
        "ye": 300,
        "ym": 150,
        "prec": "period",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 11.jpg",
        "ru": "Армазцихе — Багинети: Винный погреб (марани)",
        "en": "Armaztsikhe–Bagineti: Wine Cellar (Marani)",
    },
    {
        "id": 20207,
        "name": "არმაზციხე/ბაგინეთი. აბანო",
        "lon": 44.721271,
        "lat": 41.837093,
        "cls": "archaeology",
        "fn": "public",
        "monument": True,
        "national": False,
        "raw_date": "ახ. წ. I-III სს.",
        "y0": 1,
        "y1": 300,
        "ye": 300,
        "ym": 150,
        "prec": "period",
        "ru": "Армазцихе — Багинети: Малая баня",
        "en": "Armaztsikhe–Bagineti: Bath",
    },
    {
        "id": 11904,
        "name": "არმაზციხე/ბაგინეთი. სვეტებიანი დარბაზი",
        "lon": 44.721663,
        "lat": 41.836841,
        "cls": "archaeology",
        "fn": "public",
        "monument": True,
        "national": False,
        "raw_date": "ძვ. წ. IV-III სს.",
        "y0": -399,
        "y1": -201,
        "ye": -201,
        "ym": -300,
        "prec": "period",
        "ph": "File:Armaztsikhe archaeological site open-air museum, Mtskheta, Georgia 18.jpg",
        "ru": "Армазцихе — Багинети: Шестиколонный зал",
        "en": "Armaztsikhe–Bagineti: Six-Column Hall",
    },
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    mon = json.loads(MON_PATH.read_text(encoding="utf-8"))
    by_id = {f["properties"]["id"]: f for f in mon["features"]}
    i18n = json.loads(I18N_PATH.read_text(encoding="utf-8"))
    names = i18n["names"]

    added = 0
    added_i18n = 0
    for item in BAGINETI_MONUMENTS:
        props = {
            "id": item["id"],
            "name": item["name"],
            "address": "მცხეთა",
            "cls": item["cls"],
            "fn": item["fn"],
            "monument": item["monument"],
            "national": item["national"],
            "reg": item.get("reg"),
            "raw_date": item["raw_date"],
            "y0": item["y0"],
            "y1": item["y1"],
            "ye": item["ye"],
            "ym": item["ym"],
            "prec": item["prec"],
            "src": "Period",
            "unc": False,
        }
        if item.get("ph"):
            props["ph"] = item["ph"]
        feat = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [item["lon"], item["lat"]]},
            "properties": props,
        }
        if item["id"] not in by_id:
            mon["features"].append(feat)
            added += 1
        if item["name"] not in names:
            names[item["name"]] = {"en": item["en"], "ru": item["ru"]}
            added_i18n += 1

    if args.dry_run:
        print(f"Would add {added} monuments, {added_i18n} names_i18n entries")
        return 0

    if added:
        MON_PATH.write_text(json.dumps(mon, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    if added_i18n:
        I18N_PATH.write_text(json.dumps(i18n, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"added {added} monuments, {added_i18n} names_i18n entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
