"""Transport layer: metro, railway, funicular, cable cars, main avenues, two bridges, with opening / closing years, plus a list of events
(tram, trolleybus, station rebuilds, renamings) that have no geometry.

Geometry: OpenStreetMap (Overpass, ODbL), data/raw/osm_transport/ (tools/fetch_transport_osm.py).  OSM has almost no dates for these
objects, so the DATES come from Wikipedia pages that were read for this project (ru / ka / en), listed per feature in "src"; where the
pages disagree the feature says so in "note".  Metro lines are drawn as straight segments between consecutive stations (schematic).
A feature is shown in years [y0, y1) and [y2, y3) (the second period is for objects that were closed and reopened); 9999 = still there.
Output: site/data/transport.json (GeoJSON), site/data/transport_events.json
"""
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "raw", "osm_transport")
OUT = os.path.join(ROOT, "site", "data")
WP = "https://en.wikipedia.org/wiki/"
WPRU = "https://ru.wikipedia.org/wiki/"
WPKA = "https://ka.wikipedia.org/wiki/"
S_METRO = [WPKA + "თბილისის_მეტროპოლიტენი", WPRU + "Тбилисский_метрополитен", WP + "Tbilisi_Metro"]


def load(n):
    return json.load(open(os.path.join(RAW, n + ".json"), encoding="utf-8"))["elements"]


def line(geom):
    return [[round(p["lon"], 5), round(p["lat"], 5)] for p in geom]


def feat(geom, **p):
    p.setdefault("y1", 9999)
    p.setdefault("y2", -1)
    p.setdefault("y3", -1)
    return {"type": "Feature", "geometry": geom, "properties": p}


def way_len(geom):
    """length in metres of an OSM way given as a list of {lat, lon}"""
    return round(sum(math.hypot((geom[j + 1]["lon"] - geom[j]["lon"]) * math.cos(math.radians(geom[j]["lat"])) * 111320, (geom[j + 1]["lat"] - geom[j]["lat"]) * 111320) for j in range(len(geom) - 1)))


def outside_built_up(ways, y0, share=0.5):
    """Indexes of ways that lie mostly outside the built-up outlines of their time (site/data/urban.json: outlines of 1954, 1972, 1978, 1985, 1990, 2000, ...; the outlines
    within 12 years of the first year of the route are taken together). A tram did not run through open country. The outlines are approximate, so this is used only for the
    streets where the picture of a street drawn far into the country is obvious (see CHECK_URBAN)."""
    u = json.load(open(os.path.join(ROOT, "site", "data", "urban.json"), encoding="utf-8"))["features"]
    snaps = sorted(set(f["properties"]["snap"] for f in u))
    use = [x for x in snaps if y0 - 12 <= x <= y0 + 12] or [min(snaps, key=lambda x: abs(x - y0))]
    rings = []
    for f in u:
        if f["properties"]["snap"] in use:
            g = f["geometry"]
            rings.extend([g["coordinates"][0]] if g["type"] == "Polygon" else [q[0] for q in g["coordinates"]])

    def inside(pt, ring):
        x, y = pt
        c = False
        for i in range(len(ring)):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % len(ring)]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c
    out = []
    for i, w in enumerate(ways):
        pts = line(w["geometry"])[::2]
        if sum(1 for q in pts if any(inside(q, r) for r in rings)) / max(1, len(pts)) < share:
            out.append(i)
    return out


