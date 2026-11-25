"""The Georgian text of the descriptions of the monuments that a search found (data/cache/monuments_verified.json: ru and en are ready, "ka" is empty). Makes work/gemini/tasks/monuments_KA.md
(the rows: id, name, ru, en; the quotations are given so that Gemini translates only what they say). Answer: results/monuments_KA.json {"<id>": "ka text"}; tools/apply_monuments_ka.py checks it (Georgian letters, no Cyrillic,
the same numbers as in the Russian text, no word პროსპექტი) and writes it into data/cache/monuments_verified.json; then python -P tools/apply_monuments.py. Usage: python -P tools/ka_descriptions_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from paths import CURATED, require_file
    ver = json.load(open(require_file(os.path.join(CURATED, "monuments_verified.json")), encoding="utf-8"))["ok"]
    items = {c["id"]: c for c in json.load(open(os.path.join(R, "site", "data", "sculptures.json"), encoding="utf-8"))["items"]}
    rows = [r for r in ver if not (r["description"].get("ka") or "").strip()]
    L = []
    for r in rows:
        n = items[r["id"]]["n"]
        L.append(f"### {r['id']}  ({n.get('ka') or n.get('ru') or n.get('en')})\n- ru: {r['description']['ru']}\n- en: {r['description']['en']}\n- цитаты источника: " + " | ".join(s["quote"] for s in r["sources"]) + "\n")
    text = f"""# ЗАДАНИЕ KA: грузинский текст описаний памятников ({len(rows)} описаний)

Проект: некоммерческая карта «Тбилиси во времени». Для каждого памятника готовы русский и английский тексты описания (по цитатам с проверенных страниц). Нужен **грузинский перевод** этого описания. Не добавляй фактов, которых нет в ru/en; числа и имена сохраняй; без кириллицы; слово «проспект» только `გამზირი`; названия мест и должностей в принятой грузинской форме (имена людей по-грузински, как в Википедии ka).

## Выход
`C:/Projects/tbilisi-timeline/work/gemini/results/monuments_KA.json`: **один JSON-объект** `{{"<id>": "грузинский текст"}}` для **каждого** id ниже. В ответе дай таблицу сомнений.

## Описания
{chr(10).join(L)}
## Готовая фраза для запуска
> Прочитай файл `C:/Projects/tbilisi-timeline/work/gemini/tasks/monuments_KA.md`, выполни задание и сохрани результат в `C:/Projects/tbilisi-timeline/work/gemini/results/monuments_KA.json`.
"""
    open(os.path.join(R, "work", "gemini", "tasks/monuments_KA.md"), "w", encoding="utf-8").write(text)
    print("descriptions to translate:", len(rows))


if __name__ == "__main__":
    main()
