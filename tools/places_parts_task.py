"""The task for Gemini about the places whose name is made of words (Vazisubani = vazi + ubani): the dictionary meaning of EVERY part with its own quote from the page of that word
(ka/ru/en Wiktionary or ena.ge), the table for_gemini/from_desktop/places4_batch_01.md (the places of tools/places_etym_exclude.json whose dictionary row went beyond its quote). The answer
places4_result.json is checked by tools/verify_places_parts.py. Usage: python -P tools/places_parts_task.py
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ex = {k: v for k, v in json.load(open(os.path.join(R, "tools", "places_etym_exclude.json"), encoding="utf-8")).items() if k != "note" and "dictionary row" in v}
    cand = {x["key"]: x for x in json.load(open(os.path.join(R, "data", "cache", "places_candidates.json"), encoding="utf-8"))}
    L = ["# Места, название которых составлено из слов: значение каждой части", "", "| key | вид | ka | ru | en |", "|---|---|---|---|---|"]
    for k in ex:
        c = cand[k]
        L.append("| %s | %s | %s | %s | %s |" % (k, c["kind"], c["name"]["ka"], c["name"]["ru"], c["name"]["en"]))
    open(os.path.join(R, "for_gemini", "from_desktop", "places4_batch_01.md"), "wb").write(("\n".join(L) + "\n").encode("utf-8"))
    print("places:", len(ex))


if __name__ == "__main__":
    main()
