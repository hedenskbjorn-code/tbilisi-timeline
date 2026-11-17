# Tbilisi through time

A non-commercial hobby project: an interactive map of Tbilisi with a timeline slider (1800-2025).
Moving the slider changes what is shown: objects of the national register of immovable cultural heritage appear by their
(estimated) date of construction, and old city plans and traced city limits are shown for the years they cover.
The page is available in Georgian, English and Russian.

## Live site
Published with GitHub Pages from the `site/` folder (see `.github/workflows/pages.yml`).

## How it is built
- `site/` - the static page (plain HTML/JS/CSS, [MapLibre GL JS](https://maplibre.org/) 4.7.1 from a CDN). No build step.
- `tools/build_site_data.py` - builds `site/data/` from the working data in `data/` (not published here).
- `tools/warp.py` - georeferences old plans from control points (affine, optionally with a thin-plate-spline residual) and writes a north-up WebP.
- `tools/fetch_photos.py` - looks up Wikimedia Commons photos near each object (by coordinates only).
- `viewer/` - a local-only tool for placing control points and tracing boundaries. **Never expose it to the internet**: it can write files and run scripts on the machine it runs on.
- `sources.md` - detailed working notes: sources, methods, accuracy figures, open questions (in Russian).

## Data and licences
- Heritage objects: register of the Georgian National Agency for Cultural Heritage Preservation. No written open licence for this data could be found; only a reduced extract (name, address, coordinates, dates, register number) is used, for non-commercial purposes. Object dates are estimates derived from register records.
- Old plans (Tiflis 1735 Vakhushti, 1785 Pishchevich, 1800 Chuiko, 1844 Military Topographic Depot, 1887 A. Ilyin, 1913 city survey department): scans from Wikimedia Commons, public domain. The 1821 plan (Shvetsov) is downloaded but not georeferenced yet. The georeferenced images are derived from them and are approximate (the accuracy is shown on the page).
- Administrative boundary of Tbilisi (2019): OCHA COD-AB Georgia v01 via HDX (source: National Statistics Office of Georgia), CC BY-IGO.
- District boundaries and names (10 districts): (c) OpenStreetMap contributors, ODbL 1.0 (`site/data/districts.json` is a derived database: keep the licence and attribution when reusing it).
- An older city boundary shown for 1999-2005 comes from geoBoundaries ADM2 (metadata: 2007, public domain); its date is not confirmed.
- City area figures: N. Kharebava, PhD thesis, Ivane Javakhishvili Tbilisi State University, 2024.
- Photos: Wikimedia Commons, shown with author and licence; they are matched to objects by coordinates only and may show a neighbouring building.
- Built-up outlines since 1972: GUSV, Zenodo doi:10.5281/zenodo.14523232, CC BY 4.0 (smoothed and simplified). 1954 outline: U.S. Army Map Service sheet NK 38-8, public domain.
- Base map: [OpenFreeMap](https://openfreemap.org) vector tiles, (c) OpenMapTiles, data (c) OpenStreetMap contributors.
- The code in this repository is provided as is, without warranty.

## Limitations
Dates, boundaries and georeferencing are approximations made from open sources; they are not an authoritative record.
