"""Local research queue and receipts for handoff between agents."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import RESEARCH, ROOT, TOOLS, create_once  # noqa: E402

WORKSPACE = Path(RESEARCH)
LEDGER = WORKSPACE / "task_state.sqlite"
GROUPS = {
    "tour_ka_task": ["tour_filters"],
    "ka_descriptions_task": ["monuments_KA"],
    "parks_task": ["parks"],
    "changelog_190_task": ["changelog_190"],
    "osm_names_task": ["osm_names"],
    "church_drafts_task": ["churches_C"],
    "churches_task": ["folk_points", "churches_A", *[f"churches_B{i}" for i in range(1, 5)]],
    "monuments_enrich_task": [f"monuments_E{i}" for i in range(1, 7)],
}
PRIORITY = [
    "tour_filters", "monuments_KA", "parks", "changelog_190", "osm_names", "folk_points",
    "churches_C", "churches_A", *[f"churches_B{i}" for i in range(1, 5)],
    *GROUPS["monuments_enrich_task"],
]
CATALOG = [(f"tasks/{tid}.md", f"results/{tid}.json") for tid in PRIORITY]


def content(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def result_kind(data):
    if data is None:
        return "missing"
    if not data.strip():
        return "empty"
    try:
        result = json.loads(data)
    except (ValueError, UnicodeError):
        return "invalid"
    if not isinstance(result, (dict, list)):
        return "invalid"
    if not result:
        return "empty"
    if isinstance(result, list) and any(not isinstance(row, dict) for row in result):
        return "invalid"
    rows = result if isinstance(result, list) else result.values()
    if all(row == "not_found" or (isinstance(row, dict) and row.get("status") == "not_found") for row in rows):
        return "not_found"
    if all(not row for row in rows):
        return "empty"
    return "content"


def task_file(tid):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]*", tid):
        raise ValueError(f"Invalid task ID: {tid}")
    return WORKSPACE / "tasks" / f"{tid}.md"


def result_file(tid):
    return WORKSPACE / "results" / f"{tid}.json"


def inspect(tid, recorded):
    task, result = task_file(tid), result_file(tid)
    task_data, result_data = content(task), content(result)
    task_hash = digest(task_data)
    result_hash = digest(result_data)
    receipts_changed = recorded and any(
        digest(content(WORKSPACE / evidence["path"])) != evidence["sha256"]
        for step in ("verified", "applied") if (evidence := recorded.get(step))
    )
    if recorded and (recorded["task_sha256"] != task_hash or receipts_changed or
                     (recorded.get("result_sha256") is not None and recorded["result_sha256"] != result_hash)):
        state = "conflict"
    elif not task_data:
        state = "missing"
    elif recorded and recorded["state"] != "created":
        state = recorded["state"]
    else:
        state = "created" if result_data is None else "unbound"
    return {
        "id": tid, "state": state, "result_kind": result_kind(result_data),
        "task": task.relative_to(WORKSPACE).as_posix(), "task_sha256": task_hash,
        "result": result.relative_to(WORKSPACE).as_posix(), "result_sha256": result_hash,
        "recorded": recorded,
    }


def read_state():
    if not LEDGER.is_file():
        return {}
    with closing(sqlite3.connect(LEDGER.as_uri() + "?mode=ro", uri=True)) as connection:
        return dict((tid, json.loads(record)) for tid, record in connection.execute("SELECT id, record FROM task"))


def open_writer():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(LEDGER)
    db.execute("CREATE TABLE IF NOT EXISTS task(id TEXT PRIMARY KEY, record TEXT NOT NULL)")
    return db


def receipt(path):
    full = Path(path).resolve(strict=True)
    relative = full.relative_to(WORKSPACE.resolve())
    if relative.parts[0] != "results" or full.suffix.lower() not in (".md", ".txt", ".log"):
        raise ValueError("Put the receipt in the research workspace's results directory (.md, .txt or .log)")
    body = full.read_bytes()
    if not body.strip():
        raise ValueError(f"Empty receipt: {full}")
    return {"path": relative.as_posix(), "sha256": digest(body)}


def advance(args):
    tid = args.id
    task_file(tid)
    with closing(open_writer()) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT record FROM task WHERE id=?", (tid,)).fetchone()
        previous = json.loads(row[0]) if row else None
        info = inspect(tid, previous)
        if info["state"] in ("missing", "conflict"):
            raise ValueError(f"{tid}: {info['state']}. Preserve the files and use a new ID for a revised task.")
        if args.command == "receive":
            if args.task_sha256 != info["task_sha256"]:
                raise ValueError(f"{tid}: task hash does not match; re-read the task before submitting")
            result = result_file(tid)
            body = Path(args.source).read_bytes() if args.source else content(result)
            kind = result_kind(body)
            if kind not in ("content", "not_found"):
                raise ValueError(f"{tid}: result is {kind}; supply a complete JSON response")
            result_hash = digest(body)
            if info["result_sha256"] is None:
                create_once(result, body)
            if digest(content(result)) != result_hash:
                raise ValueError(f"{tid}: an existing result differs; it was preserved")
            record = previous if previous and previous["state"] != "created" else {
                "state": "received", "task_sha256": info["task_sha256"], "result_sha256": result_hash,
                "result_kind": kind,
            }
        else:
            step, required = ("verified", "received") if args.command == "verify" else ("applied", "verified")
            if not previous or previous["state"] not in (required, step):
                raise ValueError(f"{tid}: a {required} task is required before recording {step}")
            evidence = receipt(args.report)
            if step == "applied" and args.commit:
                evidence["commit"] = args.commit
            if previous["state"] == step and previous[step] != evidence:
                raise ValueError(f"{tid}: the existing {step} receipt was preserved")
            record = {**previous, "state": step, step: evidence}
        if record != previous:
            db.execute(
                "INSERT INTO task(id, record) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET record=excluded.record",
                (tid, json.dumps(record, ensure_ascii=False)),
            )
    print(json.dumps(inspect(tid, record), ensure_ascii=False, indent=2))


def prepare():
    # Related tasks can share a generator. Its writer protects every existing task and result.
    for script, tids in GROUPS.items():
        if any(not task_file(tid).exists() and not result_file(tid).exists() for tid in tids):
            subprocess.run([sys.executable, "-P", str(Path(TOOLS, script + ".py"))], check=True)
    with closing(open_writer()) as db, db:
        db.execute("BEGIN IMMEDIATE")
        for tid in PRIORITY:
            data = content(task_file(tid))
            if data:
                created = {"state": "created", "task_sha256": digest(data)}
                db.execute("INSERT OR IGNORE INTO task VALUES (?, ?)", (tid, json.dumps(created)))
    state = read_state()
    rows = [inspect(tid, state.get(tid)) for tid in PRIORITY]
    workspace = Path(os.path.relpath(WORKSPACE, ROOT)).as_posix()
    lines = [
        "# Очередь исследовательских заданий", "",
        "Открой `AGENTS.md` и `docs/RESEARCH_WORKFLOW.md`.",
        "Актуальные хеши и статусы показывает `python -P tools/tasks.py list`.", "",
        "| Задание | Файл | Результат | Статус на момент подготовки |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['id']} | `{workspace}/{row['task']}` | `{workspace}/{row['result']}` | {row['state']} |")
    index = WORKSPACE / "ALL_TASKS.md"
    updated = ("\n".join(lines) + "\n").encode("utf-8")
    if content(index) != updated:
        with TemporaryDirectory(dir=WORKSPACE) as folder:
            staged = Path(folder) / index.name
            staged.write_bytes(updated)
            staged.replace(index)
    print(f"Queue index: {workspace}/ALL_TASKS.md")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="show the active queue without writing files")
    listing.add_argument("--all", action="store_true")
    listing.add_argument("--json", action="store_true")
    sub.add_parser("show", help="show paths, hashes and receipts without writing files").add_argument("id")
    sub.add_parser("prepare", help="create missing task inputs, preserving existing tasks and results")
    receive = sub.add_parser("receive", help="bind a complete result to its task input")
    receive.add_argument("id")
    receive.add_argument("--task-sha256", required=True)
    receive.add_argument("--from", dest="source", help="copy a candidate result if the expected result path is free")
    for name in ("verify", "apply"):
        command = sub.add_parser(name, help=f"record a receipt after running the external {name} step")
        command.add_argument("id")
        command.add_argument("--report", required=True)
        if name == "apply":
            command.add_argument("--commit")
    args = parser.parse_args(argv)
    try:
        if args.command in ("list", "show"):
            state = read_state()
            if args.command == "show":
                print(json.dumps(inspect(args.id, state.get(args.id)), ensure_ascii=False, indent=2))
            else:
                ids = PRIORITY + (sorted(({p.stem for p in (WORKSPACE / "tasks").glob("*.md")} | state.keys()) - set(PRIORITY)) if args.all else [])
                rows = [inspect(tid, state.get(tid)) for tid in ids]
                if args.json:
                    print(json.dumps(rows, ensure_ascii=False, indent=2))
                else:
                    print("ID\tSTATE\tRESULT")
                    for row in rows:
                        print(f"{row['id']}\t{row['state']}\t{row['result_kind']}")
        elif args.command == "prepare":
            prepare()
        else:
            advance(args)
    except (OSError, sqlite3.Error, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
