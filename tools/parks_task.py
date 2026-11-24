"""Makes the task for Gemini for the parks and gardens of OpenStreetMap (tools/apply_parks.py): the names, former names and other names that lack a language (ru, en, ka), and the Georgian text of three strings of the card.
File: work/gemini/tasks/parks.md; answer results/parks.json ({"<id>": {"n": {ka, ru, en}, "o": {...}, "al": {...}}} for the fields that exist, and "ui.<key>": "ka text"). Usage: python -P tools/parks_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "site", "data", "places.json"), encoding="utf-8"))
    rows = [c for c in d["items"] if c.get("pk") and c.get("pend")]
    ui = json.load(open(os.path.join(R, "tools", "folk_mod_ui.json"), encoding="utf-8"))["places"]
    L = ["| id | field | ka | ru | en |", "|---|---|---|---|---|"]
    for c in rows:
        for f in ("n", "o", "al"):
            if c.get(f) and not all(c[f].values()):
                L.append("| %s | %s | %s | %s | %s |" % (c["id"], f, c[f]["ka"], c[f]["ru"], c[f]["en"]))
    U = [f"### ui.{k}\n- ru: {v['ru']}\n- en: {v['en']}\n" for k, v in ui.items() if not v.get("ka")]
    ui_main = json.load(open(os.path.join(R, "tools", "folk_mod_ui.json"), encoding="utf-8"))["i18n"]
    U += [f"### i18n.{k}\n- ru: {v['ru']}\n- en: {v['en']}\n" for k, v in ui_main.items() if not v.get("ka")]       # the strings of the main interface (i18n.js) that wait for the Georgian text
    text = f"""# ЗАДАНИЕ P: недостающие языки названий парков и садов Тбилиси и строки интерфейса

Проект: некоммерческая карта «Тбилиси во времени». Парки взяты из OpenStreetMap; у части названий нет русской или английской формы (или грузинской). Нужны **недостающие** языки: `ka`, `ru`, `en`. Поле `n` = название, `o` = прежнее название (`old_name`), `al` = другое название. Названия пиши так, как их принято писать (парк, сад, сквер: ka «პარკი/ბაღი/სკვერი», ru «парк/сад/сквер», en «Park/Garden/Square»); имена людей и городов (парк Риги, Эревана, Нанта) в общепринятой форме; **существующие формы не меняй**. Если в строке несколько названий через `;` или `,` — это разные названия, сохрани разделитель. Кириллицы в `ka` и `en` быть не должно. Не придумывай: если форму не знаешь, оставь пустой строкой.

## Выход
`C:/Projects/tbilisi-timeline/work/gemini/results/parks.json`: **один JSON-объект**. Для каждой строки таблицы ключ `"<id>|<field>"` и значение `{{"ka": "…", "ru": "…", "en": "…"}}` (все три языка, существующие повтори). Для строк интерфейса ключ `"ui.<key>"` (карточка) или `"i18n.<key>"` (основной интерфейс) и значение строка `ka`. В ответе в чате дай таблицу сомнений.

## Строки интерфейса (ключ → русский и английский текст)
{chr(10).join(U)}
## Названия
{chr(10).join(L)}

## Готовая фраза для запуска
> Прочитай файл `C:/Projects/tbilisi-timeline/work/gemini/tasks/parks.md`, выполни задание и сохрани результат в `C:/Projects/tbilisi-timeline/work/gemini/results/parks.json`.
"""
    open(os.path.join(R, "work", "gemini", "tasks/parks.md"), "w", encoding="utf-8").write(text)
    print("rows:", len(L) - 2, "| ui strings:", len(U))


if __name__ == "__main__":
    main()
