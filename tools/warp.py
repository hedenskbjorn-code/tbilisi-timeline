"""Warp an old plan to the modern map using ground control points (GCPs).

Usage: python tools/warp.py <plan_id> [--exclude=0,2,15] [--affine]   (indices into the saved points file; --affine forbids the TPS residual)
Reads : data/georef/<id>_gcp.json  ({"gcps":[{"px":[x,y],"lnglat":[lng,lat]}, ...]})
        viewer/maps.json           (to find the image path)
Writes: data/warped/<id>.webp  (north-up, Web Mercator-linear, transparent outside the plan)
        data/warped/<id>.json  (corner coordinates TL,TR,BR,BL + error statistics)
Prints a JSON summary on stdout.

Model: fewer than 6 points -> least-squares affine; 6 or more -> affine + thin-plate-spline
residual with mild smoothing. Errors are reported as leave-one-out (honest) and in-sample.
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image
from scipy.interpolate import RBFInterpolator

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = 6378137.0
LAT_REF = 41.7
COSL = math.cos(math.radians(LAT_REF))


def merc(lng, lat):
    x = R * math.radians(lng)
    y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def unmerc(x, y):
    lng = math.degrees(x / R)
    lat = math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
    return lng, lat


class Warp:
    """Maps A -> B (both Nx2 arrays, normalised) with affine + optional TPS residual."""

    def __init__(self, A, B, smoothing):
        self.A0, self.As = A.mean(0), A.std(0).mean() or 1.0
        self.B0, self.Bs = B.mean(0), B.std(0).mean() or 1.0
        a = (A - self.A0) / self.As
        b = (B - self.B0) / self.Bs
        X = np.hstack([a, np.ones((len(a), 1))])
        self.M, *_ = np.linalg.lstsq(X, b, rcond=None)      # 3x2 affine
        res = b - X @ self.M
        self.tps = None
        if smoothing is not None and len(a) >= 6:
            self.tps = RBFInterpolator(a, res, kernel="thin_plate_spline", smoothing=smoothing, degree=1)

    def inverse(self):
        """Exact inverse of the affine part (valid only when there is no TPS residual)."""
        assert self.tps is None
        Minv = np.linalg.inv(self.M[:2])
        class _Inv:
            def __init__(s, w):
                s.w = w
            def __call__(s, B):
                b = (np.asarray(B, float) - s.w.B0) / s.w.Bs
                a = (b - s.w.M[2]) @ Minv
                return a * s.w.As + s.w.A0
        return _Inv(self)

    def __call__(self, A):
        a = (np.asarray(A, float) - self.A0) / self.As
        out = np.hstack([a, np.ones((len(a), 1))]) @ self.M
        if self.tps is not None:
            out = out + self.tps(a)
        return out * self.Bs + self.B0


def main(plan_id, exclude=()):
    gcp_path = os.path.join(ROOT, "data", "georef", plan_id + "_gcp.json")
    gdata = json.load(open(gcp_path, encoding="utf-8"))
    gcps = gdata["gcps"]
    if not exclude:
        exclude = set(gdata.get("excluded_default", []))      # indices dropped by cleaning, stored with the points
    if exclude:
        gcps = [g for i, g in enumerate(gcps) if i not in exclude]   # indices as in the saved file
    n = len(gcps)
    if n < 3:
        raise SystemExit(json.dumps({"ok": False, "error": "need at least 3 control points, have %d" % n}))
    plans = json.load(open(os.path.join(ROOT, "viewer", "maps.json"), encoding="utf-8"))
    plan = next(p for p in plans if p["id"] == plan_id)
    img_path = os.path.join(ROOT, plan["image"].lstrip("/"))
    img = Image.open(img_path).convert("RGB")
    W, H = img.size

    P = np.array([g["px"] for g in gcps], float)                       # pixel
    M = np.array([merc(*g["lnglat"]) for g in gcps], float)            # mercator metres
    def loo_errors(smoothing):
        errs = []
        for i in range(n):
            keep = [j for j in range(n) if j != i]
            w = Warp(P[keep], M[keep], smoothing)
            errs.append(float(np.linalg.norm(w(P[i:i + 1])[0] - M[i]) * COSL))
        return errs

    # model selection by leave-one-out error: pure affine vs affine + TPS with several stiffnesses.
    # (smoothing=None means affine only). TPS needs at least 6 points (Warp ignores it below that).
    candidates = [None] + ([0.01, 0.1, 1.0, 10.0] if n >= 7 and "--affine" not in sys.argv else [])
    scores = {}
    if n >= 4:
        for s in candidates:
            scores[s] = loo_errors(s)
        smoothing = min(scores, key=lambda s: float(np.sqrt(np.mean(np.square(scores[s])))))
        loo = scores[smoothing]
    else:
        smoothing, loo = None, []
    fwd = Warp(P, M, smoothing)       # pixel -> mercator
    # affine: exact analytic inverse (an independent regression M->P would be biased when residuals are large)
    inv = fwd.inverse() if smoothing is None else Warp(M, P, smoothing)       # mercator -> pixel
    # errors in ground metres (mercator metres * cos(lat))
    ins = np.linalg.norm(fwd(P) - M, axis=1) * COSL
    model = "affine" if smoothing is None else "affine+TPS(smoothing=%g)" % smoothing
    rng = np.random.default_rng(0)
    Pr = np.stack([rng.uniform(0, W, 200), rng.uniform(0, H, 200)], 1)
    roundtrip_px = float(np.sqrt(((inv(fwd(Pr)) - Pr) ** 2).sum(1).mean()))

    # output extent: plan frame mapped to mercator
    frame = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
    edge = np.vstack([np.linspace(frame[i], frame[(i + 1) % 4], 60) for i in range(4)])
    E = fwd(edge)
    x0, y0 = E.min(0)
    x1, y1 = E.max(0)
    width_m = x1 - x0
    out_w = int(min(5000, max(1500, width_m / 1.2)))
    res = width_m / out_w                       # mercator metres per output pixel
    out_h = int(math.ceil((y1 - y0) / res))

    # evaluate inverse warp on a coarse grid, then upsample
    # Coarse sample k sits at output pixel index k*step + (step-1)/2, which is exactly where
    # cv2.resize puts block k's centre, so upsampling is aligned. One extra sample on each side
    # (k = -1 and k = K) avoids edge clamping; those margins are cropped after resizing.
    step = 40
    kx = np.arange(-1, out_w // step + 2)
    ky = np.arange(-1, out_h // step + 2)
    cx = kx * step + (step - 1) / 2.0
    cy = ky * step + (step - 1) / 2.0
    GX, GY = np.meshgrid(cx, cy)
    mx = x0 + (GX + 0.5) * res
    my = y1 - (GY + 0.5) * res
    pix = inv(np.stack([mx.ravel(), my.ravel()], 1)).reshape(GX.shape + (2,))
    big = (len(kx) * step, len(ky) * step)
    mapx = cv2.resize(pix[..., 0].astype(np.float32), big, interpolation=cv2.INTER_LINEAR)[step:step + out_h, step:step + out_w]
    mapy = cv2.resize(pix[..., 1].astype(np.float32), big, interpolation=cv2.INTER_LINEAR)[step:step + out_h, step:step + out_w]
    # clicked pixel coordinates are edge-based (0..W); remap wants index-based (centres at integers)
    mapx = np.ascontiguousarray(mapx - 0.5)
    mapy = np.ascontiguousarray(mapy - 0.5)

    src = np.array(img)
    warped = cv2.remap(src, mapx, mapy, interpolation=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    inside = ((mapx >= 0) & (mapx <= W - 1) & (mapy >= 0) & (mapy <= H - 1)).astype(np.uint8) * 255
    alpha = cv2.erode(inside, np.ones((3, 3), np.uint8))
    rgba = np.dstack([warped, alpha])

    out_dir = os.path.join(ROOT, "data", "warped")
    os.makedirs(out_dir, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, plan_id + ".webp"), quality=88, method=4)

    corners = [unmerc(x0, y1), unmerc(x1, y1), unmerc(x1, y0), unmerc(x0, y0)]   # TL,TR,BR,BL
    info = {
        "ok": True, "id": plan_id, "model": model, "points": n, "excluded_indices": sorted(exclude),
        "in_sample_rms_m": float(np.sqrt((ins ** 2).mean())),
        "in_sample_max_m": float(ins.max()),
        "loo_rms_m": float(np.sqrt((np.array(loo) ** 2).mean())) if loo else None,
        "loo_per_point_m": [round(v) for v in loo],
        "loo_by_model_rms_m": {("affine" if s is None else "tps_%g" % s): round(float(np.sqrt(np.mean(np.square(v)))), 1)
                               for s, v in scores.items()},
        "roundtrip_px_rms": round(roundtrip_px, 3),
        "corners": [[round(c[0], 8), round(c[1], 8)] for c in corners],
        "image": "/data/warped/%s.webp" % plan_id,
        "size": [out_w, out_h],
    }
    json.dump(info, open(os.path.join(out_dir, plan_id + ".json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(info))


if __name__ == "__main__":
    excl = ()
    for a in sys.argv[2:]:
        if a.startswith("--exclude="):
            excl = {int(v) for v in a.split("=", 1)[1].split(",") if v}
    main(sys.argv[1], excl)
