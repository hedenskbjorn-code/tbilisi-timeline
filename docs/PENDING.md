# Pending work and how to resume it

The layout of the folders is in `docs/LAYOUT.md` (the working area of the tasks for Gemini is `work/gemini`: tasks, results, batches, archive).

State of 2026-11-23. Everything below is local and unpublished unless it says otherwise. The weekly limits of Gemini (the group of Gemini 4 Argon and the main group) were at 0 % on 2026-11-23 and refresh about 2026-11-28 to 2026-11-30.

## 1. Gemini runs waiting for the quota (one command)

    python -P tools/gemini_all.py

regenerates every task file in `work/gemini/` (that folder is not in git) and writes `ALL_TASKS.md`, which lists the tasks, their result files and their status. Launch phrase for Gemini:
"Read `C:/Projects/tbilisi-timeline/work/gemini/ALL_TASKS.md` and carry out all the tasks in it in order; save the results next to the task files."
A result file in which every row is `not_found` counts as not done (it is what a failed run leaves).

| Task | Result file | After the result arrives |
|---|---|---|
| KA: Georgian text of the 27 descriptions of monuments (small, do first) | `results/monuments_KA.json` | `python -P tools/apply_monuments_ka.py`, then `python -P tools/apply_monuments.py` |
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

## 3a. Waiting for Gemini or for the owner's decision (site)

- **Version.** 1.8.7 was published twice under one number (commits 6696b8e and a635d4a, then 5a403c4 added content); the plan is 1.9.0 (2.0 stays for all of Georgia): move the 10 items added after 6696b8e to a new entry and add items for the parks (90), the names of 92 places of worship, "Also here", 27 descriptions of monuments and the unified old map. The Georgian text of the new items is needed first (the data check does not let a missing Georgian text through): a task "changelog_190" for Gemini.
- **Unified old map (done locally, not published):** one box "Old map of the chosen year", one opacity slider, a list "Which map" (automatic by the year / plans only / a scale of the topographic map). The Georgian strings of it were assembled from words that the site already uses and must be looked through by Gemini: `showPlan`, `planOpacity`, `mapSrc`, `mapSrcAuto`, `mapSrcPlan`; the same for `approx` and `kind_building` of the places.
- **Layers to merge (proposal, not started):** the five boxes of the register buildings into one with a filter by function; science + education; monuments + plaques; the three layers of names of areas; modernism as a style filter; the backgrounds in one group; the experimental streets of 1913 hidden.
- **Drafts:** `data/cache/church_drafts_code_artifact.md` (137 churches without sources) became the task `churches_C` (97 entries to verify); nothing from it is on the site.

## 3a2. The tour (done locally, waits for Gemini)

Five new steps about the filters were added to the tour (`site/data/tour.json`): the blocks and the counter, the old map, the groups, the layers and the years, the reset. They open the panel of the filters and put it back as it was (`site/js/tour.js`, `window.TT_panels`). Russian and English are ready; the Georgian text is the task `tour_filters` of the package (`tools/tour_ka_task.py`, then `tools/apply_tour_ka.py`); until it is there `tests/check_data.mjs` stops the deploy.

## 3a3. The panel of the filters, second pass, and the checked finds of Gemini (2026-11-24, local, not published)

Panel (tests/e2e/panel.test.mjs): transport is a group of five boxes (`showTrMetro/Tram/Rail/Road/Cable`, the master box is `secTransport`) that filter the lines by kind in `updateTransport`; the layer of places and its legend moved to the block of boundaries and streets;
"near me" and "only without a photograph" stand in the strip `#fquick` under the head; on a phone a click of the visitor opens one block and closes the others. A row with the attribute `hidden` was shown anyway (`.row{display:flex}`): `.row[hidden]{display:none}`.
The Georgian words of the five new boxes are assembled from the words of `trKinds` / `legTr*` (flagged for the review by Gemini). Not done: mini-legends as chips, presets (they need new texts), "showTransport" strings are left unused in i18n.js.

