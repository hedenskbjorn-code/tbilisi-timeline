"""All the folders of the project in one place. Scripts import the paths they use.
Layout (see docs/LAYOUT.md):
  site/ worker/ tests/ viewer/ tools/          the published site, the Cloudflare worker, the tests, the viewer, the code
  data/curated|slices|raw|cache|db             the checked data in git (data/*.json today, data/slices), the downloads and caches and the index (not in git)
  work/research/{tasks,results,batches,archive}  local research tasks, answers, batches and archives
  work/notes                                   working notes and tables (not in git)
  docs/                                        the documents of the project (PENDING.md, LAYOUT.md)
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
SITE_DATA = os.path.join(SITE, "data")
TOOLS = os.path.join(ROOT, "tools")
DATA = os.path.join(ROOT, "data")
CURATED = os.path.join(DATA, "curated")
RAW = os.path.join(DATA, "raw")
CACHE = os.path.join(DATA, "cache")
DB_DIR = os.path.join(DATA, "db")
DB = os.path.join(DB_DIR, "project.sqlite")
WORK = os.path.join(ROOT, "work")
_neutral = os.path.join(WORK, "research")
_legacy = os.path.join(WORK, "gemini")
_configured = os.environ.get("TBILISI_RESEARCH_DIR")
if not _configured and os.path.isdir(_neutral) and os.path.isdir(_legacy) and not os.path.samefile(_neutral, _legacy):
    raise RuntimeError("work/research and work/gemini refer to different directories; resolve the research path before proceeding")
RESEARCH = os.path.abspath(_configured or (
    _legacy if os.path.isdir(_legacy) and not os.path.lexists(_neutral) else _neutral
))
GEMINI = RESEARCH  # compatibility for earlier tools
TASKS = os.path.join(RESEARCH, "tasks")
RESULTS = os.path.join(RESEARCH, "results")
BATCHES = os.path.join(RESEARCH, "batches")
ARCHIVE = os.path.join(RESEARCH, "archive")
NOTES = os.path.join(WORK, "notes")
DOCS = os.path.join(ROOT, "docs")


def create_once(path, content):
    """Publish a complete file without replacing a path claimed by another process."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=path.parent) as directory:
        staged = Path(directory) / path.name
        staged.write_bytes(content)
        try:
            os.link(staged, path)
        except FileExistsError:
            return False
    return True


def write_task(name, text):
    """A generated task is immutable. An older answer also reserves its task ID."""
    path = Path(RESEARCH, name)
    if path.exists() or Path(RESULTS, path.stem + ".json").exists():
        return False
    workspace = Path(os.path.relpath(RESEARCH, ROOT)).as_posix()
    return create_once(path, text.replace("work/research/", workspace + "/").encode("utf-8"))


def require_file(path, hint=""):
    """Return path if it exists, otherwise raise FileNotFoundError before any output is written."""
    if not os.path.isfile(path):
        msg = f"Missing required input file: {path}"
        if hint:
            msg += f" ({hint})"
        raise FileNotFoundError(msg)
    return path
