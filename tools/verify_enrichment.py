"""Deterministic anti-hallucination verifier for Tbilisi Timeline enrichment batches.

Two modes:
  1. Bundle mode:  python -P tools/verify_enrichment.py <evidence_bundle.json>
     Checks every item against its immutable `fetched_text` snapshot:
       - Exact verbatim `aq` substring match (after whitespace/NBSP normalization)
       - Year/number grounding against `fetched_text`, resolved register `y0`/`y1`, or `owner_approved_facts`
       - Cross-language year parity across `ru`, `en`, `ka`
       - Strict Unicode script purity (blocks Cyrillic/Greek/Arabic/Turkish leaks & homoglyphs)
       - Domain glossary (`გამზირი` not `პროსპექტ`, `მტკვარი` not `ყურა`/`ურტყული`, `კონკა` not `cable car`)
       - Chronology sanity check against linked `monuments.json` `y0`/`y1` (blocks e.g. "Early 19th c." vs 1895)
  2. Repo mode:    python -P tools/verify_enrichment.py --check-repo
     Audits current `data/curated/catalog_links.json` and `site/data/places.json` for script purity,
     glossary compliance, cross-language year parity, and phase-vs-register chronology consistency.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RE_CYR = re.compile(r"[\u0400-\u04FF]")
RE_GRK = re.compile(r"[\u0370-\u03FF]")
RE_ARB = re.compile(r"[\u0600-\u06FF]")
RE_TRK = re.compile(r"[ıİğĞşŞ]")
RE_GEO = re.compile(r"[\u10A0-\u10FF]")
RE_LAT_WORD = re.compile(r"[A-Za-z]{2,}")
RE_YEAR = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-9]{2}|[1-9][0-9]{2})(?:s)?(?!\d)")
RE_ROMAN_ONLY = re.compile(r"^[IVXLCDM]+$")

DEFAULT_KA_LATIN = {
    "IMEL", "IMELI", "UNESCO", "OSRM", "GPS", "LED", "TV", "VIP",
    "Biltmore", "Radisson", "Marriott", "Hilton", "Sheraton", "Mercure",
}


def sq(s):
    return re.sub(r"\s+", " ", (s or "").replace("\u00a0", " ")).strip()


def extract_years(text):
    return set(RE_YEAR.findall(text or ""))


def check_script_purity(lang, text, allowed_latin=()):
    errs = []
    t = text or ""
    if RE_GRK.search(t):
        errs.append(f"{lang}: contains Greek characters")
    if RE_ARB.search(t):
        errs.append(f"{lang}: contains Arabic characters")
    if RE_TRK.search(t):
        errs.append(f"{lang}: contains Turkish diacritics")
    if lang == "ka":
        if RE_CYR.search(t):
            errs.append("ka: contains Cyrillic characters")
        allow = DEFAULT_KA_LATIN | set(allowed_latin or ())
        for w in RE_LAT_WORD.findall(t):
            if not RE_ROMAN_ONLY.match(w) and w not in allow:
                errs.append(f"ka: unexpected Latin word '{w}'")
    elif lang == "en":
        if RE_CYR.search(t):
            errs.append("en: contains Cyrillic characters (possible homoglyph)")
        if RE_GEO.search(t):
            errs.append("en: contains Georgian script")
    return errs


def check_glossary(lang, text, source_text=""):
    errs = []
    t = text or ""
    if lang == "ka":
        if "პროსპექტ" in t:
            errs.append("ka: use 'გამზირი' instead of 'პროსპექტ'")
        if re.search(r"მდინარე\s+(ყურ|ურტყულ)", t):
            errs.append("ka: use 'მტკვარი' for the Kura River")
    if lang == "en" and "კონკა" in (source_text or "") and re.search(r"\bcable car\b", t, re.I):
        errs.append("en: 'კონკა' must be translated as horse tram (konka), not cable car")
    return errs


def check_century_vs_register(text_ru, text_en, text_ka, y0, y1):
    errs = []
    if y0 is None or y1 is None:
        return errs
    combined = f"{text_ru} | {text_en} | {text_ka}"
    # Detect explicit "early 19th c." / "начало XIX в." / "XIX ს. დასაწყის"
    if re.search(r"(early\s+19th|нач(?:ало|але)\s+XIX|XIX\s*ს\.?\s*დასაწყის)", combined, re.I):
        if y0 >= 1850:
            errs.append(f"chronology contradiction: text claims early 19th c. but register y0..y1 is {y0}..{y1}")
    if re.search(r"(late\s+19th|кон(?:ец|це)\s+XIX|XIX\s*ს\.?\s*დასასრულ)", combined, re.I):
        if y1 <= 1840:
            errs.append(f"chronology contradiction: text claims late 19th c. but register y0..y1 is {y0}..{y1}")
    return errs


def load_monuments_by_id():
    p = ROOT / "site/data/monuments.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {str(f["properties"]["id"]): f["properties"] for f in data.get("features", [])}


def verify_bundle(bundle, monuments_by_id=None):
    mon = monuments_by_id if monuments_by_id is not None else load_monuments_by_id()
    items = bundle.get("items") or []
    if not items:
        return {"ok": [], "errors": [{"id": "<bundle>", "reasons": ["bundle has no items"]}]}
    report = {"ok": [], "errors": []}
    for item in items:
        iid = str(item.get("id", "<missing-id>"))
        kind = item.get("kind", "place")
        fetched = sq(item.get("fetched_text", ""))
        approved = sq(item.get("owner_approved_facts", ""))
        aq = item.get("aq")
        texts = item.get("texts") or {}
        allowed_lat = item.get("allowed_latin") or []
        errs = []

        if not fetched and not approved:
            errs.append("missing 'fetched_text' or 'owner_approved_facts'")

        if kind == "place":
            if not aq or not sq(aq):
                errs.append("missing verbatim quote 'aq'")
            elif fetched and sq(aq) not in fetched:
                errs.append("quote 'aq' is NOT a verbatim substring of fetched_text")

        if set(texts.keys()) != {"ru", "en", "ka"}:
            errs.append(f"texts must have exact keys ru/en/ka, got {sorted(texts.keys())}")
        else:
            max_len = 330 if kind == "dw" else 320
            yrs = {}
            for lg in ("ru", "en", "ka"):
                val = (texts.get(lg) or "").strip()
                if not val:
                    errs.append(f"{lg}: empty text")
                    continue
                if len(val) > max_len:
                    errs.append(f"{lg}: length {len(val)} exceeds {max_len}")
                errs.extend(check_script_purity(lg, val, allowed_lat))
                errs.extend(check_glossary(lg, val, fetched))
                yrs[lg] = extract_years(val)

            if len(yrs) == 3 and not (yrs["ru"] == yrs["en"] == yrs["ka"]):
                errs.append(f"cross-language year mismatch: ru={sorted(yrs['ru'])}, en={sorted(yrs['en'])}, ka={sorted(yrs['ka'])}")

            # Grounding pool for years
            reg_id = str(item.get("reg_id") or (iid[2:] if iid.startswith("o:") else iid))
            m = mon.get(reg_id)
            ground_pool = f"{fetched} {approved}"
            if m:
                ground_pool += f" {m.get('y0', '')} {m.get('y1', '')} {m.get('ye', '')}"
            grounded_years = extract_years(ground_pool)
            all_text_years = set().union(*yrs.values()) if yrs else set()
            for y in sorted(all_text_years):
                if y not in grounded_years:
                    errs.append(f"ungrounded year '{y}' not found in fetched_text, register dates, or owner_approved_facts")

            if m and not item.get("conflict_note"):
                errs.extend(check_century_vs_register(texts.get("ru", ""), texts.get("en", ""), texts.get("ka", ""), m.get("y0"), m.get("y1")))

        if errs:
            report["errors"].append({"id": iid, "reasons": errs})
        else:
            report["ok"].append(iid)
    return report


def check_repo():
    mon = load_monuments_by_id()
    errors = []

    # 1. catalog_links.json
    cat_p = ROOT / "data/curated/catalog_links.json"
    if cat_p.exists():
        cat = json.loads(cat_p.read_text(encoding="utf-8"))
        for e in cat.get("links", []):
            cid = e.get("cat", "?")
            refs = [r[2:] for r in e.get("refs", []) if r.startswith("o:")]
            for idx, ph in enumerate(e.get("phases") or []):
                for lg in ("ru", "en", "ka"):
                    t = ph.get(lg, "")
                    for err in check_script_purity(lg, t):
                        errors.append(f"catalog_links {cid} phase[{idx}]: {err}")
                    for err in check_glossary(lg, t):
                        errors.append(f"catalog_links {cid} phase[{idx}]: {err}")
                yr_ru, yr_en, yr_ka = extract_years(ph.get("ru", "")), extract_years(ph.get("en", "")), extract_years(ph.get("ka", ""))
                if not (yr_ru == yr_en == yr_ka):
                    errors.append(f"catalog_links {cid} phase[{idx}]: year parity mismatch ru={sorted(yr_ru)} en={sorted(yr_en)} ka={sorted(yr_ka)}")
                for oid in refs:
                    m = mon.get(oid)
                    if m and not e.get("conflict_note"):
                        for err in check_century_vs_register(ph.get("ru", ""), ph.get("en", ""), ph.get("ka", ""), m.get("y0"), m.get("y1")):
                            errors.append(f"catalog_links {cid} vs o:{oid}: {err}")

    # 2. places.json (script purity & glossary on a/e)
    pl_p = ROOT / "site/data/places.json"
    if pl_p.exists():
        pl = json.loads(pl_p.read_text(encoding="utf-8"))
        for c in pl.get("items", []):
            pid = c.get("id", "?")
            for fld in ("a", "e"):
                d = c.get(fld)
                if not isinstance(d, dict):
                    continue
                for lg in ("ru", "en", "ka"):
                    t = d.get(lg) or ""
                    if not t:
                        continue
                    if RE_GRK.search(t) or RE_ARB.search(t) or RE_TRK.search(t):
                        errors.append(f"places {pid}.{fld}.{lg}: foreign script leak (Greek/Arabic/Turkish)")
                    if lg in ("ka", "en") and RE_CYR.search(t):
                        errors.append(f"places {pid}.{fld}.{lg}: Cyrillic character leak")
                    for err in check_glossary(lg, t):
                        errors.append(f"places {pid}.{fld}: {err}")

    return errors


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if not args or args[0] == "--check-repo":
        errs = check_repo()
        if errs:
            print(f"FAIL: {len(errs)} problem(s) in repo:")
            for e in errs:
                print(" -", e)
            sys.exit(1)
        print("verify_enrichment --check-repo: OK")
        return

    bundle_path = Path(args[0])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    rep = verify_bundle(bundle)
    if rep["errors"]:
        print(f"FAIL: {len(rep['errors'])} item(s) rejected, {len(rep['ok'])} ok:")
        for r in rep["errors"]:
            print(f" - {r['id']}: {'; '.join(r['reasons'])}")
        sys.exit(1)
    print(f"verify_enrichment OK: {len(rep['ok'])} item(s) verified")


if __name__ == "__main__":
    main()