Also removed on the owner's word: the filter and the layer of the City Run route (the run has its own page /run/; its data files stay; the i18n strings `showRun`, `run*` are unused now); the one-line legends of the layers of one kind
(plaques, modernism) are replaced by a colour dot in the row of the box.

The names of OSM quarters, squares and bridges (answer osm_names of Gemini, 127 rows) are in the layer of places as cards without a description (`tools/apply_osm_names.py`, `pk: 1`, ids `osm-<n|w|r><id>`): 118 added, 9 villages outside the city left out;
the three dropped district pins and the names with "raioni" never come back (the task and the applier both skip them). Run order of the places: apply_places, apply_folk, apply_parks, apply_osm_names, apply_places_edits.
The Wikipedia intros of monuments and plaques (level B, decided 2026-11-24) live in `data/cache/wiki_intros.json` (not in git) and are merged by `tools/apply_monuments.py`.

The outlines of quarters and squares of the layer of places (`g`, 72 added by hand on 2026-11-24, source not recorded: see the open question below) have their own box `showPlaceAreas` (off by default, shown only while the layer is on, in the block of boundaries and streets);
the outline of the hippodrome goes with the layer; every outline keeps its own colour of the palette; the note about the hippodrome (`area_note`) stands on its card only. The Georgian label is assembled from the words of the site (to be read by Gemini).
The contours are kept in `tools/place_contours.json` and given back by `tools/apply_places_edits.py` (checked: a places.json without them comes back byte-identical); `notes/roads_report.md`, deleted by hand on 2026-11-24, was restored from git. Rules for Gemini: `GEMINI.md` in the project root (local, not in git).

Finds of Gemini: monuments_KA (27 descriptions) and the search results E1-E3 are in `site/data/sculptures.json` (41 descriptions, 36 with ka); churches B2, B3 and the new churches of C (5 of 6, `tools/verify_church_drafts.py`, `data/cache/church_drafts_verified.json`) are verified but NOT yet in the data
(an `apply_churches_b.py` / apply for C is to be written; B4 the mosque and C no. 56 were rejected for the proof of the place). Lesson: `data/cache/monuments_names_verified.json` was emptied when the batch table `batches/monuments_names/monuments_names_batch_01.md`
was regenerated for 5 rows; it was rebuilt from `results/monuments_names.json` (229 rows) and `apply_monuments.py` then gave the same names as git. Do not regenerate a batch table before its answer is applied.

## 3b. Tidy of the folders

Done (2026-11-24): `for_gemini/from_desktop` became `work/gemini/{tasks,results,batches,archive}`, `notes/` became `work/notes/`, `PENDING.md` moved to `docs/`, `tools/paths.py` holds the paths; 883 files moved and checked by SHA-256, every builder and verifier was run again on the new layout and the files of `site/data` stayed byte for byte the same.
To do (step 3, after the release of 1.9.0): the checked data files of the root of `data/` to `data/curated/`, `tools/` into subfolders by role (fetch, verify, build, apply, db, gemini) with `git mv`; the two tables `work/notes/tbilisi_monuments_full.csv` and `tbilisi_plaques_osm.csv` are inputs of `tools/build_monuments.py` and are not in git: they belong to `data/curated/`.

## 3c. District cores and pins (`data/district_labels.json`, `site/data/districts.json`, `site/data/places.json`)

