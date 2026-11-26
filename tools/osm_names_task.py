"""The task for a research agent: the names, in ka / ru / en, of the named objects of OpenStreetMap that no card of the site has yet (the section 4 of tools/db_gaps.py): quarters / neighbourhoods / suburbs, squares and named bridges
(2026-11-24: 99 quarters, 16 squares, 12 bridges). Only the NAME in three languages, a point and a link to OpenStreetMap: no description is asked for and none may be made up.
File: work/research/tasks/osm_names.md; answer results/osm_names.json ({"<id>": {"ka": "...", "ru": "...", "en": "..."}}). The cards are made from the answer by a script that is written when the answer is there
(the scheme of tools/apply_parks.py). Usage: python -P tools/osm_names_task.py
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_gaps import norm  # noqa: E402
from paths import write_task  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEL = {"quarter": "json_extract(tags,'$.place') IN ('neighbourhood','quarter','suburb')", "square": "json_extract(tags,'$.place') = 'square'",
       "bridge": "json_extract(tags,'$.bridge') IS NOT NULL AND json_extract(tags,'$.name') LIKE '%ხიდი%'"}
KIND_RU = {"quarter": "квартал / микрорайон / пригород", "square": "площадь", "bridge": "мост"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect("file:%s?mode=ro" % os.path.join(R, "data", "db", "project.sqlite").replace("\\", "/"), uri=True)
    have_names = {norm(n) for (n,) in con.execute("SELECT name FROM name WHERE object_id LIKE 'TB/pl:%' OR object_id LIKE 'TB/st:%'")}
    have_ids = {m for (m,) in con.execute("SELECT local_id FROM object WHERE layer = 'pl'")}
    have_tail = {h.split("-", 1)[-1] for h in have_ids}
    dropped = set()                                                       # the pins that tools/places_edits.json dropped as duplicates ("district-n123" is OSM "node/123") must not come back as new cards
    for k in json.load(open(os.path.join(R, "tools", "places_edits.json"), encoding="utf-8")).get("drop", {}):
        kind, num = k.split("-", 1)[1][0], k.split("-", 1)[1][1:]
        dropped.add({"n": "node", "w": "way", "r": "relation"}[kind] + "/" + num)
    rows, seen = [], set()
    for kind, cond in SEL.items():
        for rid, tags, lat, lon in con.execute("SELECT DISTINCT rid, tags, lat, lon FROM raw_record WHERE source = 'osm' AND " + cond):
            t = json.loads(tags)
            nm = t.get("name:ka") or t.get("name")
            if rid in dropped or not nm or "რაიონი" in nm or norm(nm) in seen or norm(nm) in have_names:      # an administrative district ("raioni") has its polygon and label in the layer of districts
                continue
            short = rid.replace("/", "-").replace("way-", "w").replace("node-", "n").replace("relation-", "r")
            if short in have_tail:
                continue
            seen.add(norm(nm))
            rows.append((kind, rid, nm, t.get("name:ru") or "", t.get("name:en") or "", lat, lon))
    L = ["| id | kind | ka | ru | en | lat | lon |", "|---|---|---|---|---|---|---|"]
    for kind, rid, ka, ru, en, lat, lon in rows:
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (rid, KIND_RU[kind], ka, ru, en, "" if lat is None else "%.5f" % lat, "" if lon is None else "%.5f" % lon))
    text = f"""# ЗАДАНИЕ O: названия объектов OpenStreetMap, которых ещё нет на карте ({len(rows)} строк)

Проект: некоммерческая карта «Тбилиси во времени». Ниже именованные объекты OpenStreetMap (кварталы и микрорайоны, площади, мосты Тбилиси), для которых на сайте ещё нет карточки. Нужно **только название на трёх языках**: `ka`, `ru`, `en`. Описание, историю и значение названия **не писать и не выдумывать**.

Правила:
- Заполненные в таблице формы **повтори без изменений** (они взяты из OSM), если только они не стоят в поле другого алфавита (кириллица в `ka` или `en`, грузинские буквы в `ru` или `en`): тогда исправь.
- `ka` с грузинскими буквами, без кириллицы. `ru` кириллицей, `en` латиницей, без грузинских и кириллических букв.
- Для пустых `ru` и `en`: если у объекта есть устоявшаяся форма (статья в Википедии, подпись на карте, официальная форма), возьми её; иначе передай название транслитерацией (ru: практическая транскрипция, en: национальная романизация, как в OSM, например «Saburtalo»). Слова вида «квартал», «район», «мост», «площадь» пиши в названии так, как их пишут для таких объектов в Википедии (например «мост Бараташвили», «Baratashvili Bridge»).
- Слово «проспект» по-грузински только `გამზირი` (никогда `პროსპექტი`).
- Если не уверен в форме, всё равно дай лучший вариант и отметь строку в таблице сомнений ответа.

## Выход
`work/research/results/osm_names.json`: **один JSON-объект**: ключ `id` из таблицы, значение `{{"ka": "…", "ru": "…", "en": "…"}}` для **каждой** строки. В ответе дай таблицу сомнений.

## Объекты
{chr(10).join(L)}

## Готовая фраза для запуска
> Прочитай файл `work/research/tasks/osm_names.md`, выполни задание и сохрани результат в `work/research/results/osm_names.json`.
"""
    write_task("tasks/osm_names.md", text)
    import collections
    print("rows:", len(rows), dict(collections.Counter(r[0] for r in rows)), "| with ru:", sum(1 for r in rows if r[3]), "| with en:", sum(1 for r in rows if r[4]))


if __name__ == "__main__":
    main()
