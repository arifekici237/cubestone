"""
Markdown -> PDF converter (Windows, no external toolchain).

Renders a Markdown file to a styled, print-ready A4 PDF using the local
Microsoft Edge (Chromium) in headless "--print-to-pdf" mode. No pandoc/LaTeX
required. Usage:

    python tools/md_to_pdf.py [input.md] [output.pdf]

Defaults: TDD_Teknik_Tasarim_Dokumani.md  ->  TDD_Cubestone.pdf
"""
import sys
import time
import tempfile
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).parent.parent

CSS = """
@page { size: A4; margin: 1.5cm 1.7cm; }
* { box-sizing: border-box; }
body {
  font-family: 'Segoe UI', 'Calibri', Arial, sans-serif;
  font-size: 10.3pt; line-height: 1.45; color: #1b1b1b; margin: 0;
}
h1 { font-size: 19pt; text-align: center; margin: 0 0 2px; color: #14223b; }
h1 + h3 { text-align: center; color: #5a6473; font-weight: 500;
          margin: 0 0 6px; font-size: 11pt; }
h2 { font-size: 13.5pt; color: #14223b; margin: 16px 0 6px;
     padding-bottom: 3px; border-bottom: 2px solid #2d4a7a;
     page-break-after: avoid; }
h3 { font-size: 11.3pt; color: #25304a; margin: 11px 0 4px;
     page-break-after: avoid; }
p { margin: 5px 0; text-align: justify; }
ul, ol { margin: 5px 0 5px 0; padding-left: 20px; }
li { margin: 2px 0; }
strong { color: #10203a; }
table { width: 100%; border-collapse: collapse; margin: 8px 0;
        font-size: 9.3pt; page-break-inside: avoid; }
th, td { border: 1px solid #bcc4d0; padding: 4px 7px; text-align: left;
         vertical-align: top; }
th { background: #eef2f8; color: #14223b; font-weight: 600; }
tr:nth-child(even) td { background: #fafbfd; }
code { font-family: 'Consolas', 'Courier New', monospace; font-size: 8.9pt;
       background: #eef1f5; padding: 1px 4px; border-radius: 3px;
       color: #b8002e; }
pre { background: #f6f8fa; border: 1px solid #d5dbe2; border-radius: 5px;
      padding: 8px 10px; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; color: #1b1b1b; padding: 0; font-size: 8.7pt; }
blockquote { border-left: 3px solid #8a97a8; margin: 8px 0; padding: 2px 12px;
             color: #4a5360; font-style: italic; background: #f7f8fa; }
hr { border: none; border-top: 1px solid #dde1e7; margin: 12px 0; }
a { color: #1b1b1b; text-decoration: none; }
"""

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser() -> str:
    for c in EDGE_CANDIDATES:
        if Path(c).exists():
            return c
    raise SystemExit("No Edge/Chrome found for PDF printing.")


def build_html(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    return (
        "<!DOCTYPE html><html lang='tr'><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


def main():
    md_in = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "TDD_Teknik_Tasarim_Dokumani.md"
    pdf_out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "TDD_Cubestone.pdf"

    browser = find_browser()
    # Do ALL browser I/O inside a clean temp dir: Edge's --print-to-pdf / file://
    # arguments choke on the project path's spaces, parentheses and non-ASCII
    # characters ("Yeni klasör (8)"). We render to temp, then copy out.
    work = Path(tempfile.mkdtemp(prefix="edgepdf_"))
    profile = work / "prof"
    html_file = work / "doc.html"
    tmp_pdf = work / "doc.pdf"
    html_file.write_text(build_html(md_in), encoding="utf-8")

    def launch(headless_flag: str):
        cmd = [
            browser, headless_flag,
            "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
            f"--user-data-dir={profile}",
            f"--print-to-pdf={tmp_pdf}",
            html_file.as_uri(),
        ]
        # Edge spawns a detached child and the launcher returns immediately,
        # so we fire-and-poll for the output file rather than waiting on exit.
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        for _ in range(30):                 # poll up to ~30 s
            if tmp_pdf.exists() and tmp_pdf.stat().st_size > 0:
                return True
            time.sleep(1)
        return tmp_pdf.exists()

    print("Rendering PDF via:", Path(browser).name)
    ok = launch("--headless") or launch("--headless=new")

    if ok and tmp_pdf.exists():
        import shutil
        if pdf_out.exists():
            pdf_out.unlink()
        shutil.copyfile(tmp_pdf, pdf_out)
        shutil.rmtree(work, ignore_errors=True)
        kb = pdf_out.stat().st_size / 1024
        print(f"OK -> {pdf_out.name} ({kb:.0f} KB)")
    else:
        print("FAILED to produce PDF (temp:", work, ")")
        sys.exit(1)


if __name__ == "__main__":
    main()