def far_pieces(ways, limit=1000, join=40, core=None):
    """The OSM query takes every way with a street name in the whole box, and the names repeat in other parts of the city and the suburbs (found out 2026-11-19: tram tracks in
    Tskneti, Okrokana, near Zahesi and so on). The ways of one name are joined into lines (ends closer than `join` m); the longest line is the main one; a piece that lies
    farther than `limit` m from the main line is another street with the same name and is returned to be dropped."""
    def hav(a, b):
        k = math.cos(math.radians(a[1]))
        return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 111320)
    geoms = [line(w["geometry"]) for w in ways]
    n = len(geoms)
    par = list(range(n))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if min(hav(a, b) for a in (geoms[i][0], geoms[i][-1]) for b in (geoms[j][0], geoms[j][-1])) < join:
                par[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    length = lambda idx: sum(hav(geoms[i][k], geoms[i][k + 1]) for i in idx for k in range(len(geoms[i]) - 1))
    main = max(groups.values(), key=length)
    if core:
        # the longest line can be the wrong one (found out 2026-11-19: Pirosmani Street, 0.6 km in the east against 0.5 km by the railway station): when another line of the
        # name lies more than 3 km nearer to the centre of the old network, that one is the main line
        dist = lambda idx: min(hav(a, c) for i in idx for a in geoms[i][::2] for c in core[::2])
        near = min(groups.values(), key=dist)
        if dist(main) - dist(near) > 3000:
            main = near
    mp = [pt for i in main for pt in geoms[i]]
    far = []
    for i in range(n):
        if i in main:
            continue
        if min(hav(a, b) for a in geoms[i][::3] for b in mp[::3]) > limit:
            far.append(i)
    return far


def main():
    feats = []
    # ---------------- metro
    # Russian names of the stations whose name:ru in OSM is only a transliteration of the Georgian one: the translations (the Russian Wikipedia, "Tbilisi metro": "Государственный университет",
    # "Политехнический институт", "Вокзальная-II", "Вагзлис моедани (Вокзальная площадь)"; the English names of the stations are translations too); the owner's remark of 2026-11-22
    RU_STATION = {"Akhmeteli Theatre": "Театр Ахметели", "Station Square-1": "Вокзальная площадь-1", "Station Square-2": "Вокзальная площадь-2", "Liberty Square": "Площадь Свободы",
                  "Technical University": "Технический университет", "Medical University": "Медицинский университет", "State University": "Государственный университет"}
    LINE1 = ["Akhmeteli Theatre", "Sarajishvili", "Guramishvili", "Ghrmaghele", "Didube", "Gotsiridze", "Nadzaledevi", "Station Square-1", "Marjanishvili",
             "Rustaveli", "Liberty Square", "Avlabari", "300 Aragveli", "Isani", "Samgori", "Varketili"]
    LINE2 = ["Station Square-2", "Tsereteli", "Technical University", "Medical University", "Delisi", "Vazha-Pshavela", "State University"]
    YEAR = {"Didube": 1966, "Gotsiridze": 1966, "Nadzaledevi": 1966, "Station Square-1": 1966, "Marjanishvili": 1966, "Rustaveli": 1966,
            "Liberty Square": 1967, "Avlabari": 1967, "300 Aragveli": 1967, "Isani": 1971, "Samgori": 1971, "Varketili": 1985,
            "Guramishvili": 1985, "Ghrmaghele": 1985, "Akhmeteli Theatre": 1989, "Sarajishvili": 1989,
            "Station Square-2": 1979, "Tsereteli": 1979, "Technical University": 1979, "Medical University": 1979, "Delisi": 1979,
            "Vazha-Pshavela": 2000, "State University": 2017}
    NOTE = {"Varketili": "ka/ru Wikipedia: 9 Nov 1985, en: 8 Nov 1985", "Samgori": "ka/en Wikipedia: 5 May 1971, ru: 10 May 1971", "Isani": "ka/en Wikipedia: 5 May 1971, ru: 10 May 1971",
            "Guramishvili": "section Didube-Guramishvili opened 16 Nov 1985; Ghrmaghele (ru) 28 Nov 1985", "Ghrmaghele": "ru Wikipedia: 28 Nov 1985",
            "Akhmeteli Theatre": "7 Jan 1989 (ka, ru)", "Sarajishvili": "7 Jan 1989 (ka, ru)",
            "Vazha-Pshavela": "2 Apr 2000", "State University": "16 Oct 2017 (the station was mothballed in 2000)", "Gotsiridze": "reopened after reconstruction 18 Mar 2023 (ru)"}
    st = {}
    for e in load("stations"):
        t = e["tags"]
        if t.get("railway") == "station" and t.get("station") == "subway":
            nm = t.get("name:en") or t.get("name")
            c = (e["lon"], e["lat"]) if e["type"] == "node" else (e["center"]["lon"], e["center"]["lat"])
            st[nm] = (c, t)
    for ln, names in (("1", LINE1), ("2", LINE2)):
        for nm in names:
            if nm not in st:
                print("metro station not found in OSM:", nm)
        for a, b in zip(names, names[1:]):
            if a in st and b in st:
                y = max(YEAR[a], YEAR[b])
                feats.append(feat({"type": "LineString", "coordinates": [[round(st[a][0][0], 5), round(st[a][0][1], 5)], [round(st[b][0][0], 5), round(st[b][0][1], 5)]]},
                                  id="metro%s_%s_%s" % (ln, a, b), kind="metro_line", line=ln, name_en=("Tbilisi Metro, Akhmeteli-Varketili line" if ln == "1" else "Tbilisi Metro, Saburtalo line"),
                                  name_ru=("Тбилисское метро, Ахметели-Варкетилийская линия" if ln == "1" else "Тбилисское метро, Сабурталинская линия"),
                                  name_ka=("თბილისის მეტრო, ახმეტელი-ვარკეთილის ხაზი" if ln == "1" else "თბილისის მეტრო, საბურთალოს ხაზი"), y0=y, note="schematic line between stations; section opened %d" % y, src=S_METRO))
        for nm in names:
            if nm in st:
                (lon, lat), t = st[nm]
                feats.append(feat({"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}, id="metrost_" + nm, kind="metro_station", line=ln,
                                  name_en=nm if nm != "Nadzaledevi" else "Nadzaladevi", name_ru=RU_STATION.get(nm) or t.get("name:ru") or "", name_ka=t.get("name:ka") or "", y0=YEAR[nm], note=NOTE.get(nm, ""), src=S_METRO))
    # ---------------- railway: main line through Tbilisi, west of the central station from 1872, east of it from 1883
    CENTRAL = 44.7995
    SR = [WP + "Georgian_Railway", WP + "Transcaucasus_Railway", WP + "Tbilisi_railway_station"]
    for e in load("railways"):
        t = e["tags"]
        if t.get("railway") != "rail" or t.get("usage") != "main" or t.get("service") or "Bypass" in (t.get("name") or ""):
            continue
        g = line(e["geometry"])
        lon = sum(p[0] for p in g) / len(g)
        west = lon < CENTRAL
        feats.append(feat({"type": "LineString", "coordinates": g}, id="rail%d" % e["id"], kind="railway", name_en="Main railway (Tbilisi)", name_ru="Главная железная дорога (Тбилиси)",
                          name_ka="მთავარი რკინიგზა (თბილისი)", y0=1872 if west else 1883,
                          note=("west of the central station: Poti-Tiflis line, first passenger train 10 Oct 1872" if west else
                                "east of the central station: Tiflis-Baku line, operational 1883; branch lines (for example towards Gyumri, 1899) are not separated, so some stretches may be drawn too early"), src=SR))
    # ---------------- funicular
    for e in load("railways"):
        t = e["tags"]
        if t.get("railway") == "funicular":
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="fun%d" % e["id"], kind="funicular", name_en="Mtatsminda funicular", name_ru="Фуникулёр Мтацминда",
                              name_ka="მთაწმინდის ფუნიკულიორი", y0=1905, y1=2000, y2=2013, y3=9999,
                              note="opened 30 Dec 1905; closed 21 Jun 2000 after a cable broke; modernised 2012; reopened 30 Jan 2013 (ru Wikipedia)", src=[WPRU + "Тбилисский_фуникулёр"]))
    # ---------------- Rustaveli - Mtatsminda cable car
    for e in load("aerialway"):
        t = e["tags"]
        if "Rustaveli - Mtatsminda" in ((t.get("name") or "") + " " + (t.get("name:en") or "")):
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="cc%d" % e["id"], kind="cablecar", name_en="Rustaveli-Mtatsminda cable car", name_ru="Канатная дорога Руставели — Мтацминда",
                              name_ka="რუსთაველი-მთაწმინდის საბაგირო", y0=1958, y1=1990, y2=2024, y3=9999,
                              note="1958 opened; 1 Jun 1990 two cabins crashed and the line closed; rebuilt, opened to passengers 18 Oct 2024; the line drawn is the present one (ru Wikipedia)",
                              src=[WPRU + "Канатная_дорога_Руставели_—_Мтацминда"]))
    # ---------------- other cable cars: the lost Samgori-Vazisubani and Nutsubidze-Lisi Lake lines, the present Rike-Narikala line
    WD = "https://www.wikidata.org/wiki/Q134961500"
    for e in load("aerialway"):
        t = e["tags"]
        if e["id"] == 142360838:
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="cc%d" % e["id"], kind="cablecar", name_en="Samgori-Vazisubani cable car", name_ru="Канатная дорога Самгори — Вазисубани",
                              name_ka="სამგორი-ვაზისუბნის საბაგირო", y0=1986, y1=2002,
                              note="years from the Wikidata / Commons infobox of the line (1986-2002, no reference given there); the line is marked disused in OpenStreetMap", src=[WD, "https://commons.wikimedia.org/wiki/Category:Samgori-Vazisubani_Ropeway"]))
        if e["id"] == 154331558:
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="cc%d" % e["id"], kind="cablecar", name_en="Rike-Narikala cable car", name_ru="Канатная дорога Рике — Нарикала",
                              name_ka="რიყე-ნარიყალას საბაგირო", y0=2012,
                              note="opened 2012 (OpenStreetMap start_date of the lower station; gondolaproject.com)", src=["https://commons.wikimedia.org/wiki/Category:Rike-Narikala_Ropeway", "https://www.gondolaproject.com/2017/02/03/tbilisi-georgian-ropeways-part-1/"]))
    GT = "https://georgiatoday.ge/bagebi-maglivi-ropeway-to-open-april-20/"
    GP = "https://www.gondolaproject.com/2017/03/14/tbilisigeorgian-ropeways-part-1-2-tbilisi-state-university-ropeway/"
    for e in load("aerialway"):
        if e["id"] == 176163231:
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="cc%d" % e["id"], kind="cablecar", name_en="University-Bagebi cable car", name_ru="Канатная дорога Университет — Багеби",
                              name_ka="უნივერსიტეტი-ბაგების საბაგირო", y0=1983, y1=1995, y2=2021, y3=9999,
                              note="built 1982 (OpenStreetMap) or 1983 (Wikidata/Commons, gondolaproject); stopped 'sometime in the 90s' (gondolaproject) - the exact year is NOT established, 1995 is a placeholder; rehabilitated, the city mayor announced the start of service for 20 April 2021 (Georgia Today, 25 Mar 2021: a plan, the actual opening day was not confirmed); works today (Georgia Travel, Madloba)",
                              src=[GP, GT, "https://commons.wikimedia.org/wiki/Category:Tbilisi_State_University_ropeway"]))
        if e["id"] == 149928375:
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="cc%d" % e["id"], kind="cablecar", name_en="Vake Park - Turtle Lake cable car", name_ru="Канатная дорога Парк Ваке — озеро Туртл (Кус Тба)",
                              name_ka="ვაკის პარკი-კუს ტბის საბაგირო", y0=1965, y1=2008, y2=2016, y3=9999,
                              note="gondolas first appeared in 1965 (Georgia Travel); civil.ge in Nov 2010 called it the last Tbilisi cable car and said it had 'ceased running a couple of years ago' (so about 2008, the exact year is not established); modernised 2016 (gondolaproject); works today (Georgia Travel)",
                              src=["https://georgia.travel/ka/საოჯახო-სანახაობები/საბაგირო-გზები", "https://civil.ge/?p=120679", "https://www.gondolaproject.com/2017/02/03/tbilisi-georgian-ropeways-part-1/"]))
    feats.append(feat({"type": "LineString", "coordinates": [[44.74325, 41.72873], [44.74213, 41.73868]]}, id="cc_lisi", kind="cablecar", name_en="Nutsubidze-Lisi Lake cable car", name_ru="Канатная дорога Нуцубидзе — озеро Лиси",
                      name_ka="ნუცუბიძე-ლისის ტბის საბაგირო", y0=1978, y1=1995,
                      note="WEAK DATES: 1978-1995 is only from a railway-enthusiast forum list (seen in a search snippet, the page itself was not readable); a 2025 ICOMOS poster says 'a 1980s line, decommissioned in the late 1990s'. Schematic straight line between the two former stations (OpenStreetMap ways 633414853 on Nutsubidze Street and 742183462, the former upper station near Lisi Lake)",
                      src=["https://commons.wikimedia.org/wiki/Category:Former_Lisi_Lake_cable_car"]))
    # ---------------- avenues
    def avenue(files, pred, fid, y0, y1, names, note, src):
        n = 0
        for f in files:
            for e in load(f):
                t = e["tags"]
                if pred(t) and "geometry" in e:
                    n += 1
                    feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="%s_%d" % (fid, e["id"]), kind="avenue", y0=y0, y1=y1, note=note, src=src, **names))
        print(fid, "ways:", n)
    avenue(["rustaveli"], lambda t: t.get("name:en") == "Shota Rustaveli Avenue", "rustaveli", 1840, 9999,
           {"name_en": "Rustaveli Avenue", "name_ru": "Проспект Руставели (Головинский проспект)", "name_ka": "რუსთაველის გამზირი"},
           "built in the 1840s on the order of viceroy Vorontsov (Golovinsky prospekt); named Rustaveli in 1918; renovation and closure to traffic 2024-2026 (en Wikipedia)", [WP + "Rustaveli_Avenue"])
    avenue(["avenues"], lambda t: t.get("name:en") == "David Aghmashenebeli Avenue", "aghmashenebeli", 1851, 9999,
           {"name_en": "David Aghmashenebeli Avenue", "name_ru": "Проспект Давида Агмашенебели (Михайловская ул., в 1918-1988 Плеханова)", "name_ka": "დავით აღმაშენებლის გამზირი"},
           "already existed in 1851 as Mikheil Street (en Wikipedia); Plekhanov Avenue 1918-1988; major rehabilitation since 2010. The date of construction is not given in the page; 1851 is the earliest date found", [WP + "David_Agmashenebeli_Avenue"])
    avenue(["avenues"], lambda t: t.get("name:en") == "Ilia Chavchavadze Avenue", "chavchavadze", 1930, 9999,
           {"name_en": "Ilia Chavchavadze Avenue", "name_ru": "Проспект Ильи Чавчавадзе (в 1935-1957 ул. Нико Марра)", "name_ka": "ილია ჭავჭავაძის გამზირი"},
           "construction began in the 1930s (infobox, en Wikipedia); named after Niko Marr 1935-1957", [WP + "Ilia_Chavchavadze_Avenue"])
    # ---------------- main roads (2026-11-22): the avenues, the main streets and the highways of the lists of tools/mainroads_task.py, with the year of the ENCYCLOPEDIA of 2008
    # (data/cache/mainroads_verified.json: the phrase "originated ...", kind "avenue": the sign of an avenue) or the earliest document of the article (mainroads_verified2.json: a plan, a list,
    # kind "road": a thin line, the year is the first mention, not the origin). The roads without a year are not drawn (see sources.md). Geometry: data/raw/osm_roads/main_roads.json
    # (tools/fetch_main_roads_osm.py), only the ways inside the present city boundary (the middle of a way), so the highways end at the border.
    ring = json.load(open(os.path.join(OUT, "admin.json"), encoding="utf-8"))["features"][0]["geometry"]["coordinates"][0]

    def inside(x, y):
        c = False
        for i in range(len(ring) - 1):
            (x1, y1), (x2, y2) = ring[i], ring[i + 1]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c

    def mid_inside(g):
        return inside(sum(p["lon"] for p in g) / len(g), sum(p["lat"] for p in g) / len(g))
    def rdp(pts, tol=2.0):
        """Douglas-Peucker in metres (the first screen is limited in weight; 2 m is far below what the line width of the map shows)"""
        import math as _m
        k = _m.cos(_m.radians(41.7)) * 111320
        xy = [((x - pts[0][0]) * k, (y - pts[0][1]) * 111320) for x, y in pts]
        keep = [False] * len(pts)
        keep[0] = keep[-1] = True
        stack = [(0, len(pts) - 1)]
        while stack:
            i, j = stack.pop()
            (x1, y1), (x2, y2) = xy[i], xy[j]
            dx, dy = x2 - x1, y2 - y1
            n = _m.hypot(dx, dy) or 1e-9
            best, bi = 0, -1
            for m in range(i + 1, j):
                d = abs(dy * (xy[m][0] - x1) - dx * (xy[m][1] - y1)) / n
                if d > best:
                    best, bi = d, m
            if best > tol and bi > 0:
                keep[bi] = True
                stack += [(i, bi), (bi, j)]
        return [pts[i] for i in range(len(pts)) if keep[i]]
    def chain(lines):
        """the ways that meet end to end become one line (fewer points: the shared end point is stored once)"""
        lines = [list(l) for l in lines]
        done = False
        while not done:
            done = True
            for i in range(len(lines)):
                for j in range(len(lines)):
                    if i == j:
                        continue
                    a, b = lines[i], lines[j]
                    if a[-1] == b[0]:
                        lines[i] = a + b[1:]
                    elif a[-1] == b[-1]:
                        lines[i] = a + b[::-1][1:]
                    else:
                        continue
                    del lines[j]
                    done = False
                    break
                if not done:
                    break
        return lines
    mr_ways = json.load(open(os.path.join(ROOT, "data", "raw", "osm_roads", "main_roads.json"), encoding="utf-8"))["elements"]
    V1 = {x["key"]: x for x in json.load(open(os.path.join(ROOT, "data", "cache", "mainroads_verified.json"), encoding="utf-8"))["ok"]}
    V2 = {x["key"]: x for x in json.load(open(os.path.join(ROOT, "data", "cache", "mainroads_verified2.json"), encoding="utf-8"))["ok"]}
    BOOK = "Encyclopedia 'Tbilisi. Streets, avenues, squares' (2008), PDF p. %d: %s"
    HWC = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified"}
    MAIN = {"tamar": (["Tamar Mepe Avenue"], "проспект Тамар Мепе", "Tamar Mepe Avenue", "თამარ მეფის გამზირი"),
            "moscow": (["Moscow Avenue"], "Московский проспект", "Moscow Avenue", "მოსკოვის გამზირი"),
            "vazha": (["Vazha-Pshavela Avenue"], "проспект Важа-Пшавела", "Vazha-Pshavela Avenue", "ვაჟა-ფშაველას გამზირი"),
            "pekini": (["Pekini Avenue"], "проспект Пекини", "Pekini Avenue", "პეკინის გამზირი"),
            "kakheti": (["Kakheti Highway"], "Кахетинское шоссе", "Kakheti Highway", "კახეთის გზატკეცილი"),
            "guramishvili": (["David Guramishvili Avenue"], "проспект Давида Гурамишвили", "David Guramishvili Avenue", "დავით გურამიშვილის გამზირი"),
            "dedoplis": (["Tsminda Ketevan Dedoflis Avenue"], "проспект Кетеван Дедоплис", "Ketevan Dedoplis Avenue", "წმინდა ქეთევან დედოფლის გამზირი"),
            "kostava": (["Merab Kostava Street"], "улица Мераба Костава", "Merab Kostava Street", "მერაბ კოსტავას ქუჩა"),
            "tsereteli": (["Akaki Tsereteli Avenue"], "проспект Акакия Церетели", "Akaki Tsereteli Avenue", "აკაკი წერეთლის გამზირი"),
            "melikishvili": (["Petre Melikishvili Avenue"], "проспект Петре Меликишвили", "Petre Melikishvili Avenue", "პეტრე მელიქიშვილის გამზირი"),
            "kazbegi": (["Alexander Kazbegi Avenue"], "проспект Александра Казбеги", "Alexander Kazbegi Avenue", "ალექსანდრე ყაზბეგის გამზირი"),
            "gorgasali": (["Vakhtang Gorgasali Street"], "улица Вахтанга Горгасали", "Vakhtang Gorgasali Street", "ვახტანგ გორგასალის ქუჩა"),
            "tsabadze": (["Giorgi Tsabadze Street"], "улица Георгия Цабадзе", "Giorgi Tsabadze Street", "გიორგი ცაბაძის ქუჩა")}
    n_main = {}
    for key, (osm_names, nru, nen, nka) in MAIN.items():
        v = V1.get(key) or V2.get(key)
        if not v:
            continue
        # an avenue sign only for the origin that names a year or a decade (or a part of the XX century); a century of the XIX or earlier gives a road from the first document of the article
        origin = key in V1 and (V1[key]["kind"] in ("year", "decade") or (V1[key]["kind"] == "century_part" and V1[key]["from"] >= 1900))
        v = V1[key] if origin else (V2.get(key) or V1[key])
        ways = [e for e in mr_ways if e["tags"].get("name:en") in osm_names and e["tags"].get("highway") in HWC and "geometry" in e and mid_inside(e["geometry"])]
        if origin:
            y0, note = v["from"], BOOK % (v["page"], v["quote"]) + " (the exact year is not given: the beginning of the period named; the sign of an avenue from this year)"
        else:
            y0, note = v["year"], BOOK % (v["page"], v["quote"]) + " (the first document named in the article, NOT the year of the origin; the street is drawn as a road from this year)"
        if ways:                     # one feature per road (MultiLineString): a feature per way would add half a megabyte to the first screen
            feats.append(feat({"type": "MultiLineString", "coordinates": [rdp(l) for l in chain(line(e["geometry"]) for e in ways)]}, id="main_" + key, kind="avenue" if origin else "road", y0=y0, name_en=nen, name_ru=nru,
                              name_ka=nka, note=note, src=[]))
        n_main[key] = len(ways)
    # the avenues already drawn (from the page of Wikipedia): the same ways as a road before the avenue (the first document of the encyclopedia)
    for key, y1 in (("rustaveli", 1840),):               # (Chavchavadze: the road of 1925 would last 5 years, only the avenue of 1930 is drawn)
        v = V2.get(key)
        if not v:
            continue
        old = [x for x in feats if str(x["properties"].get("id", "")).startswith(key + "_") and x["properties"]["kind"] == "avenue"]
        if old:
            p = dict(old[0]["properties"])
            p.update(id="road_" + key, kind="road", y0=v["year"], y1=y1, note=BOOK % (v["page"], v["quote"]) + " (the first document named in the article: a road on the line of the later avenue, drawn as a road until the avenue)")
            feats.append({"type": "Feature", "geometry": {"type": "MultiLineString", "coordinates": [rdp(l) for l in chain(x["geometry"]["coordinates"] for x in old)]}, "properties": p})
        n_main[key + "_road"] = len(old)
    print("main roads (ways inside the city):", n_main)
    # ---------------- horse tram (konka) 1883-1910: only what ru.wikipedia says (the first line ran along Mikhailovsky = today's Aghmashenebeli Avenue); drawn on the avenue ways, so the endpoints are approximate
    for e in load("avenues"):
        if e["tags"].get("name:en") == "David Aghmashenebeli Avenue" and "geometry" in e:
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="konka_%d" % e["id"], kind="tram", y0=1883, y1=1910,
                              name_en="Horse tram (konka), Mikhailovsky Avenue line", name_ru="Конка (конный трамвай), линия по Михайловскому проспекту", name_ka="კონკა (ცხენის ტრამვაი)",
                              note="SCHEMATIC. ru.wikipedia: the first konka line (1883) ran along Mikhailovsky (today David Aghmashenebeli) Avenue between Vorontsov Square and the railway station and was soon extended to Erivan (Freedom) Square (year not stated); the konka ceased in 1910 (gauge 914 mm). Opening date: ru.wikipedia 10 March 1883, en.wikipedia 3 April 1883. The line is drawn on the whole avenue as mapped today, so the real ends differ; the Freedom Square extension and the 1904 line on Kirochnaya (Marjanishvili) Street are not drawn. Electric tram lines (from 25 December 1904 to 4 December 2006) are not drawn: no open source gives their streets.",
                              src=["https://ru.wikipedia.org/wiki/%D0%A2%D0%B1%D0%B8%D0%BB%D0%B8%D1%81%D1%81%D0%BA%D0%B8%D0%B9_%D1%82%D1%80%D0%B0%D0%BC%D0%B2%D0%B0%D0%B9", WP + "Trams_in_Tbilisi"]))
    # ---------------- bridges (only those with dates found)
    for e in load("bridges"):
        t = e["tags"]
        nm = t.get("name:en") or ""
        if nm == "Nikoloz Baratashvili Bridge":
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="br%d" % e["id"], kind="bridge", name_en="Baratashvili Bridge", name_ru="Мост Бараташвили", name_ka="ბარათაშვილის ხიდი",
                              y0=1966, note="built in 1966 in place of the dismantled Mukhrani Bridge (the year of the dismantling is not given)", src=[WP + "Baratashvili_Bridge"]))
        if nm == "Bridge of Peace":
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="br%d" % e["id"], kind="bridge", name_en="Bridge of Peace", name_ru="Мост Мира", name_ka="მშვიდობის ხიდი",
                              y0=2010, note="officially opened 6 May 2010", src=[WP + "Bridge_of_Peace"]))
    # ---------------- tram network by street (route lists of 1962 and 1986 from ka.wikipedia, closures from the lists of routes of 2000, 2003, 2005 on ru.wikipedia; see data/tram_verified.json)
    # Each street is drawn over its whole OSM length, so the drawn track is longer than the real one; streets not found in OSM under these names are missing (gaps).
    TRAM_OSM = {
        "dadiani": ["Tsotne Dadiani Street"], "eristavi": ["Tornike Eristavi Street"], "tsereteli": ["Akaki Tsereteli Avenue"], "tsabadze": ["Giorgi Tsabadze Street"],
        "mghvdeli": ["Tevdore Mghvdeli Street"], "abastumani": ["Abastumani Street"], "tsinam": ["Mikheil Tsinamdzghvrishvili Street"], "khudadov": ["Nikoloz Khudadov Street"],
        "tseronisi": ["Tseronisi Street"], "akhtala": ["Akhtala Street"], "kakhiani": ["Nikoloz Kakhiani Street"], "lotkini": ["Lotkini Street (now Vasil Tamarashvili Street in OSM)"],
        "guramishvili": ["David Guramishvili Avenue"], "sarajishvili": ["David Sarajishvili Street"], "libani": ["Libani Street"], "moscow": ["Moscow Avenue"],
        "navtlughi": ["Navtlughi Street"], "salosi": ["Beri Gabriel Salosi Avenue"], "purtseladze": ["Anton Purtseladze Street"], "atoneli": ["Giorgi Atoneli Street"],
        "gogiberidze": ["Mose Gogiberidze Street"], "javakhishvili": ["Ivane Javakhishvili Street"], "sheshelidze": ["Tengiz Sheshelidze Street"],
        "khizanishvili": ["Omar Khizanishvili Street"], "beliashvili": ["Akaki Beliashvili Street"], "alley": ["David Aghmashenebeli Alley"], "pirosmani": ["Niko Pirosmani Street"],
        "kostava": ["Merab Kostava Street"], "melikishvili": ["Petre Melikishvili Avenue"], "chavchavadze": ["Ilia Chavchavadze Avenue"], "tamar": ["Tamar Mepe Avenue"],
        "khetagurov": ["Kosta Khetagurov Street"], "asc": ["Nikoloz Baratashvili Ascent"], "dedoplis": ["Tsminda Ketevan Dedoflis Avenue"], "barisakhos": ["Barisakho Street"],
        "anapa": ["Anapis 414 Divizia Street"], "zghvi": ["Tbilisi Zghvi Street"],
        "uridia": ["Revaz Uridia Street"], "makhaldiani": ["Vakhtang Makhaldiani Lane"], "rkinigza": ["Rkinigza Street"], "holbrooke": ["Richard Holbrooke Street"], "khmelnitsky": ["Bogdan Khmelnitski Street"],
    }
    # Ways picked by hand (2026-11-22, see sources.md): the old Lotkini Street is the present Alexi-Meskhishvili Street of the encyclopedia of 2008 (PDF p. 15: from Likani Street to Lotkini Gorge);
    # in OSM the stretch from the junction with Kakhiani Street to the start of Lotkini Gorge is named Vasil Tamarashvili Street (ways 1134264978, 1293979096). Lotkini Mta Street is another street higher up the hill.
    LOTKINI_WAYS = {1134264978, 1293979096}
    # Streets drawn only where the route of the list runs (the street itself is longer): route 2 of 1986 = Uridia (east to the junction at 44.82757) - the short link of Khudadov (44.82757 -> 44.83006) - Tseronisi back west to Akhtala
    # (the ways join end to end); route 6 / route 4 of 1962 reach Kakhiani Street at its crossing with Uridia (node 44.80878, 41.72961), so the stretch of Kakhiani south of it is not drawn.
    TRAM_ONLY = {"khudadov": {1134264964, 1133504974, 1484539403}, "kakhiani": {487811705}}
    TRAM_SKIP = {"tseronisi": {58502835}}                    # the way west of the junction with Akhtala Street
    CHECK_URBAN = {"alley"}      # streets whose pieces in open country are dropped (checked on the topographic map and the outlines of the built-up area, 2026-11-19)
    NOT_MATCHED = {"zghvi"}                                  # streets with no usable OSM way: nothing is drawn (Tbilisi Sea Ascent != Tbilisi Zghvi Street at 44.840, 41.765)
    R1986 = {1: "dadiani eristavi tsereteli tsabadze mghvdeli abastumani tsinam", 2: "dadiani uridia khudadov tseronisi akhtala", 3: "tsereteli eristavi guramishvili zghvi anapa",
             4: "dadiani guramishvili zghvi anapa", 5: "purtseladze atoneli gogiberidze javakhishvili tsinam tsereteli", 6: "dadiani makhaldiani rkinigza uridia kakhiani lotkini",
             7: "moscow dedoplis navtlughi holbrooke salosi khmelnitsky", 8: "eristavi guramishvili sheshelidze khizanishvili", 9: "tsereteli beliashvili alley",
             10: "purtseladze atoneli gogiberidze javakhishvili tsinam tsereteli beliashvili alley", 11: "dadiani guramishvili sarajishvili libani barisakhos",
             12: "eristavi guramishvili sarajishvili libani barisakhos"}
    R1962 = {1: "abastumani tsinam tamar kostava melikishvili chavchavadze", 3: "abastumani tsereteli eristavi guramishvili sarajishvili",
             4: "purtseladze atoneli gogiberidze javakhishvili tsinam abastumani pirosmani dadiani kakhiani lotkini", 6: "abastumani pirosmani dadiani eristavi tsereteli",
             7: "tamar tsinam javakhishvili khetagurov asc dedoplis navtlughi salosi", 8: "tamar tsinam javakhishvili khetagurov asc dedoplis moscow",
             9: "asc dedoplis navtlughi salosi", 10: "purtseladze atoneli gogiberidze javakhishvili tsinam tsereteli", 11: "abastumani pirosmani dadiani guramishvili sarajishvili",
             12: "tsereteli tsinam tamar kostava melikishvili chavchavadze", 14: "abastumani pirosmani dadiani guramishvili", 15: "asc dedoplis moscow"}
    END1986 = {12: 2007, 1: 2005, 7: 2005, 11: 2005, 2: 2003, 3: 2003, 4: 2003, 6: 2003, 5: 2000, 8: 2000, 9: 2000, 10: 2000}   # first year WITHOUT the route (lists of 2000, 2003, 2005; the end of 2006)
    tram_iv = {}
    for r, st in R1962.items():
        for k in st.split():
            tram_iv.setdefault(k, []).append((1962, 1986))
    for r, st in R1986.items():
        for k in st.split():
            tram_iv.setdefault(k, []).append((1986, END1986[r]))
    ways_tram = {}
    extra = os.path.join(RAW, "tram_streets_extra.json")
    for e in load("tram_streets") + (load("tram_streets_extra") if os.path.exists(extra) else []):
        if "geometry" in e:
            ways_tram.setdefault(e["tags"].get("name:en"), []).append(e)
    rc = json.load(open(os.path.join(ROOT, "data", "raw", "osm_roads", "roads_center.json"), encoding="utf-8"))["elements"]
    for e in rc:
        if e.get("id") in LOTKINI_WAYS and "geometry" in e:
            e = dict(e, tags=dict(e["tags"], **{"name:en": "Lotkini Street (now Vasil Tamarashvili Street in OSM)"}))
            ways_tram.setdefault(e["tags"]["name:en"], []).append(e)
    miss = []
    dropped_tram = []
    konka_core = [c for f in feats if str(f["properties"].get("id", "")).startswith("konka_") for c in f["geometry"]["coordinates"]]
    for k, ivs in tram_iv.items():
        ivs = sorted(set(ivs))
        merged = []
        for a0, b0 in ivs:
            if merged and a0 <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b0)
            else:
                merged.append([a0, b0])
        ws = [w for nm in TRAM_OSM[k] for w in ways_tram.get(nm, [])]
        if k in TRAM_ONLY:
            dropped_tram.extend((k + " (not on the route)", w["id"], way_len(w["geometry"])) for w in ws if w["id"] not in TRAM_ONLY[k])
            ws = [w for w in ws if w["id"] in TRAM_ONLY[k]]
        if k in TRAM_SKIP:
            dropped_tram.extend((k + " (not on the route)", w["id"], way_len(w["geometry"])) for w in ws if w["id"] in TRAM_SKIP[k])
            ws = [w for w in ws if w["id"] not in TRAM_SKIP[k]]
        if not ws:
            miss.append(k)
        if k in NOT_MATCHED:                                   # no street of this name lies where the routes of the lists run: nothing is drawn rather than a wrong street
            dropped_tram.extend((k, w["id"], way_len(w["geometry"])) for w in ws)
            ws = []
        drop = set(far_pieces(ws, core=konka_core)) if ws else set()           # other streets with the same name far away (Tskneti, Okrokana, the north, the east)
        for i in sorted(drop):
            dropped_tram.append((k, ws[i]["id"], way_len(ws[i]["geometry"])))
        ws = [w for i, w in enumerate(ws) if i not in drop]
        if k in CHECK_URBAN and ws:
            out = set(outside_built_up(ws, merged[0][0]))
            for i in sorted(out):
                dropped_tram.append((k + " (outside the built-up area)", ws[i]["id"], way_len(ws[i]["geometry"])))
            ws = [w for i, w in enumerate(ws) if i not in out]
        r62 = ", ".join(str(r) for r in sorted(r for r, st in R1962.items() if k in st.split()))       # the numbers of the routes that name the street in the list of 1962 / of 1986
        r86 = ", ".join(str(r) for r in sorted(r for r, st in R1986.items() if k in st.split()))
        more = {}
        if r62:
            more["r62"] = r62
        if r86:
            more["r86"] = r86
        for w in ws:
            for a0, b0 in merged:
                feats.append(feat({"type": "LineString", "coordinates": line(w["geometry"])}, id="tramnet_%s_%d_%d" % (k, w["id"], a0), kind="tram", y0=a0, y1=b0, **more,
                                  name_en="Tram street (routes of the ka.wikipedia lists)", name_ru="Улица трамвайных маршрутов (по спискам ka.wikipedia)", name_ka="ტრამვაის მარშრუტების ქუჩა",
                                  note="SCHEMATIC. The street is drawn over its whole length in OpenStreetMap; the tram did not necessarily run along all of it. Years: the route lists of 1962 and 1986 (ka.wikipedia) and the lists of routes of 2000 (8 routes), 2003 (4 routes), 2005 (route 12) and the closing on 4 December 2006 (ru.wikipedia): between the lists the state is not known. Several streets of the routes are missing (no matching way in OSM). Pieces of a street that lie far from its main line (other streets with the same name) and, for some streets, pieces in open country outside the built-up area of the time are left out; the real tracks are not known (checked 2026-11-19, see sources.md).",
                                  src=["https://ka.wikipedia.org/wiki/%E1%83%97%E1%83%91%E1%83%98%E1%83%9A%E1%83%98%E1%83%A1%E1%83%98%E1%83%A1_%E1%83%A2%E1%83%A0%E1%83%90%E1%83%9B%E1%83%95%E1%83%90%E1%83%98", "https://ru.wikipedia.org/wiki/%D0%A2%D0%B1%D0%B8%D0%BB%D0%B8%D1%81%D1%81%D0%BA%D0%B8%D0%B9_%D1%82%D1%80%D0%B0%D0%BC%D0%B2%D0%B0%D0%B9"]))
    print("tram network streets:", len(tram_iv), "missing in OSM:", miss)
    print("tram pieces dropped (the same street name far from the main line):", len(dropped_tram), "total m:", sum(d[2] for d in dropped_tram))
    for d in dropped_tram:
        print("   dropped", d)
    # ---------------- tram lines drawn on the 1913 plan (read by Gemini from gridded tiles, snapped to the red line by tools/snap_tram_1913.py); shown with the plan of 1913
    sp = os.path.join(ROOT, "data", "boundaries", "tram_1913_snapped.json")
    if os.path.exists(sp):
        meta = json.load(open(os.path.join(ROOT, "data", "warped", "tbilisi_1913.json"), encoding="utf-8"))
        (lon0, lat0), (lon1, _), (_, lat1) = meta["corners"][0], meta["corners"][1], meta["corners"][2]
        sw, sh = meta["size"]
        import math
        my = lambda la: math.log(math.tan(math.pi / 4 + math.radians(la) / 2))
        def pll(x, y):
            return [round(lon0 + (lon1 - lon0) * x / sw, 5), round(math.degrees(2 * math.atan(math.exp(my(lat0) + (my(lat1) - my(lat0)) * y / sh)) - math.pi / 2), 5)]
        nline = 0
        for o in json.load(open(sp, encoding="utf-8")):
            if len(o["path"]) < 4:
                continue
            nline += 1
            feats.append(feat({"type": "LineString", "coordinates": [pll(x, y) for x, y in o["path"]]}, id="tram1913_" + o["id"], kind="tram", prec=1, y0=1913, y1=1923,
                              name_en="Tram line on the plan of 1913", name_ru="Трамвайная линия на плане 1913 года", name_ka="ტრამვაის ხაზი 1913 წლის გეგმაზე",
                              note="DRAWN ON THE 1913 PLAN (legend: 'line of the tram'). The points were read from the plan by an AI (Gemini) and snapped to the printed red line by a program, then checked by eye; the line can deviate by tens of metres and some stretches (for example in Avlabari and along the river) are uncertain. Streets as printed on the plan: " + "; ".join(o.get("streets") or []) + ". Years: the plan is of 1913; the lines are shown while the plan is shown (1913-1922).",
                              src=["https://commons.wikimedia.org/wiki/File:Map_of_Tbilisi_1913.jpg"]))
        print("tram lines of the 1913 plan:", nline)
    # ---------------- other Kura bridges (years from ru.wikipedia articles, read 2026-11-18; the position is the present bridge, older bridges stood close by)
    br_ways = {}
    for fn in ("bridges", "bridges_all"):
        for e in load(fn):
            br_ways[e["id"]] = e
    def bridge(ids, fid, ne, nr, nk, y0, note, src, **yy):
        n = 0
        for i in ids:
            e = br_ways.get(i)
            if not e or "geometry" not in e:
                continue
            n += 1
            feats.append(feat({"type": "LineString", "coordinates": line(e["geometry"])}, id="%s_%d" % (fid, i), kind="bridge", name_en=ne, name_ru=nr, name_ka=nk, y0=y0, note=note, src=[RUW + src], **yy))
        print(fid, "ways:", n, "of", len(ids))
    RUW = "https://ru.wikipedia.org/wiki/"
    bridge([371166394], "aragv_old", "300 Aragvians Bridge (earlier bridges)", "Мост 300 арагвинцев (прежние мосты)", "სამასი არაგველის ხიდი (ძველი)", 1851,
           "wooden arch bridge of 1851 (collapsed 1869), iron bridge of 1882 (stood until 1952); known then as the Mnatsakanov bridge", "%D0%9C%D0%BE%D1%81%D1%82_300_%D0%B0%D1%80%D0%B0%D0%B3%D0%B2%D0%B8%D0%BD%D1%86%D0%B5%D0%B2", y1=1869, y2=1882, y3=1952)
    bridge([371166394], "aragv", "300 Aragvians Bridge", "Мост 300 арагвинцев", "სამასი არაგველის ხიდი", 1956,
           "present reinforced-concrete bridge on the Ortachala dam, built 1952-1956", "%D0%9C%D0%BE%D1%81%D1%82_300_%D0%B0%D1%80%D0%B0%D0%B3%D0%B2%D0%B8%D0%BD%D1%86%D0%B5%D0%B2")
    bridge([370148693, 1537993938], "metekhi", "Metekhi Bridge", "Мост Метехи", "მეტეხის ხიდი", 1805,
           "the Metekhi and Avlabari bridges were built side by side in 1805, rebuilt in 1821, 1843, 1870; in 1950-1951 both were replaced by the present single reinforced-concrete bridge (the crossing is older, the infobox says 8th century)", "%D0%9C%D0%BE%D1%81%D1%82_%D0%9C%D0%B5%D1%82%D0%B5%D1%85%D0%B8")
    bridge([159460389, 1329889793, 1329889794], "galaktion", "Galaktion Tabidze Bridge (Vera Bridge)", "Мост Галактиона Табидзе (Верийский мост)", "გალაკტიონის ხიდი", 1885,
           "opened 10 February 1885 as the Vera bridge; in 1951-1953 rebuilt; Stalin bridge in the Soviet period, original name restored 1991, the present name since 2001", "%D0%9C%D0%BE%D1%81%D1%82_%D0%93%D0%B0%D0%BB%D0%B0%D0%BA%D1%82%D0%B8%D0%BE%D0%BD%D0%B0_%D0%A2%D0%B0%D0%B1%D0%B8%D0%B4%D0%B7%D0%B5")
    bridge([304966624], "saarbr", "Saarbrucken Bridge (Big Mikhailovsky Bridge)", "Саарбрюкенский мост (Большой Михайловский)", "ზაარბრიუკენის ხიდი", 1853,
           "opened 8 November 1853; widened 1884 and 1962; named after Saarbrucken in 1994 (Commons name: Guram Dochanashvili Bridge)", "%D0%A1%D0%B0%D0%B0%D1%80%D0%B1%D1%80%D1%8E%D0%BA%D0%B5%D0%BD%D1%81%D0%BA%D0%B8%D0%B9_%D0%BC%D0%BE%D1%81%D1%82")
    bridge([174304320], "dry", "Dry Bridge", "Сухой мост", "მშრალი ხიდი", 1851,
           "built 1848-1851 (architect Scudieri, ru.wikipedia); called Dry after 1933 when the Kura side channel under it was filled in; capital repair 1962", "%D0%A1%D1%83%D1%85%D0%BE%D0%B9_%D0%BC%D0%BE%D1%81%D1%82")
    bridge([373877209], "tamar", "Queen Tamar Bridge", "Мост царицы Тамар", "თამარ მეფის ხიდი", 1935,
           "built 1932-1935 as the Chelyuskintsev bridge; renamed after Queen Tamar in 1989", "%D0%9C%D0%BE%D1%81%D1%82_%D1%86%D0%B0%D1%80%D0%B8%D1%86%D1%8B_%D0%A2%D0%B0%D0%BC%D0%B0%D1%80_(%D0%A2%D0%B1%D0%B8%D0%BB%D0%B8%D1%81%D0%B8)")
    bridge([481615266, 481615268], "shalik", "Shota Shalikashvili Bridge (Didube Bridge)", "Мост Шота Шаликашвили (Дидубийский)", "შოთა შალიკაშვილის ხიდი", 1954,
           "built 1953-1954 where a ferry had crossed; renamed in 1990", "%D0%9C%D0%BE%D1%81%D1%82_%D0%A8%D0%BE%D1%82%D0%B0_%D0%A8%D0%B0%D0%BB%D0%B8%D0%BA%D0%B0%D1%88%D0%B2%D0%B8%D0%BB%D0%B8")
    bridge([25626513, 47657170], "gulia", "Dimitri Gulia Bridge", "Мост Дмитрия Гулиа", "დიმიტრი გულიას ხიდი", 1961,
           "built 1959-1961; also called the Aqueduct bridge", "%D0%9C%D0%BE%D1%81%D1%82_%D0%94%D0%BC%D0%B8%D1%82%D1%80%D0%B8%D1%8F_%D0%93%D1%83%D0%BB%D0%B8%D0%B0")
    bridge([77628182, 1460513573], "vakhushti", "Vakhushti Bagrationi Bridge", "Мост Вахушти Багратиони", "ვახუშტი ბაგრატიონის ხიდი", 1976,
           "built 1974-1976", "%D0%9C%D0%BE%D1%81%D1%82_%D0%92%D0%B0%D1%85%D1%83%D1%88%D1%82%D0%B8_%D0%91%D0%B0%D0%B3%D1%80%D0%B0%D1%82%D0%B8%D0%BE%D0%BD%D0%B8")
    json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "transport.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    print("features:", len(feats), Counter(f["properties"]["kind"] for f in feats))


if __name__ == "__main__":
    main()
