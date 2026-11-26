"""The pack of ALL squares (entries whose heading holds "მოედანი") for the full pass of Gemini (the rules are those of tasks/enc4_streets.md; the answer is checked by tools/verify_enc4.py):
work/gemini/batches/enc/enc4_batch_91.md. The first passes missed the squares whose text had a former name without a clear year (Baratashvili Square, Zhvania Square, Jerusalem Square).
Usage: python -P tools/squares_batch.py
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ents = json.load(open(os.path.join(ROOT, "data", "cache", "enc2008_entries.json"), encoding="utf-8"))
head = lambda t: re.split(r"[,.;:(]", t.strip(), maxsplit=1)[0][:80]
sq = [e for e in ents if re.search(r"მოედან", head(e["text"]))]
lines = ["# Полный проход, партия 91: ВСЕ площади энциклопедии (годы в тексте исправлены); не пропускай статью, если в тексте названо любое прежнее название, даже без года", ""]
for e in sq:
    lines.append("## %s | PDF p. %s | район: %s | заголовок (OCR): %s\n\n```\n%s\n```\n" % (e["id"], e["page"], e["district"], e["name"], e.get("text_long") or e["text"]))
open(os.path.join(ROOT, "work", "gemini", "batches", "enc", "enc4_batch_91.md"), "w", encoding="utf-8").write("\n".join(lines))
print("squares:", len(sq))
