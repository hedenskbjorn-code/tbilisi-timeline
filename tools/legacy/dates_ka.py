import re

def _centuries(seg):
    return [int(m.group(1)) for m in re.finditer(r"მე\s*-\s*(\d{1,2})(?!\d)(?!\s*ნახევარ)", seg)] + \
           [int(m.group(1)) for m in re.finditer(r"(?<![\d-])(\d{1,2})\s*-\s*ე(?!\S)", seg)] + \
           [int(m.group(1)) for m in re.finditer(r"(?<![\d-])(\d{1,2})\s*-\s*ე\s", seg)]

def parse_segment(seg):
    seg = seg.strip().strip(".")
    if not seg or seg == "0":
        return None
    years = [int(y) for y in re.findall(r"(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)", seg)]
    decade = re.search(r"(1[0-9]{2}0)\s*-\s*იანი", seg)
    if years:
        if decade and len(years) == 1:
            return (years[0], years[0] + 9, "decade")
        return (min(years), max(years), "exact" if min(years) == max(years) else "years")
    if "ძვ" in seg:
        return None
    cs = _centuries(seg)
    if not cs and "ნახევარ" in seg:
        pass
    if cs:
        c = cs[0]
        base = (c - 1) * 100
        lo, hi, prec = base + 1, base + 100, "century"
        if re.search(r"1-ლი\s*ნახევარ|პირველი\s*ნახევარ|მე\s*-\s*1\s*ნახევარ", seg):
            lo, hi, prec = base + 1, base + 50, "half"
        elif re.search(r"მეორე\s*ნახევარ|მე\s*-\s*2\s*ნახევარ", seg):
            lo, hi, prec = base + 51, base + 100, "half"
        elif re.search(r"დასაწყის", seg):
            lo, hi, prec = base + 1, base + 25, "quarter"
        elif re.search(r"დასასრულ|ბოლო|მიწურულ", seg):
            lo, hi, prec = base + 76, base + 100, "quarter"
        elif re.search(r"შუა", seg):
            lo, hi, prec = base + 31, base + 70, "middle"
        if len(cs) > 1 and prec == "century":     # e.g. "მე-20-21-ე სს" -> 20th..21st
            lo, hi = (min(cs) - 1) * 100 + 1, (max(cs)) * 100
        return (lo, min(hi, 2026), prec)
    if "ადრე შუა" in seg:
        return (400, 900, "era")
    if "შუა საუკუნე" in seg:
        return (400, 1700, "era")
    return None

def parse_text(s):
    if not s:
        return None
    parts = [p for p in re.split(r"[;/]", s) if p.strip()]
    res = [parse_segment(p) for p in parts]
    res = [r for r in res if r]
    if not res:
        return None
    # if some segments are exact years and others only centuries, prefer the exact ones
    exact = [r for r in res if r[2] in ("exact", "years", "decade")]
    use = exact or res
    lo, hi = min(r[0] for r in use), max(r[1] for r in use)
    prec = use[0][2] if len(use) == 1 else ("years" if exact else "mixed")
    return (lo, hi, prec)
