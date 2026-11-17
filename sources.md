# Tbilisi timeline: data sources (checked 2026-11-17)

Status legend: OK = opened and read; BLOCKED = could not be read (reason given); NOT CHECKED = not opened.

## Boundaries / urban growth
| Source | What | Status |
|---|---|---|
| Tsitsagi et al., "Tbilisi Through Time", Georgian Geographical Journal, 2022 https://journals.4science.ge/index.php/GGJ/article/view/758 | Georeferenced plans (1735, 1800, 1828, 1844, 1867, 1887, 1902, 1913; also 1924 1:6000, 1934 1:8000, 1955 1:25000, 1970 1:10000), WGS-84 / UTM 38N | Mentioned in search snippet only. NOT CHECKED: whether layers are downloadable. Ask the authors. |
| Georgian Encyclopedia: Tbilisi Governorate (1846-1917), Tbilisi Uezd | Administrative history, no geometry | Seen in search results only |
| Wikipedia: districts (2014: 10 districts, 33 boroughs; Didgori abolished 2013; Old Tbilisi district 2007-2013) | Dates only, no historical geometry | Seen in search results only |

## Old plans (scans)
| Year | Source | License | Georeferenced |
|---|---|---|---|
| 1735 Vakhushti, 1782, 1785 (Pishchevich), 1800, 1802, 1809, 1821, 1844, 1850, 1876, 1878, 1884, 1887, 1911, 1913, 1914 (Baedeker, Wagner & Debes) | Wikimedia Commons, Category:Old maps of Tbilisi (47 files) https://commons.wikimedia.org/wiki/Category:Old_maps_of_Tbilisi | All 47 files carry "Public domain" / "No restrictions" in Commons metadata (checked via Commons API 2026-11-17). Commons' own claim, not independently verified; per-file source pages checked for 1782 (CGVIA fund VUA 22656), 1850 (Kavkazsky kalendar 1851, dlib.rsl.ru), 1887 (PD-RusEmpire, Ilyin, St Petersburg). | No (verified for the three above). Resolution: 1782 8966x6021; 1821 7059x12735; 1844 9364x8432; 1878 9534x7077; 1913 5907x5935; 1887 4925x4746; 1850 2023x2310 (low) |
| 1850 colour plan; 1909 plan from Kavkazsky kalendar | National Archives of Georgia library catalogue https://library.archives.gov.ge/bib/2156 , /2116 | Catalogue records only, no scans seen | No |
| 1914 Wagner & Debes | Avenza (paid, app only) | Commercial | n/a |
| Soviet: USSR map NK 38-8 (Tbilisi), dated 1954 in Commons metadata, 5922x4739 | Commons (same category) | Commons says Public domain. Original publisher and basis for PD NOT CHECKED (verify before use). | No |
| Also in category: 1671 Chardin (published 1723), 1730s Khojivank cemetery maps, 1850/1878/1887 Khojivank cemetery maps, 1871 Vakhushti (Russian version), 1879 "Plan de Tiflis (2e ed.)" BnF, 1897 map | Commons | Public domain per metadata | No |
| 1934, 1950s, 1970s, 1971 | Ilia State University, Urban Assemblage https://urbanassemblage.iliauni.edu.ge/?p=3577 | NOT CHECKED | NOT CHECKED |

## Monuments
| Source | Status |
|---|---|
| National Agency for Cultural Heritage Preservation of Georgia, GIS portal | Open download/API not confirmed. NOT CHECKED directly. |
| Wikidata SPARQL (items located in Tbilisi Q994, P131*), run 2026-11-17 | Items with a heritage designation (P1435): 165. By designation: "cultural heritage in Georgia" 161, "Cultural Monuments of National Importance" 3, ensemble 1, tentative World Heritage 1. With inception date (P571): about 45-60 (counting differs by query: 45 distinct items, 60 item/century pairs). By century of inception: 7th:1, 12th:1, 14th:1, 15th:1, 17th:1, 18th:2, 19th:20, 20th:33. Additionally 179 items with coordinates and inception date but no heritage designation. |
| Conclusion | Wikidata is too thin on its own (about 165 designated monuments vs thousands in the national register). Need the national register or manual curation for the MVP (about 100-300 key monuments). |

## Russian / international catalogues
| Resource | Status |
|---|---|
| prlib.ru (Presidential Library) | BLOCKED: browser-check page ("Проверка безопасности"); not bypassed |
| rusneb.ru (NEB) | BLOCKED: page "Отключите VPN". The owner is in Georgia and says it is geo-blocking of foreign IPs, not a VPN. RF sites are likely closed to access from abroad. |
| loc.gov | BLOCKED: bot-verification page; not bypassed |
| davidrumsey.com | BLOCKED: "Verifying your access" page; not bypassed |
| oldmapsonline.org | Opens. At the Tbilisi position the list showed only regional maps (1:750,000 to 1:2,000,000, 1827-1870: Vandermaelen, Kiepert, Handtke, Flemming, Zakrzewski 1840 etc.), no city plans. Second attempt at higher zoom returned the same list (page may not have re-applied the position), so city-scale plans there are not excluded. |
| retromap.ru | Opens, map-viewport based; no text search for Tiflis. NOT CHECKED for Tbilisi. |
| etomesto.ru | BLOCKED: TLS certificate mismatch (cert issued for another host) |
| dlib.rsl.ru (RSL) | NOT CHECKED (linked from Commons 1850 file) |
| dspace.nplg.gov.ge (Georgia NPLG) | Only views/photos found via search; map search by "გეგმა"/"план Тифлиса" NOT CHECKED |

