"""Makes the light copies ("overviews") of the old plans for the first screen and writes them into site/data/plans.json (fields overview, overview_mpp).

The page shows the overview first (about 8 m per pixel on the ground: sharper than the screen at the starting scale) and puts the full picture of the plan in
its place when the map is zoomed in (or on a screen with a dense pixel grid): the first view no longer waits for a file of 2.4 MB, and no quality is lost, because
the full picture is what the page ends up showing (the function upgradePlans of site/app.js).
Run it after tools/build_site_data.py (that script writes plans.json without these fields).
Usage: python -X utf8 -P tools/make_plan_overviews.py
"""
import json
import math
import os

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
TARGET_MPP = 8.0          # metres on the ground per pixel of the overview
MIN_W = 500


def main():
    path = os.path.join(SITE, "data", "plans.json")
    plans = json.load(open(path, encoding="utf-8"))
    total_full = total_ov = 0
    for p in plans:
        full = os.path.join(SITE, p["image"])
        im = Image.open(full)
        w, h = im.size
        c = p["corners"]
        extent_m = (c[1][0] - c[0][0]) * 111320 * math.cos(math.radians((c[0][1] + c[3][1]) / 2))
        ow = int(max(MIN_W, min(w, round(extent_m / TARGET_MPP))))
        oh = round(h * ow / w)
        ov = im.convert("RGB").resize((ow, oh), Image.LANCZOS) if ow < w else im.convert("RGB")
        name = os.path.splitext(os.path.basename(p["image"]))[0] + "_s.webp"
        ov.save(os.path.join(SITE, "data", name), "WEBP", quality=80, method=6)
        p["overview"] = "data/" + name
        p["overview_mpp"] = round(extent_m / ow, 2)
        total_full += os.path.getsize(full)
        total_ov += os.path.getsize(os.path.join(SITE, "data", name))
        print("%s: %dx%d -> %dx%d, %.2f MB -> %.2f MB, %.1f m/px" % (p["id"], w, h, ow, oh, os.path.getsize(full) / 1e6, os.path.getsize(os.path.join(SITE, "data", name)) / 1e6, p["overview_mpp"]))
    open(path, "w", encoding="utf-8", newline="").write(json.dumps(plans, ensure_ascii=False, indent=1))
    print("plans: %.1f MB, overviews: %.1f MB" % (total_full / 1e6, total_ov / 1e6))


if __name__ == "__main__":
    main()
