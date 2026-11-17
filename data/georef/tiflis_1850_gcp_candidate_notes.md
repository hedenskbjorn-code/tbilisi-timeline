# Tiflis 1850 plan: candidate ground control points

Image: `data/raw/plans/1850_map.jpg` (2023 x 2310 px, x right, y down). Output: `tiflis_1850_gcp_candidate.json` (17 points, `lnglat` = lng first).

## Method

- Pixels were read from crops of the original at 5.6x-7.5x magnification with a 10-20 px grid labelled in original pixel coordinates. The pixel is the centre of the symbol.
- The scan is low resolution (about 2.85 m per pixel). Church symbols are 5-10 px blobs and the legend numbers are not legible, so no object was identified by its number. Reading accuracy is about +-2-3 px (6-9 m).
- Identification aid: modern OSM roads and churches were overlaid on the plan with a rough similarity transform (Metekhi as origin, 2.82 m/px, no rotation). The old-town street network coincides with the plan, which was used to decide which cross belongs to which church. The pixel itself was always taken from the plan symbol, never from the predicted position.
- Modern coordinates: the project-verified list given in the task, or OpenStreetMap objects returned by Overpass queries run on 2026-11-17 (bbox 41.672,44.775 - 41.722,44.855, `amenity=place_of_worship`, `historic=*`, named bridges; plus a by-id query for ways 246757401, 1150481713, 123574142, 758009917, 220702092, 1207608184). Dates were checked with the Wikidata API (`wbgetentities`).

## Points

| # | Point | Pixel (x, y) | On the plan | Modern object and source | lat, lng | Confidence |
|---|---|---|---|---|---|---|
| 0 | Metekhi church | 903, 1397 | cross inside the walled enclosure, label "Зам. Метехскій" | project-verified; OSM way 1064270003, Wikidata Q20577625 | 41.69014, 44.81125 | medium-high (position inside the enclosure +-4 px) |
| 1 | Sioni cathedral | 796, 1353 | church symbol in a light yard, north-west of the dark riverside caravanserai blocks; no legible label | project-verified; OSM way 77895547, Q248050 | 41.69132, 44.80753 | high |
| 2 | Anchiskhati | 777, 1193 | cross at the river bank (second mark at 787,1193) | project-verified; OSM way 337365208, Q609419 | 41.69552, 44.80687 | medium |
| 3 | Mamadaviti | 247, 1179 | church symbol at the end of label "Мон. Св. Давида" | project-verified; OSM way 337269648, Q12866896 | 41.69583, 44.78887 | high |
| 4 | Echmiadzin church, Avlabari | 973, 1306 | cross in a block north-west of "III" | OSM way 220702092 (Q2613137, inception 1806) | 41.6925552, 44.8137412 | medium-high |
| 5 | St Minas church (ruins), Avlabari | 927, 1260 | cross with a small circle below | OSM way 758009917 (same as the "Gelati 13" point of the 1844 file) | 41.6935849, 44.8120732 | medium |
| 6 | Transfiguration church at Darejan palace | 944, 1338 | cross right of the ravine, east of letter "L" | OSM way 123574142 | 41.6916914, 44.812693 | medium-high |
| 7 | Surb Gevorg cathedral (Meidan) | 834, 1437 | cross south-west of roman "I" (another cross at 855,1425 was not used) | project-verified; OSM way 373390884, Q3653178 | 41.68918, 44.80888 | medium |
| 8 | Kari St George church | 766, 1222 | cross above a dark bar numbered "47", north of letter "E" | OSM way 1125780341 (Q55753705) | 41.6946588, 44.8065072 | medium |
| 9 | Surb Nshan church | 715, 1238 | cross inside a block | OSM way 661361748 (Q3653183, inception 1711) | 41.6943292, 44.8047262 | medium |
| 10 | Norashen church | 766, 1363 | pair of crosses west of Sioni (Jvaris Mama is adjacent and cannot be separated) | project-verified; OSM way 284620213, Q2046924 | 41.69097, 44.80653 | medium |
| 11 | Surb Gevorg of Mughni | 697, 1387 | cross south-east of letter "F" | project-verified; OSM way 690062898, Q3653195 | 41.69030, 44.80423 | medium-low |
| 12 | Vank cathedral | 741, 1112 | centre of a dark building complex on the river bank; no cross legible | project-verified bell tower, OSM way 661366844. The pixel is the complex centre while the coordinate is the bell tower (possible 20-40 m offset). Wikidata Q4793165 gives 41.696328, 44.806723, which is about 120 m away and was not used | 41.69739, 44.80575 | medium-low |
| 13 | Kashveti (old church) | 556, 1092 | dark bar numbered "6" on the north-east side of "Головинскій проспектъ" | project-verified (present church, OSM way 65299828, start 1910). That the old church stood on the same spot is assumed, not checked against a source | 41.69797, 44.79930 | medium-low |
| 14 | Chugureti St Nicholas church | 781, 957 | cross with "c" in a hatched block at the river bank | OSM way 246757401 (Q124430106). No construction date in OSM or Wikidata, so existence in 1850 is not verified | 41.7015005, 44.8070697 | low |
| 15 | Dry Bridge (small Mikhailovsky bridge) | 658, 999 | short bridge over the side channel, letter "R"; midpoint of the drawn bridge | OSM way 1150481713 (Q12867285, start 1851, old name "Малый Михайловский мост") | 41.7004726, 44.8025609 | low |
| 16 | Kharpukhi St Nicholas church | 1154, 1605 | cross "+c" south of label "Заст. Эриванская" | OSM way 1207608184 (Q42637630, inception 1853). The plan (1850) already shows a church symbol here; whether it is this building or a predecessor is not verified | 41.6845886, 44.820021 | low |