## Update 2026-11-17 (article and register)
- "Tbilisi Through Time" (PDF read in full, 11 pages; article is CC BY): corresponding author Nino Kharebava (TSU), email printed in the article: [e-mail removed]. Table 1 lists 15 sources: 1735 (1:500 000), 1800, 1828, 1844 (1:4100), 1867 (1:8400), 1887 (1:11 300), 1902 (1:4100), 1913 (1:8400), 1924 (1:6000), 1934 scheme (1:8000), 1955 topographic (1:25 000), 1970 general plan (1:10 000), Landsat 1988/2010/2020. No archive or library source is given for any plan. No data availability statement, no repository link. Layers: built-up and green areas drawn per map in ArcMap 10.8, WGS-84 / UTM 38N; Fig. 1 shows area and administrative-territorial division through time. City area 356 km2 until 2006, 502 km2 from 2006 (annexed villages). Five stages: pre-1800, 1800-1850, 1850-1930, 1930-1990, 1990-present, with lists of districts per stage (Table 2).
- Monument register: OFFICIAL GIS portal found: https://memkvidreoba.gov.ge (National Agency for Cultural Heritage Preservation, Norwegian-funded). Page https://memkvidreoba.gov.ge/downloadServices offers downloads (Shapefile, GeoJSON, Geodatabase), data dated 2026-11-16: immovable monument/object points (GeoJSON 86 MB, Content-Length 85,910,670) and polygons (GeoJSON 122 MB), physical and visual protection areas, general protection zones, museums, world heritage buffer zones. Covers all of Georgia, so Tbilisi must be filtered. A note on the page says the location accuracy field may say "needs refinement" (approximate). License/terms of reuse NOT FOUND on the pages read (not checked: contact page); must be clarified before publishing. NOT YET DOWNLOADED (needs owner approval). Whether the data has build/construction dates is NOT CHECKED (to see in the attributes).

## Update 2026-11-17 (register downloaded and inspected)
- Downloaded: `data/raw/PS.ImmovableMonumentObjectP_16.11.2026.geojson` (85,910,670 bytes, matches server Content-Length), from https://memkvidreoba.gov.ge/downloads/PS.ImmovableMonumentObjectP/ . CRS84 (lon/lat), MultiPoint geometry, 20,722 features for all of Georgia.
- Fields: ID, Name, FullName, ComplexName, Description (long Georgian text), StatusName, StatusDocDate/Number, RegistryN, CategoryName, WorldCategoryName, Region, Municipality, Settlement, Address, Period, ExactDate, DateRangeFrom, DateRangeTo, InitialFunction, CurrentFunction, Classification, Accuracy, X, Y, CreateDate.
- Tbilisi (Region/Municipality = თბილისი): 2,599 objects. Status: 1,841 cultural heritage monuments, 758 objects without status. Category: 17 "national", 2,582 without category. Classification: mostly architecture (about 2,176 plain "architecture"). Accuracy: 2,551 correct, 48 "needs refinement".
- Dating: ExactDate non-empty 2,391 (free-text Georgian, e.g. "1827 წ.", "end of the 19th century", "early 20th century"); Period non-empty 2,451 (mostly "19th century" 1,447 and "20th-21st centuries" 852; medieval about 100; bronze/iron age a few); DateRangeFrom/To only 73/70. So most dates are century-level; exact years are a minority. A parser for ExactDate (Georgian text -> year range) is needed.
- License: contact page ([e-mail removed], [phone removed]) and about pages have NO license or terms of reuse; footer says "© 2020 ყველა უფლება დაცულია" (all rights reserved). Data is publicly offered for download, but there is no explicit open license. For a non-commercial hobby project this is a gray area, not a permission; safest path: attribute the National Agency and ask by email for written permission (not sent; the owner said no letters for now).

## Update 2026-11-17 (plan aligner)
- Downloaded `data/raw/maps/tiflis_1887.jpg` (7,580,677 bytes) from Commons (File:Tiflis city plan, 1887.jpg, PD-RusEmpire).
- Built `viewer/` (index.html, app.js, maps.json, server.py): MapLibre overlay of the plan on OpenStreetMap, opacity slider, 4 draggable corners + centre handle, Save writes `data/georef/<id>.json` (TL,TR,BR,BL, lng/lat). Run: `python viewer/server.py`, open http://127.0.0.1:8765/viewer/ (127.0.0.1 only).
- Initial placement: similarity transform from 2 landmarks (Tbilisi Central Station 44.79778, 41.72333 and National Botanical Garden 44.8075, 41.68611; coordinates from Wikidata; plan pixels estimated by eye). Result: about 1.49 m per original pixel, rotation about -0.7 degrees, extent about 7.3 x 7.1 km. Visual check: Kura on the plan runs roughly parallel to the modern river with an offset of order 100-200 m (estimate from a screenshot, not measured).

## Update 2026-11-17 (auto-alignment experiment, 1913)
- Tried automatic fit of the 1913 plan to the OSM Mtkvari river (water extracted from the scan by colour: the river is drawn as thin navy hatching, extraction is fragmentary and noisy; similarity transform with bounded scale/rotation, robust loss).
- Result: FAILED validation against the owner's manual alignment. Auto fit differs from manual by 420-1070 m at sample points. Cost of the river fit is nearly the same for both (trimmed mean 97 m auto vs 103 m manual), so the river alone does not pin the position (the plan can slide along the river; the 1913 river also differs from the modern engineered channel).
- The initial 2-landmark guess was 390-860 m off the manual alignment, so manual refinement matters.
- Conclusion: river-only automation is not reliable. Better options: ground control points (6-10 per plan) with a warp, or add railway/street constraints.

