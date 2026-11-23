"""Makes the tasks for Gemini that fill the cards of the monuments and sculptures which have nothing to read (data/sculptures.json: 9 of 628 cards have a description, 277 a photograph).
Objects taken: the ones that have a name in some language and have NO description and NO photograph (the nameless ones cannot be searched). Files (for_gemini/from_desktop/, not in git):
monuments_E<n>_TASK_for_gemini.md, batches of 30. Answer: monuments_E<n>_result.json. A description is accepted only with quotations that stand verbatim on a downloadable page; a photograph only as a file of
Wikimedia Commons whose page names the object or is geotagged within 100 m of it (checked by the program, tools/verify_monuments_enrich.py).
Usage: python -P tools/monuments_enrich_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FD = os.path.join(R, "for_gemini", "from_desktop")
SIZE = 30


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "site", "data", "sculptures.json"), encoding="utf-8"))
    st = d["streets"]
    rows = []
    for c in d["items"]:
        named = any((c["n"] or {}).values())
        has_d = c.get("d") and any(c["d"].values())
        if named and not c["ph"] and not has_d:
            s = st.get(c["st"]) if c.get("st") else None
            sc = c["sc"] if isinstance(c.get("sc"), str) else ((c.get("sc") or {}).get("en") or "")
            rows.append({"id": c["id"], "kind": c["k"], "ka": c["n"].get("ka", ""), "ru": c["n"].get("ru", ""), "en": c["n"].get("en", ""), "year": c["y"] if c["y"] is not None else "",
                         "sculptor": sc, "lat": c["lat"], "lon": c["lon"], "street": (s or {}).get("en", "")})
    batches = [rows[i:i + SIZE] for i in range(0, len(rows), SIZE)]
    for i, b in enumerate(batches, 1):
        L = ["| " + " | ".join(["id", "kind", "ka", "ru", "en", "year", "sculptor", "lat", "lon", "street"]) + " |", "|" + "---|" * 10]
        for r in b:
            L.append("| " + " | ".join(str(r[k]) for k in ["id", "kind", "ka", "ru", "en", "year", "sculptor", "lat", "lon", "street"]) + " |")
        text = f"""# ЗАДАНИЕ E{i}: описание и фото памятников и скульптур Тбилиси (пачка {i} из {len(batches)}, {len(b)} объектов)

Проект: некоммерческая карта «Тбилиси во времени». В карточках этих объектов (OpenStreetMap) нет ни описания, ни фото. Нужно найти в интернете (поиск Google и другие) **что это за объект**, кто автор, когда установлен, и **качественное фото на Wikimedia Commons**. Результат проверяется программой: цитата без дословного совпадения на скачиваемой странице отклоняет строку; кириллицы в `ka` и `en` быть не должно; слово «проспект» по-грузински только `გამზირი`. Ничего не придумывай и не бери из памяти: лучше `not_found`, чем неверное. Страницы должны скачиваться как обычный HTML (Википедия, Викиданные, сайты музеев, новости, travel-сайты, Wikimapia; **не** Google Maps и не страницы с входом).

Объект определяется координатами `lat, lon` и названием; **страница должна говорить об этом объекте в этом месте** (улица, район или парк совпадают; тёзки в других городах не годятся).

## Выход
`C:/Projects/tbilisi-timeline/for_gemini/from_desktop/monuments_E{i}_result.json`: **один JSON-массив**, по объекту на **каждую** строку таблицы, в том же порядке:
```json
{{"id": "OSM_n…", "status": "found", "description": {{"ru": "…", "en": "…", "ka": "…"}}, "year": 2022, "sculptor": "как в источнике",
 "commons_file": "File:Name.jpg", "sources": [{{"url": "https://…", "lang": "en", "quote": "дословная цитата до 30 слов", "fact": "about"}}]}}
```
- `status`: `found` (есть хотя бы описание с цитатой) или `not_found` (остальные поля пустые, `sources` = `[]`, `commons_file` = `""`).
- `description`: одно-два предложения на ru, en, ka **только по цитатам** (годы и имена из цитат); `year`: число, **только если назван в цитате с `fact: "year"`**, иначе `null`; `sculptor`: только если назван в цитате с `fact: "sculptor"`, иначе `""`.
- `sources`: не меньше одного; `fact` ∈ `about`, `year`, `sculptor`, `name`. Не копируй имена пользователей форумов.
- `commons_file`: файл Викисклада (заголовок `File:…`), **на котором виден именно этот объект**; лучше большой и чёткий снимок. Программа примет файл, если его страница называет объект или геотег файла в пределах 100 м от `lat, lon`. Если подходящего файла нет, `""`. Фото из других источников (Flickr, Google) не давать.

## Таблица
{chr(10).join(L)}

## Готовая фраза для запуска
> Прочитай файл `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/monuments_E{i}_TASK_for_gemini.md`, выполни задание и сохрани `monuments_E{i}_result.json` рядом с ним.
"""
        open(os.path.join(FD, f"monuments_E{i}_TASK_for_gemini.md"), "w", encoding="utf-8").write(text)
    print("objects:", len(rows), "in", len(batches), "batches of", SIZE)


if __name__ == "__main__":
    main()