## Rejected candidates

| Candidate | Pixel | Reason |
|---|---|---|
| Lurji monastery, Vera (41.70792, 44.78899) | 204, 703 (cross under "Кладб. Православное") | About 140-160 m west of the position implied by all other points; leave-one-out error 157 m when included. The cross is probably the cemetery symbol, not the monastery. Other marks nearby (255,713 and 262,715) are unlabelled, so no re-read was possible. |
| Khojivank (41.69842, 44.81863) | 1066, 1117 (walled rectangle, "Мон. Хаджи-ванкъ") | 11 of 18 pair scales outside +-15%, about 195 m off. The plan symbol is clear; the modern coordinate is the pantheon, not the demolished church. No source with the church's exact position was found. |
| Catholic church of the Assumption (41.69279, 44.80357) | 677, 1283 | About 34 m off in north-south; the symbol could not be identified with confidence among several marks. |
| Kashveti, alternative symbol | 583, 1090 (irregular building in the corner of square "C") | About 80 m off; one pair scale outside +-15%. |
| Surb Karapet (OSM way 691709671) | around 870, 1093 | No legible symbol. |
| Betlemi churches, Kldisubani St George, Juma mosque, Old Trinity, Jvaris Mama, Church of the Red Gospel | - | Several similar marks, no unambiguous symbol. |
| German colony / Kukia street crossings | - | The colony main street on the plan does not follow modern Agmashenebeli Avenue in the overlay (direction differs by about 10 degrees), so no crossing could be matched. |
| Navtlug military hospital (octagonal building at about 1790, 1692) | - | No surviving building in OSM within 600 m of the expected place (Isani Mall, new apartment blocks, a military logistics area). |

No usable point was found for the north-west (Vera, colony), the far north, the east (Navtlug, military settlement) or the far south (Krtsanisi, Ortachala gardens).

## Scale consistency (pairs more than 250 px apart)

| Set | Pairs | Median m/px | Min | Max | Pairs outside +-15% |
|---|---|---|---|---|---|
| 14 core points (0-13) | 32 | 2.843 | 2.800 | 2.904 | 0 |
| 17 points (0-16) | 69 | 2.868 | 2.785 | 2.941 | 0 |
| 21 candidates including the rejected ones | 124 | 2.868 | 2.581 | 3.549 | 11 (all involve Khojivank) |

## Least-squares affine fit (plan pixel to local metres)

17 points: scale 2.847 m/px in x, 2.879 m/px in y, axis rotation -0.2 and +0.6 degrees. In-sample RMSE 10.6 m; leave-one-out RMSE 14.4 m, median 12.3 m, maximum 27.2 m.

14 core points: scale 2.843 / 2.855 m/px, rotation -0.1 / +0.2 degrees. In-sample RMSE 9.0 m; leave-one-out RMSE 12.8 m, median 10.3 m, maximum 25.6 m.

| # | Point | In-sample, m (17) | Leave-one-out, m (17) | Leave-one-out, m (14 core) |
|---|---|---|---|---|
| 0 | Metekhi | 4.1 | 4.6 | 1.8 |
| 1 | Sioni | 8.9 | 9.7 | 6.6 |
| 2 | Anchiskhati | 12.5 | 13.5 | 16.2 |
| 3 | Mamadaviti | 10.3 | 27.2 | 25.6 |
| 4 | Echmiadzin | 12.5 | 14.4 | 14.0 |
| 5 | St Minas | 8.4 | 9.5 | 11.8 |
| 6 | Darejan Transfiguration | 6.2 | 6.9 | 5.4 |
| 7 | Surb Gevorg | 11.6 | 13.4 | 7.7 |
| 8 | Kari St George | 2.3 | 2.4 | 3.9 |
| 9 | Surb Nshan | 10.4 | 11.1 | 12.2 |
| 10 | Norashen | 6.0 | 6.7 | 8.7 |
| 11 | Mughni | 10.3 | 12.3 | 17.5 |
| 12 | Vank | 16.3 | 18.4 | 16.8 |
| 13 | Kashveti | 8.6 | 10.2 | 8.7 |
| 14 | Chugureti St Nicholas | 9.6 | 15.2 | (4.8 off the core fit) |
| 15 | Dry Bridge | 16.8 | 21.7 | (24.4 off the core fit) |
| 16 | Kharpukhi St Nicholas | 13.9 | 22.6 | (26.9 off the core fit) |

## Caveats

- The points cover only about x 250-1150, y 950-1600 of the 2023 x 2310 image. Mamadaviti is the only western point and has high leverage. Outside this area (north-west, east, south) the fit is an extrapolation and is not checked by any point.
- For points 4-11 the choice between neighbouring crosses relied on the overlay of modern OSM positions, so their small residuals partly reflect that choice and are not a fully independent accuracy test.
- Points 14-16 are dated 1851, 1853 or undated in the sources opened. They agree with the core fit to 5-27 m, but their existence in 1850 rests only on the plan showing a symbol there.
