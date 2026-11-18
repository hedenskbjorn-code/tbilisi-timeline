"""Contact sheets for a manual (or Gemini) check of photos found 30-60 m from a register object.

The photos come from Commons geosearch by coordinates only, so a photo 30-60 m away can show another house (found 2026-11-18: a plaque
of a residential house on the card of a church). tools/build_site_data.py shows such photos only if they are listed in
data/photos_far_approved.json {"approved": {"<object id>": ["File:..."]}}.
This script writes for_gemini/photos/photos_in.json (objects with their far candidates) and for_gemini/photos/sheet_NN.jpg
(8 objects per sheet, up to 3 thumbnails each, from the local thumbnail cache; no new requests to Commons).
Usage: python -P tools/make_photo_sheets.py
"""
import hashlib
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(ROOT, "data", "cache")
OUT = os.path.join(ROOT, "for_gemini", "photos")
NEAR = 30
ROWS, TH = 8, 210


def main():
    hits = json.load(open(os.path.join(CACHE, "photos_geosearch.json"), encoding="utf-8"))
    info = json.load(open(os.path.join(CACHE, "photos_info.json"), encoding="utf-8"))
    people = json.load(open(os.path.join(CACHE, "photos_people.json"), encoding="utf-8"))
    rej = set(json.load(open(os.path.join(ROOT, "data", "photos_manual_reject.json"), encoding="utf-8"))["titles"])
    names = {}
    try:
        names = json.load(open(os.path.join(ROOT, "site", "data", "names_i18n.json"), encoding="utf-8"))
        names = names.get("names", names)
    except Exception:
        names = {}
    mon = {f["properties"]["id"]: f for f in json.load(open(os.path.join(ROOT, "site", "data", "monuments.json"), encoding="utf-8"))["features"]}

    def ok(t):
        return info.get(t, {}).get("thumb") and info[t].get("license") and not people.get(t, {}).get("reject") and t not in rej

    objs = []
    for oid, v in hits.items():
        far = [(t, d) for t, d in v if d > NEAR and ok(t)]
        f = mon.get(int(oid))
        if not far or not f:
            continue
        p = f["properties"]
        thumb = lambda t: os.path.join(CACHE, "thumbs", hashlib.sha1(t.encode("utf-8")).hexdigest() + ".jpg")
        far = [(t, d) for t, d in far if os.path.exists(thumb(t))]
        if not far:
            continue
        nm = names.get(p["name"], {}) if isinstance(names, dict) else {}
        objs.append({"n": 0, "id": p["id"], "name_ka": p["name"], "name_en": (nm.get("en") if isinstance(nm, dict) else None), "address": p.get("address"),
                     "class": p.get("cls"), "function": p.get("fn"), "lonlat": f["geometry"]["coordinates"],
                     "has_near_photo": any(d <= NEAR for t, d in hits[oid] if ok(t)),
                     "candidates": [{"title": t, "dist_m": round(d), "commons": info[t].get("page")} for t, d in far[:3]]})
    objs.sort(key=lambda o: o["id"])
    for i, o in enumerate(objs, 1):
        o["n"] = i
    os.makedirs(OUT, exist_ok=True)
    json.dump({"objects": objs}, open(os.path.join(OUT, "photos_in.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
        small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    except Exception:
        font = small = ImageFont.load_default()
    W = 150 + 3 * (TH + 6)
    ns = 0
    for s0 in range(0, len(objs), ROWS):
        chunk = objs[s0:s0 + ROWS]
        sheet = Image.new("RGB", (W, len(chunk) * (TH + 6)), "white")
        d = ImageDraw.Draw(sheet)
        for r, o in enumerate(chunk):
            y = r * (TH + 6)
            d.text((6, y + 6), "#%d" % o["n"], fill="black", font=font)
            d.text((6, y + 36), "id %d" % o["id"], fill=(80, 80, 80), font=small)
            d.text((6, y + 56), (o["class"] or "")[:16], fill=(80, 80, 80), font=small)
            d.text((6, y + 76), (o["function"] or "")[:16], fill=(80, 80, 80), font=small)
            for c, cand in enumerate(o["candidates"]):
                im = Image.open(os.path.join(CACHE, "thumbs", hashlib.sha1(cand["title"].encode("utf-8")).hexdigest() + ".jpg")).convert("RGB")
                im.thumbnail((TH, TH))
                x = 150 + c * (TH + 6)
                sheet.paste(im, (x, y))
                d.rectangle((x, y, x + 74, y + 20), fill="white")
                d.text((x + 3, y + 2), "%s %dm" % ("abc"[c], cand["dist_m"]), fill="red", font=small)
        ns += 1
        sheet.save(os.path.join(OUT, "sheet_%02d.jpg" % ns), quality=82)
    print("objects", len(objs), "candidates", sum(len(o["candidates"]) for o in objs), "sheets", ns)


if __name__ == "__main__":
    main()
