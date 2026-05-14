#!/usr/bin/env python3
"""Build a PDF of the rapids table from index.html (legend + color rows)."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
OUT_PDF = ROOT / "Grand-Canyon-Rapids-May-2026.pdf"

CHROME_MAC = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)

PRINT_CSS = """
/* PDF / print layout */
@page {
  size: landscape;
  margin: 10mm 12mm;
}
@media print {
  body { margin: 0; }
}
body {
  margin: 0;
  padding: 14mm 16mm 16mm;
  color: #1a1a1a;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.doc-header {
  border-bottom: 2px solid #2c5282;
  padding-bottom: 10px;
  margin-bottom: 14px;
}
.doc-header h1 {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 6px;
  color: #1a365d;
  letter-spacing: -0.02em;
}
.doc-header .trip-lede {
  font-size: 0.88rem;
  margin: 0;
  color: #444;
  line-height: 1.45;
}
.legend {
  margin: 0 0 14px;
  padding: 10px 14px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
  max-width: none;
}
.legend h2 {
  font-size: 0.95rem;
  margin: 0 0 8px;
  font-weight: 650;
  color: #2d3748;
}
.legend-items { gap: 1rem 2rem; }
.legend-item { font-size: 0.82rem; color: #374151; }
.legend-swatch { width: 14px; height: 14px; }
table {
  width: 100%;
  max-width: none;
  font-size: 8.5pt;
  border: 1px solid #94a3b8;
}
thead th {
  position: static;
  box-shadow: none;
  background: #334155 !important;
  color: #f8fafc;
  font-weight: 600;
  padding: 6px 7px;
  border-color: #475569;
}
th, td {
  border-color: #cbd5e0;
  padding: 4px 6px;
  vertical-align: top;
}
tbody tr.rank-none td { background: #c8e6c9 !important; }
tbody tr.rank-must-scout td { background: #ffcdd2 !important; }
tbody tr.rank-5 td { background: #fff9c4 !important; }
td:nth-child(1) { width: 4%; white-space: nowrap; font-variant-numeric: tabular-nums; }
td:nth-child(2) { width: 8%; white-space: nowrap; }
td:nth-child(3) { width: 22%; }
td:nth-child(4) { width: 66%; font-size: 8pt; line-height: 1.35; }
"""


def strip_resources(html: str) -> str:
    return re.sub(
        r'<section class="resources">.*?</section>\s*',
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )


def inject_print_styles(html: str) -> str:
    # Replace opening body margin and append print wrapper styles after existing style block
    if "</style>" not in html:
        raise ValueError("index.html missing </style>")
    return html.replace(
        "body { font-family: system-ui, sans-serif; margin: 1.5rem; }",
        "body { font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; margin: 0; }",
        1,
    ).replace("</style>", PRINT_CSS + "\n</style>", 1)


def wrap_header(html: str) -> str:
    """Wrap h1 + trip-lede in a header div for PDF styling."""
    html = html.replace(
        "<body>\n<h1>",
        "<body>\n<div class=\"doc-header\">\n<h1>",
        1,
    )
    html = html.replace(
        "</p>\n<section class=\"legend\"",
        "</p>\n</div>\n<section class=\"legend\"",
        1,
    )
    return html


def main() -> int:
    if not INDEX.is_file():
        print("Missing index.html", file=sys.stderr)
        return 1
    raw = INDEX.read_text(encoding="utf-8")
    out = strip_resources(raw)
    out = inject_print_styles(out)
    out = wrap_header(out)

    chrome = Path(CHROME_MAC)
    if not chrome.is_file():
        print(f"Chrome not found at {chrome}", file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(out)
        tmp_path = Path(tmp.name)

    url = tmp_path.as_uri()
    cmd = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUT_PDF}",
        url,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        tmp_path.unlink(missing_ok=True)
    print(f"Wrote {OUT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
