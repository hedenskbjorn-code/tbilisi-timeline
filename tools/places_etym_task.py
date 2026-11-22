"""The second search of the origin of the names of the local places: the places of data/cache/places_verified.json that came back without an etymology (the first pass read only the paragraphs of the
article of the place; it missed a gloss such as "lit. the apple cross" of the English article of Vashlijvari and "Vake means a plain" of the article of Vake Park). Makes
for_gemini/from_desktop/places3_batch_01.md (key | kind | ka | ru | en | the articles already read); the task is places3_TASK_for_gemini.md; the answer places3_result.json is checked by tools/verify_places_etym.py.
Usage: python -P tools/places_etym_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    v = json.load(open(os.path.join(R, "data", "cache", "places_verified.json"), encoding="utf-8"))["ok"]
    cand = {x["key"]: x for x in json.load(open(os.path.join(R, "data", "cache", "places_candidates.json"), encoding="utf-8"))}
    wiki = json.load(open(os.path.join(R, "data", "cache", "places_wiki.json"), encoding="utf-8"))
    L = ["# Места Тбилиси без происхождения названия: повторный поиск", "", "| key | вид | ka | ru | en | уже прочитанные статьи |", "|---|---|---|---|---|---|"]
    n = 0
    for r in v:
        if r["etym"]:
            continue
        c = cand[r["key"]]
        arts = " ".join(p["url"] for p in wiki[r["key"]]["pages"].values())
        L.append("| %s | %s | %s | %s | %s | %s |" % (r["key"], c["kind"], r["name"]["ka"], r["name"]["ru"], r["name"]["en"], arts))
        n += 1
    open(os.path.join(R, "for_gemini", "from_desktop", "places3_batch_01.md"), "wb").write(("\n".join(L) + "\n").encode("utf-8"))
    print("places:", n)


if __name__ == "__main__":
    main()
