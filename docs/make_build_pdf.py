"""Makes docs/BLIPR Build Guide.pdf from docs/BLIPR Build Guide.docx (run docs/make_build_doc.py first).
Needs LibreOffice (soffice on the PATH; on a Mac: brew install --cask libreoffice). Run from anywhere:
    python docs/make_build_pdf.py"""
import shutil
import subprocess
import tempfile
from pathlib import Path

DOCS = Path(__file__).resolve().parent
SRC = DOCS / "BLIPR Build Guide.docx"
OUT = DOCS / "BLIPR Build Guide.pdf"

soffice = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(SRC)], check=True,
                   stdout=subprocess.DEVNULL)
    shutil.move(str(Path(tmp) / (SRC.stem + ".pdf")), OUT)
print("wrote", OUT)
