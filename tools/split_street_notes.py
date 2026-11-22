"""Move the notes of the streets out of site/data/street_names.json into site/data/street_notes.json ({"notes": {<key of the geometry or the English name today>: {"ru","en","ka"}}}):
the notes are 60% of the weight of the street names and are needed only when the card of a street is opened (the app loads the file then). Idempotent.
Usage: python -P tools/split_street_notes.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NAMES = os.path.join(ROOT, "site", "data", "street_names.json")
NOTES = os.path.join(ROOT, "site", "data", "street_notes.json")
DRY = "--dry-run" in sys.argv


def main():
    d = json.load(open(NAMES, encoding="utf-8"))
    notes = json.load(open(NOTES, encoding="utf-8"))["notes"] if os.path.exists(NOTES) else {}
    moved = 0
    for s in d["streets"]:
        if "note" in s:
            key = s.get("geom") or s["now"]["en"]
            notes[key] = s.pop("note")
            moved += 1
    d["note"] = "from data/street_names_verified.json: only names with years stated by the cited Wikipedia pages and by the encyclopedia of the streets (2008); the notes are in street_notes.json"
    if not DRY:
        # keep the form of the files: compact JSON, no final newline; the line endings of the names file stay
        raw = open(NAMES, "rb").read()
        crlf = b"\r\n" in raw
        out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        open(NAMES, "wb").write((out.replace("\n", "\r\n") if crlf else out).encode("utf-8"))
        open(NOTES, "wb").write(json.dumps({"notes": notes}, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print("notes moved: %d; the notes file has %d notes" % (moved, len(notes)))


if __name__ == "__main__":
    main()
