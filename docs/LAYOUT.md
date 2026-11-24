# Layout of the project

    tbilisi-timeline/
      site/            the published site (GitHub Pages): index.html, app.js, i18n.js, data/*.json, topo/, ...
      worker/          the Cloudflare Worker (photos, reports)
      tests/           unit tests (tests/*.test.mjs), end-to-end tests (tests/e2e/), the data check (tests/check_data.mjs)
      viewer/          the viewer of the old plans
      tools/           the code that makes the data: fetch_* download, verify_* check quotations, build_* / apply_* make the files of the site,
                       db_* the project index, gemini_all.py the tasks for Gemini; paths.py holds the paths of all the folders
      data/            (step 3 of the tidy is still to come: the checked data files of the root of data/ go to data/curated/)
        raw/ cache/    downloads and caches (not in git; made again by the scripts)
        db/            the project index data/db/project.sqlite and its snapshots (not in git)
        osm_slices/ register_slices/   dated slices of OpenStreetMap and of the register (in git)
      docs/            documents of the project: PENDING.md (what is left), LAYOUT.md (this file)
      work/            the working area, NOT in git
        gemini/
          ALL_TASKS.md    the index of the tasks (made by tools/gemini_all.py) and the one phrase to start them
          tasks/          a task for Gemini: <name>.md
          results/        the answer to a task: <name>.json (or .md)
          batches/<family>/   batches of a long task together with their answers (<family>_batch_NN.md and <family>_batch_NN_result.json)
          archive/        old tasks (TASK_*.md), experiments and their material (plans, photos, tram1913 ...)
        notes/            working notes and tables (some scripts read tbilisi_monuments_full.csv and tbilisi_plaques_osm.csv from here)
      README.md  LICENSE  NOTICE.md  BIBLIOGRAPHY.md  sources.md

Rules: a script takes the folders from `tools/paths.py`; a new task for Gemini is made by a script into `work/gemini/tasks/` and its answer is read from `work/gemini/results/`;
nothing in `work/` is published or committed. Until 2026-11-24 the working area was `for_gemini/from_desktop` and `notes/`.

## Saving tokens (rules for the assistant that works on the project)

The JSON files are large (site/data: transport 1.7 MB, monuments 1.3 MB, urban 0.9 MB ...; data/raw: up to 24 MB per file). Reading or rewriting them whole costs most of the tokens of a session.
- Do not read a data file whole. Ask the project index (`tools/db_query.py`, `tools/db_gaps.py`) or print only the keys and the rows that are needed (`python -I -c` with a filter, `head`, `grep -c`).
- Never open `data/raw/` and `data/register_slices/` directly: they are loaded into the index by `tools/db_build.py`.
- Change a JSON file with a script that touches only the needed keys (`tools/apply_*.py`), not by reading the file and writing it back by hand.
- An answer of Gemini is checked by its `verify_*` / `apply_*` script and only a summary is shown (taken / rejected / not found), not the rows.
- A long file is read with an offset and a limit, a long command output is cut (`| tail`, `| head`).
- The scripts that print to the console start with `sys.stdout.reconfigure(encoding="utf-8")` (the console of Windows is cp1252).