Why the 10 administrative district labels and `places.json` pins sit in the **urban/historical cores** rather than geometric polygon centroids or raw OSM admin nodes:
- **Geometric/OSM admin centroids fall on mountain slopes or outer suburbs** (km away from the city core): Samgori in Lilo/Tetrikhevges (+7.25 km), Saburtalo near the Dighomi border (+5.99 km), Mtatsminda on the Tsavkisi slope (+4.24 km), Vake in Bagebi valley (+3.75 km), Krtsanisi toward Ponichala (+4.14 km), Didube in Dighomi Massive (+3.19 km), Chugureti on the Kukia slope (+2.33 km), and Nadzaladevi up near Sanzona/Tbilisi Sea.
- **Urban-core conventions kept across `district_labels.json`, `districts.json`, and `places.json`:**
  - `Saburtalo`: 26 May Square (`41.7179, 44.7781`, by the owner's request).
  - `Nadzaladevi`: moved to the urban/historical core at Metro Nadzaladevi / Tsotne Dadiani Ave (`41.7316, 44.8026`), separated from `Старый Надзаладеви` (`41.73113, 44.80905`).
  - `Mtatsminda`, `Vake`, `Saburtalo`: only the urban quarter cards (`district-n1650325626`, `district-n919711142`, `district-n930153087`) are kept in `places.json`; the outer `район ...` duplicates are omitted.
  - `Chugureti`, `Isani`, `Samgori`, `Krtsanisi`, `Didube`: the `district-n*` cards (which carry descriptions/etymologies) are placed at the `district_labels.json` urban cores.
- **Note for builders (`apply_osm_names.py` / `osm_names_task.py`):** do not re-add bare `osm-n*` / `osm-r*` nodes that sit on top of `district-n*` urban cores (`osm-n13477133330` Chugureti, `osm-n1665566310` Samgori, `osm-n12456415259` Krtsanisi, `osm-n12456415257` Isani, `osm-r10790351` Nadzaladevi — all removed as 0.2–0.5 m / Lotkini duplicates).

## 4. The project index (SQLite)

`python -P tools/db_build.py --check` builds `data/db/project.sqlite` (not in git, rebuilt from nothing in under a second) from `site/data/*.json`, the verifiers' results and the Gemini task files; `--check` compares its counts with the JSON files. Schema: `tools/db/schema.sql`. Questions: `python -P tools/db_query.py stats|missing|tasks|find|near|sql` (read-only).
It is derived data: the JSON files stay the source of truth, nothing reads the index at runtime, the site does not use it.
Built for the whole of Georgia: objects have a region (country > city > district), ids carry a city code (`TB/mn:KAW_015`), every fact keeps source, quotation and status (imported / verified), positions are in an R-tree, names in a full-text index; a synthetic test with 1,000,000 objects loads in about 9 s. A new city = a new entry in `CITIES` of `tools/db_build.py` plus its data folder (same layout as `site/data`). Filled by default: the layers of the site for Tbilisi and the register of Tbilisi (2,599 objects; the index is about 22 MB). `--georgia` additionally loads the WHOLE register of immovable cultural heritage of Georgia (kept opt-in: the project is about Tbilisi for now) (`data/raw/PS.ImmovableMonumentObjectP_<date>.geojson`, the newest file is taken): 20,715 objects with region, municipality, address, period, functions, protection status and the description (Georgian), the Tbilisi ones joined to the derived fields of the site by place and name. With `--georgia` the index is about 100 MB and builds in about 2 s.
Not done yet: nothing outside the register is loaded for the other regions (OSM, Wikidata, Commons are the next sources); about 16 % of the register objects have a year (only dates written as "<year> წ."), the rest have a period in words (`fact: period`); the importers read fixed file names; the register has only Georgian names; the old `*_verified.json` caches are not imported as facts (only what is in the site files); tasks are matched to objects by id prefix; the weekly register download is not yet turned into updates of the index.

## 5. Before a release

1. `python -P tools/verify_<x>.py --refresh` for the verifiers whose data changed (the page cache `data/cache/http_text_cache.json.gz` is otherwise used).
2. `node tests/check_data.mjs`, `node --test tests/*.test.mjs`, `node --test --test-concurrency=1 tests/e2e/*.test.mjs`.
3. `python -P tools/db_build.py --check` (the index agrees with the files).
4. Commit only own files (not `work/`, not `tests/e2e/_*.mjs`); push `main`; fast-forward `v2-foundation`; check the live site.