## Update 2026-11-17 (control points + warp)
- Viewer now has a Control points mode (click a feature on the plan, then the same spot on the base map). Points are saved to `data/georef/<id>_gcp.json`. "Compute warp" runs `tools/warp.py` (affine or affine + thin-plate spline; model chosen by leave-one-out error; needs 3+ points, 6-10 recommended) and writes `data/warped/<id>.webp` + `.json` (north-up, Web Mercator-linear, transparent outside the plan). Server: `python viewer/server.py` on port 8799 (8765 belongs to the glovo-shelf container).
- Tested on synthetic points in a scratch copy (8 points, ~15 m noise): in-sample RMS 0.15 m, leave-one-out RMS about 60 m (mostly at the plan corners, extrapolation), inverse-warp round trip 0.33 px. Real accuracy depends on the clicked points.

## Update 2026-11-17 (1887 plan warped with control points)
- 7 control points on the 1887 plan, placed by me by reading labelled church symbols on crops around the predicted positions; target coordinates from OSM: Metekhi, Sioni, Anchiskhati, Vank, St Nicholas (Kharpukhi), Mama Daviti church, Ascension church. File: `data/georef/tiflis_1887_gcp.json`. Result: `data/warped/tiflis_1887.webp` + `.json`.
- Quality: affine fit residuals <= 26 m; model chosen by leave-one-out: leave-one-out RMS 30 m (per point 0-53 m); inverse-warp round trip 2.2 px. Scale about 1.44 x 1.36 m/px, close to the manual alignment. Weakness: points cluster in the old town and west-east axis, none in the far north/south, so the corners are extrapolated.
- The control-point alignment differs from the manual four-corner alignment by 110-180 m (nearly uniform shift, mostly toward the west/south-west). Not yet decided which one to prefer; point features (churches) support the control-point one.
- 1913 plan: not done. Buildings there are numbered (legend table), so church identification from the scan is ambiguous (tentative offsets +50 to +80 px east, 40-95 px north from the manual alignment, unverified).

## Update 2026-11-17 (1887 built-up boundary, draft)
- `data/boundaries/tiflis_1887.geojson`: 2 polygons (main built-up area, Navtlugi settlement), type built_up, confidence approximate. Outlined by eye on a gridded overview of the plan (automatic density detection failed: it picked up river hatching), converted to lng/lat with the 1887 control-point warp. Edges follow the dense street grid; open gardens and hillsides at the margins are only roughly separated. To be refined by the owner in the viewer.
- Fixed a viewer bug: boundary outlines were not drawn because MapLibre does not allow a data-driven line-dasharray; now solid (precise) and dashed (approximate) layers.

## Update 2026-11-17 night (1913 auto-registration attempts: all failed, nothing applied; monuments file built)
- Goal: georeference the 1913 plan automatically (owner asked: control points, river, railway). Everything below was tried against the 1887 control-point warp and OSM; none gave a reliable signal, so NO correction was applied: 1913 keeps the owner's manual four-corner alignment (`data/georef/tbilisi_1913.json`).
  - ECC (affine, multi-resolution) on thin-line maps of the two plans: correlation 0.32 -> 0.21 as resolution rose; result implied a 9 % scale change and 345 m shift: implausible.
  - Local phase correlation of line maps (80 windows): responses <= 0.07, shifts random.
  - Street corridors of the 1913 plan (light, unsaturated pixels) vs OSM roads (185k points, band-pass score): flat landscape, no peak (baseline -0.003, best 0.004 at a random shift).
  - Public-building footprints (red on 1887 vs black on 1913): only 2.6k red pixels vs 65k black; global response 0.02, local shifts erratic.
  - Railway extraction from 1913: rails are thin lines, thick-line extraction returned only frame artefacts. River hatching mask vs OSM Mtkvari (earlier test): same fit quality for very different alignments.
  - Manual cross-plan matching on side-by-side crops: displacements disagreed by 50-100 m between candidate features; 1913 buildings are numbered via a legend table I cannot read from the scan, so churches cannot be identified safely.
- Conclusion: the plans differ in style (1887 line drawing, 1913 filled blocks), so image-based matching fails; remaining option is manual control points on 1913 (viewer, Control points mode).
- Built `data/tbilisi_monuments.geojson` (7.2 MB, 2,599 Tbilisi objects, Point geometry) with parsed dates: year_from, year_to, year_est, date_precision (exact 340, quarter 1,477, middle 363, century 123, mixed 52, half 48, years 36, decade 10, era 21, unknown 129), date_source (ExactDate 2,338; Period 92; DateRange 40). Parser: `scratchpad` copy of `dates_ka.py` (Georgian text -> years; "end of 19th century" = 1876-1900, "beginning" = first 25 years, "middle" = years 31-70, "second half" = 51-100). Counts of objects with year_from <= year: 1800: 119; 1850: 645; 1887: 1,596; 1913: 2,254; 1950: 2,382; 2000: 2,457. Licence of the register data still unclear (see above).

## Next steps
1. Contact authors of "Tbilisi Through Time" / Ilia State University about layers and Soviet-era plans (and their license).
2. Commons licenses: done (all PD per metadata). Verify the Soviet 1954 map origin.
3. Monuments: Wikidata gives only 165 designated items; check the National Agency register/GIS portal and Georgian Wikipedia lists.
4. Blocked catalogues (prlib.ru, rusneb.ru, loc.gov, Rumsey): need a browser session from the owner (CAPTCHA/bot check; RF sites need a Russian IP).

