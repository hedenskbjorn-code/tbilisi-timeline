"""Label points of the modern districts, put in the real urban core of each district.

The OSM district polygons (since the 2006 enlargement) contain a lot of empty land and outlying villages, so a label put in the
middle of the polygon lands far from the district proper (Saburtalo's ended up near Dighomi and Lisi Lake, Vake's in the west,
Mtatsminda's in the south forests). Rule used here:
  * Saburtalo: the place of "М. Сабурталo" on the topographic sheet of c.1911 (the project's georeferencing of that sheet,
    pixel read by eye, point at the label of the village), confirmed by the owner, a native of Saburtalo;
  * other districts: the OpenStreetMap place node of the neighbourhood with the same name (a person put it in the core of the area),
    else the district's own "suburb" node.
Output: data/district_labels.json {district name_en: [lon, lat, "source"]}; read by tools/build_site_data.py.
"""
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def px_to_lonlat(pid, x, y):
    j = json.load(open(os.path.join(ROOT, "data", "warped", pid + ".json"), encoding="utf-8"))
    (w0, n0), (w1, _), (_, s0) = j["corners"][0], j["corners"][1], j["corners"][3]
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    W, H = Image.open(os.path.join(ROOT, "data", "warped", pid + ".webp")).size
    my = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    imy = lambda v: math.degrees(2 * math.atan(math.exp(v)) - math.pi / 2)
    return w0 + x / W * (w1 - w0), imy(my(n0) + y / H * (my(s0) - my(n0)))


def main():
    els = json.load(open(os.path.join(ROOT, "data", "raw", "admin", "osm_places.json"), encoding="utf-8"))
    els = els.get("elements", els) if isinstance(els, dict) else els
    by = {}
    for e in els:
        t = e.get("tags", {})
        by.setdefault(t.get("name:en") or t.get("name"), []).append((t.get("place"), e["lon"], e["lat"]))
    out = {}
    for d in ["Mtatsminda", "Vake", "Didube", "Chugureti", "Isani", "Nadzaladevi", "Gldani", "Samgori", "Krtsanisi", "Saburtalo"]:
        if d == "Saburtalo":
            lon, lat = px_to_lonlat("tiflis_1911", 1430, 1686)         # "М. САБУРТАЛО" on the 1911 sheet
            out[d] = [round(lon, 5), round(lat, 5), "label of the village on the 1911 sheet"]
            continue
        hood = [x for x in by.get(d, []) if x[0] == "neighbourhood"]
        sub = [x for x in by.get(d + " District", []) if x[0] == "suburb"]
        pick = hood[0] if hood else sub[0]
        out[d] = [round(pick[1], 5), round(pick[2], 5), "OSM place node (%s)" % pick[0]]
    json.dump(out, open(os.path.join(ROOT, "data", "district_labels.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in out.items():
        print("%-12s %s" % (k, v))


if __name__ == "__main__":
    main()
