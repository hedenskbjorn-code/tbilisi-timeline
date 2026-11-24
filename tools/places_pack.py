"""The pack for Gemini about the layer "Local names": for every candidate (data/cache/places_candidates.json) with an article (data/cache/places_wiki.json) the first paragraph of the article in each language
and the paragraphs that speak about the origin of the name (cue words), as plain text with the address of the article. Writes work/gemini/places2_batch_NN.md (PER places each). The answer is
checked by tools/verify_places.py. The packs places_batch_NN.md of an earlier idea (the dictionary pages of the encyclopedia) are not touched. Usage: python -P tools/places_pack.py
"""
import json
import os
import re
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PER = 45
CUES = {
    "ka": re.compile(r"სახელ|წარმოშობ|ეტიმოლოგ|მომდინარე|ერქვა|ეწოდა|ნიშნავს|დაერქვა"),
    "ru": re.compile(r"назван|происх|этимолог|означа|получил|именуем|переимен|в честь|от слова"),
    "en": re.compile(r"\bname[ds]?\b|derive|etymolog|origin|means|meaning|renamed|in honou?r|from the word", re.I),
}


def paras(text):
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n+", text) if p.strip() and not p.strip().startswith("=")]


def pick(lg, text):
    ps = paras(text)
    out, seen = [], set()
    for i, p in enumerate(ps):
        if (i == 0 or CUES[lg].search(p)) and p not in seen and len(p) > 25:
            seen.add(p)
            out.append(p[:900])
        if len(out) >= 5:
            break
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cand = json.load(open(os.path.join(R, "data", "cache", "places_candidates.json"), encoding="utf-8"))
    wiki = json.load(open(os.path.join(R, "data", "cache", "places_wiki.json"), encoding="utf-8"))
    rows = [(c, wiki[c["key"]]) for c in cand if c["key"] in wiki and wiki[c["key"]]["pages"]]
    n = 0
    for a in range(0, len(rows), PER):
        n += 1
        L = ["# Пакет %02d: места Тбилиси и статьи Википедии о них (%d–%d из %d)" % (n, a + 1, min(a + PER, len(rows)), len(rows)), ""]
        for c, w in rows[a:a + PER]:
            L += ["## %s" % c["key"], "", "- вид: %s" % c["kind"], "- названия (OSM): ka=%s | ru=%s | en=%s" % (c["name"]["ka"], c["name"]["ru"], c["name"]["en"])]
            if c["etym"]:
                L.append("- в OSM указано, в честь кого/чего название: %s" % json.dumps(c["etym"], ensure_ascii=False))
            for lg in ("ka", "ru", "en"):
                pg = w["pages"].get(lg)
                if not pg:
                    continue
                L += ["", "### статья %s: %s", ""]
                L[-2] = "### статья %s: %s (%s)" % (lg, pg["title"], pg["url"])
                for p in pick(lg, pg["text"]):
                    L += ["> " + p, ""]
            L.append("")
        open(os.path.join(R, "work", "gemini", "batches", "places2", "places2_batch_%02d.md" % n), "wb").write(("\n".join(L) + "\n").encode("utf-8"))
    print("places with an article:", len(rows), "| packs:", n)


if __name__ == "__main__":
    main()
