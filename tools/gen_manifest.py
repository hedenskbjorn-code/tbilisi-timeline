"""Generate site/data/manifest.json and stamp ?v=<hash> onto site/index.html and site/sw.js.

Idempotent: running twice changes nothing.
Flags:
  --check    Exit 1 if manifest.json, index.html, or sw.js is out of date.
  --dry-run  Show planned changes without writing files.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
MANIFEST_PATH = SITE / "data" / "manifest.json"
INDEX_PATH = SITE / "index.html"
SW_PATH = SITE / "sw.js"

# Local shell assets referenced in index.html (ES module app.js includes site/js/*.js)
ASSET_TAG_RE = re.compile(
    r'(<(?:script\b[^>]*\bsrc|link\b[^>]*\brel="stylesheet"[^>]*\bhref)=")([^"?#]+)(?:\?v=[0-9a-f]{8})?(")',
    re.IGNORECASE,
)


def norm_bytes(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n")


def sha8(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:8]


def asset_hash(rel_path: str) -> str | None:
    p = SITE / rel_path
    if not p.is_file():
        return None
    h = hashlib.sha256(norm_bytes(p))
    if rel_path == "app.js":
        for dep in sorted((SITE / "js").glob("*.js")):
            h.update(norm_bytes(dep))
    return h.hexdigest()[:8]


def build_state() -> tuple[dict, str, str]:
    files_map: dict[str, str] = {}
    for p in sorted((SITE / "data").glob("*.json")):
        if p.name == "manifest.json":
            continue
        files_map["data/" + p.name] = sha8(p.read_bytes())
    ms_path = SITE / "vendor" / "minisearch.js"
    if ms_path.is_file():
        files_map["vendor/minisearch.js"] = sha8(norm_bytes(ms_path))

    idx_src = INDEX_PATH.read_text(encoding="utf-8")
    asset_hashes: dict[str, str] = {}

    def _sub_asset(m: re.Match) -> str:
        prefix, url, suffix = m.group(1), m.group(2), m.group(3)
        if url.startswith(("http://", "https://", "//")):
            return m.group(0)
        h = asset_hash(url)
        if not h:
            return m.group(0)
        asset_hashes[url] = h
        return f"{prefix}{url}?v={h}{suffix}"

    new_index = ASSET_TAG_RE.sub(_sub_asset, idx_src)

    overall_h = hashlib.sha256()
    for k in sorted(asset_hashes):
        overall_h.update(f"{k}:{asset_hashes[k]}\n".encode("utf-8"))
    for k in sorted(files_map):
        overall_h.update(f"{k}:{files_map[k]}\n".encode("utf-8"))
    overall = overall_h.hexdigest()[:8]

    manifest = {"v": overall, "f": files_map}

    sw_src = SW_PATH.read_text(encoding="utf-8")
    new_sw, n_sw = re.subn(
        r'^(const\s+VERSION\s*=\s*")[^"]*(";)',
        rf'\g<1>tt-{overall}\g<2>',
        sw_src,
        count=1,
        flags=re.MULTILINE,
    )
    if n_sw != 1:
        raise RuntimeError("Could not find const VERSION in site/sw.js")

    return manifest, new_index, new_sw


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Check that manifest.json, index.html, and sw.js are up to date")
    ap.add_argument("--dry-run", action="store_true", help="Print planned changes without writing")
    args = ap.parse_args()

    manifest, new_index, new_sw = build_state()
    new_manifest_str = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n"

    cur_manifest_str = MANIFEST_PATH.read_text(encoding="utf-8") if MANIFEST_PATH.exists() else ""
    cur_index = INDEX_PATH.read_text(encoding="utf-8")
    cur_sw = SW_PATH.read_text(encoding="utf-8")

    dirty = []
    if cur_manifest_str != new_manifest_str:
        dirty.append("site/data/manifest.json")
    if cur_index != new_index:
        dirty.append("site/index.html")
    if cur_sw != new_sw:
        dirty.append("site/sw.js")

    if args.check:
        if dirty:
            print("OUT OF DATE:", ", ".join(dirty), "(run python -P tools/gen_manifest.py)")
            return 1
        print(f"ok: manifest v={manifest['v']} ({len(manifest['f'])} data files)")
        return 0

    if args.dry_run:
        print("Would update:" if dirty else "Up to date:", ", ".join(dirty) or f"v={manifest['v']}")
        return 0

    if cur_manifest_str != new_manifest_str:
        MANIFEST_PATH.write_text(new_manifest_str, encoding="utf-8", newline="\n")
    if cur_index != new_index:
        INDEX_PATH.write_text(new_index, encoding="utf-8", newline="\n")
    if cur_sw != new_sw:
        SW_PATH.write_text(new_sw, encoding="utf-8", newline="\n")

    print(f"updated {len(dirty)} file(s): v={manifest['v']} ({len(manifest['f'])} data files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
