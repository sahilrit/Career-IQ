"""Render a resume's plain text into a PDF file for form uploads.

fpdf2 is free/open-source (no service, no key), so this stays within
the zero-cost constraint. ATS forms overwhelmingly accept PDF; the
text layout is deliberately plain so parsers read it cleanly.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

_MARGIN_MM = 18
_BODY_SIZE = 10
_LINE_HEIGHT = 5


def write_resume_pdf(resume_text: str, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF(format="A4")
    pdf.set_margins(_MARGIN_MM, _MARGIN_MM)
    pdf.set_auto_page_break(auto=True, margin=_MARGIN_MM)
    pdf.add_page()
    pdf.set_font("helvetica", size=_BODY_SIZE)

    # Core fonts are latin-1; degrade exotic characters instead of crashing.
    safe_text = resume_text.encode("latin-1", "replace").decode("latin-1")
    usable_width = pdf.w - 2 * _MARGIN_MM
    for line in safe_text.splitlines():
        pdf.multi_cell(usable_width, _LINE_HEIGHT, line or " ")

    pdf.output(str(output_path))
    return output_path
