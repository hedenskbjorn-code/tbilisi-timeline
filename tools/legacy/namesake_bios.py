"""The second pass about the namesakes: the street cards that have no namesake yet (Gemini answered "unsure" or "no namesake", or the card has no entry id) get candidate bios from the biographical part of
the encyclopedia of 2008 (PDF pages 247-354, alphabetical: "Surname Name Patronymic (years), description"). The OCR spoils the surnames ("Shartava" is "შარრამვა" there), so the candidates are found by the likeness of
the first name (exact stem) and of the surname (difflib >= 0.6). Makes work/gemini/batches/namesake2/namesake2_batch_01.md and data/cache/namesake2_index.json (S001 -> the key of the street).
The answer (batches/namesake2/namesake2_batch_01_result.json, the rows as in tasks/namesake.md, ids S001...) is checked by tools/verify_namesakes.py. Usage: python -P tools/namesake_bios.py
"""
import difflib
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_enc_spec import name_forms, norm_name  # noqa: E402
from verify_mainroads import norm  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import GEMINI as FD  # noqa: E402
FIRST, LAST = 244, 360
TYPES = {"ქუჩა", "გამზირი", "მოედანი", "სანაპირო", "ხეივანი", "გზატკეცილი", "შესახვევი", "ჩიხი", "გასასვლელი", "ბულვარი", "დაღმართი", "აღმართი", "ქუჩის", "გამზირის", "მოედნის"}


def pages():
    s = open(os.path.join(R, "data", "cache", "ocr", "streets_enc2008_kat.txt"), encoding="utf-8", errors="replace").read()
    return {int(m.group(1)): norm(m.group(2)) for m in re.finditer(r"=====PAGE (\d+)=====\n(.*?)(?======PAGE |\Z)", s, re.S)}


def unresolved():
    sn = json.load(open(os.path.join(R, "site", "data", "street_names.json"), encoding="utf-8"))["streets"]
    ns = json.load(open(os.path.join(R, "site", "data", "namesakes.json"), encoding="utf-8"))["streets"]
    ents = {e["id"]: e for e in json.load(open(os.path.join(R, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))}
    enc_ka = {}
    for fn in ("enc2008_verified.json", "enc2008_verified4.json", "cards_verified.json"):
        for r in json.load(open(os.path.join(R, "data", "cache", fn), encoding="utf-8"))["ok"]:
            enc_ka[r["id"]] = r["ka_now"]
    by_id = {}
    for i, ka in enc_ka.items():
        for f in name_forms(ka):
            by_id.setdefault(norm_name(f), []).append(i)
    out = []
    for s in sn:
        key = s.get("geom") or s["now"]["en"]
        if key in ns:
            continue
        ids = sorted({i for f in name_forms(s["now"]["ka"]) for i in by_id.get(norm_name(f), [])})
        out.append((key, s["now"]["ka"], ids[0] if ids else None, ents.get(ids[0]) if ids else None))
    return out


def main():
    pg = pages()
    text, spans = "", []
    for p in range(FIRST, LAST + 1):
        spans.append((len(text), p))
        text += pg.get(p, "") + " "
    page_at = lambda pos: [p for st, p in spans if st <= pos][-1]
    todo = unresolved()
    lines = ["# Пакет 2: улицы без «в честь кого» и кандидаты-справки из биографической части энциклопедии (страницы PDF 244–360)", "",
             "Кандидаты найдены по имени и приблизительному сходству фамилии (распознавание искажает фамилии). Выбери справку, в которой названо именно то лицо, в честь которого названа улица; **если подходящей нет, skip**. Весь текст книги: `C:/Projects/tbilisi-timeline/data/cache/ocr/streets_enc2008_kat.txt`.", ""]
    index = {}
    for n, (key, ka, eid, e) in enumerate(todo, 1):
        sid = "S%03d" % n
        index[sid] = {"key": key, "ka": ka, "entry": eid}
        words = [w for w in re.findall(r"[ა-ჰ]+", ka) if w not in TYPES]
        cands = []
        if len(words) >= 2:
            first, sur = words[0], re.sub(r"(ის|ს)$", "", words[1])
            for m in re.finditer(re.escape(first[:4]), text):
                win = re.findall(r"[ა-ჰ]+", text[max(0, m.start() - 60):m.start() + 80])
                best = max([difflib.SequenceMatcher(None, sur, w[:len(sur) + 1]).ratio() for w in win] or [0])
                if best >= 0.6:
                    cands.append((best, m.start()))
        cands.sort(reverse=True)
        used, picked = [], []
        for r, pos in cands:
            if all(abs(pos - u) > 300 for u in used):
                used.append(pos)
                picked.append((r, pos))
            if len(picked) >= 3:
                break
        lines += ["## %s | %s | %s | запись энциклопедии: %s" % (sid, key, ka, eid or "нет"), ""]
        if e:
            lines += ["Текст статьи об улице (PDF p. %s): %s" % (e["page"], (e.get("text_long") or e["text"]).replace("\n", " ")[:500]), ""]
        for r, pos in picked:
            lines += ["- кандидат (сходство %.2f), PDF p. %s: %s" % (r, page_at(pos), text[max(0, pos - 40):pos + 460]), ""]
        if not picked:
            lines += ["- кандидатов нет (ищи по полному тексту книги или skip)", ""]
    open(os.path.join(FD, "batches/namesake2/namesake2_batch_01.md"), "wb").write(("\n".join(lines) + "\n").encode("utf-8"))
    json.dump(index, open(os.path.join(R, "data", "cache", "namesake2_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("streets:", len(todo), "| with candidates:", sum(1 for x in lines if x.startswith("- кандидат (")))


if __name__ == "__main__":
    main()
