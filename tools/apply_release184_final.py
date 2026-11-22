"""Release 1.8.4, the last texts: two items of the changelog (the streets of the encyclopedia with the street card; the fix of the tram routes no. 3 and 4) and the Georgian texts of two interface lines
(stTitle, stUndated). The Georgian texts are Gemini's (for_gemini/from_desktop/tbilisi_release184_final_result.md), checked here: no Cyrillic, no the calque of the word "prospect".
The numbers of the streets are taken from the spec (tools/streets_enc1_spec.json): the Georgian text of Gemini was written with the numbers of an earlier run, they are replaced here. Idempotent.
"""
import json
import os
import re
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(R, "for_gemini", "from_desktop", "tbilisi_release184_final_result.md")
SPEC = os.path.join(R, "tools", "streets_enc1_spec.json")
CHANGELOG = os.path.join(R, "site", "data", "changelog.json")
I18N = os.path.join(R, "site", "i18n.js")
DRY = "--dry-run" in sys.argv
CYR = re.compile("[Ѐ-ӿ]")
CR, LF = chr(13), chr(10)


def main():
    ka = {}
    for line in open(RES, encoding="utf-8").read().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] in ("CL184e", "CL184t", "UI_stTitle", "UI_stUndated"):
            ka[cells[0]] = cells[1]
    assert len(ka) == 4, "missing rows: %s" % sorted(ka)
    for k, v in ka.items():
        assert not CYR.search(v) and "პროსპექტ" not in v, "bad Georgian text in " + k
    sp = json.load(open(SPEC, encoding="utf-8"))
    n_new, n_merged = len(sp["spec"]), len(sp["merge"])
    assert len(re.findall(r"\b483\b", ka["CL184e"])) == 1 and len(re.findall(r"\b54\b", ka["CL184e"])) == 1
    ka_e = re.sub(r"\b483\b", str(n_new), ka["CL184e"])
    ka_e = re.sub(r"\b54\b", str(n_merged), ka_e)
    ru_e = ("На карте и в данных появились истории названий ещё %d улиц Тбилиси по энциклопедии «Тбилиси. Улицы, проспекты, площади» (2008), у %d улиц, уже бывших на карте, добавлены прежние названия; "
            "у каждой улицы есть карточка (клик по подписи на карте, строка в списке названий или поиск), где собраны все прежние названия с годами, в том числе названия без года, примечание и источник; "
            "поиск находит улицы по любому прежнему названию." % (n_new, n_merged))
    en_e = ("Name histories of %d more Tbilisi streets appear on the map and in the data after the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008), earlier names are added to %d streets that were already on the map; "
            "every street has a card (a click on the label on the map, a row of the list of the names or the search) that gathers all the former names with their years, also the names without a year, the note and the source; "
            "the search finds the streets by any former name." % (n_new, n_merged))
    ru_t = "Исправлены линии трамвайных маршрутов № 3 и № 4 1986 года: убран ошибочный участок у улицы Тбилисис Згви (подъём к Тбилисскому морю не совпадает с этой улицей)."
    en_t = "The lines of the tram routes no. 3 and no. 4 of 1986 are corrected: the wrong section at Tbilisis Zghvi Street is removed (the Tbilisi Sea Ascent is not that street)."
    raw = open(CHANGELOG, encoding="utf-8", newline="").read()
    rel = json.loads(raw)
    assert rel[0]["version"] == "1.8.4"
    items = rel[0]["items"]
    if not any(i["en"] == en_e for i in items):
        items[:] = [i for i in items if not i["en"].startswith("Name histories of ")] + [{"t": "new", "ru": ru_e, "en": en_e, "ka": ka_e}]   # replaces the item of an earlier count
    if not any(i["en"] == en_t for i in items):
        items.append({"t": "fix", "ru": ru_t, "en": en_t, "ka": ka["CL184t"]})
    out = json.dumps(rel, ensure_ascii=False, indent=1)
    if CR + LF in raw:
        out = out.replace(LF, CR + LF)
    js = open(I18N, encoding="utf-8", newline="").read()
    ka_block_start = js.index("stNow: \"დღეს\"")
    seg_start = js.rfind("stTitle:", 0, ka_block_start)
    assert seg_start > 0
    old_title = js[seg_start:js.index("\n", seg_start)]
    new_title = "stTitle: \"%s\"," % ka["UI_stTitle"]
    js2 = js.replace(old_title, ("      " if False else "") + new_title, 1)
    old_und = re.search(r"stUndated: \"ადრე ერქვა[^\"]*\",", js2).group(0)
    js2 = js2.replace(old_und, "stUndated: \"%s\"," % ka["UI_stUndated"], 1)
    if not DRY:
        open(CHANGELOG, "wb").write(out.encode("utf-8"))
        open(I18N, "wb").write(js2.encode("utf-8"))
    print("changelog items of 1.8.4: %d; i18n ka updated: %s; streets %d, merged %d; %s" % (len(items), js2 != js, n_new, n_merged, "dry run" if DRY else "written"))


if __name__ == "__main__":
    main()
