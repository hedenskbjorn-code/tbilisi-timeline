"""Generate the site manifest and stamp versioned URLs in the application shell.

Idempotent: running twice changes nothing.
Flags:
  --check    Exit 1 if a generated file is out of date.
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
APP_PATH = SITE / "app.js"

# Local shell assets referenced in index.html (ES module app.js includes site/js/*.js)
ASSET_TAG_RE = re.compile(
    r'(<(?:script\b[^>]*\bsrc|link\b[^>]*\brel="stylesheet"[^>]*\bhref)=")([^"?#]+)(?:\?v=[0-9a-f]{8})?(")',
    re.IGNORECASE,
)
MODULE_URL_RE = re.compile(r'"\./(js/[^"/?#]+\.js)(?:\?v=[0-9a-f]{8})?"')
SHELL_RE = re.compile(r"^const SHELL = (\[[^\n]*\]);$", re.MULTILINE)
VERSION_RE = re.compile(r'^(const\s+VERSION\s*=\s*")[^"]*(";)$', re.MULTILINE)


def norm_bytes(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n")


def sha8(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:8]


def build_state() -> tuple[dict, dict[Path, str]]:
    files_map: dict[str, str] = {}
    for p in sorted((SITE / "data").glob("*.json")):
        if p.name == "manifest.json":
            continue
        files_map["data/" + p.name] = sha8(p.read_bytes())
    ms_path = SITE / "vendor" / "minisearch.js"
    if ms_path.is_file():
        files_map["vendor/minisearch.js"] = sha8(norm_bytes(ms_path))

    asset_hashes: dict[str, str] = {}

    def stamp_module(m: re.Match) -> str:
        path = m[1]
        asset_hashes[path] = sha8(norm_bytes(SITE / path))
        return f'"./{path}?v={asset_hashes[path]}"'

    new_app = MODULE_URL_RE.sub(stamp_module, APP_PATH.read_text(encoding="utf-8"))
    asset_hashes["app.js"] = sha8(new_app.encode("utf-8"))

    def _sub_asset(m: re.Match) -> str:
        prefix, url, suffix = m.group(1), m.group(2), m.group(3)
        if url.startswith(("http://", "https://", "//")):
            return m.group(0)
        path = SITE / url
        if not path.is_file():
            return m.group(0)
        if url not in asset_hashes:
            asset_hashes[url] = sha8(norm_bytes(path))
        return f"{prefix}{url}?v={asset_hashes[url]}{suffix}"

    new_index = ASSET_TAG_RE.sub(_sub_asset, INDEX_PATH.read_text(encoding="utf-8"))
    files_map["index.html"] = sha8(new_index.encode("utf-8"))
    sw_src = SW_PATH.read_text(encoding="utf-8")
    shell_match = SHELL_RE.search(sw_src)
    if not shell_match:
        raise RuntimeError("Could not find const SHELL in site/sw.js")
    shell_urls = []
    for entry in json.loads(shell_match[1]):
        path = entry.split("?", 1)[0]
        if path in asset_hashes:
            shell_urls.append(f"{path}?v={asset_hashes[path]}")
        else:
            shell_urls.append(path)
            if path != "data/manifest.json" and path not in files_map:
                files_map[path] = sha8(norm_bytes(SITE / path))
    sw_shell = SHELL_RE.sub(f"const SHELL = {json.dumps(shell_urls)};", sw_src, count=1)

    overall_h = hashlib.sha256()
    for k in sorted(asset_hashes):
        overall_h.update(f"{k}:{asset_hashes[k]}\n".encode("utf-8"))
    for k in sorted(files_map):
        overall_h.update(f"{k}:{files_map[k]}\n".encode("utf-8"))
    overall_h.update(VERSION_RE.sub(r'\g<1>\g<2>', sw_shell).encode("utf-8"))
    overall = overall_h.hexdigest()[:8]

    manifest = {"v": overall, "f": files_map}

    new_sw, n_sw = VERSION_RE.subn(rf'\g<1>tt-{overall}\g<2>', sw_shell, count=1)
    if n_sw != 1:
        raise RuntimeError("Could not find const VERSION in site/sw.js")

    files = {
        APP_PATH: new_app,
        INDEX_PATH: new_index,
        SW_PATH: new_sw,
        MANIFEST_PATH: json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n",
    }
    return manifest, files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Check that manifest.json, index.html, and sw.js are up to date")
    ap.add_argument("--dry-run", action="store_true", help="Print planned changes without writing")
    args = ap.parse_args()

    manifest, files = build_state()
    dirty = [path for path, expected in files.items() if not path.exists() or path.read_text(encoding="utf-8") != expected]
    dirty_names = ", ".join(path.relative_to(ROOT).as_posix() for path in dirty)

    if args.check:
        if dirty:
            print("OUT OF DATE:", dirty_names, "(run python -P tools/gen_manifest.py)")
            return 1
        print(f"ok: manifest v={manifest['v']} ({len(manifest['f'])} resources)")
        return 0

    if args.dry_run:
        print("Would update:" if dirty else "Up to date:", dirty_names or f"v={manifest['v']}")
        return 0

    for path in dirty:
        path.write_text(files[path], encoding="utf-8", newline="\n")

    print(f"updated {len(dirty)} file(s): v={manifest['v']} ({len(manifest['f'])} resources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
