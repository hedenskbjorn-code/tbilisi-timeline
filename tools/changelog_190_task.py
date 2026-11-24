"""The task for Gemini: the Georgian text of two items of the entry 1.9.0 of site/data/changelog.json that were corrected / added after the first version of the entry (2026-11-24):
  "panel": the item about the panel of the filters (rewritten: the rows "near me" / "only without a photo" are under the head and only in the mode of photo collecting; one block at a time on a phone; five NEW steps of the tour);
  "streets": a NEW item: lines of 113 streets, dates of nine register objects, five district points moved to the urban core, three duplicates removed, the filter of the City Run route removed.
The Russian and English texts are in this file (PANEL, STREETS); the answer results/changelog_190.json ({"panel": {"ka": "..."}, "streets": {"ka": "..."}}) is checked and put into changelog.json by tools/apply_changelog_190.py.
Until the answer is there the entry stays as it is (accurate, without these two points): the deploy is not stopped. Usage: python -P tools/changelog_190_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PANEL = {
    "ru": "Обновлена панель фильтров: единая галочка «Старая карта» с выбором источника и прозрачности, группа «Транспорт и дороги» с пятью видами линий (метро, трамвай, железная дорога, дороги и мосты, фуникулёр и канатная дорога), строки «Рядом со мной» и «Только без фото» под шапкой (в режиме сбора фото), на телефоне открыт один блок за раз; в туториале пять новых шагов про фильтры.",
    "en": "Updated Filters panel: a single \"Old map\" box with source and opacity controls, a \"Transport and roads\" group with five line kinds (metro, tram, railway, roads and bridges, funicular and cable car), the \"Near me\" and \"Only without a photo\" rows under the header (in photo-collection mode), one block open at a time on a phone; the tour has five new steps about the filters.",
}
STREETS = {
    "ru": "Улицы и места: на карте появились линии 113 улиц, которые раньше были только карточками; девять объектов реестра получили год или диапазон дат; точки пяти районов перенесены с окраин в городские ядра, три дубля «район X» убраны; убран фильтр маршрута City Run (у забега своя страница).",
    "en": "Streets and places: the map now draws the lines of 113 streets that used to have a card only; nine register objects got a year or a range of dates; the points of five districts moved from the outskirts into the urban core, three duplicates \"district X\" were removed; the City Run route filter was removed (the run has its own page).",
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ka = {}
    c = json.load(open(os.path.join(R, "site", "data", "changelog.json"), encoding="utf-8"))
    for it in c[0]["items"]:
        if it["en"].startswith("Updated Filters panel"):
            ka = it["ka"]
    text = f"""# ЗАДАНИЕ: грузинский текст двух пунктов записи 1.9.0 в списке изменений (2 пункта)

Проект: некоммерческая карта «Тбилиси во времени». Запись версии 1.9.0 в `site/data/changelog.json` исправлена; нужен **грузинский** (`ka`) текст двух пунктов. Смысл и числа (113, пять, девять, три) не менять. Без кириллицы; слово «проспект» только `გამზირი`. Названия блоков и кнопок пиши так, как они уже стоят в интерфейсе: «ძველი რუკა», «ტრანსპორტი და გზები», «ჩემ გვერდით», «მხოლოდ უფოტოო», «ფილტრები». Кавычки грузинские „…“.

Старый грузинский текст пункта про панель (для сверки терминов; пункт переписан, переводить новый русский текст):
> {ka}

## Пункт «panel»
- ru: {PANEL['ru']}
- en: {PANEL['en']}

## Пункт «streets»
- ru: {STREETS['ru']}
- en: {STREETS['en']}

## Выход
`C:/Projects/tbilisi-timeline/work/gemini/results/changelog_190.json`: **один JSON-объект** `{{"panel": {{"ka": "…"}}, "streets": {{"ka": "…"}}}}`. В ответе дай таблицу сомнений.

## Готовая фраза для запуска
> Прочитай файл `C:/Projects/tbilisi-timeline/work/gemini/tasks/changelog_190.md`, выполни задание и сохрани результат в `C:/Projects/tbilisi-timeline/work/gemini/results/changelog_190.json`.
"""
    os.makedirs(os.path.join(R, "work", "gemini", "tasks"), exist_ok=True)
    open(os.path.join(R, "work", "gemini", "tasks", "changelog_190.md"), "w", encoding="utf-8").write(text)
    print("task written: work/gemini/tasks/changelog_190.md")


if __name__ == "__main__":
    main()
