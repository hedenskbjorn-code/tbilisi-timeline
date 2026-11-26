"""Build precomputed client search index site/data/search_index.json for MiniSearch.

Combines all layers (including lazy places, sculptures, plaques, modernism, plus architects,
sculptors, folk names, translated addresses, and old street names) so client search works across
the entire dataset with zero first-screen weight penalty.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
OUT = DATA / "search_index.json"


def translate_monument_fields(pairs: list[tuple[str, str]]) -> list[tuple[str, str, str, str]]:
    """Translate Georgian addresses and raw dates via site/translit.js so index matches runtime GeoTr."""
    if not pairs:
        return []
    js = (
        "const fs=require('fs'), G=require('./site/translit.js');"
        "G.setDict(JSON.parse(fs.readFileSync('./site/data/names_i18n.json','utf8')));"
        "const inp=JSON.parse(fs.readFileSync(0,'utf8'));"
        "process.stdout.write(JSON.stringify(inp.map(([a,d])=>[a?(G.address(a,'ru')||''):'',a?(G.address(a,'en')||''):'',d?(G.date(d,'ru')||''):'',d?(G.date(d,'en')||''):''])));"
    )
    r = subprocess.run(["node", "-e", js], input=json.dumps(pairs, ensure_ascii=False), capture_output=True, text=True, encoding="utf-8", cwd=ROOT, check=True)
    return [tuple(x) for x in json.loads(r.stdout)]


def load(name: str):
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def join_uniq(parts) -> str:
    seen = set()
    out = []
    for p in parts:
        s = str(p or "").strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return " | ".join(out)


def compact_i18n(ru: str, en: str, ka: str):
    ru, en, ka = str(ru or "").strip(), str(en or "").strip(), str(ka or "").strip()
    if not (ru or en or ka):
        return None
    if ru == en == ka:
        return ru
    return [ru, en, ka]


def main() -> int:
    docs = []
    i18n = load("names_i18n.json") or {"names": {}, "streets": {}}
    names_dict = i18n.get("names", {})
    catalog = load("catalog.json") or {"items": [], "by_ref": {}}
    cat_by_ref = catalog.get("by_ref", {})

    # Collect per-ref records for catalog-backed layers first
    ref_docs = {}

    # 1. Register monuments
    mon = load("monuments.json")
    if mon:
        feats = mon.get("features", [])
        tr_fields = translate_monument_fields([
            (f.get("properties", {}).get("address") or "", f.get("properties", {}).get("raw_date") or "")
            for f in feats
        ])
        for f, (ad_ru, ad_en, dt_ru, dt_en) in zip(feats, tr_fields):
            p = f.get("properties", {})
            ka = p.get("name") or ""
            d = names_dict.get(ka, {})
            ru = d.get("ru") or ka
            en = d.get("en") or ka
            wp_names = [x.split(":", 1)[1] for x in str(p.get("wp") or "").split("|") if ":" in x]
            ad_ka = p.get("address") or ""
            y0, y1, ye = p.get("y0"), p.get("y1"), p.get("ye")
            if p.get("prec") == "exact" and ye is not None:
                dt = str(ye)
            elif p.get("raw_date"):
                dt = compact_i18n(dt_ru or p.get("raw_date"), dt_en or p.get("raw_date"), p.get("raw_date"))
            elif y0 is not None and y1 is not None and y0 != y1:
                dt = f"{y0}\u2013{y1}"
            elif ye is not None:
                dt = str(ye)
            else:
                dt = None
            ref = f"o:{p.get('id')}"
            ref_docs[ref] = {
                "id": ref,
                "k": "rl" if p.get("fn") == "religious" else "o",
                "n_parts": [ru, en, ka, *wp_names],
                "ex_parts": [ad_ka, ad_ru, ad_en, p.get("fo"), p.get("cls")],
                "y": ye,
                "l": [ru, en, ka],
                "ll": f.get("geometry", {}).get("coordinates"),
                "ad": compact_i18n(ad_ru or ad_ka, ad_en or ad_ka, ad_ka),
                "tp": f"o:{p.get('cls')}" if p.get("cls") else None,
                "dt": dt,
            }

    # 4. Science, education, museums
    for kind, fname in [("sc", "science.json"), ("ed", "education.json"), ("mu", "museums.json")]:
        arr = load(fname) or []
        for c in arr:
            nm = c.get("name", {})
            ref = f"{kind}:{c.get('id')}"
            dt = c.get("built") or c.get("founded") or (c.get("from") if not c.get("undated") else None)
            ref_docs[ref] = {
                "id": ref,
                "k": kind,
                "n_parts": [nm.get("ru"), nm.get("en"), nm.get("ka")],
                "ex_parts": [c.get("founded"), c.get("built"), c.get("from"), c.get("kind")],
                "y": c.get("from"),
                "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
                "ll": [c.get("lon"), c.get("lat")],
                "ad": None,
                "tp": f"{kind}:{c.get('kind')}" if c.get("kind") else None,
                "dt": str(dt) if dt is not None else None,
            }

    # 5. Religious (curated + OSM)
    for r in (load("religious.json") or []):
        nm = r.get("name", {})
        ref = f"rl:{r.get('id')}"
        ref_docs[ref] = {
            "id": ref,
            "k": "rl",
            "n_parts": [nm.get("ru"), nm.get("en"), nm.get("ka")],
            "ex_parts": [r.get("date"), r.get("rel")],
            "y": r.get("from"),
            "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
            "ll": [r.get("lon"), r.get("lat")],
            "ad": None,
            "tp": f"rl:{r.get('rel')}" if r.get("rel") else None,
            "dt": str(r.get("date")) if r.get("date") else (str(r.get("from")) if r.get("from") is not None and not r.get("undated") else None),
        }

    # Merge catalog-linked refs into one search document per canonical cat:... object
    KN_PRIO = {"rl": 0, "mu": 1, "ed": 2, "sc": 3, "o": 4}
    used_refs = set()
    for it in catalog.get("items", []):
        refs = [r for r in it.get("refs", []) if r in ref_docs]
        if not refs:
            continue
        used_refs.update(refs)
        prim = ref_docs[it["primary"]] if it.get("primary") in ref_docs else ref_docs[refs[0]]
        best_k = min((ref_docs[r]["k"] for r in refs), key=lambda k: KN_PRIO.get(k, 9))
        # Prefer curated name (mu/rl/ed/sc) over raw register name when linked, keeping all names in n
        l_src = next((ref_docs[r] for r in refs if r.split(":")[0] in ("rl", "mu", "ed", "sc") and any(ref_docs[r]["l"])), prim)
        ad = next((ref_docs[r]["ad"] for r in refs if ref_docs[r]["ad"]), None)
        tp = next((ref_docs[r]["tp"] for r in refs if ref_docs[r]["k"] == best_k and ref_docs[r]["tp"]), prim.get("tp"))
        dt = next((ref_docs[r]["dt"] for r in refs if ref_docs[r]["dt"]), None)
        if it.get("phases"):
            # For multi-phase monuments, show combined phases/years if available
            dt = dt or prim.get("dt")
        n_all = []
        ex_all = []
        for r in refs:
            n_all.extend(ref_docs[r]["n_parts"])
            ex_all.extend(ref_docs[r]["ex_parts"])
        doc = {
            "id": it["id"],
            "k": best_k,
            "n": join_uniq(n_all),
            "ex": join_uniq(ex_all),
            "y": prim.get("y"),
            "l": l_src["l"],
            "ll": prim.get("ll"),
        }
        if ad:
            doc["ad"] = ad
        if tp:
            doc["tp"] = tp
        if dt:
            doc["dt"] = dt
        docs.append(doc)

    # Any non-cataloged refs (if any) + OSM religious (which are not in catalog.json)
    for ref, rd in ref_docs.items():
        if ref in used_refs:
            continue
        doc = {"id": ref, "k": rd["k"], "n": join_uniq(rd["n_parts"]), "ex": join_uniq(rd["ex_parts"]), "y": rd["y"], "l": rd["l"], "ll": rd["ll"]}
        if rd["ad"]:
            doc["ad"] = rd["ad"]
        if rd["tp"]:
            doc["tp"] = rd["tp"]
        if rd["dt"]:
            doc["dt"] = rd["dt"]
        docs.append(doc)

    for r in ((load("religious_osm.json") or {}).get("items") or []):
        nm = r.get("name", {})
        doc = {
            "id": f"rl:{r.get('id')}",
            "k": "rl",
            "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
            "ex": join_uniq([r.get("date"), r.get("rel")]),
            "y": r.get("from"),
            "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
            "ll": [r.get("lon"), r.get("lat")],
        }
        if r.get("rel"):
            doc["tp"] = f"rl:{r.get('rel')}"
        if r.get("date"):
            doc["dt"] = str(r.get("date"))
        docs.append(doc)

    # 2. History events
    ev = load("history_events.json")
    if ev:
        for idx, e in enumerate(ev.get("events", [])):
            doc = {
                "id": f"e:{idx}",
                "n": join_uniq([e.get("ru"), e.get("en"), e.get("ka")]),
                "ex": join_uniq([e.get("date"), e.get("year"), e.get("cat")]),
                "y": e.get("year"),
                "l": [e.get("ru") or "", e.get("en") or "", e.get("ka") or ""],
            }
            if e.get("cat"):
                doc["tp"] = f"e:{e.get('cat')}"
            if e.get("date"):
                doc["dt"] = str(e.get("date"))
            docs.append(doc)

    # 3. Rulers & states
    rul = load("rulers.json")
    if rul:
        for u in rul.get("rulers", []) + rul.get("states", []):
            nm = u.get("name", {})
            ti = u.get("title", {})
            doc = {
                "id": f"u:{u.get('id')}",
                "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
                "ex": join_uniq([ti.get("ru"), ti.get("en"), ti.get("ka"), int(u["from"]) if u.get("from") is not None else None]),
                "y": int(u["from"]) if u.get("from") is not None else None,
                "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
            }
            if u.get("from") is not None and u.get("to") is not None:
                doc["dt"] = f"{int(u['from'])}\u2013{int(u['to'])}"
            docs.append(doc)

    # 6. Streets (current + all historical names)
    stn = load("street_names.json")
    if stn:
        for st in stn.get("streets", []):
            now = st.get("now", {})
            old = []
            for iv in st.get("iv", []):
                if len(iv) > 2 and isinstance(iv[2], dict):
                    old.extend([iv[2].get("ru"), iv[2].get("en"), iv[2].get("ka")])
            for u in st.get("undated") or []:
                if isinstance(u, dict):
                    old.extend([u.get("ru"), u.get("en"), u.get("ka")])
            key = st.get("geom") or now.get("en")
            docs.append({
                "id": f"st:{key}",
                "n": join_uniq([now.get("ru"), now.get("en"), now.get("ka")]),
                "ex": join_uniq(old),
                "l": [now.get("ru") or "", now.get("en") or "", now.get("ka") or ""],
            })

    # 7. Metro stations
    tr = load("transport.json")
    if tr:
        for f in tr.get("features", []):
            p = f.get("properties", {})
            if p.get("kind") == "metro_station" and p.get("id"):
                docs.append({
                    "id": f"ms:{p.get('id')}",
                    "n": join_uniq([p.get("name_ru"), p.get("name_en"), p.get("name_ka")]),
                    "ex": "metro метро მეტრო",
                    "y": p.get("y0"),
                    "l": [p.get("name_ru") or "", p.get("name_en") or "", p.get("name_ka") or ""],
                    "ll": f.get("geometry", {}).get("coordinates"),
                })

    # 8. Places (lazy layer)
    pl = load("places.json")
    if pl:
        for c in pl.get("items", []):
            nm = c.get("n", {})
            fk = [v for k in ("w", "o", "al") if isinstance(c.get(k), dict) for v in c[k].values()]
            for fo in c.get("f") or []:
                if isinstance(fo, dict) and isinstance(fo.get("n"), dict):
                    fk.extend(fo["n"].values())
            docs.append({
                "id": f"pl:{c.get('id')}",
                "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
                "ex": join_uniq(fk + [c.get("k")]),
                "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
                "ll": [c.get("lon"), c.get("lat")],
            })

    # 9. Sculptures, Plaques, Modernism (lazy layers, including architects, sculptors & folk names)
    for prefix, fname in [("mn", "sculptures.json"), ("pq", "plaques.json"), ("md", "modernism.json")]:
        obj = load(fname)
        if not obj:
            continue
        for c in obj.get("items", []):
            nm = c.get("n", {})
            if not any([nm.get("ru"), nm.get("en"), nm.get("ka")]):
                continue
            sc = c.get("sc")
            sc_vals = list(sc.values()) if isinstance(sc, dict) else [sc]
            fk = list(c.get("w", {}).values()) if isinstance(c.get("w"), dict) else []
            for fo in c.get("f") or []:
                if isinstance(fo, dict) and isinstance(fo.get("n"), dict):
                    fk.extend(fo["n"].values())
            doc = {
                "id": f"{prefix}:{c.get('id')}",
                "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
                "ex": join_uniq(fk + sc_vals + [c.get("ar"), c.get("k")]),
                "y": c.get("y"),
                "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
                "ll": [c.get("lon"), c.get("lat")],
            }
            if c.get("k") or prefix == "pq":
                doc["tp"] = f"{prefix}:{'plaque' if prefix == 'pq' else c.get('k')}"
            if c.get("y") is not None:
                doc["dt"] = str(c.get("y"))
            docs.append(doc)

    # 10. Mtskheta & Armazi walking tour objects (lazy layer)
    MT_FROM = {
        "svet_wall": 1010, "svet_cathedral": 1010, "svet_pillar": 330, "svet_tombs": 401,
        "svet_sepulchre": 1301, "svet_palace": 1001, "antiokia": 301, "samtavro_monastery": 330,
        "samtavro_necropolis": 100, "bebristsikhe": 801, "pompey_bridge": 100, "armaziskhevi": 100,
        "armazi_monastery": 1178, "armazi_fortress": 1201, "bagineti": 100,
        "bagineti_queens_bath": 100, "bagineti_kings_bath": 100, "bagineti_six_apsed_temple": 100,
        "bagineti_wine_cellar": 100, "bagineti_bath": 100, "bagineti_six_column_hall": 100, "jvari": 545,
    }
    mt = load("mtskheta_tour.json")
    if mt:
        for part in mt.get("parts", []):
            for s in part.get("stops", []):
                nm = s.get("name", {})
                ad = s.get("address", {})
                yr = s.get("year", {})
                doc = {
                    "id": f"mt:{s.get('id')}",
                    "k": "mt",
                    "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
                    "ex": join_uniq([ad.get("ru"), ad.get("en"), ad.get("ka"), yr.get("ru"), yr.get("en"), yr.get("ka"), s.get("kind"), "Мцхета Mtskheta მცხეთა Армази Armazi არმაზი"]),
                    "y": MT_FROM.get(s.get("id"), 100),
                    "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
                    "ll": [s.get("lon"), s.get("lat")],
                }
                ad_c = compact_i18n(ad.get("ru"), ad.get("en"), ad.get("ka"))
                if ad_c:
                    doc["ad"] = ad_c
                dt_c = compact_i18n(yr.get("ru"), yr.get("en"), yr.get("ka"))
                if dt_c:
                    doc["dt"] = dt_c
                docs.append(doc)

    OUT.write_text(json.dumps(docs, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(docs)} docs ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