## 1913 plan: georeferencing by user control points (2026-11-17)
- User placed 17 control points (data/georef/tbilisi_1913_gcp.json). Points 0, 2, 15 (0-based) are outliers (130-250 m; 0 and 2 share the same SW shift of ~160-180 m, likely a systematic click error) and are excluded via `python tools/warp.py tbilisi_1913 --exclude=0,2,15`.
- Result: affine, 14 points, in-sample RMS 35 m (max 67 m), leave-one-out RMS 46 m; TPS variants were worse (47-55 m). Scale ~1.29 m/px, rotation ~0.5 deg.
- The earlier manual 4-corner quad had ~140 m RMS at the same points.
- Visual check against OSM (river bend, bridges, old town): river and main streets overlap within a few tens of metres. Not checked at the far north/south edges (no control points there).
- tools/warp.py: added --exclude and an exact analytic inverse for the affine model (old regression-based inverse gave a 97 px round-trip error).
- Output: data/warped/tbilisi_1913.webp + .json

## Site prototype: timeline page (2026-11-17)
- site/index.html + app.js + style.css (MapLibre 4.7.1, RU/EN toggle). Data built by `python tools/build_site_data.py` into site/data (monuments.json slim 1.2 MB, plans.json, plan WebPs, boundary).
- Slider 1800-2025. Monuments appear when the estimated year (year_est, middle of the date range) <= slider year; objects with coarse date precision (century / half-century / mixed) are drawn hollow and faded; 129 undated objects are not shown. Colour: built within the last 25 years / earlier / national significance (17 objects).
- Plan shown = the latest plan with year <= slider year (no cross-fade between plans, no invented intermediate states). Boundary is shown only where one exists (1887 draft; 1913 not traced yet).
- Base map is OpenStreetMap raster tiles: fine for local development; before any public hosting use a basemap/provider that allows it (OSM tile usage policy).
- Open: register licence unclear (do not publish monuments data before clarifying); 1913 boundary; more plans; popups show Georgian names only.

## 1913 boundary (partial) and plan display period (2026-11-17)
- The green "границы города" line (legend colour RGB ~192,201,123) was found by colour; automatic extraction fails because park fills have a similar tint, so vertices were read by eye from half-resolution crops (tools/trace_1913_boundary.py). Only the north and east arc is traced (top edge, NE diagonal, Avlabar side, SE diagonal; ~15-40 m from the drawn line in four spot checks). West and south stretches are hidden under parks/tables and are NOT traced; no closed polygon.
- Site: a plan is shown from its year until the next plan; the last plan only for 10 more years (PLAN_AFTER in site/app.js), so 2000 shows the modern base map, not the 1913 plan.
- Register terms of use: memkvidreoba.gov.ge is a JavaScript-rendered site; a plain fetch of /downloadServices, /en and / returned only the page title, so terms could not be read that way. Web search found no stated licence either. Status: NOT FOUND (not "confirmed absent"). Owner decided not to write to the agency.
- Register coverage: all 2,599 Tbilisi objects (Municipality = Tbilisi). Objects dated after 1913: 240 (220 of them inside the 1913 plan area); after 1950: 90. Peak is 1875-1925 (1,608 objects). The register therefore contains almost nothing from the Soviet-era districts.

## Sources read on the owner's instruction (2026-11-17)
- "Тбилиси глазами инженера": found only a commercial excursion brand (ge.engineer-history.com; pages on Sputnik8, Tripster, Yandex Maps). No book/archive; its texts/photos are commercial content with no reuse licence, so NOT used.
- Kharebava N., "Mapping of Spatial-temporal Changes of Landcover (LULC) in Tbilisi" (Georgian title: მიწათსარგებლობის ცვლილება თბილისში – სივრცე-დროითი ანალიზი და ციფრული კარტოგრაფირება), PhD thesis, TSU 2024, 148 pp. https://tsu.ge/assets/media/files/shares/test folder/zustebi/Biblioteka/sadoqtoro_naSromebi/დისერტაცია_ხარებავა.pdf (6.7 MB, downloaded to scratchpad only, not in the project; no licence stated on the file). Only facts (areas, settlement lists) are used and cited; no text or figures copied.
  - City boundary area by plan: 1735 2 km2; 1800 3; 1828 9; 1844 13; 1887 28; 1913 29 (built-up 14.3 km2 = 49%, green 5 km2); 1999 354 (kept to 2005); 2006 502 km2 (annexation of neighbouring villages). Stored in data/city_area.json. The thesis also gives 26,070 ha for 1960, which does not fit this series; not used.
  - Settlement lists by period (usable for a future "districts" layer): by 1800 Chughureti and Kukia added; by 1921 Chughureti, Vera, Vake, Mtatsminda, Isani, Ortachala, Krtsanisi, Didube, Ghrmaghele; by 1990 Nadzaladevi, Svaneti quarter, Kukia, Metromsheni, Navtlughi, Saburtalo, Lotkini, Sanzona, Dighomi massif, Vashlijvari, Vedzisi, Delisi, Dampalo, Vazisubani, Varketili, Avchala, Zghvisubani (Temka); after 1991 villages such as Koshigora, Dighomi, Gldani, Zahesi, Mukhiani, Mukhatgverdi, Telovani, Didgori, Ponichala, Lilo, Okrokana, Tkhinvali, Tskneti, Kojori, Kikveti, Akhaldaba, Tsavkisi, Shindisi, Tabakhmela, Betania, Kvesheti. Exact years of each addition NOT given in the passages read.
