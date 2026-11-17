"""Local dev server for the Tbilisi timeline viewer.

Serves the project folder on 127.0.0.1 only and accepts POST /save/<id>
to write data/georef/<id>.json (corner coordinates of an old plan).
Run:  python server.py   (from the viewer folder or anywhere)
"""
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PORT = 8799  # not 8765: that port is published by the glovo-shelf container


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def save_boundary(self, plan_id):
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0 or n > 2_000_000:
            self.send_error(400)
            return
        try:
            data = json.loads(self.rfile.read(n))
            feats = data["features"]
            assert isinstance(feats, list) and len(feats) <= 200
            for f in feats:
                assert f["geometry"]["type"] == "Polygon"
                for ring in f["geometry"]["coordinates"]:
                    assert len(ring) >= 4
                    for c in ring:
                        assert len(c) == 2 and -180 <= c[0] <= 180 and -90 <= c[1] <= 90
                assert isinstance(f["properties"], dict)
        except Exception:
            self.send_error(400)
            return
        out_dir = os.path.join(ROOT, "data", "boundaries")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, plan_id + ".geojson")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"type": "FeatureCollection", "features": feats}, fh, ensure_ascii=False, indent=1)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def reply_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def save_gcp(self, plan_id):
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0 or n > 200_000:
            self.send_error(400)
            return
        try:
            gcps = json.loads(self.rfile.read(n))["gcps"]
            assert isinstance(gcps, list) and len(gcps) <= 100
            clean = []
            for g in gcps:
                px = [float(g["px"][0]), float(g["px"][1])]
                ll = [float(g["lnglat"][0]), float(g["lnglat"][1])]
                assert 0 <= px[0] <= 20000 and 0 <= px[1] <= 20000
                assert -180 <= ll[0] <= 180 and -90 <= ll[1] <= 90
                clean.append({"px": px, "lnglat": ll, "label": str(g.get("label", ""))[:80]})
        except Exception:
            self.send_error(400)
            return
        out_dir = os.path.join(ROOT, "data", "georef")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, plan_id + "_gcp.json"), "w", encoding="utf-8") as fh:
            json.dump({"gcps": clean}, fh, indent=1)
        self.reply_json({"ok": True, "count": len(clean)})

    def run_warp(self, plan_id):
        script = os.path.join(ROOT, "tools", "warp.py")
        try:
            r = subprocess.run([sys.executable, script, plan_id], capture_output=True, text=True,
                               timeout=300, cwd=ROOT)
        except subprocess.TimeoutExpired:
            self.reply_json({"ok": False, "error": "warp timed out"}, 500)
            return
        out = (r.stdout or "").strip().splitlines()
        if r.returncode == 0 and out:
            try:
                self.reply_json(json.loads(out[-1]))
                return
            except Exception:
                pass
        msg = (r.stdout or "") + (r.stderr or "")
        try:
            self.reply_json(json.loads(msg.strip().splitlines()[-1]), 400)
        except Exception:
            self.reply_json({"ok": False, "error": msg[-800:]}, 500)

    def do_POST(self):
        mb = re.fullmatch(r"/save_boundary/([a-z0-9_]{1,40})", self.path)
        if mb:
            self.save_boundary(mb.group(1))
            return
        mg = re.fullmatch(r"/save_gcp/([a-z0-9_]{1,40})", self.path)
        if mg:
            self.save_gcp(mg.group(1))
            return
        mw = re.fullmatch(r"/warp/([a-z0-9_]{1,40})", self.path)
        if mw:
            self.run_warp(mw.group(1))
            return
        m = re.fullmatch(r"/save/([a-z0-9_]{1,40})", self.path)
        if not m:
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0 or n > 10_000:
            self.send_error(400)
            return
        try:
            data = json.loads(self.rfile.read(n))
            corners = data["corners"]
            assert len(corners) == 4 and all(len(c) == 2 for c in corners)
            corners = [[float(c[0]), float(c[1])] for c in corners]
        except Exception:
            self.send_error(400)
            return
        out_dir = os.path.join(ROOT, "data", "georef")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, m.group(1) + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"corners": corners, "order": "TL,TR,BR,BL", "crs": "EPSG:4326 lng,lat"}, f, indent=1)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as srv:
        print(f"http://127.0.0.1:{PORT}/viewer/  (Ctrl+C to stop)")
        srv.serve_forever()
