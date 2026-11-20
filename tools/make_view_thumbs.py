"""Makes the small copies (400 px wide) of the pictures of the window "Views" for the tiles of the grid.

  python tools/make_view_thumbs.py

The tiles of the grid are about 130-180 px wide; before the thumbnails they loaded the whole picture (up to 750 KB, 16 MB for all of them).
The viewer (a click on a tile) still loads the whole picture. Writes site/data/views/thumb/<name>.webp for every local picture of site/data/views.json;
a picture that is on Wikimedia gets its small copy from a Wikimedia thumbnail address in app.js (function viewThumb), nothing is made for it here.
"""
import json
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(SITE, "data", "views", "thumb")
W = 400
Q = 66


def main():
    views = json.load(open(os.path.join(SITE, "data", "views.json"), encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    made = skipped = total = 0
    for v in views:
        src = v["image"]
        if src.startswith("http"):
            continue
        name = os.path.splitext(os.path.basename(src))[0] + ".webp"
        dst = os.path.join(OUT, name)
        s = os.path.join(SITE, src)
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(s):
            skipped += 1
            total += os.path.getsize(dst)
            continue
        im = Image.open(s)
        im = im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im
        if im.width > W:
            im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
        im.save(dst, "WEBP", quality=Q, method=6)
        made += 1
        total += os.path.getsize(dst)
    print(f"thumbnails: made {made}, up to date {skipped}, {total / 1024:.0f} KB in all")


if __name__ == "__main__":
    main()
