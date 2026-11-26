"""Per-file gzip & line-count diagnostic against a git ref (default: HEAD).

Use BEFORE proposing any change to tests/e2e/budget.json so root causes of weight growth
are measured per file rather than guessed. Flags accidental pretty-print (`INDENT_BLOAT`)
when a compact JSON file grows from <=2 lines to >5 lines.

Usage: python -P tools/perf_diff.py [--ref HEAD]
"""
import gzip
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def gz_kb(data: bytes) -> float:
    return len(gzip.compress(data, 6)) / 1024.0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ref = "HEAD"
    if len(sys.argv) >= 3 and sys.argv[1] == "--ref":
        ref = sys.argv[2]

    targets = [
        "site/index.html", "site/app.js", "site/style.css", "site/i18n.js", "site/translit.js",
        "site/js/plans.js", "site/js/timeline.js",
        "site/data/monuments.json", "site/data/photos.json", "site/data/names_i18n.json",
        "site/data/history_events.json", "site/data/religious.json", "site/data/science.json",
        "site/data/education.json", "site/data/museums.json", "site/data/places.json",
        "site/data/mtskheta_tour.json", "site/data/catalog.json", "site/data/search_index.json",
        "site/data/changelog.json", "site/data/version.json",
    ]

    print(f"{'File':32s} {'Lines(old->new)':>17s} {'OldGZ':>7s} {'CurGZ':>7s} {'Delta':>8s}  Flags")
    print("-" * 88)
    total_delta = 0.0
    bloat = []
    for rel in targets:
        p = ROOT / rel
        if not p.exists():
            continue
        cur_b = p.read_bytes()
        cur_gz = gz_kb(cur_b)
        cur_lines = cur_b.count(b"\n") + (0 if cur_b.endswith(b"\n") else 1)
        try:
            old_b = subprocess.check_output(["git", "show", f"{ref}:{rel}"], cwd=ROOT, stderr=subprocess.DEVNULL)
            old_gz = gz_kb(old_b)
            old_lines = old_b.count(b"\n") + (0 if old_b.endswith(b"\n") else 1)
        except subprocess.CalledProcessError:
            old_b, old_gz, old_lines = b"", 0.0, 0
        delta = cur_gz - old_gz
        total_delta += delta
        flags = []
        if rel.endswith(".json") and old_lines <= 2 and old_b and cur_lines > 5:
            compact_b = (json.dumps(json.loads(cur_b.decode("utf-8")), ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            waste = cur_gz - gz_kb(compact_b)
            flags.append(f"INDENT_BLOAT(+{waste:.1f}KB)")
            bloat.append((rel, waste))
        if abs(delta) >= 0.1 or flags:
            print(f"{rel:32s} {old_lines:7d}->{cur_lines:<8d} {old_gz:6.1f}K {cur_gz:6.1f}K {delta:+7.1f}K  {' '.join(flags)}")

    print("-" * 88)
    print(f"Total tracked gzip delta vs {ref}: {total_delta:+.1f} KB")
    if bloat:
        print("WARNING: accidental pretty-print bloat detected in compact JSON file(s):")
        for fn, w in bloat:
            print(f"  - {fn}: +{w:.1f} KB pure whitespace")
        sys.exit(2)


if __name__ == "__main__":
    main()
