"""A one-page picture of the project for its owner: data/db/overview.html (a single file, no network, opens in a browser). It is made from the project index (tools/db_build.py) and says: how the data flows
(sources > raw > curated > site), what of the site is in the index and what is not (every file of site/data), how complete every layer is, where the objects lie (a map of Tbilisi, a switch per layer), the state of the
tasks for Gemini. Usage: python -P tools/db_overview.py   (builds the index first when it is missing)
"""
import html
import json
import os
import sqlite3
import subprocess
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(R, "data", "db", "project.sqlite")
OUT = os.path.join(R, "data", "db", "overview.html")
D = os.path.join(R, "site", "data")
LAYERS = {"reg": ("Реестр наследия (здания)", "#495057"), "rel": ("Религия, отобранное", "#862e9c"), "relosm": ("Храмы из OpenStreetMap", "#be4bdb"), "sci": ("Наука и культура", "#1c7ed6"),
          "edu": ("Образование", "#0ca678"), "pl": ("Местные названия, парки", "#2b8a3e"), "mn": ("Памятники и скульптуры", "#e67700"), "pq": ("Мемориальные доски", "#a61e4d"), "md": ("Советский модернизм", "#364fc7"),
          "st": ("Улицы и их названия", "#868e96")}
# the files of site/data: what they are and whether the index has them (layer id) ; None = not in the index
FILES = {"monuments.json": ("реестр наследия Тбилиси (слой «здания»)", "reg"), "religious.json": ("религиозные здания (отобранные)", "rel"), "religious_osm.json": ("храмы из OSM", "relosm"),
         "science.json": ("наука и культура", "sci"), "education.json": ("образование", "edu"), "places.json": ("местные названия, парки, народные названия", "pl"),
         "sculptures.json": ("памятники и скульптуры", "mn"), "plaques.json": ("мемориальные доски", "pq"), "modernism.json": ("советский модернизм", "md"), "street_names.json": ("улицы: названия по годам", "st"),
         "districts.json": ("районы города (границы)", "regions"),
         "transport.json": ("трамвай, метро, дороги, мосты (линии)", None), "urban.json": ("застроенная площадь города по годам", None), "history_events.json": ("события истории города", None),
         "streets_1913.json": ("улицы по плану 1913 года", None), "street_notes.json": ("справки об улицах", None), "namesakes.json": ("в честь кого названы улицы", None), "photos.json": ("фото объектов реестра", None),
         "street_geom.json": ("линии улиц", None), "views.json": ("виды города (картинки)", None), "changelog.json": ("журнал изменений", None), "run_details.json": ("маршрут забега: подробности", None),
         "rulers.json": ("правители", None), "names_i18n.json": ("переводы имён", None), "run_trc2026.json": ("маршрут забега", None), "street_objects.json": ("объекты на улицах", None), "entrances.json": ("парадные", None),
         "transport_events.json": ("события транспорта", None), "water.json": ("реки и озёра", None), "lost.json": ("утраченные места", None), "city1894.json": ("план города 1894", None), "metro_names.json": ("названия станций метро", None),
         "population.json": ("население", None), "admin.json": ("административное деление", None), "tour.json": ("текст тура по сайту", None)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(DB):
        subprocess.run([sys.executable, "-P", os.path.join(R, "tools", "db_build.py")], check=True)
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    layers = con.execute("""SELECT layer, COUNT(*), SUM(has_name), SUM(name_languages = 3), SUM(has_description), SUM(has_photo), SUM(has_verified_fact) FROM v_object_state GROUP BY layer""").fetchall()
    pts = {}
    for layer, lat, lon in con.execute("SELECT layer, lat, lon FROM object WHERE lat IS NOT NULL AND region LIKE 'GE-TB%'"):
        pts.setdefault(layer, []).append([round(lon, 5), round(lat, 5)])
    tasks = con.execute("SELECT id, status, result_rows, found FROM task WHERE status != 'archive' AND (status != 'done' OR id IN ('parks', 'churches_A', 'folk_points', 'ui_mod_folk')) ORDER BY CASE status WHEN 'queued' THEN 0 WHEN 'empty' THEN 1 ELSE 2 END, id").fetchall()
    raw = con.execute("SELECT source, COUNT(*) FROM raw_record GROUP BY source").fetchall()
    n_names, n_facts, n_ver, n_src, n_media = [con.execute(q).fetchone()[0] for q in ("SELECT COUNT(*) FROM name", "SELECT COUNT(*) FROM fact", "SELECT COUNT(*) FROM fact WHERE status='verified'", "SELECT COUNT(*) FROM source", "SELECT COUNT(*) FROM media")]
    dist = []
    for f in json.load(open(os.path.join(D, "districts.json"), encoding="utf-8"))["features"]:
        if f["geometry"]["type"] == "MultiPolygon":
            dist.append([[p[0] for p in poly[0]][::3] and [[q[0], q[1]] for q in poly[0]][::3] for poly in f["geometry"]["coordinates"]])
    sizes = {n: os.path.getsize(os.path.join(D, n)) for n in os.listdir(D) if n.endswith(".json")}
    tot = sum(sizes.values())
    in_db = sum(sizes[n] for n, v in FILES.items() if n in sizes and v[1])
    rows_files = []
    for n, (desc, layer) in sorted(FILES.items(), key=lambda kv: -sizes.get(kv[0], 0)):
        if n in sizes:
            ok = "да" if layer else "нет"
            rows_files.append("<tr class='%s'><td>%s</td><td>%s</td><td class='n'>%d КБ</td><td>%s</td></tr>" % ("yes" if layer else "no", html.escape(n), html.escape(desc), sizes[n] // 1024, ok if not layer else "да: слой «%s»" % layer))
    rows_layers = []
    for layer, n, named, n3, desc, ph, ver in sorted(layers, key=lambda r: -r[1]):
        def bar(v):
            return "<td><span class='bar'><i style='width:%d%%'></i></span> %d</td>" % (round(100 * v / n) if n else 0, v)
        rows_layers.append("<tr><td><span class='dot' style='background:%s'></span>%s</td><td class='n'>%d</td>%s%s%s%s%s</tr>" % (LAYERS[layer][1], html.escape(LAYERS[layer][0]), n, bar(named), bar(n3), bar(desc), bar(ph), bar(ver)))
    rows_tasks = "".join("<tr><td>%s</td><td class='%s'>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>" % (t[0], t[1], {"queued": "ждёт Gemini", "empty": "пусто (сбой запуска)", "done": "готово"}[t[1]], t[2] if t[2] is not None else "", t[3] if t[3] is not None else "") for t in tasks)
    page = TEMPLATE.replace("@@LAYERS@@", "".join(rows_layers)).replace("@@FILES@@", "".join(rows_files)).replace("@@TASKS@@", rows_tasks) \
        .replace("@@DATA@@", json.dumps({"pts": pts, "dist": dist, "layers": {k: v[1] for k, v in LAYERS.items()}, "names": {k: v[0] for k, v in LAYERS.items()}}, separators=(",", ":"))) \
        .replace("@@NUMS@@", "%d объектов в %d слоях · %d имён · %d фактов (из них %d проверено программой) · %d источников · %d фото · сырых записей: %s" % (sum(l[1] for l in layers), len(layers), n_names, n_facts, n_ver, n_src, n_media, ", ".join("%s %d" % r for r in raw))) \
        .replace("@@N_IN@@", str(sum(1 for n, v in FILES.items() if n in sizes and v[1]))).replace("@@N_ALL@@", str(sum(1 for n in FILES if n in sizes)))         .replace("@@SITE@@", "%d из %d КБ JSON сайта (%d%%)" % (in_db // 1024, tot // 1024, round(100 * in_db / tot)))
    open(OUT, "w", encoding="utf-8").write(page)
    print("overview:", os.path.relpath(OUT, R), "%d KB" % (os.path.getsize(OUT) // 1024))


TEMPLATE = r"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Тбилиси во времени: карта проекта</title>
<style>
:root{--bg:#f8f9fa;--fg:#212529;--mut:#6c757d;--card:#fff;--line:#dee2e6;--ok:#2b8a3e;--no:#c92a2a}
@media (prefers-color-scheme:dark){:root{--bg:#16181d;--fg:#e9ecef;--mut:#9aa1a9;--card:#20242b;--line:#343a42;--ok:#69db7c;--no:#ff8787}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 60px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:34px 0 10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}.mut{color:var(--mut)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}td.n{text-align:right;white-space:nowrap}
tr.yes td:last-child{color:var(--ok)}tr.no td:last-child{color:var(--no)}td.queued{color:var(--no)}td.empty{color:var(--no)}td.done{color:var(--ok)}
.bar{display:inline-block;width:70px;height:8px;background:var(--line);border-radius:4px;vertical-align:middle;margin-right:6px}.bar i{display:block;height:100%;background:var(--ok);border-radius:4px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}.box{flex:1 1 200px;border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:var(--card)}.box b{display:block;margin-bottom:4px}.arrow{align-self:center;color:var(--mut);font-size:22px}
#map{width:100%;height:520px;background:var(--card);border:1px solid var(--line);border-radius:10px}#sw label{display:inline-block;margin:2px 12px 2px 0;white-space:nowrap;cursor:pointer}
</style></head><body><main>
<h1>Тбилиси во времени: что где лежит</h1><div class="mut">Картина проекта на сегодня. Данные сайта (файлы JSON) остаются главными; база SQLite это их производный индекс и сырьё.</div>
<div class="card"><b>Ответ коротко.</b> Сайт целиком в базе <b>ещё нет</b>: в индекс загружены @@N_IN@@ файлов из @@N_ALL@@ (@@SITE@@): объектные слои с карточками. Линии (трамвай, метро, дороги, улицы), застройка по годам, события истории, население, правители, переводы и тексты сайта остаются только в JSON. Сам сайт базу <b>не читает</b>.<br><span class="mut">@@NUMS@@</span></div>

<h2>1. Как идут данные</h2>
<div class="flow">
<div class="box"><b>Источники</b>OpenStreetMap · реестр наследия (выгрузка раз в неделю) · Википедия, Викисклад · энциклопедия 2008 · Gemini (поиск и переводы)</div><div class="arrow">→</div>
<div class="box"><b>Сырьё</b>файлы в <code>data/raw</code> и кэш страниц <code>data/cache</code>. В базе: таблица <code>raw_record</code> (как пришло)</div><div class="arrow">→</div>
<div class="box"><b>Проверка и сборка</b>скрипты <code>tools/*.py</code>: проверка цитат на страницах, <code>apply_*</code>, <code>build_*</code>. Задания Gemini: <code>for_gemini</code></div><div class="arrow">→</div>
<div class="box"><b>Сайт</b><code>site/data/*.json</code> загружаются лениво, GitHub Pages. Жалобы и фото: Worker Cloudflare</div></div>
<div class="card mut" style="margin-top:10px">Рядом с этой цепочкой лежит <b>база</b> <code>data/db/project.sqlite</code>: она собирается из JSON и сырья командой <code>tools/db_build.py</code> и отвечает на вопросы (<code>tools/db_query.py</code>). В обратную сторону пока ничего не пишет.</div>

<h2>2. Что из сайта уже в базе</h2>
<div class="card"><table><tr><th>Файл</th><th>Что это</th><th>Размер</th><th>В базе</th></tr>@@FILES@@</table><div class="mut" style="margin-top:8px">Картинки карт (webp, около 20 МБ) и растры в базу не идут и не должны.</div></div>

<h2>3. Насколько полны слои</h2>
<div class="card"><table><tr><th>Слой</th><th>Объектов</th><th>Есть название</th><th>Названия на 3 языках</th><th>Есть описание</th><th>Есть фото</th><th>Есть проверенный факт</th></tr>@@LAYERS@@</table></div>

<h2>4. Где лежат объекты</h2>
<div class="card"><div id="sw"></div><svg id="map" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet"></svg><div class="mut">Точки объектов базы по районам Тбилиси (без трамвая и улиц). Галочки включают слои.</div></div>

<h2>5. Задания для Gemini</h2>
<div class="card"><table><tr><th>Задание</th><th>Состояние</th><th>Строк</th><th>Найдено</th></tr>@@TASKS@@</table><div class="mut" style="margin-top:8px">Одна команда готовит всё: <code>python -P tools/gemini_all.py</code>. Список дел: <code>PENDING.md</code>.</div></div>
</main>
<script>
const D=@@DATA@@;const svg=document.getElementById("map");const NS="http://www.w3.org/2000/svg";
const all=[].concat(...Object.values(D.pts));const ds=[].concat(...D.dist.flat());
let x0=44.66,x1=44.98,y0=41.62,y1=41.87;const k=Math.cos(41.7*Math.PI/180);
const W=1000,H=600;const sx=W/((x1-x0)*k),sy=H/(y1-y0),s=Math.min(sx,sy);
const px=(lon)=>(lon-x0)*k*s+(W-(x1-x0)*k*s)/2,py=(lat)=>(y1-lat)*s+(H-(y1-y0)*s)/2;
const g0=document.createElementNS(NS,"g");svg.appendChild(g0);
for(const poly of D.dist){for(const ring of poly){const p=document.createElementNS(NS,"polygon");p.setAttribute("points",ring.map(q=>px(q[0]).toFixed(1)+","+py(q[1]).toFixed(1)).join(" "));p.setAttribute("fill","none");p.setAttribute("stroke","#adb5bd");p.setAttribute("stroke-width","1");g0.appendChild(p)}}
const groups={};const sw=document.getElementById("sw");
for(const [layer,pts] of Object.entries(D.pts)){const g=document.createElementNS(NS,"g");g.setAttribute("fill",D.layers[layer]);g.setAttribute("opacity","0.8");
 for(const q of pts){const c=document.createElementNS(NS,"circle");c.setAttribute("cx",px(q[0]).toFixed(1));c.setAttribute("cy",py(q[1]).toFixed(1));c.setAttribute("r","1.8");g.appendChild(c)}
 svg.appendChild(g);groups[layer]=g;
 const l=document.createElement("label");const cb=document.createElement("input");cb.type="checkbox";cb.checked=layer!=="reg";g.style.display=cb.checked?"":"none";
 cb.onchange=()=>{g.style.display=cb.checked?"":"none"};l.appendChild(cb);l.insertAdjacentHTML("beforeend"," <span class='dot' style='background:"+D.layers[layer]+"'></span>"+D.names[layer]+" ("+pts.length+")");sw.appendChild(l)}
</script></body></html>
"""


if __name__ == "__main__":
    main()
