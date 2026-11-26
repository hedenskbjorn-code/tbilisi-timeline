"""Reproducible build orchestrator and staged verification for tbilisi-timeline.

Modes:
  --check-inputs  Verify all curated inputs in tools/curated_inputs.json exist and match SHA-256.
  --stage         Verify inputs, rebuild derived outputs (bibliography, search_index, manifest)
                  inside a temporary directory, and verify byte-identical SHA-256 against site/.
  --apply         Verify inputs, rebuild derived outputs in place, and run manifest/DB checks.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, require_file

DERIVED_TARGETS = [
    "site/data/bibliography.json",
    "site/data/catalog.json",
    "site/data/search_index.json",
    "site/data/manifest.json",
    "site/index.html",
    "site/sw.js",
]


def sha256_bytes(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def check_inputs(root: Path) -> None:
    reg_path = require_file(str(root / "tools" / "curated_inputs.json"))
    inputs = json.loads(Path(reg_path).read_text(encoding="utf-8")).get("inputs", {})
    for rel, meta in inputs.items():
        p = Path(require_file(str(root / rel), "curated input"))
        got = sha256_bytes(p)
        want = meta["sha256"]
        if got != want:
            raise ValueError(f"Curated input SHA-256 mismatch for {rel}: got {got[:12]}, expected {want[:12]}")
    print(f"inputs ok: {len(inputs)} curated files verified")


def copy_stage_tree(root: Path, stage: Path) -> None:
    for rel in ("tools", "BIBLIOGRAPHY.md", "package.json", "data/curated"):
        src = root / rel
        if src.is_dir():
            shutil.copytree(src, stage / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif src.is_file():
            (stage / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, stage / rel)
    site_src = root / "site"
    site_dst = stage / "site"
    site_dst.mkdir(parents=True, exist_ok=True)
    for entry in site_src.iterdir():
        if entry.name == "topo":
            continue
        dst = site_dst / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dst)
        elif entry.is_file():
            shutil.copy2(entry, dst)


def run_step(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def run_stage(root: Path) -> int:
    check_inputs(root)
    with TemporaryDirectory() as tmp:
        stage = Path(tmp)
        copy_stage_tree(root, stage)
        for script in ("tools/build_bibliography.py", "tools/build_catalog.py", "tools/build_search_index.py", "tools/gen_manifest.py"):
            run_step([sys.executable, "-P", script], stage)
        run_step([sys.executable, "-P", "tools/gen_manifest.py", "--check"], stage)
        diffs = []
        for rel in DERIVED_TARGETS:
            h_stage = sha256_bytes(stage / rel)
            h_work = sha256_bytes(root / rel)
            if h_stage != h_work:
                diffs.append(f"{rel}: stage={h_stage[:12]} != workspace={h_work[:12]}")
        if diffs:
            print("STAGE MISMATCH:")
            for d in diffs:
                print(" -", d)
            return 1
    print(f"stage ok: {len(DERIVED_TARGETS)} derived files match reproducibly")
    return 0


def run_apply(root: Path) -> int:
    check_inputs(root)
    for script in ("tools/build_bibliography.py", "tools/build_catalog.py", "tools/build_search_index.py", "tools/gen_manifest.py"):
        run_step([sys.executable, "-P", script], root)
    run_step([sys.executable, "-P", "tools/gen_manifest.py", "--check"], root)
    run_step([sys.executable, "-P", "tools/db_build.py", "--check"], root)
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(ROOT)
    args = set(sys.argv[1:])
    if "--check-inputs" in args:
        check_inputs(root)
        return 0
    if "--apply" in args:
        return run_apply(root)
    return run_stage(root)


if __name__ == "__main__":
    raise SystemExit(main())
