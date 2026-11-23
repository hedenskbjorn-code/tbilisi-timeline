"""Questions to the project index (data/db/project.sqlite, made by tools/db_build.py). Read-only.
  python -P tools/db_query.py stats [layers]              objects of every layer and region (or of every layer), how many have a name / a description / a photo / a verified fact
  python -P tools/db_query.py missing <layer> [name|description|photo] [limit]    the objects of a layer that lack something (default: name)
  python -P tools/db_query.py tasks                       the tasks for Gemini: state, rows, found
  python -P tools/db_query.py find <words>                the full-text search of the names (all kinds: official, old, folk, alt)
  python -P tools/db_query.py near <lat> <lon> [metres]   the objects near a point (R-tree, then the distance)
  python -P tools/db_query.py sql "<SELECT ...>"           any SELECT (the connection is read-only)
"""
import math
import os
import sqlite3
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(R, "data", "db", "project.sqlite")


def table(rows, head):
    rows = [tuple("" if v is None else v for v in r) for r in rows]
    w = [max(len(str(x)) for x in col) for col in zip(head, *rows)] if rows else [len(h) for h in head]
    print("  ".join(str(h).ljust(n) for h, n in zip(head, w)))
    for r in rows:
        print("  ".join(str(v)[:70].ljust(n) for v, n in zip(r, w)))
    print("(%d rows)" % len(rows))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(DB):
        sys.exit("no index: python -P tools/db_build.py")
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    a = sys.argv[1:] or ["stats"]
    cmd = a[0]
    if cmd == "stats" and len(a) > 1 and a[1] == "layers":
        table(con.execute("""SELECT layer, COUNT(*) n, SUM(has_name) named, SUM(name_languages = 3) names_3_languages, SUM(has_description) described, SUM(has_photo) photographed, SUM(has_verified_fact) verified
                             FROM v_object_state GROUP BY layer ORDER BY n DESC""").fetchall(), ["layer", "objects", "named", "3 languages", "described", "photo", "verified"])
    elif cmd == "stats":
        table(con.execute("""SELECT layer, region, COUNT(*) n, SUM(has_name) named, SUM(name_languages = 3) names_3_languages, SUM(has_description) described, SUM(has_photo) photographed, SUM(has_verified_fact) verified
                             FROM v_object_state GROUP BY layer, region ORDER BY layer, n DESC""").fetchall(), ["layer", "region", "objects", "named", "3 languages", "described", "photo", "verified"])
    elif cmd == "missing":
        layer, what, lim = a[1], (a[2] if len(a) > 2 else "name"), int(a[3]) if len(a) > 3 else 40
        col = {"name": "has_name", "description": "has_description", "photo": "has_photo"}[what]
        table(con.execute(f"""SELECT v.id, v.kind, v.region, (SELECT name FROM name n WHERE n.object_id = v.id ORDER BY (lang='en') DESC LIMIT 1) FROM v_object_state v WHERE v.layer = ? AND v.{col} = 0 LIMIT ?""", (layer, lim)).fetchall(), ["id", "kind", "region", "a name"])
        print("total lacking:", con.execute(f"SELECT COUNT(*) FROM v_object_state WHERE layer = ? AND {col} = 0", (layer,)).fetchone()[0])
    elif cmd == "tasks":
        table(con.execute("SELECT id, status, result_rows, found, result_file FROM task ORDER BY status, id").fetchall(), ["task", "status", "rows", "found", "result file"])
    elif cmd == "find":
        q = " ".join('"%s"' % w.replace('"', "") for w in a[1:])
        table(con.execute("SELECT f.object_id, f.kind, f.lang, f.name FROM name_fts f WHERE name_fts MATCH ? LIMIT 40", (q,)).fetchall(), ["object", "kind", "lang", "name"])
    elif cmd == "near":
        la, lo, m = float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 150.0
        dla, dlo = m / 111320.0, m / (111320.0 * math.cos(math.radians(la)))
        rows = con.execute("""SELECT o.id, o.kind, o.lat, o.lon, (SELECT name FROM name n WHERE n.object_id = o.id ORDER BY (lang='en') DESC LIMIT 1)
                              FROM object_geo g JOIN object o ON o.rowid_ = g.id WHERE g.min_lon BETWEEN ? AND ? AND g.min_lat BETWEEN ? AND ?""", (lo - dlo, lo + dlo, la - dla, la + dla)).fetchall()
        out = []
        for oid, kind, y, x, nm in rows:
            d = 12742000 * math.asin(math.sqrt(math.sin(math.radians(y - la) / 2) ** 2 + math.cos(math.radians(la)) * math.cos(math.radians(y)) * math.sin(math.radians(x - lo) / 2) ** 2))
            if d <= m:
                out.append((round(d), oid, kind, nm))
        table(sorted(out), ["metres", "object", "kind", "a name"])
    elif cmd == "sql":
        if not a[1].lstrip().lower().startswith("select"):
            sys.exit("only SELECT")
        cur = con.execute(a[1])
        table(cur.fetchmany(200), [d[0] for d in cur.description])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
