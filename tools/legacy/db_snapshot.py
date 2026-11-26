"""A local snapshot of the project database: a dated folder data/db/snapshots/<date>_<git commit>/ with
  curated.sqlite   the curated tables only (regions, layers, objects with their R-tree, names with their full-text index, sources, facts, photographs, tasks), WITHOUT the raw records (those are re-made from data/raw);
  tables/*.ndjson  every curated table as one JSON line per row, sorted by key: readable, comparable with a diff, loadable into any engine (this is what a later upload to D1 or PostgreSQL starts from);
  manifest.json    when, which git commit, how many rows per table, the SHA-256 of every file of the snapshot, of the schema and of the JSON files of the site that the database was made from.
The snapshot is checked at once: the NDJSON tables are loaded into an empty database made from tools/db/schema.sql and the counts and the keys must be the same as in curated.sqlite; otherwise the exit code is 1.
Older snapshots are never deleted. data/db is not in git. Usage: python -P tools/db_snapshot.py [--georgia] [--raw-all]   (the options go to tools/db_build.py)
"""
import datetime
import hashlib
import json
import os
import sqlite3
import subprocess
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(R, "data", "db", "project.sqlite")
SCHEMA = os.path.join(R, "tools", "db", "schema.sql")
SKIP = {"raw_file", "raw_record", "raw_geo"}                       # re-made from data/raw
KEYS = {"region": "id", "layer": "id", "object": "id", "name": "object_id, lang, kind, name", "source": "id", "fact": "id", "media": "object_id, file", "task": "id", "task_row": "task_id, row_id"}
ORDER = ["region", "layer", "object", "name", "source", "fact", "media", "task", "task_row"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=R, capture_output=True, text=True).stdout.strip() or "nogit"
    except OSError:
        return "nogit"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    subprocess.run([sys.executable, "-P", os.path.join(R, "tools", "db_build.py"), "--check"] + [a for a in sys.argv[1:] if a in ("--georgia", "--raw-all")], check=True, capture_output=True)
    now = datetime.datetime.now()
    out = os.path.join(R, "data", "db", "snapshots", "%s_%s" % (now.strftime("%Y-%m-%d_%H%M"), git_commit()))
    os.makedirs(os.path.join(out, "tables"), exist_ok=True)
    src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    # 1. the curated copy (the backup API copies everything, the raw tables are dropped afterwards)
    cur_path = os.path.join(out, "curated.sqlite")
    dst = sqlite3.connect(cur_path)
    src.backup(dst)
    for t in SKIP:
        dst.execute("DROP TABLE IF EXISTS %s" % t)
    dst.commit()
    dst.execute("VACUUM")
    dst.close()
    # 2. NDJSON tables
    counts, files = {}, {}
    for t in ORDER:
        cols = [r[1] for r in src.execute("PRAGMA table_info(%s)" % t)]
        p = os.path.join(out, "tables", t + ".ndjson")
        n = 0
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            for row in src.execute("SELECT %s FROM %s ORDER BY %s" % (", ".join(cols), t, KEYS[t])):
                f.write(json.dumps(dict(zip(cols, row)), ensure_ascii=False, separators=(",", ":")) + "\n")
                n += 1
        counts[t] = n
        files["tables/%s.ndjson" % t] = sha(p)
    files["curated.sqlite"] = sha(cur_path)
    # 3. the check: the NDJSON tables loaded into an empty database
    chk = sqlite3.connect(":memory:")
    chk.executescript(open(SCHEMA, encoding="utf-8").read())
    for t in ORDER:
        cols = [r[1] for r in chk.execute("PRAGMA table_info(%s)" % t)]
        rows = []
        with open(os.path.join(out, "tables", t + ".ndjson"), encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                rows.append(tuple(d[c] for c in cols))
        chk.executemany("INSERT INTO %s (%s) VALUES (%s)" % (t, ", ".join(cols), ", ".join("?" * len(cols))), rows)
    bad = []
    cur = sqlite3.connect(cur_path)
    for t in ORDER:
        a, b = chk.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0], cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        if a != b or a != counts[t]:
            bad.append("%s: ndjson %d, curated.sqlite %d, written %d" % (t, a, b, counts[t]))
    if chk.execute("SELECT group_concat(id) FROM (SELECT id FROM object ORDER BY id)").fetchone() != cur.execute("SELECT group_concat(id) FROM (SELECT id FROM object ORDER BY id)").fetchone():
        bad.append("the keys of the objects differ")
    # 4. the manifest
    site = os.path.join(R, "site", "data")
    manifest = {"created": now.isoformat(timespec="seconds"), "git_commit": git_commit(), "options": [a for a in sys.argv[1:] if a.startswith("--")], "rows": counts, "files": files,
                "schema_sha256": sha(SCHEMA), "inputs": {n: sha(os.path.join(site, n)) for n in sorted(os.listdir(site)) if n.endswith(".json")}, "restorable": not bad,
                "note": "the raw records (OSM, register) are not in the snapshot: they are loaded from data/raw by tools/db_build.py"}
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(R, "data", "db", "snapshots", "LATEST.txt"), "w", encoding="utf-8").write(os.path.basename(out) + "\n")
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(out) for f in fs)
    print("snapshot:", os.path.relpath(out, R), "| %d KB" % (size // 1024), "| rows:", counts)
    print("check:", "the NDJSON tables rebuild the same database" if not bad else "DIFFERENCES: " + "; ".join(bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
