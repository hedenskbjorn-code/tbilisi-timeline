# Tbilisi through time

A non-commercial hobby project: an interactive map of Tbilisi with a timeline slider (100–2026; the early centuries are compressed, and the scale can be zoomed).
Moving the slider changes what is shown: objects of the national register of immovable cultural heritage appear by their (estimated) date of construction, and old city plans and traced city limits are shown for the years they cover.
Along the scale: historical events with sources (invasions, floods, earthquakes, as well as buildings, openings and the oldest surviving monuments), a "Views" panel with historical and recent photographs of the period, and a search over objects, events and years.
The site is available in Georgian, English and Russian.

## Live site
Published with GitHub Pages from the `site/` folder (see `.github/workflows/pages.yml`).

## How it is built
- `site/` — the static site (plain HTML/JS/CSS, [MapLibre GL JS](https://maplibre.org/) 4.7.1 from a CDN). No bundler/build step.
- `tools/` — Python and Node.js data preparation, georeferencing (`warp.py`), photo lookup (`fetch_photos.py`), and verification scripts.
- `viewer/` — a local-only helper tool for placing control points and tracing boundaries. **Never expose it to the internet**: it can write files and run scripts on the machine it runs on.

## Data and licences

### Sources and data attributions
- **Heritage objects:** register of the Georgian National Agency for Cultural Heritage Preservation. No written open licence for this data could be found; only a reduced extract (name, address, coordinates, dates, register number) is used, for non-commercial purposes. Object dates are estimates derived from register records.
- **Old plans:** Tiflis 1735 (Vakhushti), 1785 (Pishchevich), 1800 (Chuiko), 1844 (Military Topographic Depot), 1887 (A. Ilyin), and 1913 (city survey department) — scans from Wikimedia Commons (public domain). The georeferenced images are approximate; estimated accuracy is shown on the page.
- **Administrative & city boundaries:**
  - Tbilisi administrative boundary (2019): OCHA COD-AB Georgia v01 via HDX (source: National Statistics Office of Georgia), CC BY-IGO.
  - District boundaries and names (10 districts): © OpenStreetMap contributors, ODbL 1.0 (`site/data/districts.json` is a derived database; keep the licence and attribution when reusing it).
  - 1999–2005 city boundary: geoBoundaries ADM2 (metadata: 2007, public domain; date unconfirmed).
  - Built-up outlines since 1972: GUSV, Zenodo (`doi:10.5281/zenodo.14523232`), CC BY 4.0 (smoothed and simplified). 1954 outline: U.S. Army Map Service sheet NK 38-8 (public domain).
  - 1924 and 1934 outlines & city area figures: digitised from land-use maps in N. Kharebava, PhD thesis, Ivane Javakhishvili Tbilisi State University, 2024.
  - Tbilisi Sea & earlier salt lakes: © OpenStreetMap contributors (ODbL 1.0), with pre-reservoir lakes traced from a c. 1911 Tiflis environs topographic sheet (Wikimedia Commons, public domain).
- **Base map:** [OpenFreeMap](https://openfreemap.org) vector tiles, © OpenMapTiles, data © OpenStreetMap contributors.
- **Curated layers & historical data:**
  - **Religious buildings:** curated buildings plus worship buildings extracted from the heritage register and OpenStreetMap.
  - **Science, culture & education:** curated institutions (universities, institutes, libraries, observatories, museums, theatres, cinemas, concert halls) plus schools and kindergartens from the heritage register (register dates reflect the building rather than founding year).
  - **Entrance halls (`/entrances/`):** three walking routes past 20 historic residential buildings, using facts from T. Kutateladze's dissertation (2015) and the heritage register (no door codes are published).
  - **Tbilisi Running Club layer (`/run/`):** geometry of the TRC City Run 2026 GPX track (9.69 km, no personal data) and nearby architectural sights.
  - **Historical events & battle points:** compiled from cited Wikipedia articles and historical literature (see `site/data/history_events.json`), with coordinates from Wikipedia and Wikidata.
  - **Rulers & flags:** portraits and attested state flags from Wikidata and Wikimedia Commons under free licences.
- **Photographs:** object cards and the "Views" panel use Wikimedia Commons photographs under public domain or free licences (CC0 / CC BY / CC BY-SA) with author, licence, and source link, alongside owner-permitted photographs. Object photos matched by coordinates are checked against titles and addresses, though occasional mismatches with adjacent buildings may remain.

### User submissions and privacy
- Visitor-submitted photographs and problem reports undergo pre-moderation and are never published automatically.
- Approved visitor photographs are published under **CC BY-SA 4.0** with EXIF metadata stripped; optional geolocation is used solely to verify proximity during moderation and is never published.
- Site visits are counted via cookie-free Cloudflare Web Analytics.

### Project licences
- The code in this repository is provided as is, without warranty, under the **PolyForm Noncommercial License 1.0.0** (`LICENSE`).
- Compiled texts and project datasets are licensed under **CC BY-NC 4.0**; third-party materials retain their respective licences and attributions (see `NOTICE.md`).

## Limitations
Dates, boundaries and georeferencing are approximations made from open sources; they are not an authoritative record.