- GTU journal "Modern problems of architecture and urban planning" No.2, 2012 (192 pp, repository iverieli.nplg.gov.ge, 12.5 MB, scratchpad only): planning history, mentions the 1934 first general plan of Tbilisi (Giprograd, Kharkov), 1933-34 Dinamo stadium competition, the 1970 general plan with a design horizon of 2000. Notes that old maps and engineering schemes sit in archives behind high access fees. Little directly usable for boundaries; not mined further.
- Photos: tools/fetch_photos.py (Commons geosearch, ~100 m grid cells, then local 30 m matching; Commons answers many requests with HTTP 429 so the run is slow). Output data/cache/photos_*.json, merged by build_site_data.py.

## 1887: новые точки на севере (2026-11-17)
- Файл точек: 11 точек. Точка 7 (1015,3383) выбивается на ~150 м, точка 10 (609,416) почти наверняка промах (масштаб между 9 и 10 ≈1,03 м/пикс против ≈1,4; ошибка 386 м относительно подгонки по 8 точкам).
- Точка 9 (1292,614): с ней TPS даёт 12,7 м внутри выборки, но LOO 66,7 м (сама точка по LOO 181 м); без неё LOO 29,5 м. Опубликована подгонка по 8 точкам (`--exclude=7,9,10`). Нужна независимая точка на севере (Нахаловка/Дидубе), чтобы проверить точку 9.

## Фото (Commons)
- Поиск по координатам (радиус 30 м) завершён: у 939 из 2599 объектов есть хотя бы одно фото, 1230 файлов, лицензии копируются из extmetadata Commons (в основном CC BY-SA 4.0, CC0, CC BY 4.0).
- Совпадение только по координатам: фото может показывать соседнее здание.
- `tools/fetch_photos.py`: запросы описаний переведены на POST (GET упирался в HTTP 414 из-за длинных грузинских названий), кэш пишется после каждой пачки.

### 1887: решение по северным точкам (2026-11-17)
- Владелец подтвердил: точка 9 стоит на вокзальной площади (Station Square, по OSM ≈ 44.798, 41.721; точка 9 в 30 м от неё). Точка 9 включена в подгонку, точки 7, 10, 11 исключены (`--exclude=7,10,11`): affine+TPS(1), 9 точек, in-sample 12,7 м (макс. 31), LOO 66,7 м (по самой точке 9 — 181 м, т.е. это экстраполяция на север от единственной опоры).
- Прежняя подгонка по 8 точкам: `scratchpad/tiflis_1887_8pt.*` (копия вне проекта). Точки 10, 11 (добавлены владельцем) на карте поставлены, вероятно, не на тот объект: по подгонке они должны лежать около 44.7854, 41.7229 и 44.7935, 41.7259.

### 1887: точки 12 и 13, повторная привязка (2026-11-17)
- Добавлены в `data/georef/tiflis_1887_gcp.json` (резерв: `.bak`): церковь Св. Александра Невского (пиксели 1547,1355; OSM 41.7113449, 44.8010227) и католическая церковь Св. Петра и Павла, «Нов. катол. соборъ» (1589,1456; OSM 41.7099554, 44.8018217). Пиксели сняты на глаз с увеличенных фрагментов (≈±10 px), координаты — центры зданий в OSM. Независимая проверка до включения: привязка по 8 южным точкам давала по этим церквам 93–106 м (смещение на юг), с точкой 9 — 40–52 м.
- Результат (исключены 7, 10, 11): affine+TPS(1), 11 точек, in-sample 14,3 м (макс. 37), LOO 38,2 м; LOO точки 9 — 82 м, церквей — 31 и 8 м. Прежняя версия (9 точек): `scratchpad/tiflis_1887_9pt.*`.
- Проверка точек сторонним ИИ (Gemini, с открытыми изображениями) совпала по точкам 7, 9, 10, 11; его утверждение, что точка 3 (Ванкский собор) стоит неверно, опровергнуто OSM (Ванкский собор 41.69739, 44.80575 = точка 3). Его новые точки N3 (обсерватория) и N4 (перекрёсток) не проверены и не использованы.
- Церкви стоят в ~100 м друг от друга: это практически одна опора. Нужна ещё одна независимая точка на севере (напр. здание станции).

### Повторная привязка по проверке внешним ИИ (2026-11-17)
- 1913: точка 15 — пиксель перенесён на значок церкви Кашвети (1755,3302; №66 по легенде плана; проверка: 23 м к привязке), точка 2 — пиксель на Верийский мост (1365,2445; 50 м). Точка 0 остаётся исключённой (предложенные ИИ «верные» координаты дали ровно 0 м к привязке, т.е. были получены из неё же). Итог: affine, 16 точек, in-sample 35,1 м (макс. 64,7), LOO 45,2 м (было 14 точек, LOO ≈46 м). Резерв: `tbilisi_1913_gcp.json.bak`, прежние результаты в scratchpad (`tbilisi_1913_14pt.*`).
- 1887: добавлены 4 точки на севере (обсерватория, перекрёсток Елизаветинская/Вокзальное шоссе, угол здания на Михайловском пр., перекрёсток Михайловского/Кирочной), координаты и пиксели предложены внешним ИИ, согласуются с привязкой на 14–53 м. Итог: affine+TPS(10), 15 точек, in-sample 28,1 м (макс. 56), LOO 39,9 м (было 11 точек, LOO 38,2 м). Точность по метрикам не улучшилась, выросло покрытие севера. Резерв: `tiflis_1887_gcp.json.bak2`, scratchpad `tiflis_1887_11pt.*`.
- Типы объектов (9 групп по полю initial_function) и ссылки на статьи Википедии: интерфейс готов, данные ссылок ещё не подключены.

