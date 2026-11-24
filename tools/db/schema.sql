-- The project index (tools/db_build.py builds it from the JSON files; the JSON files stay the source of truth, this file is derived and may be deleted and rebuilt at any time).
-- Made to grow from Tbilisi to the whole of Georgia: every object belongs to a region (country > region > city > district, a tree), ids are "<layer>:<local id>" and never repeat across layers or cities,
-- every fact keeps its source, its quotation and its status, positions are indexed by an R-tree, names by full-text search. Nothing here is specific to one city.

CREATE TABLE region (
  id TEXT PRIMARY KEY,                 -- GE, GE-TB, GE-TB-Samgori ...
  kind TEXT NOT NULL,                  -- country | region | city | district
  parent TEXT REFERENCES region(id),
  name_ka TEXT, name_ru TEXT, name_en TEXT
);

CREATE TABLE layer (
  id TEXT PRIMARY KEY,                 -- reg, rel, relosm, sci, edu, pl, mn, pq, md, st
  title TEXT NOT NULL,
  file TEXT,                           -- the file of the site that this layer is published in
  license TEXT
);

CREATE TABLE object (
  rowid_ INTEGER PRIMARY KEY,          -- the key of the R-tree
  id TEXT NOT NULL UNIQUE,             -- layer:local id
  layer TEXT NOT NULL REFERENCES layer(id),
  local_id TEXT NOT NULL,
  region TEXT REFERENCES region(id),
  kind TEXT,
  lat REAL, lon REAL,
  year_from INTEGER, year_to INTEGER,
  status TEXT,
  props TEXT                           -- the fields that only this layer has, as JSON
);
CREATE INDEX object_layer ON object(layer);
CREATE INDEX object_region ON object(region);
CREATE INDEX object_years ON object(year_from, year_to);                      -- "what existed in 1913"
CREATE VIRTUAL TABLE object_geo USING rtree(id, min_lon, max_lon, min_lat, max_lat);   -- id = object.rowid_

CREATE TABLE name (
  object_id TEXT NOT NULL REFERENCES object(id),
  lang TEXT NOT NULL,                  -- ka | ru | en
  name TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'official',   -- official | old | folk | alt
  year_from INTEGER, year_to INTEGER,
  pend INTEGER NOT NULL DEFAULT 0      -- the name waits for a language
);
CREATE INDEX name_object ON name(object_id);
CREATE VIRTUAL TABLE name_fts USING fts5(name, object_id UNINDEXED, lang UNINDEXED, kind UNINDEXED, tokenize='unicode61');

CREATE TABLE source (
  id INTEGER PRIMARY KEY,
  url TEXT NOT NULL UNIQUE,
  host TEXT,
  lang TEXT
);

CREATE TABLE fact (
  id INTEGER PRIMARY KEY,
  object_id TEXT NOT NULL REFERENCES object(id),
  key TEXT NOT NULL,                   -- description | origin | folk_meaning | function | sculptor | architect | status | note | ...
  lang TEXT,
  value TEXT NOT NULL,
  source_id INTEGER REFERENCES source(id),
  quote TEXT,
  status TEXT NOT NULL DEFAULT 'imported'  -- imported (curated data) | verified (the quotation stands on its page: a verify_*.py script) | pending | rejected
);
CREATE INDEX fact_object ON fact(object_id, key);
CREATE INDEX fact_status ON fact(status, key);                                -- the views of what is verified and what is not

CREATE TABLE media (
  object_id TEXT NOT NULL REFERENCES object(id),
  kind TEXT NOT NULL DEFAULT 'photo',
  file TEXT, thumb TEXT, page TEXT, author TEXT, license TEXT,
  near INTEGER NOT NULL DEFAULT 0      -- found by the coordinates only: may show a neighbouring object
);
CREATE INDEX media_object ON media(object_id);

CREATE TABLE task (                    -- a task for Gemini (or for anyone else): the file, the result, the state
  id TEXT PRIMARY KEY,                 -- the stem of the file: churches_B1, monuments_E3 ...
  kind TEXT,
  task_file TEXT, result_file TEXT,
  status TEXT NOT NULL,                -- queued | done | empty (a result in which every row is not_found: a failed run)
  result_rows INTEGER, found INTEGER
);
CREATE TABLE task_row (
  task_id TEXT NOT NULL REFERENCES task(id),
  object_id TEXT,                      -- as far as the id of the answer is an object of the index
  row_id TEXT,
  status TEXT
);
CREATE INDEX task_row_object ON task_row(object_id);

-- what a layer still lacks
CREATE VIEW v_object_state AS
SELECT o.id, o.layer, o.region, o.kind,
       EXISTS (SELECT 1 FROM name n WHERE n.object_id = o.id AND n.kind = 'official') AS has_name,
       (SELECT COUNT(DISTINCT n.lang) FROM name n WHERE n.object_id = o.id AND n.kind = 'official') AS name_languages,
       EXISTS (SELECT 1 FROM fact f WHERE f.object_id = o.id AND f.key = 'description') AS has_description,
       EXISTS (SELECT 1 FROM media m WHERE m.object_id = o.id) AS has_photo,
       EXISTS (SELECT 1 FROM fact f WHERE f.object_id = o.id AND f.status = 'verified') AS has_verified_fact
FROM object o;

-- ---- RAW data as it came from the sources (nothing is interpreted here: what the source said, with the file it came from) -------------------------------------------------------------------------------
-- The curated tables above (object, name, fact, ...) are made from this and from the verified answers; a raw record is never edited, it is replaced when the file is downloaded again.
CREATE TABLE raw_file (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL,                -- osm | register | geoboundaries ...
  kind TEXT NOT NULL,                  -- overpass | geojson | list
  bytes INTEGER, sha256 TEXT,
  records INTEGER
);
CREATE TABLE raw_record (
  id INTEGER PRIMARY KEY,
  file_id INTEGER NOT NULL REFERENCES raw_file(id),
  source TEXT NOT NULL,
  rid TEXT NOT NULL,                   -- way/123, node/5, a register ID ...
  type TEXT,                           -- way | node | relation | feature
  lat REAL, lon REAL,                  -- the centre (or the point)
  tags TEXT,                           -- the tags / properties of the source as JSON, whole
  geom TEXT                            -- the geometry as compact JSON when the source gives one
);
CREATE INDEX raw_record_rid ON raw_record(source, rid);
CREATE INDEX raw_record_file ON raw_record(file_id);
CREATE VIRTUAL TABLE raw_geo USING rtree(id, min_lon, max_lon, min_lat, max_lat);       -- id = raw_record.id (only the records that have a position)
