"""Flag Commons photos that show people (selfies, portraits, groups close up) so the site can leave them out.

1. Downloads each candidate thumbnail once (data/cache/thumbs/, resumable, polite delay).
2. Detects faces locally with the YuNet neural face detector shipped as a model for OpenCV
   (data/raw/models/face_detection_yunet_2023mar.onnx, from github.com/opencv/opencv_zoo, 232 589 bytes).
3. Writes data/cache/photos_people.json  {title: {"faces": n, "skin_faces": n, "face": widest face / image width, "title_hit": bool,
   "missing": bool, "reject": bool}}

Rule (deliberately on the side of dropping a photo - a missing photo is better than a selfie on the map):
reject if the title contains a word for people, or any detected face has skin colour (a person; busts and reliefs on
memorial plaques have none and are kept), or a face is wider than BIG_FACE of the image (close-up portrait).
People seen from behind, in shadow or too small to detect can still pass: see sources.md.

Wikimedia asks automated clients to identify themselves: set WIKIMEDIA_CONTACT in the environment (never commit it).
Usage:  python tools/filter_photos.py [--analyse-only]
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE = os.path.join(ROOT, "data", "cache")
THUMBS = os.path.join(CACHE, "thumbs")
MODEL = os.path.join(ROOT, "data", "raw", "models", "face_detection_yunet_2023mar.onnx")
os.makedirs(THUMBS, exist_ok=True)
_contact = os.environ.get("WIKIMEDIA_CONTACT")
UA = "tbilisi-timeline-hobby/0.1 (non-commercial hobby project; Wikimedia Commons client%s)" % ("; contact: " + _contact if _contact else "")
DELAY = 0.3

SCORE = 0.7             # YuNet confidence threshold
SKIN_MIN = 0.30         # a detected face counts as a real person if this share of its box is skin-coloured
BIG_FACE = 0.30         # a face wider than 30% of the image is a close-up portrait whatever its colour
TITLE = re.compile(r"selfie|portrait|people|person|\bman\b|\bmen\b|woman|women|girl|\bboy\b|child|\bkids?\b|family|wedding|"
                   r"group|friends|tourist|crowd|dance|concert|party|student|face|smile|me and|with my|"
                   r"self-portrait|bride|groom|musician|singer|player", re.I)


def path_for(title):
    return os.path.join(THUMBS, hashlib.sha1(title.encode("utf-8")).hexdigest() + ".jpg")


def download(info):
    n = 0
    for title, f in info.items():
        url = f.get("thumb")
        p = path_for(title)
        if not url or os.path.exists(p):
            continue
        for k in range(5):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r, open(p + ".part", "wb") as out:
                    out.write(r.read())
                os.replace(p + ".part", p)
                break
            except Exception as e:
                wait = 20 * (k + 1)
                ra = getattr(getattr(e, "headers", None), "get", lambda *_: None)("Retry-After")
                if ra and str(ra).isdigit():
                    wait = max(wait, int(ra) + 5)
                print("  retry %s in %ds (%s)" % (title[:40], wait, e), flush=True)
                time.sleep(wait)
        n += 1
        if n % 100 == 0:
            print("  downloaded %d" % n, flush=True)
        time.sleep(DELAY)


def skin_fraction(img, box):
    """Share of skin-coloured pixels (YCrCb range) inside a face box: a bust or a relief on a plaque has almost none."""
    x, y, w, h = [int(v) for v in box]
    x, y = max(x, 0), max(y, 0)
    crop = img[y:y + h, x:x + w]
    if crop.size == 0:
        return 0.0
    ycc = cv2.cvtColor(crop, cv2.COLOR_BGR2YCrCb)
    m = cv2.inRange(ycc, (0, 133, 77), (255, 173, 127))
    return float((m > 0).mean())


def analyse(info):
    det = cv2.FaceDetectorYN.create(MODEL, "", (320, 320), SCORE, 0.3, 5000)
    res = {}
    for title in info:
        p = path_for(title)
        row = {"faces": 0, "skin_faces": 0, "face": 0.0, "title_hit": bool(TITLE.search(title)), "missing": False}
        img = cv2.imread(p) if os.path.exists(p) else None
        if img is None:
            row["missing"] = True
            row["reject"] = row["title_hit"]
            res[title] = row
            continue
        h, w = img.shape[:2]
        det.setInputSize((w, h))
        _, faces = det.detect(img)
        faces = [] if faces is None else list(faces)
        widths = [float(f[2]) / w for f in faces]
        skin = [skin_fraction(img, f[:4]) >= SKIN_MIN for f in faces]
        row["faces"] = len(faces)
        row["skin_faces"] = sum(skin)
        row["face"] = round(max(widths, default=0.0), 3)
        # reject: any real (skin-coloured) face, or a very large face of any colour (close-up portrait, old photograph)
        row["reject"] = bool(row["title_hit"] or row["skin_faces"] > 0 or row["face"] >= BIG_FACE)
        res[title] = row
    return res


if __name__ == "__main__":
    info = json.load(open(os.path.join(CACHE, "photos_info.json"), encoding="utf-8"))
    if "--analyse-only" not in sys.argv:
        print("thumbnails: %d files" % len(info), flush=True)
        download(info)
    res = analyse(info)
    json.dump(res, open(os.path.join(CACHE, "photos_people.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("analysed %d; rejected %d (title %d, skin face %d, big face %d); faces without skin (busts, plaques) kept: %d; missing %d" % (
        len(res), sum(r["reject"] for r in res.values()), sum(r["title_hit"] for r in res.values()),
        sum(r.get("skin_faces", 0) > 0 for r in res.values()), sum(r["face"] >= BIG_FACE for r in res.values()),
        sum(1 for r in res.values() if r["faces"] > 0 and not r.get("skin_faces") and not r["reject"]), sum(r["missing"] for r in res.values())))
