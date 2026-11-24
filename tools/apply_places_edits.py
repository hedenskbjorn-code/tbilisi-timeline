"""Makes the edits of tools/places_edits.json in site/data/places.json: "drop" (ids that repeat another point), "add" (items that no script makes), the outlines of tools/place_contours.json and "move_to" (an id to a given [lon, lat]), "move_to_label" (the pin of an administrative district goes to the label point of
data/district_labels.json, [lon, lat, source], key = the English name of the district). Run it AFTER tools/apply_places.py, apply_folk.py and apply_parks.py. Idempotent: a second run changes nothing.
Usage: python -P tools/apply_places_edits.py [--dry-run]
"""
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    ed = json.load(open(os.path.join(R, "tools", "places_edits.json"), encoding="utf-8"))
    labels = json.load(open(os.path.join(R, "data", "district_labels.json"), encoding="utf-8"))
    p = os.path.join(R, "site", "data", "places.json")
    raw = open(p, "rb").read().decode("utf-8")
    doc = json.loads(raw)
    assert json.dumps(doc, ensure_ascii=False, separators=(",", ":")) == raw, "unexpected layout of places.json"
    dropped = moved = 0
    keep = []
    for it in doc["items"]:
        if it["id"] in ed["drop"]:
            dropped += 1
            continue
        mv = ed.get("move_to", {}).get(it["id"])
        if mv:
            lon, lat = mv
            if (it["lon"], it["lat"]) != (lon, lat):
                it["lon"], it["lat"] = lon, lat
                moved += 1
        k = ed["move_to_label"].get(it["id"])
        if k:
            lon, lat = round(labels[k][0], 5), round(labels[k][1], 5)
            if (it["lon"], it["lat"]) != (lon, lat):
                it["lon"], it["lat"] = lon, lat
                moved += 1
        keep.append(it)
    have = {it["id"] for it in keep}
    added = 0
    for it in ed.get("add", []):                                         # an item that was put in by hand and is not made by a script: added when it is missing
        if it["id"] not in have and it["id"] not in ed["drop"]:
            keep.append(it)
            have.add(it["id"])
            added += 1
    cp = os.path.join(R, "tools", "place_contours.json")                  # the outlines of quarters and squares (tools/place_contours.json): given to an item that lacks one
    contours = json.load(open(cp, encoding="utf-8"))["contours"] if os.path.exists(cp) else {}
    outlined = 0
    for it in keep:
        if it["id"] in contours and not it.get("g"):
            it["g"] = contours[it["id"]]
            outlined += 1
    doc["items"] = keep
    if (dropped or moved or added or outlined) and not dry:
        open(p, "wb").write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print("dropped:", dropped, "| moved:", moved, "| added:", added, "| outlines given:", outlined, "| items now:", len(keep), "| dry-run:", dry)


if __name__ == "__main__":
    main()
