#!/usr/bin/env python3
"""Build a PDF of the tide chart from tide-chart-colorado-grand-canyon.html."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tide-chart-colorado-grand-canyon.html"
OUT_PDF = ROOT / "Grand-Canyon-Tide-Chart.pdf"

CHROME_MAC = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)

PRINT_CSS = """
/* PDF layout — matches rapids PDF styling */
@page {
  size: landscape;
  margin: 10mm 12mm;
}
body {
  margin: 0;
  padding: 12mm 14mm 14mm;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
main { max-width: none; }
h1 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0 0 6px;
  color: #1a365d;
  letter-spacing: -0.02em;
  border-bottom: 2px solid #2c5282;
  padding-bottom: 8px;
}
.subtitle {
  font-size: 0.88rem;
  margin: 10px 0 12px;
  color: #374151;
  line-height: 1.45;
  max-width: 72rem;
}
.back { display: none !important; }
.pdf-dl { display: none !important; }
table {
  width: 100%;
  max-width: none;
  font-size: 9.5pt;
  border: 1px solid #94a3b8;
}
thead th {
  position: static !important;
  box-shadow: none !important;
  background: #334155 !important;
  color: #f8fafc !important;
  font-weight: 600;
  padding: 6px 8px;
  border-color: #475569;
}
th, td {
  border-color: #cbd5e0;
  padding: 4px 7px;
}
tbody tr:nth-child(even) td { background: #f1f5f9 !important; }
tbody tr:nth-child(odd) td { background: #fff !important; }
.num { font-size: 9pt; }
.source-note {
  margin-top: 10px;
  font-size: 8.5pt;
  color: #4b5563;
  line-height: 1.4;
}
footer.tide-disclaimer {
  position: static !important;
  margin-top: 12px;
  padding: 10px 12px;
  font-size: 8pt;
  line-height: 1.45;
  color: #1f2937;
  background: #f8fafc !important;
  border: 1px solid #cbd5e0;
  border-radius: 4px;
  box-shadow: none !important;
}
footer.tide-disclaimer p {
  margin: 0;
  max-width: none;
}
"""


def prepare_html(raw: str) -> str:
    html = re.sub(
        r'<p class="back">.*?</p>\s*',
        "",
        raw,
        count=1,
        flags=re.DOTALL,
    )
    if "</style>" not in html:
        raise ValueError("source HTML missing </style>")
    return html.replace("</style>", PRINT_CSS + "\n</style>", 1)


def main() -> int:
    if not SOURCE.is_file():
        print(f"Missing {SOURCE.name}", file=sys.stderr)
        return 1

    chrome = Path(CHROME_MAC)
    if not chrome.is_file():
        print(f"Chrome not found at {chrome}", file=sys.stderr)
        return 1

    out = prepare_html(SOURCE.read_text(encoding="utf-8"))

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
