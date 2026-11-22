"""site/data/version.json = the version and the date of the first entry of site/data/changelog.json (the button of the version reads this small file; the log itself is loaded when the button is pressed).
Run after every change of the changelog: python -P tools/build_version.py (tests/check_data.mjs stops the deploy when the two differ).
"""
import json
import os

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
c = json.load(open(os.path.join(R, "site", "data", "changelog.json"), encoding="utf-8"))
open(os.path.join(R, "site", "data", "version.json"), "wb").write(json.dumps({"version": c[0]["version"], "date": c[0]["date"]}).encode("utf-8"))
print("version", c[0]["version"], c[0]["date"])
