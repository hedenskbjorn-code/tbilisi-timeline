"""Contact sheets of old (before 1960) public-domain / free photographs of Tbilisi from Wikimedia Commons (the files found by tools/probe_old_photos.py),
for a check of WHERE each photo was taken and WHEN (Commons titles and dates are often rough: 'Ermakov' photos carry 1845, his birth year).
Downloads each thumbnail once (360 px, data/cache/oldthumbs/, resumable, polite delay) from Commons; writes for_gemini/oldphotos/photos_in.json and sheet_NN.jpg.
Contact only from the environment (WIKIMEDIA_CONTACT). Usage: python -P tools/make_oldphoto_sheets.py
"""
import hashlib, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(ROOT, "data", "cache")
TH = os.path.join(CACHE, "oldthumbs")
OUT = os.path.join(ROOT, "for_gemini", "oldphotos")
c = os.environ.get("WIKIMEDIA_CONTACT", "")
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project%s)" % (("; contact: " + c) if c else "")
os.makedirs(TH, exist_ok=True)
os.makedirs(OUT, exist_ok=True)


def yr(s):
    m = re.findall(r"(1[89]\d\d|20[0-2]\d)", s or "")
    return min(int(x) for x in m) if m else None


def api(**p):
    p["format"] = "json"
    for k in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php", data=urllib.parse.urlencode(p).encode(), headers={"User-Agent": UA}), timeout=60).read())
        except Exception:
            time.sleep(5 * (k + 1))
    raise SystemExit("api failed")


def main():
    probe = json.load(open(os.path.join(CACHE, "old_photos_probe.json"), encoding="utf-8"))
    titles = [t for t, v in probe.items() if (yr(v["date"]) or 9999) < 1960 and v["license"] and ("Public" in v["license"] or v["license"].startswith("CC0") or v["license"] == "No restrictions")]
    titles.sort()
    info = {}
    for i in range(0, len(titles), 40):
        j = api(action="query", titles="|".join(titles[i:i + 40]), prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=360, iiextmetadatafilter="ImageDescription|DateTimeOriginal|Artist")
        for pg in j["query"]["pages"].values():
            ii = (pg.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata", {})
            info[pg["title"]] = {"thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"),
                                 "description": re.sub(r"<[^>]+>", "", (em.get("ImageDescription") or {}).get("value", ""))[:300], "artist": re.sub(r"<[^>]+>", "", (em.get("Artist") or {}).get("value", ""))[:80]}
        time.sleep(0.5)
    ok = []
    for t in titles:
        u = info.get(t, {}).get("thumb")
        if not u:
            continue
        p = os.path.join(TH, hashlib.sha1(t.encode("utf-8")).hexdigest() + ".jpg")
        if not os.path.exists(p):
            for k in range(5):
                try:
                    data = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60).read()
                    open(p, "wb").write(data)
                    break
                except Exception as e:
                    time.sleep(5 * (k + 1))
            time.sleep(0.3)
        if os.path.exists(p):
            ok.append(t)
    objs = []
    for i, t in enumerate(ok, 1):
        objs.append({"n": i, "title": t, "commons": info[t]["page"], "date_on_commons": probe[t]["date"], "year_guess_from_date_field": yr(probe[t]["date"]), "license": probe[t]["license"],
                     "description": info[t]["description"], "artist": info[t]["artist"], "location_template": probe[t]["location_tpl"]})
    json.dump({"photos": objs}, open(os.path.join(OUT, "photos_in.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
    COLS, ROWS, S = 3, 3, 360
    for s0 in range(0, len(objs), COLS * ROWS):
        chunk = objs[s0:s0 + COLS * ROWS]
        sheet = Image.new("RGB", (COLS * (S + 6), ((len(chunk) + COLS - 1) // COLS) * (S + 6)), "white")
        d = ImageDraw.Draw(sheet)
        for k, o in enumerate(chunk):
            im = Image.open(os.path.join(TH, hashlib.sha1(o["title"].encode("utf-8")).hexdigest() + ".jpg")).convert("RGB")
            im.thumbnail((S, S))
            x, y = (k % COLS) * (S + 6), (k // COLS) * (S + 6)
            sheet.paste(im, (x, y))
            d.rectangle((x, y, x + 62, y + 30), fill="white")
            d.text((x + 4, y + 2), "#%d" % o["n"], fill="red", font=font)
        sheet.save(os.path.join(OUT, "sheet_%02d.jpg" % (s0 // (COLS * ROWS) + 1)), quality=82)
    print("photos", len(objs), "sheets", (len(objs) + COLS * ROWS - 1) // (COLS * ROWS))


if __name__ == "__main__":
    main()
