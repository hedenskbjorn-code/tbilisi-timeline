"""Split the encyclopedia 'Tbilisi. Streets, avenues, squares' (2008) into entries and prepare the batches for Gemini.

Input: data/cache/ocr/streets_enc2008_kat.txt (the page OCR of tools/ocr_book.py with OCR_PSM=3, lang kat; the pages are the PDF pages of data/cache/nplg_pdfs/tbilisi_streets_2008.pdf).
Output: data/cache/enc2008_entries.json (all entries; the cache is not committed) and, with --batches, the inputs of the task of Gemini in for_gemini/from_desktop/enc_batches/
(the folder for_gemini/ is ignored by git): the entries with a statement about a name and a year that are not on the map yet, 60 entries per batch.
Usage: python -P tools/parse_street_encyclopedia.py [--batches [--force]]
"""
import difflib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "data", "cache", "ocr", "streets_enc2008_kat.txt")
OUT = os.path.join(ROOT, "data", "cache", "enc2008_entries.json")
NAMES = os.path.join(ROOT, "site", "data", "street_names.json")
KIND = r"(?:ქუჩა|გამზირი|მოედანი|ხეივანი|აღმართი|დაღმართი|სანაპირო|გზატკეცილი|ბულვარი)"
HEAD = re.compile(r"((?:[ა-ჰ()\-–.«»„“0-9]+ ){1,7}" + KIND + r")[.,] ((?:[ა-ჰ\-]+ ?){1,3}რ-ნი(?: \([^)]{2,40}\))?)")
YEAR = re.compile(r"\b(1[0-9]{3})\b")
NAMEW = re.compile(r"სახელი|ეწოდა|დაერქვა|ერქვა|ეწოდებოდა")
PER_BATCH = 60


def entries():
    t = open(SRC, encoding="utf-8").read()
    parts = re.split(r"\n=====PAGE (\d+)=====\n", t)
    pages = {int(parts[i]): re.sub(r"\s+", " ", parts[i + 1]) for i in range(1, len(parts) - 1, 2)}
    txt = " ".join("\u0001%d\u0002 %s" % (p, pages[p]) for p in range(4, 213) if p in pages)  # the pages 4-212: the entries; 215-244: the index of the old names
    hs = list(HEAD.finditer(txt))
    out = []
    for i, m in enumerate(hs):
        end = hs[i + 1].start() if i + 1 < len(hs) else len(txt)
        pg = re.findall(r"\u0001(\d+)\u0002", txt[:m.start()])[-1:]
        body = re.sub(r"\s+", " ", re.sub(r"\u0001\d+\u0002", "", txt[m.start():end]))
        toks = m.group(1).strip().split(" ")
        cut = 0
        for j, tk in enumerate(toks[:-1]):  # the tail of the previous entry: a word of two letters or more that ends with a full stop
            if tk.endswith(".") and len(tk.rstrip(".")) >= 2 and not re.fullmatch(r"[ა-ჰ]\.", tk):
                cut = j + 1
        name = " ".join(toks[cut:])
        body = body[body.find(toks[cut]):] if toks[cut] in body else body
        body = body[:1500]
        out.append({"id": "E%04d" % (i + 1), "page": int(pg[0]) if pg else None, "name": name, "district": m.group(2).strip(), "text": fix_digits(body), "text_raw": body})
    return out


def fix_digits(s):
    """The OCR reads the digit 1 in a year as I, l, L or | (I990, 192I, I99L) and breaks a year with a space (19 23): the years are repaired in the text (the raw text is kept in text_raw)."""
    def year(m):
        tok = m.group(0)
        d = sum(c.isdigit() for c in tok)
        return re.sub(r"[IlL|]", "1", tok) if d >= 2 and tok[0] in "1Il|" else tok
    s = re.sub(r"(?<![A-Za-z0-9])[0-9IlL|]{4}(?![A-Za-z0-9])", year, s)
    return re.sub(r"(?<![0-9])(1[0-9]) ([0-9]{2})(?= წ|-იდან|-მდე| –)", r"\1\2", s)


