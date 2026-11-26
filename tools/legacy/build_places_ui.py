"""tools/places_ui.json: the strings of the layer "Local names" (the legend, the card) in ru / en (written here) and ka (the answer of Gemini, work/gemini/results/places_ui.json;
the Georgian text only through Gemini; while the answer is missing the strings have no ka and the page shows the English text). Usage: python -P tools/build_places_ui.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RU_EN = {
    "layer": ("Местные названия: районы, сады, холмы, мосты (что значит название)", "Local names: quarters, gardens, hills, bridges (what the name means)"),
    "kind_district": ("Район, квартал, посёлок", "Quarter, neighbourhood, settlement"),
    "kind_garden": ("Сад или парк", "Garden or park"),
    "kind_hill": ("Холм или гора", "Hill or mountain"),
    "kind_bridge": ("Мост", "Bridge"),
    "kind_cemetery": ("Кладбище или пантеон", "Cemetery or pantheon"),
    "kind_market": ("Рынок", "Market"),
    "kind_bath": ("Баня", "Bath"),
    "kind_area": ("Территория", "Area"),
    "etym": ("Откуда название", "Origin of the name"),
    "no_etym": ("Происхождение названия в источнике не названо", "The source does not say where the name comes from"),
    "src": ("Источник", "Source"),
    "quote": ("Цитата", "Quotation"),
    "attr": ("Описание и происхождение названия взяты из статей Википедии (лицензия CC BY-SA), положение точки из OpenStreetMap.",
             "The description and the origin of the name are taken from Wikipedia articles (CC BY-SA licence); the position of the point is from OpenStreetMap."),
    "area_approx": ("граница приблизительная", "the boundary is approximate"),
    "dict_note": ("Словарное значение слова (не источник происхождения топонима).", "Dictionary meaning of the word (not a source of the toponym's origin)."),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = os.path.join(R, "work", "gemini", "results/places_ui.json")
    ka = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    if ka:
        assert set(ka) == set(RU_EN), set(ka) ^ set(RU_EN)
        for k, v in ka.items():
            assert not re.search("[А-Яа-яЁё]", v) and "პროსპექტ" not in v, k
    ui = {k: {"ru": a, "en": b, **({"ka": ka[k]} if k in ka else {})} for k, (a, b) in RU_EN.items()}
    mu = json.load(open(os.path.join(R, "tools", "metro_ui.json"), encoding="utf-8"))      # the line "Encyclopedia ..., p." is the same as in the card of a metro station (three languages)
    ui["enc"] = mu["enc"] if "enc" in mu else mu["ui"]["enc"]
    mp = os.path.join(R, "work", "gemini", "results/places_manual.json")           # the card of the former hippodrome (tools/places_hippodrome.py): name, text, the note about the contour
    mk = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    ui["area_note"] = {"ru": "Показана территория Центрального парка по данным OpenStreetMap; ипподром занимал больше (по georgia.travel около 36 га, в прошлом до 57 га).",
                       "en": "The territory of the Central Park is shown (OpenStreetMap); the hippodrome was larger (about 36 ha according to georgia.travel, up to 57 ha in the past).", **({"ka": mk["area_note"]} if mk else {})}
    if mk:
        assert set(mk) == {"name", "about", "area_note"}, set(mk)
        for k, v in mk.items():
            assert not re.search("[А-Яа-яЁё]", v) and "პროსპექტ" not in v, k
        open(os.path.join(R, "tools", "places_manual_ka.json"), "wb").write(json.dumps({"name": mk["name"], "about": mk["about"]}, ensure_ascii=False, indent=1).encode("utf-8"))
    open(os.path.join(R, "tools", "places_ui.json"), "wb").write(json.dumps({"ui": ui}, ensure_ascii=False, indent=1).encode("utf-8"))
    print("strings:", len(ui), "| Georgian:", "yes" if ka else "not yet")


if __name__ == "__main__":
    main()
