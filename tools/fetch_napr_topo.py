"""Download the open WMTS tiles of the topographic maps of the National Agency of Public Registry of Georgia (maps.gov.ge, host mp.napr.gov.ge)
for the Tbilisi area only. The portal itself requests these URLs without any key (found by watching its requests); the owner decided (2026-11-18) that
this is public data to be used like the heritage register.
Output: data/cache/napr/<key>/<z>/<x>_<y>.jpg (raw, not committed; resumable). Polite: 4 threads, small pause, identifies itself as a hobby project.
Usage: python tools/fetch_napr_topo.py            (all series)
"""
import concurrent.futures
import math
import os
import sys
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "cache", "napr")
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"
BASE = "https://mp.napr.gov.ge/"
# series key -> (service path, max zoom with data)
SERIES = {
    "t100": ("TOPO_100K_1978_1990/wmts/TOPO_100000", 14),
    "t50": ("TOPO_50k_1973-1990/wmts/TOPO_50000_1973_1990", 15),
    "t25": ("TOPO_25k_1953-2004/wmts/TOPO_25000_1953-2004", 16),
    "t10": ("TOPO_10k_1952_2007/wmts/TOPO_10000_1952_2007", 16),
    "t2": ("TOPO_2k_Cityes/wmts/TOPO_2000_Cityes", 17),
}
WIDE = (44.60, 41.55, 45.05, 41.88)      # lon0, lat0, lon1, lat1: overview zooms 11-14
CORE = (44.72, 41.64, 44.93, 41.80)      # zooms 15-16
HIST = (44.76, 41.67, 44.86, 41.75)      # zoom 17 (only the 1:2 000 city plan)
MINZ = 11


def tile_xy(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def tiles_for(z):
    bb = WIDE if z <= 14 else CORE if z <= 16 else HIST
    x0, y1 = tile_xy(bb[0], bb[1], z)
    x1, y0 = tile_xy(bb[2], bb[3], z)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def fetch(job):
    key, z, x, y = job
    p = os.path.join(OUT, key, str(z), "%d_%d.jpg" % (x, y))
    if os.path.exists(p):
        return "have"
    url = "%s%s/GLOBAL_MERCATOR/%d/%d/%d.png" % (BASE, SERIES[key][0], z, x, y)
    for k in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read()
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(b)
            time.sleep(0.15)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "wb").write(b"")          # empty marker: the service has no tile here
                return "none"
        except Exception:
            time.sleep(3 * (k + 1))
    return "fail"


def main():
    keys = sys.argv[1:] or list(SERIES)
    jobs = []
    for key in keys:
        for z in range(MINZ, SERIES[key][1] + 1):
            jobs += [(key, z, x, y) for x, y in tiles_for(z)]
    print("tiles:", len(jobs), flush=True)
    done = {"ok": 0, "have": 0, "none": 0, "fail": 0}
    with concurrent.futures.ThreadPoolExecutor(4) as ex:
        for i, r in enumerate(ex.map(fetch, jobs), 1):
            done[r] += 1
            if i % 500 == 0:
                print(i, done, flush=True)
    print("finished", done, flush=True)


if __name__ == "__main__":
    main()
