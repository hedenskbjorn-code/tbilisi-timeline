"""One command for Gemini: regenerates every pending task file (tools/churches_task.py, tools/monuments_enrich_task.py, tools/parks_task.py) and writes for_gemini/from_desktop/ALL_TASKS_for_gemini.md,
a master file that lists them in the order of value and says how to work through them (one task after another, the result of each saved at once, a stop at the border of a task when the quota ends, a report of
what is done). The launch phrase is printed at the end. Usage: python -P tools/gemini_all.py
"""
import json
import os
import subprocess
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FD = os.path.join(R, "for_gemini", "from_desktop")
# (task file, result file, what it is, size) in the order of value: what the owner saw as a gap comes first
TASKS = [
    ("monuments_KA_TASK_for_gemini.md", "monuments_KA_result.json", "грузинский перевод 27 готовых описаний памятников (малое, самое выгодное)", "малое"),
    ("parks_TASK_for_gemini.md", "parks_result.json", "названия парков/садов на всех языках + 4 строки интерфейса (грузинский)", "малое"),
    ("folk_points_TASK_for_gemini.md", "folk_points_result.json", "где находятся 8 народных названий (точки на карте)", "малое"),
    ("churches_A_TASK_for_gemini.md", "churches_A_result.json", "недостающие языки названий 92 храмов", "среднее"),
    ("churches_B1_TASK_for_gemini.md", "churches_B1_result.json", "поиск названий безымянных храмов, пачка 1 (32)", "большое (поиск)"),
    ("churches_B2_TASK_for_gemini.md", "churches_B2_result.json", "поиск названий безымянных храмов, пачка 2 (32)", "большое (поиск)"),
    ("churches_B3_TASK_for_gemini.md", "churches_B3_result.json", "поиск названий безымянных храмов, пачка 3 (32)", "большое (поиск)"),
    ("churches_B4_TASK_for_gemini.md", "churches_B4_result.json", "поиск названий безымянных храмов, пачка 4 (29)", "большое (поиск)"),
] + [(f"monuments_E{i}_TASK_for_gemini.md", f"monuments_E{i}_result.json", f"описание и фото памятников без информации, пачка {i} (30)", "большое (поиск)") for i in range(1, 7)]


def empty_result(path):
    """a result in which EVERY row is "not_found" was written when a run failed (the quota ended): it counts as not done"""
    try:
        d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return isinstance(d, list) and bool(d) and all(isinstance(x, dict) and x.get("status") == "not_found" for x in d)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for script in ("churches_task.py", "monuments_enrich_task.py", "parks_task.py", "ka_descriptions_task.py"):
        r = subprocess.run([sys.executable, "-P", os.path.join(R, "tools", script)], capture_output=True, text=True, encoding="utf-8")
        print(script, "->", (r.stdout.strip().splitlines() or [r.stderr.strip()[-200:]])[-1])
    rows, todo = [], 0
    for task, result, what, size in TASKS:
        exists = os.path.exists(os.path.join(FD, task))
        done = os.path.exists(os.path.join(FD, result)) and not empty_result(os.path.join(FD, result))
        todo += 1 if exists and not done else 0
        rows.append(f"| {len(rows) + 1} | `{task}` | `{result}` | {what} | {size} | {'уже есть, пропусти' if done else ('ГОТОВО К ЗАПУСКУ (старый файл результата пуст: все not_found, перезапиши его)' if exists and os.path.exists(os.path.join(FD, result)) else 'ГОТОВО К ЗАПУСКУ' if exists else 'файла задания нет')} |")
    text = f"""# ПАКЕТ ЗАДАНИЙ: выполни все по порядку

Проект: некоммерческая карта «Тбилиси во времени». Ниже {len(TASKS)} заданий. Каждое лежит в своём файле в папке `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/`; в нём описаны правила, схема результата и таблица объектов. Результат каждого задания проверяет программа: **цитата, которой нет дословно на скачиваемой странице, отклоняет строку**, поэтому лучше `not_found`, чем неверное.

## Порядок работы
1. Иди по таблице сверху вниз. Для каждой строки со статусом «ГОТОВО К ЗАПУСКУ»: прочитай файл задания, выполни его **полностью по его правилам** и **сразу сохрани** файл результата рядом (имя в столбце «результат»). Не копи результаты в памяти и не переходи к следующему, пока этот не сохранён.
2. Строки «уже есть, пропусти» не трогай.
3. Модель: **Gemini 4 Argon** (другая группа модели почти без квоты). Если квота кончается, **остановись на границе задания** (не оставляй наполовину записанный файл) и в ответе перечисли: что выполнено, что нет.
4. В конце дай **одну сводную таблицу**: номер задания, сколько объектов найдено / не найдено, сомнения и спорные места (по каждому заданию 1–3 строки).

## Задания
| № | Файл задания | Файл результата | Что делаем | Объём | Статус |
|---|---|---|---|---|---|
{chr(10).join(rows)}

## Общие правила (одинаковые для всех)
- Кириллицы в полях `ka` и `en` нет; слово «проспект» по-грузински только `გამზირი`.
- Страницы для цитат должны скачиваться как обычный HTML (Википедия, Викиданные, сайты епархий и музеев, новости, travel-сайты, Wikimapia); **не** Google Maps, не страницы с входом, не имена пользователей форумов.
- Цитата до 25–30 слов, дословно как на странице; годы и имена в описании только из цитат.
- Файл результата: чистый JSON в UTF-8, ровно такая схема, как в задании.

## Готовая фраза для запуска (одна на всё)
> Прочитай файл `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/ALL_TASKS_for_gemini.md` и выполни все задания из него по порядку, как там написано; результаты сохраняй рядом с файлами заданий.
"""
    open(os.path.join(FD, "ALL_TASKS_for_gemini.md"), "w", encoding="utf-8").write(text)
    print(f"tasks: {len(TASKS)} | to run: {todo}\n\nФраза для Gemini (одна):\n> Прочитай файл `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/ALL_TASKS_for_gemini.md` и выполни все задания из него по порядку, как там написано; результаты сохраняй рядом с файлами заданий.")


if __name__ == "__main__":
    main()
