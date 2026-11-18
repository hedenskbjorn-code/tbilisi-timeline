"""Tiles of the warped 1913 plan with a pixel grid, for the Gemini task for_gemini/TASK_tram1913.md (the tram lines drawn on the plan).
Each tile is 1200 x 1200 px (overlap 200 px), cut from data/warped/tbilisi_1913.webp (5000 x 5134 px, the same image as on the site, 1 px = about 1.5 m).
A grid line every 100 px is drawn and labelled with the GLOBAL pixel coordinates of the whole plan, so that points read from a tile are global.
Output: for_gemini/tram1913/tile_<row>_<col>.png, tiles_index.json, legend.png (the legend of the plan, from the full scan).
Usage: python -P tools/make_tram_tiles.py
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "for_gemini", "tram1913")
S, STEP = 1200, 1000
X0S = [300, 1300, 2300, 3300]
Y0S = [300, 1300, 2300, 3300, 4100]


def main():
    os.makedirs(OUT, exist_ok=True)
    im = Image.open(os.path.join(ROOT, "data", "warped", "tbilisi_1913.webp")).convert("RGB")
    W, H = im.size
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    idx = []
    for r, y0 in enumerate(Y0S):
        for c, x0 in enumerate(X0S):
            x1, y1 = min(W, x0 + S), min(H, y0 + S)
            if x1 - x0 < 400 or y1 - y0 < 400:
                continue
            t = im.crop((x0, y0, x1, y1)).copy()
            d = ImageDraw.Draw(t)
            for gx in range((x0 // 100 + 1) * 100, x1, 100):
                X = gx - x0
                d.line([(X, 0), (X, t.size[1])], fill=(0, 140, 255), width=1)
                d.text((X + 2, 2), str(gx), fill=(0, 60, 200), font=font)
                d.text((X + 2, t.size[1] - 18), str(gx), fill=(0, 60, 200), font=font)
            for gy in range((y0 // 100 + 1) * 100, y1, 100):
                Y = gy - y0
                d.line([(0, Y), (t.size[0], Y)], fill=(0, 140, 255), width=1)
                d.text((2, Y + 2), str(gy), fill=(0, 60, 200), font=font)
                d.text((t.size[0] - 44, Y + 2), str(gy), fill=(0, 60, 200), font=font)
            name = "tile_%d_%d.png" % (r, c)
            t.save(os.path.join(OUT, name))
            idx.append({"tile": name, "x0": x0, "y0": y0, "x1": x1, "y1": y1})
    json.dump({"note": "pixel coordinates of the warped plan (5000 x 5134); grid labels in the tiles are the same global coordinates", "tiles": idx}, open(os.path.join(OUT, "tiles_index.json"), "w", encoding="utf-8"), indent=1)
    full = Image.open(os.path.join(ROOT, "for_gemini", "tbilisi_1913_full.jpg"))
    full.crop((4300, 3150, 5700, 3600)).save(os.path.join(OUT, "legend.png"))
    print(len(idx), "tiles")


if __name__ == "__main__":
    main()
