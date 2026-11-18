"""Convert the downloaded NAPR topographic tiles (data/cache/napr, see fetch_napr_topo.py) to compact WebP tiles for the static site:
site/topo/<key>/<z>/<x>/<y>.webp. Tiles with no content (empty marker or a uniform blank image) are skipped, the site then simply shows no overlay there.
Usage: python -P tools/build_topo_tiles.py [key ...]
"""
import io
import os
import sys

from PIL import Image, ImageStat

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "data", "cache", "napr")
OUT = os.path.join(ROOT, "site", "topo")
Q = 62


def main():
    keys = sys.argv[1:] or sorted(os.listdir(SRC))
    total = {"written": 0, "blank": 0, "empty": 0, "bytes": 0}
    for key in keys:
        n = {"written": 0, "blank": 0, "empty": 0, "bytes": 0}
        for z in sorted(os.listdir(os.path.join(SRC, key)), key=int):
            zd = os.path.join(SRC, key, z)
            for f in os.listdir(zd):
                p = os.path.join(zd, f)
                x, y = os.path.splitext(f)[0].split("_")
                if os.path.getsize(p) == 0:
                    n["empty"] += 1
                    continue
                im = Image.open(p)
                im.load()
                if im.mode in ("P", "LA"):
                    im = im.convert("RGBA")
                elif im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGB")
                st = ImageStat.Stat(im.convert("RGB"))
                if max(st.stddev) < 1.0 and min(st.mean) > 245:     # uniform white tile
                    n["blank"] += 1
                    continue
                d = os.path.join(OUT, key, z, x)
                os.makedirs(d, exist_ok=True)
                buf = io.BytesIO()
                im.save(buf, "WEBP", quality=Q, method=6)
                open(os.path.join(d, y + ".webp"), "wb").write(buf.getvalue())
                n["written"] += 1
                n["bytes"] += buf.tell()
        print(key, n, "MB: %.1f" % (n["bytes"] / 1e6), flush=True)
        for k in total:
            total[k] += n[k]
    print("total", total, "MB: %.1f" % (total["bytes"] / 1e6))


if __name__ == "__main__":
    main()