### Публикация (2026-11-17)
- Выбран GitHub Pages (деплой папки `site/` через `.github/workflows/pages.yml`), вариант «Б»: сначала подложка и фильтр фото, потом публикация. Подготовлены `.gitignore`, `README.md` (англ.), раздел «О проекте и источниках» на сайте (ru/en/ka), `noindex` в `index.html` (убрать при открытии для поисковиков).
- Подложка: OSM-растр заменён на векторные тайлы OpenFreeMap (positron/dark). Условия на openfreemap.org прочитаны: публичный экземпляр бесплатен, без ключей, регистрации и лимитов просмотров, атрибуция обязательна (MapLibre добавляет её сам), SLA нет.
- Реестр памятников: владелец прочитал условия и считает данные открытыми для некоммерческого использования. Сам портал (JS-страница) я прочитать не смог; внешний ИИ процитировал на портале фразу о защите прав изготовителя базы данных (не проверено мной). Решение о публикации сокращённой выборки принято владельцем.
- Реестр, уточнение владельца (2026-11-17): основание для использования данных — устное обсуждение в сообществе; письменной лицензии/условий нет. На сайте и в README формулировка приведена в соответствие: «письменной открытой лицензии найти не удалось, сокращённая выборка в некоммерческих целях». Устная договорённость не является документированной лицензией — риск остаётся на владельце. После создания репозитория добавить на страницу способ связи для правообладателей (Issues).

- Подложка (2026-11-17): по просьбе владельца выбран стиль OpenFreeMap liberty для светлой и тёмной темы (positron и bright выглядели серыми). Liberty содержит объёмные здания; на слабых устройствах может быть тяжелее.

### Граница застройки по советской топокарте (2026-11-17)
- Скачан `data/raw/nakarte/topo500.mbtiles` (6 382 784 512 байт, tiles.nakarte.me/files/; на странице лицензия не указана; в репозиторий не входит). Тбилиси покрыт полностью до масштаба z14 (195 из 195 тайлов рамки 44.68–44.98 E, 41.60–41.80 N), z15/16 нет. Метаданные mbtiles пустые, год съёмки листа из тайлов не определён.
- `tools/trace_topo_boundary.py`: застройка залита на карте оранжево-красным; контур выделен по цвету (HSV), очищен морфологией, переведён в lon/lat (сетка Web Mercator, ~7,1 м/пикс) → `data/boundaries/tbilisi_1980_topo.geojson` (46 полигонов: 5 — сплошной город ≈32 км² по залитой застройке, 41 — отдельные посёлки; confidence approximate, year 1980 условно: «поздний СССР, 1970–80-е»). Проверка на глаз по наложению: контур повторяет застройку; есть мелкие ложные пятна на склонах (штриховка рельефа). Дыры внутри не учтены. В публикацию идёт только контур, не карта. Правовой статус советской карты не выяснен.
- Годовая привязка уточнить по GUSV (1978 и 1985).

### Границы застройки GUSV 1972–2021 (2026-11-17)
- Скачаны 7 архивов GUSV (Zenodo 14523232, CC BY 4.0): 1972, 1978, 1985, 1990, 2000, 2010, 2021 (≈1,84 ГБ, MD5 совпали), в `data/raw/urban/`; `tools/fetch_urban.py` (скачивание), `tools/extract_urban.py` (чтение .shp без GIS-библиотек, вырезка Тбилиси, отбрасывание дыр, упрощение ≈15 м) → `data/boundaries/tbilisi_urban_gusv.geojson` (42 полигона: по одному «city» на год + 5 «other» — соседние поселения).
- Площадь «city»: 1972 — 83,9 км²; 1978 — 84,0; 1985 — 85,0; 1990 — 95,8; 2000 — 108,6; 2010 — 114,0; 2021 — 122,4. Это сглаженная огибающая застройки (метод KDE по Landsat), шире, чем залитые кварталы на карте; не административная граница. 1972, 1978 и 1985 почти не различаются — для ранних лет это нужно считать грубой оценкой.
- Сверка на глаз с советской топокартой: контур GUSV 1985 близок к залитой застройке на карте, так что лист соответствует 1980-м (но год съёмки не определён); совпадение положения также подтверждает преобразование пикселей в координаты.

### Административная граница (2026-11-17)
- Источник: OCHA COD-AB Georgia v01 (HDX; исходник — Национальная статистическая служба Грузии; CC BY-IGO), admin1 «Tbilisi», действительна с 2019-10-18, пересмотр 2024-01-31; площадь по метаданным 502,5 км² — совпадает с цифрой диссертации Харебава для периода после 2006 года. Скачан `data/raw/admin/hdx/geo_admin_boundaries.geojson.zip` (11 МБ); `tools/extract_admin.py` → `data/boundaries/tbilisi_admin_2019.geojson` (упрощено до ≈30 м, 563 вершины) → `site/data/admin.json`. На сайте — пунктирная линия «для сравнения», включена всегда.
- geoBoundaries Georgia (ADM1 2015 = 249 км², ADM2 2007 = 329 км²) скачаны в `data/raw/admin/` и НЕ используются: площади не согласуются с HDX и диссертацией. Районов Тбилиси (admin3) в HDX нет (admin2 — «partial coverage», Тбилиси в нём нет).
- Исторических административных границ (до 2006: 354 км² в 1999 и др.) в открытом виде не найдено: в диссертации только площади, без геометрии. Не рисовать без источника.

