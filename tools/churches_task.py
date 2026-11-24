"""Makes the tasks for Gemini about the places of worship of OpenStreetMap (site/data/religious_osm.json, 217 objects) and about the folk names that have no point yet.
Files (work/gemini/, not in git):
  tasks/churches_A.md      the names that exist in one or two languages: the missing languages (ru, en, ka) for 92 objects; no search, a translation of the dedication;
  tasks/churches_B<n>.md   the 125 objects without any name, in batches of 32: search the name, the dedication, the address and the year of building on pages that can be downloaded, with quotations;
  tasks/folk_points.md     the 8 folk names (rows of results/folk.json) whose place has no point: where exactly the object is, with a quotation and a page that prints the coordinates or an OSM object.
Usage: python -P tools/churches_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI as FD  # noqa: E402
REL = {"orthodox": "Georgian Orthodox", "christianOsm": "Christian (denomination not given in OSM)", "muslim": "Muslim", "catholic": "Catholic", "armenian": "Armenian Apostolic", "russian": "Russian Orthodox",
       "lutheran": "Lutheran", "jewish": "Jewish", "yazidi": "Yazidi", "zoroastrian": "Zoroastrian"}
COMMON = """Проект: некоммерческая карта «Тбилиси во времени». Результат проверяется программой: **цитата, которой нет дословно на скачиваемой странице, отклоняет строку**; кириллицы в `ka` и `en` быть не должно; слово «проспект» по-грузински только `გამზირი`. Ничего не придумывай и не бери из памяти: лучше `not_found`, чем неверное название. Страницы должны скачиваться как обычный HTML (Википедия, Викиданные, сайты епархий и приходов, новости, travel-сайты, Wikimapia; **не** Google Maps и не страницы с входом)."""


def objects():
    d = json.load(open(os.path.join(R, "site", "data", "religious_osm.json"), encoding="utf-8"))
    st = d["streets"]
    out = []
    for x in d["items"]:
        n = x.get("name") or {}
        s = st.get(x["st"]) if x.get("st") else None
        out.append({"id": x["id"], "rel": REL.get(x["rel"], x["rel"]), "lat": x["lat"], "lon": x["lon"], "osm": x["osm"], "street": (s or {}).get("en", ""), "street_ka": (s or {}).get("ka", ""),
                    "ka": n.get("ka", ""), "ru": n.get("ru", ""), "en": n.get("en", ""), "year": x["from"] if not x["undated"] else None})
    return out


def table(rows, cols):
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        L.append("| " + " | ".join(str(r[c] if r[c] is not None else "") for c in cols) + " |")
    return "\n".join(L)


def write(name, text):
    os.makedirs(os.path.dirname(os.path.join(FD, name)), exist_ok=True)
    open(os.path.join(FD, name), "w", encoding="utf-8").write(text)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ob = objects()
    named = [o for o in ob if o["ka"] or o["ru"] or o["en"]]
    nameless = [o for o in ob if not (o["ka"] or o["ru"] or o["en"])]
    phrase = "> Прочитай файл `C:/Projects/tbilisi-timeline/work/gemini/%s`, выполни задание и сохрани результат в `C:/Projects/tbilisi-timeline/work/gemini/%s`."
    # ---- A: the missing languages of the names that exist
    write("tasks/churches_A.md", f"""# ЗАДАНИЕ A: недостающие языки названий храмов ({len(named)} объектов)

{COMMON}

В таблице храмы Тбилиси из OpenStreetMap, у которых название есть не на всех трёх языках. Нужны **недостающие** названия в `ka`, `ru`, `en`. Названия даются так, как их принято писать по-русски и по-английски (посвящение святому; «სახ.» = «сахелобис» — «имени святого», ru: «церковь Святого Антония Мартквели», en: «Church of St. Anton Martqopeli»; монастырь, собор, часовня, молельный дом по смыслу). Имя святого пиши в общепринятой форме (проверь по Википедии, ru/en/ka). Ничего не добавляй, чего нет в названии (адрес, год).
Если название `ka` уже есть, его **не менять**; если есть только `en` или `ru`, `ka` пиши как принято в Грузии.

## Выход
`C:/Projects/tbilisi-timeline/work/gemini/results/churches_A.json`: один JSON-объект `{{"<id>": {{"ka": "…", "ru": "…", "en": "…"}}}}` для **каждого** объекта таблицы, все три языка (существующие повтори как есть). В ответе дай таблицу сомнений.

## Таблица (id | ka | ru | en | рядом с улицей)
{table(named, ["id", "ka", "ru", "en", "street"])}

## Готовая фраза для запуска
{phrase % ("tasks/churches_A.md", "results/churches_A.json")}
""")
    # ---- B: the objects without a name, in batches
    size = 32
    batches = [nameless[i:i + size] for i in range(0, len(nameless), size)]
    for i, b in enumerate(batches, 1):
        write(f"tasks/churches_B{i}.md", f"""# ЗАДАНИЕ B{i}: найти названия храмов без названия (пачка {i} из {len(batches)}, {len(b)} объектов)

