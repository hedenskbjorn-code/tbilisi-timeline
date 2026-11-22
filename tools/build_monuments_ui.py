"""tools/monuments_ui.json: the strings of the cards of the monuments and plaques in ru / en (written here; the same table as in for_gemini/from_desktop/monuments_TASK_for_gemini.md) and ka (the answer of
Gemini, for_gemini/from_desktop/monuments_ui_result.json; the Georgian text only through Gemini; while it is missing the page shows the English text). Usage: python -P tools/build_monuments_ui.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RU_EN = {
    "layer_mon": ("Памятники и скульптуры", "Monuments and sculptures"),
    "layer_plq": ("Мемориальные доски", "Memorial plaques"),
    "sub_undated_mon": ("показывать и объекты без года установки", "also show objects without an installation year"),
    "sub_undated_plq": ("показывать и доски без года", "also show plaques without a year"),
    "k_sculpture": ("Скульптура", "Sculpture"), "k_bust": ("Бюст", "Bust"), "k_monument": ("Памятник", "Monument"), "k_statue": ("Статуя", "Statue"),
    "k_memorial": ("Мемориал", "Memorial"), "k_relief": ("Барельеф", "Relief"), "k_plaque": ("Мемориальная доска", "Memorial plaque"),
    "year": ("Год установки", "Installed"), "year_unknown": ("год неизвестен", "year unknown"),
    "sculptor": ("Скульптор", "Sculptor"), "architect": ("Архитектор", "Architect"), "material": ("Материал", "Material"),
    "where": ("Расположение", "Location"), "inscription": ("Надпись", "Inscription"),
    "lived_from": ("Связана с домом с {y} года (первый год жизни, названный в надписи)", "Linked to the house since {y} (the first year of residence named in the inscription)"),
    "photo": ("Фото: Wikimedia Commons", "Photo: Wikimedia Commons"), "src": ("Источник", "Source"),
    "attr": ("Данные: OpenStreetMap (ODbL), Wikidata, Википедия, Wikimedia Commons; энциклопедия «Тбилиси. Улицы, проспекты, площади» (2008).",
             "Data: OpenStreetMap (ODbL), Wikidata, Wikipedia, Wikimedia Commons; the encyclopedia “Tbilisi. Streets, avenues, squares” (2008)."),
    "mat_bronze": ("бронза", "bronze"), "mat_stone": ("камень", "stone"), "mat_metal": ("металл", "metal"), "mat_concrete": ("бетон", "concrete"), "mat_copper": ("медь", "copper"),
    "mat_marble": ("мрамор", "marble"), "mat_cast_iron": ("чугун", "cast iron"), "mat_steel": ("сталь", "steel"), "mat_basalt": ("базальт", "basalt"), "mat_plaster": ("гипс", "plaster"),
    "mat_wood": ("дерево", "wood"), "mat_aluminium": ("алюминий", "aluminium"),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = os.path.join(R, "for_gemini", "from_desktop", "monuments_ui_result.json")
    ka = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    if ka:
        assert set(ka) == set(RU_EN), set(ka) ^ set(RU_EN)
        for k, v in ka.items():
            assert not re.search("[А-Яа-яЁё]", v) and "პროსპექტ" not in v, k
        assert "{y}" in ka["lived_from"]
    ui = {k: {"ru": a, "en": b, **({"ka": ka[k]} if ka else {})} for k, (a, b) in RU_EN.items()}
    open(os.path.join(R, "tools", "monuments_ui.json"), "wb").write(json.dumps({"ui": ui}, ensure_ascii=False, indent=1).encode("utf-8"))
    print("strings:", len(ui), "| Georgian:", "yes" if ka else "not yet")


if __name__ == "__main__":
    main()
