"""Outlines of the settled city territory (dense blocks plus the gardens, suburbs and outskirts attached to them) on the plans, traced by eye on the georeferenced (north-up) images.

Vertices are pixel coordinates in data/warped/<id>.webp (output of tools/warp.py); they are converted to lon/lat with the
image corners (Web Mercator-linear grid, same convention as warp.py). Output: data/boundaries/<id>.geojson with
properties confidence "approximate". The outlines follow the dense urban fabric only (not gardens, fields or
isolated houses) and are good to roughly the georeferencing accuracy (~50 m) plus the tracing error (~30-60 m).
Usage: python tools/trace_early_boundaries.py [plan_id ...]
"""
import json
import math
import os
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = 6378137.0

# pixel vertices in the warped image, clockwise; several rings per plan allowed: (name, [(x, y), ...])
TRACES = {
    "tiflis_1844": {
        "year": 1844,
        "rings": [
            ("city_territory", [(440, 240), (1000, 220), (1360, 560), (1540, 1040), (1400, 1240), (1780, 1320), (2080, 1320), (2360, 1680), (2400, 2080), (2640, 2240), (2800, 2560), (2880, 3040), (2560, 3120), (2160, 3000), (1880, 2800), (1720, 2560), (1200, 2520), (800, 2440), (600, 2120), (600, 1680), (520, 1320), (460, 800), (440, 240)]),
        ],
    },
    "tiflis_1800": {
        "year": 1800,
        "rings": [
            ("city", [(919, 1331), (988, 1281), (1131, 1244), (1300, 1238), (1425, 1294), (1388, 1425), (1388, 1575), (1400, 1700),
                      (1369, 1812), (1413, 1912), (1500, 1981), (1619, 1981), (1694, 2000), (1694, 2125), (1700, 2288), (1662, 2425),
                      (1625, 2437), (1537, 2469), (1425, 2437), (1350, 2350), (1350, 2175), (1237, 2025), (1200, 1925), (1150, 1750),
                      (1087, 1650), (962, 1537), (900, 1412), (919, 1331)]),
            ("avlabari_metekhi", [(1690, 1960), (1760, 1930), (1820, 1900), (1900, 1840), (2000, 1820), (2100, 1840), (2130, 1920),
                                  (2120, 2010), (2060, 2070), (1850, 2075), (1820, 2085), (1700, 2080), (1680, 2000), (1690, 1960)]),
        ],
    },
    "tiflis_1785": {
        "year": 1785,
        "rings": [
            ("city", [(762, 487), (987, 475), (1100, 575), (1112, 825), (1137, 1075), (1187, 1225), (1250, 1300), (1275, 1350),
                      (1200, 1437), (1000, 1500), (875, 1500), (787, 1362), (750, 1250), (750, 750), (762, 487)]),
            ("avlabari", [(1387, 1000), (1525, 1000), (1600, 1075), (1612, 1175), (1525, 1195), (1400, 1175), (1370, 1100), (1387, 1000)]),
            ("metekhi_isani", [(1250, 1262), (1400, 1287), (1400, 1450), (1387, 1725), (1300, 1750), (1250, 1600), (1262, 1400), (1250, 1262)]),
        ],
    },
    "tiflis_1735": {
        "year": 1735,
        "rings": [
            ("kala_walled_city", [(1080, 1060), (1320, 1020), (1680, 1000), (1720, 1280), (1760, 1640), (1600, 1720), (1320, 1680),
                                  (1160, 1520), (1100, 1280), (1080, 1060)]),
            ("isani_avlabari", [(2000, 1020), (2280, 1040), (2400, 1320), (2380, 1560), (2160, 1540), (2020, 1320), (2000, 1020)]),
        ],
    },
    "tiflis_1887": {
        "year": 1887,
        "rings": [
            ("city_territory", [(480, 232), (1200, 220), (1380, 280), (1640, 460), (1720, 800), (1780, 1200), (2000, 1340), (2160, 1680), (2320, 2000), (2600, 2180), (2880, 2400), (3060, 2600), (3100, 2920), (3060, 3200), (2800, 3260), (2480, 3320), (2080, 3260), (1600, 3200), (1200, 3160), (940, 2980), (860, 2760), (820, 2560), (520, 2360), (380, 2120), (380, 1880), (520, 1620), (760, 1560), (900, 1280), (860, 1040), (520, 920), (320, 600), (480, 232)]),
            ("navtlugi", [(3600, 3620), (3940, 3580), (4180, 3780), (4240, 4000), (4040, 4100), (3700, 4060), (3580, 3800), (3600, 3620)]),
        ],
    },
    "tbilisi_1913": {
        "year": 1913,
        "rings": [
            # NE side = the "city limit" line (green line in the plan legend, traced earlier); the other sides follow the
            # edge of the settled blocks / gardens (south: Kura gardens and slopes, west: Vake-Saburtalo edge)
            ("city_territory", [(112, 150), (591, 215), (941, 277), (1290, 337), (1770, 270), (1821, 328), (2135, 715), (2501, 1166), (2781, 1515), (3087, 1906), (3130, 2008), (3148, 2119), (3125, 2231), (3227, 2315), (3398, 2605), (3618, 2899), (3855, 3154), (3991, 3341), (4076, 3477), (4247, 3716), (4348, 3817), (4568, 4090), (4755, 4310)] + [(4700,4480),(4400,4560),(4100,4560),(3800,4330),(3400,4180),(3100,3980),(2900,3880),(2600,3870),(2300,3760),(1900,3560),(1500,3560),(1000,3420),(600,3420),(230,3360),(120,3000),(110,2400),(100,1600),(100,1000),(112,150)]),
        ],
    },
    "tiflis_1879": {
        "year": 1879,
        "rings": [
            ("city_territory", [(1318, 734), (1766, 747), (2068, 945), (2147, 1234), (2226, 1445), (2463, 1589), (2621, 1787), (2661, 1984), (2832, 2116), (3042, 2234), (3200, 2392), (3279, 2550), (3253, 2655), (3042, 2668), (2832, 2629), (2621, 2629), (2305, 2629), (1989, 2576), (1766, 2497), (1739, 2234), (1792, 2024), (1753, 1787), (1595, 1642), (1411, 1445), (1318, 1076), (1318, 734)]),
            ("navtlugi", [(3647, 3050), (3937, 3076), (4055, 3261), (4029, 3524), (3805, 3576), (3634, 3445), (3595, 3208), (3647, 3050)]),
        ],
    },
    "tiflis_1802": {
        "year": 1802,
        "rings": [
            ("kala_walled_city", [(915, 1275), (1300, 1260), (1360, 1330), (1345, 1800), (1400, 1980), (1480, 2040), (1470, 2250), (1300, 2270), (915, 2260), (915, 1275)]),
            ("metekhi", [(1480, 2000), (1700, 1990), (1750, 2100), (1760, 2380), (1650, 2450), (1540, 2400), (1480, 2250), (1480, 2000)]),
            ("avlabari", [(1790, 1790), (1900, 1740), (2050, 1780), (2150, 1880), (2130, 2020), (1950, 2060), (1830, 2010), (1790, 1890), (1790, 1790)]),
        ],
    },
    "tiflis_1782": {
        "year": 1782,
        "rings": [
            ("kala_walled_city", [(2170, 590), (2400, 560), (2620, 550), (2727, 655), (2755, 855), (2764, 1000), (2791, 1182), (2860, 1340), (2930, 1470), (2900, 1640), (2650, 1660), (2300, 1640), (2150, 1560), (2140, 1100), (2150, 800), (2170, 590)]),
            ("metekhi_lower_city", [(2960, 1400), (3100, 1380), (3200, 1480), (3180, 1700), (3000, 1790), (2900, 1700), (2940, 1520), (2960, 1400)]),
            ("avlabari", [(3170, 1110), (3300, 1100), (3440, 1160), (3500, 1260), (3430, 1330), (3260, 1320), (3170, 1240), (3170, 1110)]),
        ],
    },
}


