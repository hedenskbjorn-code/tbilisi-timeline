"""OCR of a scanned PDF book with pypdfium2 (page rendering, handles JBIG2 layers) and Tesseract (data/cache/tessdata: rus, kat, eng).
Output: data/cache/ocr/<name>/p0001.txt ... and <name>.txt (all pages). Resumable, one page at a time.
Usage: python -P tools/ocr_book.py <pdf> <name> <lang> [first last]      e.g. python -P tools/ocr_book.py "C:/.../Tiflis Bakradze.pdf" bakradze rus 1 10
"""
import os
import subprocess
import sys

import pypdfium2 as pdfium

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TESS = "C:/Program Files/Tesseract-OCR/tesseract.exe"
TESSDATA = os.path.join(ROOT, "data", "cache", "tessdata")


def main():
    pdf, name, lang = sys.argv[1:4]
    pdf_doc = pdfium.PdfDocument(pdf)
    n = len(pdf_doc)
    a = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    b = int(sys.argv[5]) if len(sys.argv) > 5 else n
    out = os.path.join(ROOT, "data", "cache", "ocr", name)
    os.makedirs(out, exist_ok=True)
    for i in range(a, min(b, n) + 1):
        tp = os.path.join(out, "p%04d.txt" % i)
        if os.path.exists(tp):
            continue
        img = pdf_doc[i - 1].render(scale=3.0).to_pil().convert("L")
        ip = os.path.join(out, "tmp_%d.png" % os.getpid())
        img.save(ip)
        r = subprocess.run([TESS, ip, tp[:-4], "-l", lang, "--tessdata-dir", TESSDATA, "--psm", "6"], capture_output=True, text=True)
        if r.returncode != 0:
            print("page", i, "tesseract error", r.stderr[:100], flush=True)
        if i % 10 == 0:
            print(name, i, "/", n, flush=True)
    if len(sys.argv) > 4:                              # a page range: the joined file is made by a final full run
        return
    with open(os.path.join(ROOT, "data", "cache", "ocr", name + ".txt"), "w", encoding="utf-8") as f:
        for i in range(1, n + 1):
            tp = os.path.join(out, "p%04d.txt" % i)
            if os.path.exists(tp):
                f.write("\n=====PAGE %d=====\n" % i + open(tp, encoding="utf-8", errors="replace").read())
    print("done", name)


if __name__ == "__main__":
    main()
