"""The task for a research agent made from the DRAFT list of churches of Tbilisi (data/cache/church_drafts_code_artifact.md: 137 entries with names, addresses, coordinates and years, WITHOUT sources: a draft, not data).
Each entry is a lead to check, never a fact. Entries are put in three groups by the distance to the nearest place of worship that we have (layers rel and relosm of the project index):
  within 100 m   same object as ours (nothing to do, except the nameless one: its name is a lead);
  100-300 m      probably ours with a wrong point (the lead for a name of a nameless object, or a new object);
  over 300 m     not in our data: a new object if it exists.
The task asks for every entry of the last two groups (and the nameless-object lead): does the church exist there, with a page that says so and the exact place. Files: work/research/tasks/churches_C.md,
answer results/churches_C.json (schema as in tools/churches_task.py, plus "same_as": the id of our object when it is the same building). Usage: python -P tools/church_drafts_task.py
"""
import json
import math
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import write_task  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(R, "data", "db", "project.sqlite")


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(x))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    for line in open(os.path.join(R, "data", "cache", "church_drafts_code_artifact.md"), encoding="utf-8"):
        m = re.match(r"\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*([\d.]+),\s*([\d.]+)\s*\|\s*(.+?)\s*\|", line)
        if m:
            rows.append({"n": int(m[1]), "name": m[2], "conf": m[3], "addr": m[4], "lat": float(m[5]), "lon": float(m[6]), "year": m[7]})
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    ours = con.execute("""SELECT o.id, o.lat, o.lon, COALESCE((SELECT name FROM name n WHERE n.object_id = o.id AND n.lang = 'en' LIMIT 1), ''), v.has_name FROM object o JOIN v_object_state v ON v.id = o.id
                          WHERE o.layer IN ('rel', 'relosm') AND o.lat IS NOT NULL""").fetchall()
    ask = []
    for r in rows:
        d, o = min(((hav(r["lat"], r["lon"], x[1], x[2]), x) for x in ours), key=lambda t: t[0])
        r["near_id"], r["near_name"], r["near_m"], r["near_nameless"] = o[0], o[3], round(d), not o[4]
        if d > 100 or (d <= 100 and not o[4]):
            ask.append(r)
    head = ["n", "name", "confession", "address (draft)", "lat (draft)", "lon (draft)", "year (draft)", "nearest object of ours (m)"]
    table = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in ask:
        table.append("| %d | %s | %s | %s | %.5f | %.5f | %s | %s %s (%d m)%s |" % (r["n"], r["name"], r["conf"], r["addr"], r["lat"], r["lon"], r["year"], r["near_id"], r["near_name"], r["near_m"], " NAMELESS" if r["near_nameless"] else ""))
    text = f"""# ЗАДАНИЕ C: проверить черновой список храмов Тбилиси ({len(ask)} записей)

Проект: некоммерческая карта «Тбилиси во времени». Ниже **черновик**: список храмов, составленный без источников. Названия, адреса, координаты и годы в нём **не факты, а подсказки для поиска**: координаты приблизительные, часть записей могут быть неточными или выдуманными. Для каждой записи нужно выяснить в интернете (поиск Google и другие), **существует ли такой храм и где именно**. Результат проверяется программой: цитата, которой нет дословно на скачиваемой странице, отклоняет строку; кириллицы в `ka` и `en` быть не должно; слово «проспект» по-грузински только `გამზირი`; страницы должны скачиваться как обычный HTML (Википедия, Викиданные, сайты епархий и приходов, новости, travel-сайты, Wikimapia; **не** Google Maps и не страницы с входом). Лучше `not_found`, чем неверное.

Колонка «nearest object of ours» показывает ближайший храм из нашей базы: если запись это то же здание (точка в черновике сдвинута), укажи его `id` в поле `same_as`, и тогда название и адрес пойдут нашему объекту (пометка NAMELESS: у нашего объекта сейчас нет названия).

## Выход
`work/research/results/churches_C.json`: **один JSON-массив**, по объекту на **каждую** строку таблицы, в том же порядке:
```json
{{"n": 54, "status": "found", "same_as": "TB/relosm:osmw…", "name": {{"ka": "…", "ru": "…", "en": "…"}}, "address": "как на странице", "lat": 41.64, "lon": 44.88,
 "coord_url": "https://www.openstreetmap.org/way/…", "year": 2005, "sources": [{{"url": "https://…", "lang": "ka", "quote": "дословная цитата до 30 слов", "fact": "name"}}]}}
```
- `status`: `found` или `not_found` (остальные поля пустые, `sources` = `[]`).
- Точка принимается, если `coord_url` ведёт на объект OpenStreetMap (его центр программа узнает сама и сверит с `lat, lon` в пределах 100 м) или страница Википедии, Викиданных или другая страница печатает координаты. Координаты из черновика сами по себе **ничего не доказывают**.
- `sources`: не меньше одного; `fact` ∈ `name`, `address`, `year`, `about`. Цитата с `fact: "name"` содержит название храма на любом из языков, цитата с `fact: "address"` (может быть той же) содержит улицу, район или ориентир, по которому храм привязан к месту. `year` только если назван в цитате `fact: "year"`.

## Записи
{chr(10).join(table)}

## Готовая фраза для запуска
> Прочитай файл `work/research/tasks/churches_C.md`, выполни задание и сохрани результат в `work/research/results/churches_C.json`.
"""
    write_task("tasks/churches_C.md", text)
    g = [sum(1 for r in rows if r["near_m"] <= 100), sum(1 for r in rows if 100 < r["near_m"] <= 300), sum(1 for r in rows if r["near_m"] > 300)]
    print("entries:", len(rows), "| within 100 m of ours:", g[0], "| 100-300 m:", g[1], "| over 300 m:", g[2], "| in the task:", len(ask))


if __name__ == "__main__":
    main()
