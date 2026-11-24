"""All the folders of the project in one place. A script imports what it needs (from paths import GEMINI) and does not build the paths of the working folders itself.
Layout (see docs/LAYOUT.md):
  site/ worker/ tests/ viewer/ tools/          the published site, the Cloudflare worker, the tests, the viewer, the code
  data/curated|slices|raw|cache|db             the checked data in git (data/*.json today, data/slices), the downloads and caches and the index (not in git)
  work/gemini/{tasks,results,batches,archive}  the working area of the tasks for Gemini (not in git): the tasks, the answers, the batches with their answers, the old material
  work/notes                                   working notes and tables (not in git)
  docs/                                        the documents of the project (PENDING.md, LAYOUT.md)
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
SITE_DATA = os.path.join(SITE, "data")
TOOLS = os.path.join(ROOT, "tools")
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
CACHE = os.path.join(DATA, "cache")
DB_DIR = os.path.join(DATA, "db")
DB = os.path.join(DB_DIR, "project.sqlite")
WORK = os.path.join(ROOT, "work")
GEMINI = os.path.join(WORK, "gemini")
TASKS = os.path.join(GEMINI, "tasks")
RESULTS = os.path.join(GEMINI, "results")
BATCHES = os.path.join(GEMINI, "batches")
ARCHIVE = os.path.join(GEMINI, "archive")
NOTES = os.path.join(WORK, "notes")
DOCS = os.path.join(ROOT, "docs")
