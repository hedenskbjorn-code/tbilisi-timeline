"""The Georgian text of the steps of the tour that have none yet (site/data/tour.json: a step without "ka" in its title or text; the deploy is stopped by tests/check_data.mjs until it is there).
Makes work/gemini/tasks/tour_filters.md: for every such step the Russian and English text and, for consistency, the Georgian names that the interface already uses for the things the step names (blocks of the panel,
the old map, the groups, "Reset filters"). The answer results/tour_filters.json ({"<number of the step>": {"title": "...", "text": "..."}}) is checked and put into tour.json by tools/apply_tour_ka.py.
Usage: python -P tools/tour_ka_task.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI, SITE, SITE_DATA  # noqa: E402

KEYS = ["secBase", "secBounds", "secBuild", "secHist", "filtersTitle", "filtersReset", "showPlan", "planOpacity", "mapSrc", "mapSrcAuto", "mapSrcPlan", "gmReg", "gmSciEdu", "gmMon", "showMonUndated", "showPlqUndated"]


def ka_terms():
    """key -> the Georgian string of the interface (the third dictionary of i18n.js)"""
    s = open(os.path.join(SITE, "i18n.js"), encoding="utf-8").read()
    out = {}
    for k in KEYS:
        found = re.findall(r"\b%s: \"((?:[^\"\\]|\\.)*)\"" % k, s)
        if len(found) >= 3 and found[2]:
            out[k] = found[2]
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tour = json.load(open(os.path.join(SITE_DATA, "tour.json"), encoding="utf-8"))
    todo = [(i, st) for i, st in enumerate(tour["steps"], 1) if not (st["title"].get("ka") and st["text"].get("ka"))]
    terms = ka_terms()
    L = []
    for i, st in todo:
        L.append(f"### {i}\n- title ru: {st['title']['ru']}\n- title en: {st['title']['en']}\n- text ru: {st['text']['ru']}\n- text en: {st['text']['en']}\n")
    glossary = "\n".join(f"- `{k}`: {v}" for k, v in terms.items())
    text = f"""# ЗАДАНИЕ: грузинский текст шагов тура по сайту про фильтры ({len(todo)} шагов)

Проект: некоммерческая карта «Тбилиси во времени». Тур по сайту показывает окно «Фильтры» шаг за шагом. Для каждого шага ниже готовы русский и английский тексты, нужен **грузинский** (заголовок `title` и текст `text`). Смысл и числа не менять (годы 1913, 1953, 2005, пример 7/14). Без кириллицы; слово «проспект» только `გამზირი`. Названия блоков и кнопок пиши **ровно так, как они уже стоят в интерфейсе** (список ниже), чтобы текст тура совпадал с тем, что человек видит на экране. Кавычки в тексте грузинские „…“.

## Грузинские названия, которые уже есть в интерфейсе
{glossary}

## Выход
`C:/Projects/tbilisi-timeline/work/gemini/results/tour_filters.json`: **один JSON-объект**, ключ номер шага, значение `{{"title": "…", "text": "…"}}`, для **каждого** шага ниже. В ответе дай таблицу сомнений.

## Шаги
{chr(10).join(L)}
## Готовая фраза для запуска
> Прочитай файл `C:/Projects/tbilisi-timeline/work/gemini/tasks/tour_filters.md`, выполни задание и сохрани результат в `C:/Projects/tbilisi-timeline/work/gemini/results/tour_filters.json`.
"""
    os.makedirs(os.path.join(GEMINI, "tasks"), exist_ok=True)
    open(os.path.join(GEMINI, "tasks", "tour_filters.md"), "w", encoding="utf-8").write(text)
    print("steps without the Georgian text:", [i for i, _ in todo], "| terms taken from the interface:", len(terms))


if __name__ == "__main__":
    main()