def merc_y(lat):
    return R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def to_lonlat(corners, size, x, y):
    (lng0, lat0), (lng1, _), (_, lat1) = corners[0], corners[1], corners[2]
    W, H = size
    my = merc_y(lat0) + (merc_y(lat1) - merc_y(lat0)) * y / H
    return lng0 + (lng1 - lng0) * x / W, math.degrees(2 * math.atan(math.exp(my / R)) - math.pi / 2)


def main(ids):
    for pid in ids:
        t = TRACES[pid]
        meta = json.load(open(os.path.join(ROOT, "data", "warped", pid + ".json"), encoding="utf-8"))
        size = Image.open(os.path.join(ROOT, "data", "warped", pid + ".webp")).size
        feats = []
        for name, ring in t["rings"]:
            ll = [[round(v, 6) for v in to_lonlat(meta["corners"], size, x, y)] for x, y in ring]
            if ll[0] != ll[-1]:
                ll.append(ll[0])
            feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ll]},
                          "properties": {"plan_id": pid, "name": name, "kind": "built_up", "confidence": "approximate",
                                         "source": "traced by eye on the georeferenced plan (%s, LOO %s m)" % (pid, round(meta.get("loo_rms_m") or 0))}})
        out = {"type": "FeatureCollection", "features": feats, "properties": {"year": t["year"]}}
        path = os.path.join(ROOT, "data", "boundaries", pid + ".geojson")
        json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        print(pid, "rings:", len(feats), "->", path)


if __name__ == "__main__":
    main(sys.argv[1:] or list(TRACES))
