"""Tests for the typeset résumé PDF renderer.

The old renderer dumped the document as flat Helvetica text in latin-1,
so an accented name lost its accents and the layout was a wall of lines.
This renders the résumé Markdown into a structured one-column CV and keeps
non-latin text legible by transliterating rather than dropping it.
"""

from __future__ import annotations

import io

from pypdf import PdfReader

from careeros_api.resume_pdf import _escape_typst, _prepare_text, render_markdown_pdf


def _pdf_ok(data: bytes) -> bool:
    return data[:4] == b"%PDF" and len(data) > 800


def _extract_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() for page in reader.pages)


def test_escape_typst_neutralises_markup_characters():
    # Every character Typst gives special meaning to must round-trip as a
    # literal backslash-escape, or a résumé containing e.g. "C# & F#" or
    # "a_b" would either fail to compile or silently render as markup.
    raw = r"\ * _ # $ ` < > @ [ ] ~ / -"
    assert _escape_typst(raw) == r"\\ \* \_ \# \$ \` \< \> \@ \[ \] \~ \/ \-"


def test_renders_a_pdf():
    md = "# Ada Lovelace\n*Analytical Engine Pioneer*\nada@example.com | London\n"
    assert _pdf_ok(render_markdown_pdf("Résumé", md))


def test_a_full_resume_renders():
    md = (
        "# Ada Lovelace\n"
        "*Mathematician*\n"
        "ada@example.com | +44 123 | London\n"
        "\n## Summary\n"
        "First programmer.\n"
        "\n## Skills\n"
        "Analysis, Algorithms, Mathematics\n"
        "\n## Experience\n"
        "\n### Collaborator — Analytical Engine\n"
        "_1842-01-01 - 1843-01-01_\n"
        "Worked on the engine.\n"
        "- Wrote the first algorithm\n"
        "- Noted machine could go beyond numbers\n"
    )
    assert _pdf_ok(render_markdown_pdf("Résumé", md))


def test_prepare_text_leaves_accented_latin_untouched():
    # Typst's own embedded font renders accented Latin natively — no
    # transliteration needed (unlike the old fpdf2/latin-1 renderer).
    assert _prepare_text("José Müller") == "José Müller"


def test_prepare_text_leaves_currency_symbols_untouched():
    # £, €, ₹ all render as real glyphs in Typst's embedded font, so they
    # must stay literal rather than degrading to "EUR"/"Rs" substitutions.
    assert _prepare_text("£55,000 €70,000 ₹800000") == "£55,000 €70,000 ₹800000"


def test_prepare_text_leaves_smart_punctuation_untouched():
    assert _prepare_text("“quote” — dash … ‘apos’") == "“quote” — dash … ‘apos’"


def test_prepare_text_transliterates_cjk_which_the_embedded_font_cannot_render():
    # CJK ideographs have no glyph in Typst's bundled Latin fonts (confirmed:
    # they render as missing-glyph boxes), so they still need the same
    # graceful fallback the old renderer used — transliterate, don't vanish.
    out = _prepare_text("北京 Beijing")
    assert "Beijing" in out
    assert "北" not in out
    assert "?" not in out


def test_a_markdown_only_title_still_produces_a_valid_pdf():
    assert _pdf_ok(render_markdown_pdf("Cover Letter", "Dear team,\n\nHello.\n\nRegards,\nAda"))


def test_empty_content_still_produces_a_valid_pdf():
    assert _pdf_ok(render_markdown_pdf("Empty", ""))


def test_bullets_and_headings_do_not_crash_on_odd_input():
    weird = "### \n- \n#\n**\n_\n" + "x" * 5000
    assert _pdf_ok(render_markdown_pdf("Odd", weird))


def test_rendered_pdf_preserves_currency_and_accents_as_literal_text():
    # The old fpdf2 renderer degraded these to "EUR"/"Rs" substitutions; the
    # Typst renderer should carry them through as the real glyphs.
    md = "# José Müller\nSalary: £55,000 / €70,000 / ₹800000\n"
    text = _extract_text(render_markdown_pdf("Résumé", md))
    assert "José Müller" in text
    assert "£55,000" in text
    assert "€70,000" in text
    assert "₹800000" in text


def test_rendered_pdf_treats_typst_special_characters_in_bullets_as_literal():
    # A bullet mentioning "C# & F#" or "a_b" must survive verbatim rather
    # than breaking the Typst compile or being read as markup.
    md = "# Ada\n## Skills\n- Shipped C# and F# services, 30%_faster\n"
    text = _extract_text(render_markdown_pdf("Résumé", md))
    assert "C# and F# services, 30%_faster" in text
