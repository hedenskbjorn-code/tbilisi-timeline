# Pending work and how to resume it

State of 2026-11-23. Everything below is local and unpublished unless it says otherwise. The weekly limits of Gemini (the group of Gemini 4 Argon and the main group) were at 0 % on 2026-11-23 and refresh about 2026-11-28 to 2026-11-30.

## 1. Gemini runs waiting for the quota (one command)

    python -P tools/gemini_all.py

regenerates every task file in `for_gemini/from_desktop/` (that folder is not in git) and writes `ALL_TASKS_for_gemini.md`, which lists the tasks, their result files and their status. Launch phrase for Gemini:
"Read `C:/Projects/tbilisi-timeline/for_gemini/from_desktop/ALL_TASKS_for_gemini.md` and carry out all the tasks in it in order; save the results next to the task files."
A result file in which every row is `not_found` counts as not done (it is what a failed run leaves).

| Task | Result file | After the result arrives |
|---|---|---|
| KA: Georgian text of the 27 descriptions of monuments (small, do first) | `monuments_KA_result.json` | `python -P tools/apply_monuments_ka.py`, then `python -P tools/apply_monuments.py` |
| B1..B4: names of the 125 nameless places of worship (search) | `churches_B<n>_result.json` | `python -P tools/verify_search.py churches <file>`; **TODO: write `tools/apply_churches_b.py`** (the accepted names go to `tools/churches_names.json`-like input of `tools/build_religious_osm.py`; the name of an object that was nameless must also stop being "denomination, street") |
| E1..E6: description, year, author and Commons photo of the monuments that have nothing (search) | `monuments_E<n>_result.json` | `python -P tools/verify_search.py monuments <file>`, then `python -P tools/apply_monuments.py`; **TODO: wire `commons_file` of the verified rows into the photos** (descriptions are wired already) |

Done and applied: parks (`tools/apply_parks_result.py`), names of 88 of 92 places of worship (`tools/apply_churches_a.py`), folk-name points (`tools/verify_folk_points.py`).

## 2. Open items of the data

- Folk names without a point: Zemeli (Rustaveli Square area), "Rike jugs" (the OSM way that Gemini gave is unknown to Nominatim), "Mikhailovi" and "Aramyants" hospitals. They need a source that names the place.
- Names of places of worship from Gemini (task A) were spot-checked on 27: about 4 lost a place qualifier (for example "Orkhevi St. Nino"). The 4 rows that failed the lint (`tools/apply_churches_a.py`) keep the forms of OSM.
- 27 monument descriptions come from the introductions of Wikipedia articles about the person shown (`tools/mon_subject_leads.py`, checked by `tools/verify_search.py`); about 60 more monuments with an author or a year have no usable source yet.
- Doubtful values found on the way, not checked: the year of the memorial of the heroes of the war for the integrity of Georgia (the data says 2003, reports say 2010); the position of the statue of Kote Marjanishvili (KAW_077, far from the theatre).
- The analysis of gaps in `data/cache/` that Gemini made and that is NOT applied: `street_points_candidates.json` (388 streets without a line: 135 found in OSM under their name, 5 at a crossing of two streets named by the encyclopedia, 72 beside one neighbour; the last two groups must be looked through by hand), `register_desc_dates.json` (13 buildings whose description names the exact year), `tram_enc2008_citations.json`.
- 95 nameless plaques: only 4 have an inscription; the names may be in the descriptions or categories of their Commons files.

## 3. Ideas that were evaluated and not done

- Profile of the year slider on a phone (a 4x slower CPU gave 30 to 230 ms per step): the layers of monuments, plaques and modernism rebuild their GeoJSON with `setData` at every year; `setFilter` with from/to properties may be cheaper. Measure before changing.
- `history_events.json` is the heaviest data file of the first screen (197 KB gzip): a compact index at the start and the texts on demand.
- Presets of layers, accordion groups in the filters panel.
- A single build order (`tools/build_all.py`) and a common module for the `verify_*.py` scripts. Today the order of the last steps is: `apply_places.py`, `apply_folk.py`, `apply_parks.py`; `build_religious_osm.py`; `apply_monuments.py`.

## 4. The project index (SQLite)

`python -P tools/db_build.py --check` builds `data/db/project.sqlite` (not in git, rebuilt from nothing in under a second) from `site/data/*.json`, the verifiers' results and the Gemini task files; `--check` compares its counts with the JSON files. Schema: `tools/db/schema.sql`. Questions: `python -P tools/db_query.py stats|missing|tasks|find|near|sql` (read-only).
It is derived data: the JSON files stay the source of truth, nothing reads the index at runtime, the site does not use it.
Built for the whole of Georgia: objects have a region (country > city > district), ids carry a city code (`TB/mn:KAW_015`), every fact keeps source, quotation and status (imported / verified), positions are in an R-tree, names in a full-text index; a synthetic test with 1,000,000 objects loads in about 9 s. A new city = a new entry in `CITIES` of `tools/db_build.py` plus its data folder (same layout as `site/data`). Filled by default: the layers of the site for Tbilisi and the register of Tbilisi (2,599 objects; the index is about 22 MB). `--georgia` additionally loads the WHOLE register of immovable cultural heritage of Georgia (kept opt-in: the project is about Tbilisi for now) (`data/raw/PS.ImmovableMonumentObjectP_<date>.geojson`, the newest file is taken): 20,715 objects with region, municipality, address, period, functions, protection status and the description (Georgian), the Tbilisi ones joined to the derived fields of the site by place and name. With `--georgia` the index is about 100 MB and builds in about 2 s.
Not done yet: nothing outside the register is loaded for the other regions (OSM, Wikidata, Commons are the next sources); about 16 % of the register objects have a year (only dates written as "<year> წ."), the rest have a period in words (`fact: period`); the importers read fixed file names; the register has only Georgian names; the old `*_verified.json` caches are not imported as facts (only what is in the site files); tasks are matched to objects by id prefix; the weekly register download is not yet turned into updates of the index.

## 5. Before a release

1. `python -P tools/verify_<x>.py --refresh` for the verifiers whose data changed (the page cache `data/cache/http_text_cache.json.gz` is otherwise used).
2. `node tests/check_data.mjs`, `node --test tests/*.test.mjs`, `node --test --test-concurrency=1 tests/e2e/*.test.mjs`.
3. `python -P tools/db_build.py --check` (the index agrees with the files).
4. Commit only own files (not `notes/`, not `tests/e2e/_*.mjs`); push `main`; fast-forward `v2-foundation`; check the live site.
