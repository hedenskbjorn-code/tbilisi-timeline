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


def translate_addresses(addrs: list[str]) -> list[tuple[str, str]]:
    """Translate Georgian addresses via site/translit.js so index matches runtime GeoTr.address()."""
    if not addrs:
        return []
    js = (
        "const fs=require('fs'), G=require('./site/translit.js');"
        "G.setDict(JSON.parse(fs.readFileSync('./site/data/names_i18n.json','utf8')));"
        "const inp=JSON.parse(fs.readFileSync(0,'utf8'));"
        "process.stdout.write(JSON.stringify(inp.map(a=>[G.address(a,'ru')||'',G.address(a,'en')||''])));"
    )
    r = subprocess.run(["node", "-e", js], input=json.dumps(addrs, ensure_ascii=False), capture_output=True, text=True, encoding="utf-8", cwd=ROOT, check=True)
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


def main() -> int:
    docs = []
    i18n = load("names_i18n.json") or {"names": {}, "streets": {}}
    names_dict = i18n.get("names", {})

    # 1. Register monuments
    mon = load("monuments.json")
    if mon:
        feats = mon.get("features", [])
        tr_addrs = translate_addresses([f.get("properties", {}).get("address") or "" for f in feats])
        for f, (ad_ru, ad_en) in zip(feats, tr_addrs):
            p = f.get("properties", {})
            ka = p.get("name") or ""
            d = names_dict.get(ka, {})
            ru = d.get("ru") or ka
            en = d.get("en") or ka
            wp_names = [x.split(":", 1)[1] for x in str(p.get("wp") or "").split("|") if ":" in x]
            docs.append({
                "id": f"o:{p.get('id')}",
                "n": join_uniq([ru, en, ka, *wp_names]),
                "ex": join_uniq([p.get("address"), ad_ru, ad_en, p.get("fo"), p.get("cls")]),
                "y": p.get("ye"),
                "l": [ru, en, ka],
                "ll": f.get("geometry", {}).get("coordinates"),
            })

    # 2. History events
    ev = load("history_events.json")
    if ev:
        for idx, e in enumerate(ev.get("events", [])):
            docs.append({
                "id": f"e:{idx}",
                "n": join_uniq([e.get("ru"), e.get("en"), e.get("ka")]),
                "ex": join_uniq([e.get("date"), e.get("year"), e.get("cat")]),
                "y": e.get("year"),
                "l": [e.get("ru") or "", e.get("en") or "", e.get("ka") or ""],
            })

    # 3. Rulers & states
    rul = load("rulers.json")
    if rul:
        for u in rul.get("rulers", []) + rul.get("states", []):
            nm = u.get("name", {})
            ti = u.get("title", {})
            docs.append({
                "id": f"u:{u.get('id')}",
                "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
                "ex": join_uniq([ti.get("ru"), ti.get("en"), ti.get("ka"), int(u["from"]) if u.get("from") is not None else None]),
                "y": int(u["from"]) if u.get("from") is not None else None,
                "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
            })

    # 4. Science, education, museums
    for kind, fname in [("sc", "science.json"), ("ed", "education.json"), ("mu", "museums.json")]:
        arr = load(fname) or []
        for c in arr:
            nm = c.get("name", {})
            docs.append({
                "id": f"{kind}:{c.get('id')}",
                "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
                "ex": join_uniq([c.get("founded"), c.get("built"), c.get("from"), c.get("kind")]),
                "y": c.get("from"),
                "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
                "ll": [c.get("lon"), c.get("lat")],
            })

    # 5. Religious (curated + OSM)
    rel = (load("religious.json") or []) + ((load("religious_osm.json") or {}).get("items") or [])
    for r in rel:
        nm = r.get("name", {})
        docs.append({
            "id": f"rl:{r.get('id')}",
            "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
            "ex": join_uniq([r.get("date"), r.get("rel")]),
            "y": r.get("from"),
            "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
            "ll": [r.get("lon"), r.get("lat")],
        })

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
            docs.append({
                "id": f"{prefix}:{c.get('id')}",
                "n": join_uniq([nm.get("ru"), nm.get("en"), nm.get("ka")]),
                "ex": join_uniq(fk + sc_vals + [c.get("ar"), c.get("k")]),
                "y": c.get("y"),
                "l": [nm.get("ru") or "", nm.get("en") or "", nm.get("ka") or ""],
                "ll": [c.get("lon"), c.get("lat")],
            })

    OUT.write_text(json.dumps(docs, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(docs)} docs ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