def main():
    es = entries()
    site = [s["now"]["ka"] for s in json.load(open(NAMES, encoding="utf-8"))["streets"]]
    for e in es:
        e["on_site"] = bool(difflib.get_close_matches(e["name"], site, n=1, cutoff=0.88))
        e["has_rename_and_year"] = bool(NAMEW.search(e["text"]) and YEAR.search(e["text"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(es, f, ensure_ascii=False, indent=1)
    cand = [e for e in es if e["has_rename_and_year"] and not e["on_site"]]
    print("entries: %d; with a name and a year: %d; not on the map: %d" % (len(es), sum(e["has_rename_and_year"] for e in es), len(cand)))
    if "--batches" not in sys.argv:
        return
    d = os.path.join(ROOT, "for_gemini", "from_desktop", "enc_batches")
    os.makedirs(d, exist_ok=True)
    n = (len(cand) + PER_BATCH - 1) // PER_BATCH
    for b in range(n):
        p = os.path.join(d, "enc_batch_%02d.md" % (b + 1))
        assert "--force" in sys.argv or not os.path.exists(p), "refusing to overwrite " + p + " (use --force)"
        part = cand[b * PER_BATCH:(b + 1) * PER_BATCH]
        lines = ["# Партия %d из %d: статьи энциклопедии (OCR, страницы PDF указаны)\n" % (b + 1, n)]
        for e in part:
            lines.append("## %s | PDF p. %s | район: %s | заголовок (OCR): %s\n\n```\n%s\n```\n" % (e["id"], e["page"], e["district"], e["name"], e["text"]))
        open(p, "w", encoding="utf-8").write("\n".join(lines))
    print("batches:", n, "->", d)


def second_pass():
    """The entries that Gemini skipped as 'unsure' or 'no_named_years' although the text holds two or more different years: a second look at the PDF pages (enc2_batch_NN.md)."""
    import glob
    ents = {e["id"]: e for e in json.load(open(OUT, encoding="utf-8"))}
    d = os.path.join(ROOT, "for_gemini", "from_desktop", "enc_batches")
    pick = []
    for fp in sorted(glob.glob(os.path.join(d, "enc_batch_*_result.json"))):
        for r in json.load(open(fp, encoding="utf-8")):
            if r["status"] != "skip" or r["skip_reason"] == "gone":
                continue
            years = set(YEAR.findall(ents[r["id"]]["text"]))
            if r["skip_reason"] == "unsure" or len(years) >= 2:
                pick.append(ents[r["id"]])
    n = (len(pick) + PER_BATCH - 1) // PER_BATCH
    for b in range(n):
        p = os.path.join(d, "enc2_batch_%02d.md" % (b + 1))
        assert "--force" in sys.argv or not os.path.exists(p), "refusing to overwrite " + p + " (use --force)"
        lines = ["# Второй проход, партия %d из %d: статьи, пропущенные в первом проходе\n" % (b + 1, n)]
        for e in pick[b * PER_BATCH:(b + 1) * PER_BATCH]:
            lines.append("## %s | PDF p. %s | район: %s | заголовок (OCR): %s\n\n```\n%s\n```\n" % (e["id"], e["page"], e["district"], e["name"], e["text"]))
        open(p, "w", encoding="utf-8").write("\n".join(lines))
    task = open(os.path.join(ROOT, "for_gemini", "from_desktop", "enc_streets_TASK_for_gemini.md"), encoding="utf-8").read()
    a, b = task.index("## Схема объекта"), task.index("## Как будет проверено")
    head = ("# ЗАДАНИЕ, ВТОРОЙ ПРОХОД: те же правила, только для статей, которые в первом проходе были пропущены\n\n"
            "В первом проходе из этих %d статей ничего не выписано: часть как `unsure` (искажённые цифры в OCR), часть как `no_named_years`. Проверка показала, что в текстах есть годы, и в части статей цепочка читается. "
            "**Открой страницу PDF каждой статьи** (`C:/Projects/tbilisi-timeline/data/cache/nplg_pdfs/tbilisi_streets_2008.pdf`, номер страницы в заголовке статьи) и **прочитай напечатанные годы и названия**: цифры в OCR искажены (I990, 192I, 19 23), а на странице они читаются. "
            "Если цепочка читается по странице, дай `ok`; цитату бери из OCR-текста дословно (как в первом проходе), а исправленные годы пиши в `from`/`to`; если год в OCR искажён и в цитате его нет в нужном виде, выбери для цитаты другой фрагмент с названием, в котором год в OCR цел, или дай `skip` с `unsure`. "
            "Правило прежнее: только напечатанное, интервал без обоих годов не создаётся.\n\n"
            "Вход: `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/enc_batches/enc2_batch_01.md` … `enc2_batch_%02d.md`; выход: `enc2_batch_NN_result.json` рядом.\n\n" % (len(pick), n))
    tail = "## Как будет проверено\nТе же программные проверки, что в первом проходе.\n\n## Готовая фраза для запуска\n> Прочитай файл `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/enc2_streets_TASK_for_gemini.md`, выполни задание для всех партий второго прохода и сохрани результаты в `enc2_batch_NN_result.json` рядом с входными файлами.\n"
    out = os.path.join(ROOT, "for_gemini", "from_desktop", "enc2_streets_TASK_for_gemini.md")
    assert "--force" in sys.argv or not os.path.exists(out)
    open(out, "w", encoding="utf-8").write(head + task[a:b].replace("enc_batch_", "enc2_batch_") + tail)
    print("second pass: %d entries in %d batches" % (len(pick), n))


def third_pass():
    """The entries that stayed 'unsure' after the second pass, now with the repaired digits of the years (enc3_batch_NN.md)."""
    import glob
    ents = {e["id"]: e for e in json.load(open(OUT, encoding="utf-8"))}
    d = os.path.join(ROOT, "for_gemini", "from_desktop", "enc_batches")
    last = {}
    for pat in ("enc_batch_*_result.json", "enc2_batch_*_result.json"):
        for fp in sorted(glob.glob(os.path.join(d, pat))):
            for r in json.load(open(fp, encoding="utf-8")):
                if r["status"] == "ok" or r["id"] not in last or last[r["id"]]["status"] == "skip":
                    last[r["id"]] = r
    pick = [ents[i] for i, r in sorted(last.items()) if r["status"] == "skip" and r["skip_reason"] == "unsure"]
    n = (len(pick) + PER_BATCH - 1) // PER_BATCH
    for b in range(n):
        p = os.path.join(d, "enc3_batch_%02d.md" % (b + 1))
        assert "--force" in sys.argv or not os.path.exists(p), "refusing to overwrite " + p + " (use --force)"
        lines = ["# Третий проход, партия %d из %d: статьи, оставшиеся «не уверен» (годы в тексте исправлены)\n" % (b + 1, n)]
        for e in pick[b * PER_BATCH:(b + 1) * PER_BATCH]:
            lines.append("## %s | PDF p. %s | район: %s | заголовок (OCR): %s\n\n```\n%s\n```\n" % (e["id"], e["page"], e["district"], e["name"], e["text"]))
        open(p, "w", encoding="utf-8").write("\n".join(lines))
    task = open(os.path.join(ROOT, "for_gemini", "from_desktop", "enc2_streets_TASK_for_gemini.md"), encoding="utf-8").read()
    a, b = task.index("## Схема объекта"), task.index("## Как будет проверено")
    head = ("# ЗАДАНИЕ, ТРЕТИЙ ПРОХОД: те же правила, только для %d статей, которые остались «не уверен»\n\n"
            "В первом и втором проходе эти статьи пропущены из-за искажённых цифр. **Причина найдена и исправлена: в тексте статей искажённые годы теперь исправлены** (`I990`→`1990`, `192I`→`1921`, `19 23`→`1923`), "
            "поэтому цитату можно брать из этого текста дословно, и годы в ней будут целыми. Открой страницу PDF (`C:/Projects/tbilisi-timeline/data/cache/nplg_pdfs/tbilisi_streets_2008.pdf`), убедись, что напечатанные годы и названия совпадают с текстом, и выпиши цепочку. "
            "Правило прежнее: только напечатанное, интервал без обоих годов не создаётся; если после исправления всё равно нельзя прочитать цепочку, дай `skip`.\n\n"
            "Вход: `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/enc_batches/enc3_batch_01.md` … `enc3_batch_%02d.md`; выход: `enc3_batch_NN_result.json` рядом.\n\n" % (len(pick), n))
    tail = "## Как будет проверено\nТе же программные проверки.\n\n## Готовая фраза для запуска\n> Прочитай файл `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/enc3_streets_TASK_for_gemini.md`, выполни задание для всех партий третьего прохода и сохрани результаты в `enc3_batch_NN_result.json` рядом с входными файлами.\n"
    out = os.path.join(ROOT, "for_gemini", "from_desktop", "enc3_streets_TASK_for_gemini.md")
    assert "--force" in sys.argv or not os.path.exists(out)
    open(out, "w", encoding="utf-8").write(head + task[a:b].replace("enc2_batch_", "enc3_batch_") + tail)
    print("third pass: %d entries in %d batches" % (len(pick), n))


def full_pass():
    """The full pass (enc4_batch_NN.md): every entry that the strict passes did not accept and that has a former name or a year; the rules are in enc4_streets_TASK_for_gemini.md."""
    import glob
    ents = json.load(open(OUT, encoding="utf-8"))
    d = os.path.join(ROOT, "for_gemini", "from_desktop", "enc_batches")
    ok = set()
    for pat in ("enc_batch_*_result.json", "enc2_batch_*_result.json", "enc3_batch_*_result.json"):
        for fp in sorted(glob.glob(os.path.join(d, pat))):
            ok |= {r["id"] for r in json.load(open(fp, encoding="utf-8")) if r["status"] == "ok"}
    earl = re.compile(r"ერქვა|ეწოდებოდა")
    pick = [e for e in ents if e["id"] not in ok and (earl.search(e["text"]) or YEAR.search(e["text"]))]
    n = (len(pick) + PER_BATCH - 1) // PER_BATCH
    for b in range(n):
        p = os.path.join(d, "enc4_batch_%02d.md" % (b + 1))
        assert "--force" in sys.argv or not os.path.exists(p), "refusing to overwrite " + p + " (use --force)"
        lines = ["# Полный проход, партия %d из %d: статьи энциклопедии (годы в тексте исправлены)\n" % (b + 1, n)]
        for e in pick[b * PER_BATCH:(b + 1) * PER_BATCH]:
            lines.append("## %s | PDF p. %s | район: %s | заголовок (OCR): %s\n\n```\n%s\n```\n" % (e["id"], e["page"], e["district"], e["name"], e["text"]))
        open(p, "w", encoding="utf-8").write("\n".join(lines))
    print("full pass: %d entries in %d batches" % (len(pick), n))


if __name__ == "__main__":
    if "--full-pass" in sys.argv:
        full_pass()
    elif "--third-pass" in sys.argv:
        third_pass()
    elif "--second-pass" in sys.argv:
        second_pass()
    else:
        main()
