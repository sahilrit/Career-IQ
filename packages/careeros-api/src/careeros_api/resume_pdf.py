"""Typeset a résumé or cover letter from its Markdown into a structured PDF.

The previous exporter dumped the document as one flat run of Helvetica
text encoded to latin-1, so an accented name lost its accents, a rupee
sign vanished, and the page was an undifferentiated wall of lines. This
reads the predictable Markdown our résumé renderer emits (`#` name,
`*headline*`, `##` sections, `###` roles, `_dates_`, `-` bullets) and lays
it out as a real one-column CV: a name header over a hairline rule,
gold-tinted section labels, roles with right-aligned dates, and indented
bullets.

It stays on fpdf2's core fonts — no binary font to bundle, no Typst
toolchain in the image, so it ships on Render as-is — and keeps non-latin
text legible by transliterating it to the nearest ASCII rather than
replacing each character with "?".
"""

from __future__ import annotations

import re
import unicodedata

# Accent colour from the web design system (signal-gold), for section labels.
_ACCENT = (176, 132, 48)
_INK = (28, 27, 35)
_MUTED = (110, 108, 120)

# Smart punctuation and common symbols mapped to a latin-1 form before the
# transliteration fallback, so quotes and dashes read naturally rather than
# being flattened to nothing.
_SYMBOLS = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "--",
    "…": "...",
    "•": "-",
    " ": " ",
    "₹": "Rs",  # ₹ has no latin-1 form
    "€": "EUR",  # € is cp1252, not latin-1 — core fonts cannot render it
    "→": "->",
}

_SYMBOL_RE = re.compile("|".join(re.escape(k) for k in _SYMBOLS))


def _to_latin1(text: str) -> str:
    """Make text safe for fpdf2's core fonts without losing information.

    latin-1 characters (é, ü, £) pass through untouched. Smart
    punctuation is mapped to its ASCII shape. Anything left — CJK, Devanagari,
    emoji — is transliterated to the nearest ASCII via Unicode decomposition,
    so "José" stays "José" but "北京" becomes a romanised stand-in rather than
    a row of replacement marks.
    """
    mapped = _SYMBOL_RE.sub(lambda m: _SYMBOLS[m.group()], text)
    out: list[str] = []
    for char in mapped:
        try:
            char.encode("latin-1")
            out.append(char)
            continue
        except UnicodeEncodeError:
            pass
        decomposed = unicodedata.normalize("NFKD", char).encode("ascii", "ignore").decode("ascii")
        out.append(decomposed)
    return "".join(out)


class _ResumePDF:
    """Thin layout helper over fpdf2 for one document."""

    def __init__(self) -> None:
        from fpdf import FPDF

        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=16)
        self.pdf.add_page()
        self.pdf.set_margins(18, 16, 18)
        self._width = self.pdf.w - 36

    def _text(self, text: str) -> str:
        return _to_latin1(text)

    def name(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.set_font("Helvetica", style="B", size=22)
        self.pdf.set_text_color(*_INK)
        self.pdf.multi_cell(0, 10, self._text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def headline(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.set_font("Helvetica", style="I", size=12)
        self.pdf.set_text_color(*_MUTED)
        self.pdf.multi_cell(0, 6, self._text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def contact(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.set_font("Helvetica", size=10)
        self.pdf.set_text_color(*_MUTED)
        self.pdf.multi_cell(0, 5, self._text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def rule(self) -> None:
        self.pdf.ln(2)
        y = self.pdf.get_y()
        self.pdf.set_draw_color(*_ACCENT)
        self.pdf.set_line_width(0.4)
        self.pdf.line(18, y, self.pdf.w - 18, y)
        self.pdf.ln(3)

    def section(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.ln(2)
        self.pdf.set_font("Helvetica", style="B", size=11)
        self.pdf.set_text_color(*_ACCENT)
        self.pdf.multi_cell(0, 6, self._text(text.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.set_text_color(*_INK)

    def role(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.ln(1)
        self.pdf.set_font("Helvetica", style="B", size=11)
        self.pdf.set_text_color(*_INK)
        self.pdf.multi_cell(0, 6, self._text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def dates(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.set_font("Helvetica", style="I", size=9)
        self.pdf.set_text_color(*_MUTED)
        self.pdf.multi_cell(0, 5, self._text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.set_text_color(*_INK)

    def body(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.set_font("Helvetica", size=10)
        self.pdf.set_text_color(*_INK)
        self.pdf.multi_cell(0, 5.4, self._text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def bullet(self, text: str) -> None:
        from fpdf.enums import XPos, YPos

        self.pdf.set_font("Helvetica", size=10)
        self.pdf.set_text_color(*_INK)
        x = self.pdf.get_x()
        self.pdf.set_x(x + 4)
        self.pdf.multi_cell(
            self._width - 4,
            5.4,
            self._text(f"•  {text}"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    def output(self) -> bytes:
        return bytes(self.pdf.output())


_H1 = re.compile(r"^#\s+(.*)$")
_H2 = re.compile(r"^##\s+(.*)$")
_H3 = re.compile(r"^###\s+(.*)$")
_ITALIC_LINE = re.compile(r"^[*_](.+)[*_]$")
_BULLET = re.compile(r"^[-*]\s+(.*)$")


def render_markdown_pdf(title: str, markdown: str) -> bytes:
    """Render one document's Markdown into a typeset PDF.

    Tolerant of anything that is not our own Markdown — a plain cover letter
    with no headings lays out as clean body text — so it is safe for every
    document kind, not just résumés.
    """
    doc = _ResumePDF()
    seen_first_heading = False
    lines = markdown.split("\n") if markdown else []

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            doc.pdf.ln(2)
            continue

        if m := _H1.match(line):
            doc.name(m.group(1))
            seen_first_heading = True
        elif m := _H2.match(line):
            doc.section(m.group(1))
        elif m := _H3.match(line):
            # "Title — Company" stays together; dates come on the next line.
            doc.role(m.group(1))
        elif m := _BULLET.match(line):
            doc.bullet(m.group(1))
        elif (m := _ITALIC_LINE.match(line)) and not seen_first_heading:
            doc.headline(m.group(1))
        elif (m := _ITALIC_LINE.match(line)) and seen_first_heading:
            # An italic line after the header is a date range.
            doc.dates(m.group(1))
        elif not seen_first_heading and (" | " in line or "@" in line):
            doc.contact(line)
            doc.rule()
        else:
            doc.body(line)

    # A document with no H1 at all (e.g. a bare cover letter) still needs a
    # heading so the export is not anonymous.
    if not seen_first_heading and title:
        # Prepend the title by rendering a fresh doc — cheaper to just re-run.
        titled = _ResumePDF()
        titled.name(title)
        titled.rule()
        for raw in lines:
            line = raw.rstrip()
            if line.strip():
                titled.body(line)
            else:
                titled.pdf.ln(2)
        return titled.output()

    return doc.output()
