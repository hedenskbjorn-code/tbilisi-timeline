"""Portraits of the rulers and flags of the states for the band "Who ruled" (site/data/rulers.json).
Stage 1 (this file, no arguments): finds the Wikipedia article and the Wikidata item of every ruler by the English name and takes a portrait only when the item is a human whose
life overlaps the years of the rule (so that a namesake is not taken) and whose name matches; for the states it takes the flag (Wikidata P41; when there are several, the one
whose dates cover the period). The Commons file is accepted only with a free licence (public domain, CC0, CC BY, CC BY-SA); the author and the licence are kept.
Output: data/rulers_media_candidates.json (statuses: auto, review, noimage, none). Nothing is downloaded and the site is not changed.
Stage 2 (argument "download"): takes the accepted pictures (status auto, free licence), saves small webp copies into site/data/rulers/p (portraits) and site/data/rulers/f (flags)
and writes site/data/rulers_media.json (file, author, licence, page of the file) which the page shows under the picture.
Contact for Wikimedia only from the environment variable WIKIMEDIA_CONTACT. Usage: python -X utf8 -P tools/fetch_rulers_media.py
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_contact = os.environ.get("WIKIMEDIA_CONTACT")
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; Wikipedia/Wikidata/Commons API client%s)" % ("; contact: " + _contact if _contact else "")
FREE = re.compile(r"(?i)^(public domain|pd\b|cc0|cc[- ]by(-sa)?\b|attribution|no restrictions|copyrighted free use)")

# Flags: only for the states whose flag is historically attested (the states of the early centuries and the overlords have only reconstructions; the Wikidata items of the
# Ottoman and Safavid flags are even called "Fictitious"), so they are not shown. state id -> the Wikipedia article whose Wikidata item lists the flags with their dates (P41)
STATE_ARTICLE = {"russia": "Russian Empire", "tdfr": "Transcaucasian Democratic Federative Republic", "drg": "Democratic Republic of Georgia", "gssr": "Georgian Soviet Socialist Republic",
                 "rep1991": "Georgia (country)", "council1992": "Georgia (country)", "rep1995": "Georgia (country)", "rep2013": "Georgia (country)"}
# Flags of the early states are modern reconstructions (the Wikidata items list them as the flag of the state); they are shown with the mark "reconstruction". The specific ones come first.
EXTRA_STATE_FLAGS = {
    "iberia": [{"file": "Kartli - drosha jvari.svg", "k": "recon"}],
    "georgia": [{"file": "KingDavidtheBuilderFlag.svg", "from": 1122, "to": 1125, "k": "recon"}, {"file": "QueenTamarFlag.svg", "from": 1184, "to": 1213, "k": "recon"},
                {"file": "Flag of the Kingdom of Georgia.svg", "k": "recon"}],
    "kartli_kakheti": [{"file": "Flag of Kingdom of Kartli-Kakheti.svg", "k": "recon"}],
}
EXTRA_FLAG = {"Georgia (country)": [{"file": "Flag of Georgia (1990–2004).svg", "from": 1990, "to": 2004}]}      # absent in P41 of the item; the dates are those of the Commons file name

# Rulers: the search by name is wrong for some (a namesake), so the article is given by hand; EXCLUDE: no reliable match or no portrait expected; ACCEPT: the match was checked by hand
# (the name differs only by an epithet or a spelling, the life years overlap the rule). Everything else with a good match is taken ("auto"); the pictures are checked by eye afterwards.
TITLE_FIX = {"demetre1": "Demetrius I of Georgia", "demetre1b": "Demetrius I of Georgia", "george3": "George III of Georgia", "george4": "George IV of Georgia",
             "david9": "David IX of Georgia", "constantine1": "Constantine I of Georgia", "demetre3": "Demetrius III of Georgia", "constantine2": "Constantine II of Georgia",
             "simon2": "Simon II of Kartli", "jesse": "Jesse of Kartli", "jesse2": "Jesse of Kartli", "viceroy15": "Grand Duke Michael Nikolaevich of Russia"}
ACCEPT = {"tamar", "vakhtang1", "alexander1", "simon1", "simon1b", "luarsab2", "david_regent", "viceroy5", "viceroy8", "secretary5", "secretary6", "secretary7", "secretary9"}
EXCLUDE = {"emir0", "emir1", "emir2", "emir3", "emir4", "emir5", "emir6", "emir7", "emir8", "emir9", "emir10", "emir11", "emir12", "emir13", "emir14", "emir15",
           "aspacures2", "aspacures3", "mihrdat3", "pharasmanes4", "bacurius2", "pharasmanes6", "viceroy10", "viceroy17", "viceroy21", "secretary1", "secretary8"}
_fails = 0


def get(url):
    global _fails
    for k in range(3):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read())
            time.sleep(0.25)
            _fails = 0
            return d
        except Exception as e:
            _fails += 1
            if _fails >= 6:
                raise SystemExit("stopped: 6 failed requests in a row, last: %s (set WIKIMEDIA_CONTACT?)" % str(e)[:80])
            time.sleep(3 * (k + 1))
    return {}


def api(host, **p):
    p.update(format="json", formatversion=2)
    return get("https://%s/w/api.php?%s" % (host, urllib.parse.urlencode(p)))


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return [w for w in re.split(r"[^a-z0-9]+", s) if w and w not in ("the", "of", "de", "von", "i", "b")]


def year(claims, pid):
    for c in claims.get(pid, []):
        v = (c.get("mainsnak", {}).get("datavalue") or {}).get("value")
        if v and v.get("time"):
            m = re.match(r"([+-])(\d{4,})", v["time"])
            if m:
                return int(m.group(2)) * (1 if m.group(1) == "+" else -1)
    return None


def q_year(snak_list):
    for s in snak_list or []:
        v = (s.get("datavalue") or {}).get("value")
        if v and v.get("time"):
            m = re.match(r"([+-])(\d{4,})", v["time"])
            if m:
                return int(m.group(2)) * (1 if m.group(1) == "+" else -1)
    return None


def titles_to_items(titles):
    out = {}
    for i in range(0, len(titles), 40):
        d = api("en.wikipedia.org", action="query", titles="|".join(titles[i:i + 40]), prop="pageprops", ppprop="wikibase_item", redirects=1)
        q = d.get("query", {})
        redir = {r["from"]: r["to"] for r in q.get("redirects", [])}
        norm_t = {n["from"]: n["to"] for n in q.get("normalized", [])}
        byt = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in q.get("pages", [])}
        for t in titles[i:i + 40]:
            tt = norm_t.get(t, t)
            tt = redir.get(tt, tt)
            out[t] = (tt, byt.get(tt))
    return out


def entities(ids):
    out = {}
    ids = sorted({i for i in ids if i})
    for i in range(0, len(ids), 40):
        d = api("www.wikidata.org", action="wbgetentities", ids="|".join(ids[i:i + 40]), props="labels|descriptions|claims", languages="en")
        out.update(d.get("entities", {}))
    return out


def file_info(names):
    out = {}
    names = sorted(set(names))
    for i in range(0, len(names), 40):
        d = api("commons.wikimedia.org", action="query", titles="|".join("File:" + n for n in names[i:i + 40]), prop="imageinfo", iiprop="extmetadata|url|mime", iiurlwidth=520)
        for p in d.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata", {})
            val = lambda k: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", (em.get(k) or {}).get("value", ""))).strip()
            out[p["title"][5:]] = {"license": val("LicenseShortName"), "artist": val("Artist")[:160], "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "mime": ii.get("mime")}
    return out


def main():
    d = json.load(open(os.path.join(ROOT, "site", "data", "rulers.json"), encoding="utf-8"))
    rulers, states = d["rulers"], d["states"]
    # 1. rulers: the search of the article by the English name
    cands = {}
    for r in rulers:
        if r["id"] in EXCLUDE:
            cands[r["id"]] = []
            continue
        if r["id"] in TITLE_FIX:
            cands[r["id"]] = [TITLE_FIX[r["id"]]]
            continue
        nm = re.sub(r"\(.*?\)", "", r["name"]["en"]).strip()
        s = api("en.wikipedia.org", action="query", list="search", srsearch=nm, srlimit=4, srnamespace=0)
        cands[r["id"]] = [x["title"] for x in s.get("query", {}).get("search", [])]
    alltitles = sorted({t for v in cands.values() for t in v} | {a for a in STATE_ARTICLE.values() if a})
    t2q = titles_to_items(alltitles)
    ents = entities([q for _, q in t2q.values()])
    res = {}
    for r in rulers:
        a, b = int(r["from"]), int(r["to"] + 0.999)
        want = norm(re.sub(r"\(.*?\)", "", r["name"]["en"]))
        best = None
        for t in cands[r["id"]]:
            title, q = t2q.get(t, (t, None))
            e = ents.get(q) if q else None
            if not e or "claims" not in e:
                continue
            cl = e["claims"]
            human = any((c.get("mainsnak", {}).get("datavalue") or {}).get("value", {}).get("id") == "Q5" for c in cl.get("P31", []))
            if not human:
                continue
            by, dy = year(cl, "P569"), year(cl, "P570")
            alive = (by is None or by <= b) and (dy is None or dy >= a) and not (by is None and dy is None)
            have = norm(e.get("labels", {}).get("en", {}).get("value", title))
            ratio = len(set(want) & set(have)) / max(1, len(set(want)))
            img = next(((c.get("mainsnak", {}).get("datavalue") or {}).get("value") for c in cl.get("P18", []) if (c.get("mainsnak", {}).get("datavalue") or {}).get("value")), None)
            sc = (alive, ratio)
            if best is None or sc > best[0]:
                best = (sc, {"wp": title, "q": q, "label": e.get("labels", {}).get("en", {}).get("value"), "desc": e.get("descriptions", {}).get("en", {}).get("value"), "birth": by, "death": dy, "image": img, "ratio": round(ratio, 2), "alive": alive})
        if not best:
            res[r["id"]] = {"status": "none"}
        else:
            c = best[1]
            ok = c["alive"] and (c["ratio"] >= 0.6 or r["id"] in ACCEPT or r["id"] in TITLE_FIX)
            c["status"] = ("auto" if c["image"] else "noimage") if ok else "review"
            res[r["id"]] = c
    # 2. states: all the flags of the item with their dates (the one for a year is chosen by the page)
    sres = {}
    for s in states:
        art = STATE_ARTICLE.get(s["id"])
        if s["id"] in EXTRA_STATE_FLAGS:
            keep = [{"file": f["file"], "from": f.get("from", s["from"]), "to": f.get("to", s["to"]), "k": f["k"]} for f in EXTRA_STATE_FLAGS[s["id"]]]
            sres[s["id"]] = {"flags": keep, "status": "auto"}
            continue
        if not art:
            sres[s["id"]] = {"status": "none"}
            continue
        title, q = t2q.get(art, (art, None))
        e = ents.get(q) if q else None
        flags = []
        for c in (e or {}).get("claims", {}).get("P41", []):
            v = (c.get("mainsnak", {}).get("datavalue") or {}).get("value")
            if v and c.get("rank") != "deprecated":
                qs = c.get("qualifiers", {})
                flags.append({"file": v, "from": q_year(qs.get("P580")), "to": q_year(qs.get("P582"))})
        flags += EXTRA_FLAG.get(art, [])
        keep = []
        for f in flags:
            f0 = s["from"] if f["from"] is None else f["from"]
            f1 = s["to"] if f["to"] is None else f["to"]
            if f0 < s["to"] and f1 > s["from"]:
                # the Russian Empire: the tricolour was only the civil ensign before 1858 (en.wikipedia, Flag of Russia); the state flag was black-yellow-white 1858-1896, the tricolour since 1896
                keep.append({"file": f["file"], "from": max(f0, s["from"]), "to": f1, "k": "civil" if (s["id"] == "russia" and f1 <= 1858) else "state"})
        sres[s["id"]] = {"wp": title, "q": q, "article": art, "flags": keep, "status": "auto" if keep else "noimage"}
    # 3. licences and thumbnails of the chosen files
    files = [v["image"] for v in res.values() if v.get("image")] + [f["file"] for v in sres.values() for f in v.get("flags", [])]
    info = file_info(files)
    for v in res.values():
        if v.get("image"):
            i = info.get(v["image"].replace("_", " "), {})
            v.update({k: i.get(k) for k in ("license", "artist", "thumb", "page", "mime")})
            if v["status"] == "auto" and not FREE.match(i.get("license") or ""):
                v["status"] = "nolicence"
    for v in sres.values():
        for f in v.get("flags", []):
            i = info.get(f["file"].replace("_", " "), {})
            f.update({k: i.get(k) for k in ("license", "artist", "thumb", "page", "mime")})
            f["free"] = bool(FREE.match(i.get("license") or ""))
    out = {"rulers": res, "states": sres}
    json.dump(out, open(os.path.join(ROOT, "data", "rulers_media_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print("rulers:", dict(Counter(v["status"] for v in res.values())), "| states:", dict(Counter(v["status"] for v in sres.values())))


# checked by eye on a contact sheet: these files are not a portrait of the ruler
DROP_PORTRAIT = {"mihrdat4": "a stone relief", "secretary10": "a group photograph, the person is not clear", "bagrat7": "a seal"}


def fetch_bytes(url):
    for k in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
            time.sleep(0.4)
            return b
        except Exception as e:
            time.sleep(5 * (k + 1))
    return None


def download():
    import io
    from PIL import Image
    c = json.load(open(os.path.join(ROOT, "data", "rulers_media_candidates.json"), encoding="utf-8"))
    out = {"rulers": {}, "flags": {}}
    base = os.path.join(ROOT, "site", "data", "rulers")
    for sub in ("p", "b", "f"):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    seen = {}
    for rid, v in c["rulers"].items():
        if v.get("status") != "auto" or not v.get("thumb") or rid in DROP_PORTRAIT:
            continue
        key = v["q"]
        if key not in seen:
            b = fetch_bytes(v["thumb"])
            if not b:
                print("skip (download failed):", rid); continue
            im = Image.open(io.BytesIO(b)).convert("RGB")
            big = im.copy(); big.thumbnail((480, 600))
            im.thumbnail((96, 120))
            name = "p/%s.webp" % rid
            im.save(os.path.join(base, name), "WEBP", quality=80, method=6)
            big.save(os.path.join(base, "b/%s.webp" % rid), "WEBP", quality=82, method=6)
            seen[key] = name
        out["rulers"][rid] = {"i": seen[key], "b": seen[key].replace("p/", "b/"), "l": v.get("license"), "a": v.get("artist"), "u": v.get("page")}
    fseen = {}
    for sid, v in c["states"].items():
        for f in v.get("flags", []):
            if not f.get("free") or not f.get("thumb"):
                continue
            if any(g["from"] <= f["from"] and g["to"] >= f["to"] for g in out["flags"].get(sid, [])):      # a variant of the same flag for the same years
                continue
            if f["file"] not in fseen:
                b = fetch_bytes(f["thumb"])
                if not b:
                    continue
                im = Image.open(io.BytesIO(b)).convert("RGBA"); im.thumbnail((96, 64))
                name = "f/%s.webp" % re.sub(r"[^A-Za-z0-9]+", "_", os.path.splitext(f["file"])[0]).strip("_")
                im.save(os.path.join(base, name), "WEBP", quality=85, method=6)
                fseen[f["file"]] = name
            out["flags"].setdefault(sid, []).append({"i": fseen[f["file"]], "k": f.get("k"), "from": f["from"], "to": f["to"], "l": f.get("license"), "a": f.get("artist"), "u": f.get("page")})
    json.dump(out, open(os.path.join(ROOT, "site", "data", "rulers_media.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("portraits:", len(out["rulers"]), "files:", len(seen), "| flags for states:", len(out["flags"]), "files:", len(fseen))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        download()
    else:
        main()