### Районы и старая граница (2026-11-17)
- Районы: 10 районов из OpenStreetMap (relations admin_level=10; ODbL 1.0; названия ka/en/ru), `tools/fetch_districts.py` → `data/boundaries/tbilisi_districts_osm.geojson` → `site/data/districts.json` (упрощено, + точки для подписей). Показано современное деление; исторические изменения районов не отражены. Владелец согласился с условиями ODbL для этого набора (атрибуция в «О проекте» и README).
- geoBoundaries (ADM1 2015: 249 км²; ADM2 2007: 330 км²) сравнены с HDX 2019 (502,5 км²): оба лежат внутри HDX на 97–98 % площади, то есть выглядят как меньшие (более ранние?) очертания города. Даты не подтверждены, метаданные противоречат друг другу (ADM1 «2015» меньше ADM2 «2007»). ADM2 (330 км², близко к 354 км² из диссертации для 1999–2005) показан как ориентировочная старая граница только для 1999–2005 годов с оговоркой на странице; ADM1 не используется.

### Фильтр фото с людьми (2026-11-17)
- `tools/filter_photos.py`: миниатюры 1750 файлов (data/cache/thumbs/), детектор лиц YuNet (`data/raw/models/face_detection_yunet_2023mar.onnx`, 232 589 байт, OpenCV Zoo; в OpenCV 5.0 каскады Хаара и HOG удалены) + проверка цвета кожи в рамке лица (бюсты и барельефы на досках оставляем) + слова в названии. Отклонено 138 из 1750: по названию 27, по лицу с цветом кожи 122, по очень крупному лицу 11. Результат: `data/cache/photos_people.json`; `build_site_data.py` пропускает отклонённые.
- Проверка выборкой (контактные листы в `data/cache/review/`): среди отклонённых в основном люди и события; единичные ложные срабатывания (барельеф с «кожным» тоном, церковь, резная икона). Среди пропущенных остаются чёрно-белые уличные снимки с людьми и концерты при цветном свете (около 5 из 33 просмотренных с лицами без кожи). Полностью исключить людей автоматически нельзя.
- Ручная проверка фото (2026-11-17): просмотрены контактные листы всех 1612 принятых автоматикой фото (+33 с лицами без цвета кожи); исключены ещё 54 (люди, концерты и события, еда и напитки, автомобили, ругательства, политические вывески, посторонние предметы) — список в `data/photos_manual_reject.json`, учитывается в `build_site_data.py`. Просмотр шёл по миниатюрам ≈128 px, мелкие детали (человек вдали) могли быть пропущены.

### Ранние планы: 1735, 1785, 1800, 1844 (2026-11-17)
- Точки предложил внешний ИИ (Gemini) по легендам планов; проверены расчётом (`data/georef/tiflis_17xx_gcp.json`, список исключённых при чистке по LOO — поле `excluded_default`, его учитывает `tools/warp.py`; опция `--affine` запрещает TPS). Результаты: 1785 — affine, 9 точек, in-sample 31,6 м, LOO 48,6 м (исключены 8-я и 9-я); 1800 — affine, 10 точек, 35,7/51,5 м (исключены 9-я, 10-я); 1844 — affine, 8 точек, 26,5/49,0 м (исключены 4, 6, 7, 12-я); 1735 — схема, affine+TPS(10), 10 точек, 100/158 м (в подпись добавлена оговорка про ~150 м). Оценки LOO после отбрасывания худших точек оптимистичны (отбор по LOO). Предположение ИИ о зеркальном отражении плана 1785 расчётом не подтверждено (поворот на 180° без отражения).
- 1821 (Швецов): точки ИИ несогласованы (масштаб между парами точек 0,26–1,05 м/пикс, in-sample 209 м, LOO 334 м, гомография не лучше). Не привязан; нужны перенесённые на глаз точки (план есть в списке вьювера).
- Границы застройки обведены вручную по привязанным изображениям (`tools/trace_early_boundaries.py` → `data/boundaries/tiflis_1735|1785|1800|1844.geojson`; confidence approximate; 1735 — rough). Они подключены к слайдеру вместе с 1887, 1913, GUSV; шкала теперь с 1700 года. В список вьювера планы добавлены с `"site": false` (на сайт растры не выводятся).

### Расхождение контуров и памятников; изменения (2026-11-17)
- Замечено владельцем: с ~1810 года контур застройки мал, а памятники разбросаны. Причины (посчитано): контуры 1735/1785/1800 по 0,4 км², 1844 — 3,3 км², 1887 — 8,9 км² (диссертация: 2, 3, 13, 28 км² — территория, а не плотная застройка); на шкале между 1800 и 1844 нет срезов; 42 из 55 вне контура 1844 объектов имеют оценочный год 1813 (середина диапазона «первая четверть XIX в.»); реестр охватывает всю современную территорию (сёла, археология).
- Решение владельца: (А) расширить обводку 1844 и 1887 до сплошной городской территории и добавить срезы по мере привязки новых планов; (Б) на шкале показывать конец диапазона дат («не позже»), а не середину.
- Сделано: (Б) `build_site_data.py`: `ye` = конец диапазона для всех точностей кроме exact (середина сохранена в `ym`); текст примечания и подпись в карточке обновлены. (А) `tools/trace_early_boundaries.py`: 1844 переобведён шире («city_territory»: 5,4 км²), 1887 переобведён («city_territory» + Навтлуги: 11,1 км²); прежние узкие контуры — `data/boundaries/tiflis_18xx.geojson.bak_narrow`. Цифры диссертации (13 и 28 км²) не достигнуты: на планах нет линии городской границы, и обводить «до цифры» без источника не стал.
- 1913 (2026-11-17): по замечанию владельца (с 1913 года была только линия по северной стороне) контур замкнут в полигон «city_territory»: северо-восточная сторона — трассированная раньше «граница города» (зелёная линия в легенде плана), остальные стороны — край сплошной застройки и садов (юг: сады вдоль Куры, запад: край Ваке-Сабуртало). Площадь ≈ 24,9 км² (диссертация: 29). Прежняя частичная линия: `data/boundaries/tbilisi_1913.geojson.bak_partial`. Запад и юг — приблизительно, без явной линии границы на плане.

