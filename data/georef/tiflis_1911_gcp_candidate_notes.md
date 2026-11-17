# Tiflis "1911" topographic sheet - GCP candidates (notes)

Image: `data/raw/plans/1911_map.jpg` (5149 x 4153 px). Pixels are in original image coordinates (x right, y down),
each read from a magnified crop of the original with a labelled pixel grid (zoom 4x-9x, grid 20 or 50 px).
Modern coordinates come from OpenStreetMap objects retrieved through the Overpass API (2026-11-17), except Metekhi and
Mamadaviti, where the project's already verified coordinates were used (they agree with the OSM building centres to < 2 m).
Nothing was computed by fitting the sheet to itself; the fit below is only a check.

## Points

| # | Point | Pixel (x, y) | On the sheet (verbatim label / symbol) | Modern object (source) | lat, lng | Confidence |
|---|-------|--------------|-----------------------------------------|------------------------|----------|------------|
| 1 | Metekhi church | 2613, 2932 | no label; square block with a white cross on the left bank exactly at the Kura bend | Metekhi Church, OSM way 1064270003 (centre 41.69015, 44.81125); project-verified value used | 41.69014, 44.81125 | high |
| 2 | Mamadaviti | 2099, 2745 | cross symbol at the end of label "Мон. Св. Давида" | Mama Daviti church, OSM way 337269648, wikidata Q12866896 | 41.69583, 44.78887 | high/medium |
| 3 | Kukia St Nino church | 2613, 2157 | no label; filled symbol in the SW corner of the cemetery (field of crosses) NE of the railway | Kukia Saint Nino Church (1890), OSM way 73412942, wikidata Q42649109 | 41.71448, 44.81100 | medium |
| 4 | Vera bridge | 2177, 2376 | no label; double line across the Kura where a tree-lined road/stream arrives from the west (centre of span) | Galaktion Tabidze Bridge, OSM way 159460389 (way centre) | 41.70778, 44.79275 | medium (bridge rebuilt on the old site; +-40 m) |
| 5 | St Barbara, Ponichala | 4478, 3833 | circle-with-cross symbol left of label "Св. Варвары (дальн.)" | Saint Barbara's (historic=church), OSM way 78252000 | 41.66212, 44.89144 | medium |
| 6 | Tsavkisi church | 888, 3527 | round symbol with stem at the N edge of village "Цавкиси" (below "Прав.") | St. Nino Church, OSM way 1225528343 | 41.67084, 44.73712 | medium/low (age of the OSM church not confirmed; no start_date) |
| 7 | Digomi church | 1009, 312 | cross symbol in the E part of village "Дигоми" | "კვირაცხოვლის ეკლესია" (Kviratskhoveli church), OSM way 1179812480 | 41.77212, 44.74226 | medium/low (Digomi has 4 churches in OSM; chosen as the easternmost one, age not confirmed) |
| 8 | Kvirikobis trig point | 3822, 900 | triangle between "321.4" and "Г. Джварикобис-гора" | peak Kvirikobis Mta, ele 684 m, OSM node 9831478511, wikidata Q24687104. 321.4 sazhen = 685.7 m, so the height matches | 41.75259, 44.86459 | low (OSM peak node position is approximate) |
| 9 | Height mark 310 | 571, 1221 | square mark left of "310", W of "Оз. Лисис тба (Лисье)" | unnamed peak, ele 663.9 m, OSM node 939521932. 310 sazhen = 661.4 m | 41.74425, 44.72286 | low |
| 10 | Navtlug station | 3580, 3050 | "Ст. 4 кл." - centre of the dark building block on the N side of the tracks | Navtlughi railway station, OSM node 945217529, wikidata Q4314638 (node is on the tracks) | 41.68598, 44.85462 | low (station building not separable; a round dot at 3626,3033 next to "Ст." may be the real station symbol) |
| 11 | Didube church | 2018, 1680 | no label; cross-shaped building in the gardens W of the railway yard | St. Mariam Church of Didube, OSM way 531596101 | 41.72970, 44.78584 | low (symbol not unambiguous) |

OSM object links have the form `https://www.openstreetmap.org/way/<id>` or `/node/<id>`; the objects were read through
`https://overpass-api.de/api/interpreter` (`out center tags`), not through the website.

## Checks

Local metric frame: equirectangular at lat 41.71 (1 deg lng = 83 098 m, 1 deg lat = 111 132 m).

Pairwise scale (all 55 pairs, all > 300 px apart): median 3.55 m/px, range 3.40-3.73 m/px, i.e. every pair is within
-4 % / +5 % of the median; no point is outside +-15 %, so none was dropped by this test.

Plain least-squares affine, 11 points:
- scale 3.60 m/px along x, 3.47 m/px along y (about 3.5 % anisotropy), mean ~3.54 m/px
- rotation: x axis -0.24 deg, y axis +0.20 deg (north is up within ~0.25 deg)
- in-sample residuals (m): Metekhi 22, Mamadaviti 31, Kukia 54, Vera bridge 35, St Barbara 87, Tsavkisi 103, Digomi 4,
  Kvirikobis 94, mark 310 56, Navtlug 105, Didube 50; RMSE 67 m
- leave-one-out (m): Metekhi 25, Mamadaviti 36, Kukia 60, Vera bridge 39, St Barbara 158, Tsavkisi 213, Digomi 7,
  Kvirikobis 205, mark 310 81, Navtlug 131, Didube 56; RMSE 115 m, median 60 m, max 213 m

Without the three weakest (Navtlug, Tsavkisi, Kvirikobis), 8 points: in-sample RMSE 30 m; LOO RMSE 56 m, median 48 m,
max 83 m; scale 3.59 / 3.48 m/px. St Barbara then becomes the only point on the eastern half, so the eastern part is
effectively extrapolated in that variant.

Scale estimate: ~3.54 m/px. If the scan is 300 dpi this is 1:41 800, consistent with a one-verst (1:42 000) map.

## Caveats

- The image is a mosaic of several sheets: a vertical seam is visible at x ~ 3190-3200 (e.g. y 2600-2950), a horizontal
  one at y ~ 3730 for x > 4100, and lettering style differs between parts. A single affine may not hold across seams;
  only points 5, 8, 10 lie east of the vertical seam, and they have the largest residuals.
- Content is later than 1911 in places: "Ст. Орхеви" on the Kakheti railway (opened 1915), areas in "ГА" (hectares).
  Heights are in sazhens, so the base is the pre-revolutionary verst survey.
- The built-up city is heavily generalised; individual churches other than Metekhi cannot be told apart.

## Looked at and rejected

- Tbilisi-Passenger station: only the track fan is drawn, no separable building (throat at about 2395, 2045).
- Sioni, Anchiskhati, Vank, Kashveti, Alexander Nevsky, Sts Peter and Paul, Lurji monastery, observatory: not identifiable.
- Orkhevi station (tracks at about 5100, 3050): no railway station of that name found in OSM (Overpass, Nominatim).
- Salt lakes (Kukia, Avlabar, northern one): do not exist today.
- Lisi lake: drawn as a marshy oval about 190 x 220 px, shape unlike the present lake (about 1.1 x 0.55 km); not used.
- Shindisi church symbol (1707, 3778): no church in OSM at the corresponding place (nearest is ~900 m west).
- "Св. Георгия" (4712, 3788), "Св. Варвары (ближн.)", "Разв. цер." (about 4915, 745), "Разв. башни", Tabakhmela,
  Kharpukhi St Nicholas, Sts Peter and Paul cemetery: no unambiguous symbol or no modern counterpart found.
- Village place nodes were not used.
