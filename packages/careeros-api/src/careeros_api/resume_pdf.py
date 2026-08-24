"""Typeset a résumé or cover letter from its Markdown into a structured PDF.

The previous exporter used fpdf2's core fonts, so it had to encode text to
latin-1: an accented name lost its accents, a rupee sign vanished, and long
scripts (CJK, Devanagari) had no glyph at all. This reads the predictable
Markdown our résumé renderer emits (`#` name, `*headline*`, `##` sections,
`###` roles, `_dates_`, `-` bullets) and typesets it through Typst — a real
typesetting engine — as a one-column CV: a name header over a hairline
rule, gold-tinted section labels, roles with dates, and indented bullets.

Typst's own embedded fonts (no system fonts required — the Dockerfile.api
deploy image ships none) render full Unicode for Latin script (any accent),
smart punctuation, and currency symbols natively, so none of that needs
transliterating any more. Only scripts with genuinely no glyph in those
fonts — CJK ideographs, Hiragana/Katakana, Hangul — still fall back to
transliteration rather than rendering as an empty box.
"""

from __future__ import annotations

import os
import re
import tempfile
import unicodedata

# Accent colour from the web design system (signal-gold), for section labels.
_ACCENT = "rgb(176, 132, 48)"
_INK = "rgb(28, 27, 35)"
_MUTED = "rgb(110, 108, 120)"

# Characters Typst's markup mode gives special meaning to. Escaping every
# occurrence with a backslash -- Typst's own escape syntax -- makes them
# literal wherever they appear, so a resume containing "C# & F#" or "a_b"
# compiles as plain text instead of failing or being read as markup.
_TYPST_SPECIAL_RE = re.compile(r"[\\*_#$`<>@\[\]~/-]")


def _escape_typst(text: str) -> str:
    return _TYPST_SPECIAL_RE.sub(lambda m: "\\" + m.group(), text)


# Codepoint ranges Typst's embedded fonts (Libertinus Serif, New Computer
# Modern, DejaVu Sans Mono -- the only fonts guaranteed present in the
# Dockerfile.api deploy image, which ships no system font packages) cannot
# render: verified empirically to come back as missing-glyph boxes. Latin
# (with any accent), Cyrillic, Greek, Arabic, and all common punctuation and
# currency symbols render natively and are deliberately left off this list.
_UNRENDERABLE_RANGES = (
    (0x3040, 0x30FF),  # Hiragana + Katakana
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0xAC00, 0xD7A3),  # Hangul syllables
)


def _is_unrenderable(char: str) -> bool:
    codepoint = ord(char)
    return any(low <= codepoint <= high for low, high in _UNRENDERABLE_RANGES)


def _prepare_text(text: str) -> str:
    """Make text safe to hand to Typst's embedded fonts without losing
    information for the (common) scripts they can actually render.

    Typst renders full Unicode natively for Latin (with any accent), smart
    punctuation, and currency symbols -- no substitution needed, unlike the
    old fpdf2/latin-1 renderer. Only scripts with no glyph in the embedded
    font set (CJK ideographs, Hiragana/Katakana, Hangul) still need the
    graceful fallback: transliterate to the nearest ASCII rather than
    rendering as an empty box.
    """
    out: list[str] = []
    for char in text:
        if _is_unrenderable(char):
            decomposed = (
                unicodedata.normalize("NFKD", char).encode("ascii", "ignore").decode("ascii")
            )
            out.append(decomposed)
        else:
            out.append(char)
    return "".join(out)


class _TypstDoc:
    """Accumulates Typst markup for one document, compiled once at the end."""

    def __init__(self) -> None:
        self._parts: list[str] = [
            "#set page(width: 210mm, height: 297mm, margin: (x: 18mm, y: 16mm))\n"
            f'#set text(font: "Libertinus Serif", size: 10pt, fill: {_INK})\n'
        ]

    def _content(self, text: str) -> str:
        return _escape_typst(_prepare_text(text))

    def name(self, text: str) -> None:
        self._parts.append(f'#text(size: 22pt, weight: "bold")[{self._content(text)}]\n\n')

    def headline(self, text: str) -> None:
        self._parts.append(
            f'#text(size: 12pt, style: "italic", fill: {_MUTED})[{self._content(text)}]\n\n'
        )

    def contact(self, text: str) -> None:
        self._parts.append(f"#text(fill: {_MUTED})[{self._content(text)}]\n\n")

    def rule(self) -> None:
        self._parts.append(f"#line(length: 100%, stroke: 0.4pt + {_ACCENT})\n#v(3pt)\n")

    def section(self, text: str) -> None:
        label = self._content(text.upper())
        self._parts.append(
            f'#v(4pt)#text(size: 11pt, weight: "bold", fill: {_ACCENT})[{label}]\n\n'
        )

    def role(self, text: str) -> None:
        self._parts.append(f'#text(size: 11pt, weight: "bold")[{self._content(text)}]\n\n')

    def dates(self, text: str) -> None:
        self._parts.append(
            f'#text(size: 9pt, style: "italic", fill: {_MUTED})[{self._content(text)}]\n\n'
        )

    def body(self, text: str) -> None:
        self._parts.append(f"{self._content(text)}\n\n")

    def bullet(self, text: str) -> None:
        self._parts.append(f"- {self._content(text)}\n")

    def blank(self) -> None:
        self._parts.append("#v(4pt)\n")

    def output(self) -> bytes:
        import typst

        source = "".join(self._parts)
        fd, path = tempfile.mkstemp(suffix=".typ")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(source)
            return typst.compile(path, ignore_system_fonts=True)
        finally:
            os.unlink(path)


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
    doc = _TypstDoc()
    seen_first_heading = False
    lines = markdown.split("\n") if markdown else []

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            doc.blank()
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
        titled = _TypstDoc()
        titled.name(title)
        titled.rule()
        for raw in lines:
            line = raw.rstrip()
            if line.strip():
                titled.body(line)
            else:
                titled.blank()
        return titled.output()

    return doc.output()