### Старая административная граница, площади, названия районов, присоединённые посёлки (2026-11-17)
- Ответ Gemini по административным границам проверен выборочно. Полигон geoBoundaries ADM2 «Tbilisi» (329 км²): по OSM-координатам Цхнети, Цавкиси, Окрокана, Кикети, Бетания (присоединены в 2006) лежат вне него и внутри границы 2019; Поничала, Орхеви, Глдани, Варкетили, Мухиани (раньше 2006) — внутри обоих; Авчала, Диди Дигоми, Загэси вне старого, внутри нового. Вывод: соответствует границе до реформы 2006, но площадь 329 км² меньше 354 км² (объяснение Gemini — выступ Диди Дигоми/Авчалы ≈20–25 км² — не проверено). Показ в слайдере расширен: 1973–2005 (по решению владельца).
- Не подтвердилось/не проверено: matsne.gov.ge/ka/document/view/18150 → «Access Denied» (номер и название постановления 4173-რს из пересказа); геокодирование Коджори, Табахмелы, Шиндиси, Ахалдабы, Лило дало неверные места. Акты 22.01.2007 (№1-6), 28.01.2013 (№1-4), 05.12.2014 (№16-41), указ президента 09.11.2000 (№480), советские расширения (1934 — выделение города; 1949 — Грмагеле, Глдани, Багеби, Делиси, Соганлуги; 1962 — Авчала; 1973 — Поничала, Лило/Орхеви, аэропорт) — всё из пересказа Gemini по вторичным источникам (Какурия 1979, БСЭ 1976, энциклопедии), не по первоисточникам.
- `data/city_area.json`: добавлены 1960 (260,7 км², диссертация), 1970 (265, вторичный источник), 1975 (348,6, БСЭ через Gemini); у каждой записи поле `src` (kh — диссертация, sec — вторичный, не проверен); подпись на странице различает.
- `data/district_history.json` + блок «Районы» на панели: названия по периодам (1979–1989: 9 советских районов; 1990–1999: 10; 2000–2006: 5 укрупнённых; 2007–2012: 6 с Дидгорским; с 2013: 10) на ka/en/ru, с соответствием современным районам, БЕЗ границ. «Морской район» 1980-х (временный) не включён. Латинские названия советских районов — мои.
- Контур 1960–1972 вычитанием Поничала/Лило из ADM2 (предложение Gemini) НЕ делался: это была бы выдумка, не данные.
- Слой «Посёлки, вошедшие в состав города» (2026-11-17): `data/settlements_curated.json` (26 пунктов; годы 1949, 1962, 1973, 2006 и «из какого района» — пересказ Gemini по вторичным источникам, не проверено) + позиции и названия ka/en/ru из OSM (`data/raw/admin/osm_places.json`, ODbL), класс положения посчитан по ADM2 и границе 2019: 14 вне старой границы внутри современной (все 13 из группы 2006 + «Village Gldani»), 12 внутри старой. Найдено противоречие: «Village Gldani» (год 1949 по пересказу) лежит вне границы до 2006 года; помечено в карточке (`conflict`). Грмагеле, Делиси, Соганлуги из пересказа в OSM как place-узлы не найдены, не включены. В слайдере: серый до года включения, цветной после, синеватый — год не указан. Выключается флажком.

### Планы 1782, 1802, 1879, 1884, 1954; граница 1954 (2026-11-17)
- Точки по новым планам предложил Gemini; проверены расчётом (подгонка, LOO, масштабы пар, север): 1782 — affine, 8 точек после чистки (исключены 1-я и 4-я), in-sample 31 м, LOO 59 м, масштаб 0,328 м/пикс, север внизу (−173°); 1802 — 12 точек, 24/33 м (лучший ранний план, чистка не потребовалась); 1879 — 10 точек (исключены 2-я и 6-я), 37/60 м; 1884 — 9 точек (исключены 1, 4, 5), 22/28 м, но скан низкого разрешения (4,3 м/пикс). Оценки после чистки оптимистичны. Нулевых «круговых» невязок нет; масштабы пар сходятся с линейками планов.
- Контуры обведены вручную: `tiflis_1782` (Кала, нижний город с Метехи/Нарикала, Авлабар), `tiflis_1802` (то же), `tiflis_1879` (городская территория + Навтлуги). План 1884 привязан, но не обведён (низкое разрешение, между 1879 и 1887). Планы в списке вьювера с `"site": false`.
- 1954 (лист NK 38-8, AMS, 1:250 000): привязка Gemini по рамке листа НЕСОСТОЯТЕЛЬНА (4 угла рамки дают невязку 660–710 м, предсказания объектов расходятся на 0,5–1,7 км). Использованы 5 точек у Тбилиси (перекрестие 41°45′/44°45′, мост через Ксани, слияние Арагви/Куры, вокзал, развилка Навтлуги): невязки 21–332 м, но положение полигона вероятно неточно на 0,3–1 км (в подписи ~700 м). Оранжевая заливка застройки выделена по цвету → `data/boundaries/tbilisi_1954_ams.geojson` (34,5 км²). Лист составлен в 1951 г. по съёмкам 1920–40-х (по надписи, со слов Gemini), поэтому показывает состояние примерно 1940-х; на слайдере помечен 1954.
- Шкала: добавлены срезы 1782, 1802, 1879, 1954 (теперь 17 срезов).
