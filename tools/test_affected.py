"""Maps modified repository files to the affected tests/e2e/*.test.mjs suites.

Usage:
  python -P tools/test_affected.py              # prints affected suites from git status
  python -P tools/test_affected.py --run        # runs them via node --test --test-concurrency=1
  python -P tools/test_affected.py --files a b  # map explicit file paths
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALL_E2E = [
    "basemap.test.mjs", "battles_map.test.mjs", "close_outside.test.mjs", "filters.test.mjs",
    "groups.test.mjs", "header.test.mjs", "idle_load.test.mjs", "layers.test.mjs",
    "lazy_retry.test.mjs", "modernism.test.mjs", "monuments.test.mjs", "object_link.test.mjs",
    "osm_names.test.mjs", "panel.test.mjs", "parks.test.mjs", "perf.test.mjs",
    "place_areas.test.mjs", "places.test.mjs", "religious_osm.test.mjs", "report_button.test.mjs",
    "smoke.test.mjs", "tour.test.mjs", "ui.test.mjs",
]

RULES = [
    ("site/data/places.json", ["parks.test.mjs", "places.test.mjs", "place_areas.test.mjs", "osm_names.test.mjs", "object_link.test.mjs"]),
    ("site/data/monuments.json", ["monuments.test.mjs", "object_link.test.mjs", "perf.test.mjs", "layers.test.mjs"]),
    ("site/data/photos.json", ["monuments.test.mjs", "object_link.test.mjs", "perf.test.mjs", "modernism.test.mjs"]),
    ("site/data/religious.json", ["layers.test.mjs", "religious_osm.test.mjs", "object_link.test.mjs", "perf.test.mjs"]),
    ("site/data/religious_osm.json", ["layers.test.mjs", "religious_osm.test.mjs", "object_link.test.mjs", "perf.test.mjs"]),
    ("site/data/science.json", ["layers.test.mjs", "object_link.test.mjs", "report_button.test.mjs", "perf.test.mjs"]),
    ("site/data/education.json", ["layers.test.mjs", "object_link.test.mjs", "report_button.test.mjs", "perf.test.mjs"]),
    ("site/data/museums.json", ["layers.test.mjs", "tour.test.mjs", "object_link.test.mjs", "perf.test.mjs"]),
    ("site/data/modernism.json", ["modernism.test.mjs", "object_link.test.mjs", "lazy_retry.test.mjs", "perf.test.mjs"]),
    ("site/data/sculptures.json", ["monuments.test.mjs", "object_link.test.mjs", "idle_load.test.mjs", "perf.test.mjs"]),
    ("site/data/plaques.json", ["monuments.test.mjs", "object_link.test.mjs", "idle_load.test.mjs", "perf.test.mjs"]),
    ("site/data/rulers.json", ["tour.test.mjs", "object_link.test.mjs", "ui.test.mjs", "smoke.test.mjs", "perf.test.mjs"]),
    ("site/data/rulers_media.json", ["tour.test.mjs", "object_link.test.mjs", "perf.test.mjs"]),
    ("site/data/urban.json", ["layers.test.mjs", "perf.test.mjs"]),
    ("site/data/street_names.json", ["object_link.test.mjs", "ui.test.mjs", "report_button.test.mjs", "perf.test.mjs"]),
    ("site/data/street_geom.json", ["ui.test.mjs", "object_link.test.mjs", "perf.test.mjs"]),
    ("site/data/transport.json", ["layers.test.mjs", "panel.test.mjs", "object_link.test.mjs", "perf.test.mjs"]),
    ("site/data/lost.json", ["filters.test.mjs", "smoke.test.mjs", "perf.test.mjs"]),
    ("site/data/views.json", ["close_outside.test.mjs", "ui.test.mjs", "perf.test.mjs"]),
    ("site/data/names_i18n.json", ["monuments.test.mjs", "places.test.mjs", "osm_names.test.mjs", "smoke.test.mjs", "perf.test.mjs"]),
    ("site/data/search_index.json", ["ui.test.mjs", "places.test.mjs", "idle_load.test.mjs", "perf.test.mjs"]),
    ("site/data/mtskheta_tour.json", ["object_link.test.mjs", "smoke.test.mjs"]),
    ("data/curated/catalog_links.json", ["object_link.test.mjs", "ui.test.mjs"]),
    ("site/data/catalog.json", ["object_link.test.mjs", "ui.test.mjs"]),
    ("site/data/history_events.json", ["battles_map.test.mjs", "ui.test.mjs", "perf.test.mjs"]),
    ("site/data/tour.json", ["tour.test.mjs", "perf.test.mjs"]),
    ("site/data/plans.json", ["basemap.test.mjs", "layers.test.mjs", "perf.test.mjs"]),
    ("site/data/changelog.json", ["ui.test.mjs"]),
    ("site/data/version.json", ["ui.test.mjs"]),
    ("site/app.js", ALL_E2E),
    ("site/style.css", ["header.test.mjs", "filters.test.mjs", "panel.test.mjs", "close_outside.test.mjs", "perf.test.mjs"]),
    ("site/i18n.js", ["header.test.mjs", "smoke.test.mjs", "ui.test.mjs", "perf.test.mjs"]),
    ("site/index.html", ["header.test.mjs", "filters.test.mjs", "groups.test.mjs", "smoke.test.mjs", "perf.test.mjs"]),
    ("site/js/plans.js", ["basemap.test.mjs", "layers.test.mjs", "perf.test.mjs"]),
    ("site/js/timeline.js", ["monuments.test.mjs", "battles_map.test.mjs", "perf.test.mjs"]),
]


def changed_files():
    out = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True, encoding="utf-8")
    res = []
    for line in out.splitlines():
        if len(line) >= 4:
            p = line[3:].strip().strip('"').replace("\\", "/")
            if " -> " in p:
                p = p.split(" -> ", 1)[1]
            res.append(p)
    return res


def select_suites(files):
    selected = set()
    for f in files:
        fn = f.replace("\\", "/")
        if fn.startswith("tests/e2e/") and fn.endswith(".test.mjs"):
            selected.add(Path(fn).name)
        for prefix, suites in RULES:
            if fn == prefix:
                selected.update(suites)
    return sorted(f"tests/e2e/{s}" for s in selected if (ROOT / "tests/e2e" / s).exists())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    run = "--run" in args
    if "--files" in args:
        idx = args.index("--files")
        files = [a for a in args[idx + 1:] if not a.startswith("--")]
    else:
        files = changed_files()
    suites = select_suites(files)
    if not suites:
        print("No affected e2e suites for current changes.")
        return
    cmd = ["node", "--test", "--test-concurrency=1", *suites]
    print(f"Affected suites ({len(suites)}):", " ".join(suites))
    if run:
        sys.exit(subprocess.call(cmd, cwd=ROOT))


if __name__ == "__main__":
    main()
