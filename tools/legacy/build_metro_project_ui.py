"""tools/metro_project_ui.json: the strings of the card of a station (project names, the list of the stations that were not built) in ru / en (written here) and ka (the answer of Gemini,
work/gemini/results/metro_project_ui.json; the Georgian text only through Gemini) and the Georgian name of the manual row (manual_ka). Usage: python -P tools/build_metro_project_ui.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RU_EN = {
    "project": ("На стадии проекта", "At the design stage"),
    "working": ("Во время строительства", "During construction"),
    "planned_btn": ("Не построенные станции метро", "Metro stations that were not built"),
    "planned_title": ("Не построенные станции метро", "Metro stations that were not built"),
    "planned_intro": ("Станции, которые были запланированы, но не построены (по данным Википедии; на карте их положение не показано).",
                      "Stations that were planned but not built (according to Wikipedia; their position is not shown on the map)."),
    "g_ext1": ("Продление линии 1 (Ахметели–Варкетили)", "Extension of line 1 (Akhmeteli–Varketili)"),
    "g_l3": ("Проект линии 3 (Руставели–Вазисубани)", "Project of line 3 (Rustaveli–Vazisubani)"),
    "s_stopped": ("работы остановлены в {y} году", "work stopped in {y}"),
    "s_none": ("не построена", "not built"),
    "place": ("Где", "Where"),
    "source": ("Источник", "Source"),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ka = json.load(open(os.path.join(R, "work", "gemini", "results/metro_project_ui.json"), encoding="utf-8"))
    assert set(ka) == set(RU_EN) | {"tu_project"}, set(ka) ^ (set(RU_EN) | {"tu_project"})
    for k, v in ka.items():
        assert not re.search("[А-Яа-яЁё]", v) and "პროსპექტ" not in v, k
    assert "{y}" in ka["s_stopped"]
    out = {"ui": {k: {"ru": a, "en": b, "ka": ka[k]} for k, (a, b) in RU_EN.items()}, "manual_ka": {"tu_project": ka["tu_project"]}}
    open(os.path.join(R, "tools", "metro_project_ui.json"), "wb").write(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print("ok:", len(out["ui"]), "strings")


if __name__ == "__main__":
    main()
