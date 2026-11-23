"""Wikidata labels (ka, ru, en) of the persons / subjects (subject_qid) of the monuments and plaques (data/cache/monuments_clean.json) -> data/cache/monument_labels.json ({qid: {ka, ru, en}}).
The labels fill the names that are missing in a language (tools/build_monuments_names.py); a label is the name of the person as Wikidata gives it. Sequential, with pauses, a generic User-Agent.
Usage: python -P tools/fetch_monument_labels.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = "tbilisi-timeline-hobby/1.0 (non-commercial hobby project)"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(os.path.join(R, "data", "cache", "monuments_clean.json"), encoding="utf-8"))
    q = sorted({v for x in d["monuments"] + d["plaques"] for v in (x["qid"] + ";" + x.get("sc_qid", "")).split(";") if v.startswith("Q")})            # one object may name several subjects ("Q1;Q2")
    out = {}
    for i in range(0, len(q), 50):
        u = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels|descriptions&languages=ka|ru|en&ids=" + "|".join(q[i:i + 50])
        for k in range(5):
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60))
                break
            except Exception:
                time.sleep(10 * (k + 1))
        else:
            raise SystemExit("wikidata failed")
        if "error" in r:
            raise SystemExit("wikidata error: " + str(r["error"].get("info"))[:200])
        for qid, e in r.get("entities", {}).items():
            out[qid] = {lg: e.get("labels", {}).get(lg, {}).get("value", "") for lg in ("ka", "ru", "en")}
        time.sleep(1)
    json.dump(out, open(os.path.join(R, "data", "cache", "monument_labels.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("qids:", len(q), "| labels:", len(out), "| with ru:", sum(1 for v in out.values() if v["ru"]), "| with en:", sum(1 for v in out.values() if v["en"]), "| with ka:", sum(1 for v in out.values() if v["ka"]))


if __name__ == "__main__":
    main()