{COMMON}

В таблице места богослужения Тбилиси из OpenStreetMap **без названия**. Для каждого найди в интернете (поиск Google и другие), что это за храм: название, кому посвящён, адрес и год постройки (если страница называет). Объект определяется координатами `lat, lon` и ближайшей улицей: **страница должна называть этот храм именно в этом месте** (адрес или район совпадает с улицей/координатами; тёзки в других местах не годятся). Если уверенно найти не удалось, ставь `"status": "not_found"`.

## Выход
`C:/Projects/tbilisi-timeline/work/gemini/results/churches_B{i}.json`: **один JSON-массив**, по объекту на **каждую** строку таблицы, в том же порядке:
```json
{{"id": "osmw…", "status": "found", "name": {{"ka": "…", "ru": "…", "en": "…"}}, "address": "улица и номер, как на странице",
 "year": 1893, "sources": [{{"url": "https://…", "lang": "ka", "quote": "дословная цитата до 30 слов", "fact": "name"}}]}}
```
- `status`: `found` или `not_found` (тогда остальные поля пустые, `sources` = `[]`).
- `name`: три языка, без кириллицы в `ka` и `en`. `year`: год постройки/освящения числом, **только если он назван в цитате с `fact: "year"`**, иначе `null`.
- `sources`: не меньше одного; `fact` ∈ `name`, `address`, `year`, `about`. **Цитата с `fact: "name"` должна содержать название храма** (на любом из языков), а цитата с `fact: "address"` — улицу или номер дома, по которым храм привязан к месту (если адрес назван на другой странице, дай вторую цитату). Не копируй имена пользователей форумов и отзывов, только текст о храме.
- Если у одного источника несколько цитат, дай несколько элементов `sources` с тем же `url`.

## Таблица (id | конфессия | lat | lon | рядом с улицей | улица по-грузински)
{table(b, ["id", "rel", "lat", "lon", "street", "street_ka"])}

## Готовая фраза для запуска
{phrase % (f"tasks/churches_B{i}.md", f"results/churches_B{i}.json")}
""")
    # ---- C: the folk names without a point
    rows = json.load(open(os.path.join(FD, "results/folk.json"), encoding="utf-8"))
    pts = json.load(open(os.path.join(R, "data", "cache", "folk_points.json"), encoding="utf-8"))["unplaced"]
    body = []
    for u in pts:
        r = rows[u["row"]]
        body.append({"row": u["row"], "folk": r["folk"].get("ka") or r["folk"].get("ru"), "ru": r["folk"].get("ru", ""), "official_ka": r["official"]["ka"], "official_ru": r["official"]["ru"],
                     "meaning_ru": (r["meaning"] or {}).get("ru", "")})
    write("tasks/folk_points.md", f"""# ЗАДАНИЕ C: где находятся 8 мест с народными названиями ({len(body)} строк)

{COMMON}

Для этих народных названий нет точки на карте. Нужно **точное место объекта**: здание, площадь или район, к которому относится народное название. Дай адрес (улица, номер, район) и координаты `lat, lon` центра объекта. Координаты принимаются, **только если** их подтверждает страница, которую программа скачает: (а) объект OpenStreetMap (ссылка `https://www.openstreetmap.org/way/…`, `/node/…` или `/relation/…`: программа сама узнает его центр), или (б) статья Википедии / запись Викиданных с координатами, или (в) страница, на которой координаты напечатаны текстом (Wikimapia, сайт здания, travel-сайт). Для района из нескольких улиц дай точку пересечения двух названных улиц и скажи, что это район (`"kind": "area"`).

## Выход
`C:/Projects/tbilisi-timeline/work/gemini/results/folk_points.json`: **один JSON-массив**, по объекту на каждую строку таблицы:
```json
{{"row": 2, "status": "found", "kind": "building|square|area|market", "address": "…", "lat": 41.70, "lon": 44.79,
 "coord_url": "https://www.openstreetmap.org/way/…", "sources": [{{"url": "https://…", "lang": "ka", "quote": "дословная цитата до 30 слов, где место названо (адрес, улица или район)"}}]}}
```
`status`: `found` или `not_found`. Цитаты должны дословно стоять на странице; координаты не из памяти.

## Таблица
{table(body, ["row", "folk", "ru", "official_ka", "official_ru", "meaning_ru"])}

## Готовая фраза для запуска
{phrase % ("tasks/folk_points.md", "results/folk_points.json")}
""")
    print("named:", len(named), "| nameless:", len(nameless), "in", len(batches), "batches | folk without a point:", len(body))


if __name__ == "__main__":
    main()
