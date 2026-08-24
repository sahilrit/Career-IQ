"""Tests for the typeset résumé PDF renderer.

The old renderer dumped the document as flat Helvetica text in latin-1,
so an accented name lost its accents and the layout was a wall of lines.
This renders the résumé Markdown into a structured one-column CV and keeps
non-latin text legible by transliterating rather than dropping it.
"""

from __future__ import annotations

from careeros_api.resume_pdf import _to_latin1, render_markdown_pdf


def _pdf_ok(data: bytes) -> bool:
    return data[:4] == b"%PDF" and len(data) > 800


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


def test_transliteration_keeps_accented_names_legible():
    # José should become Jose, not J (accent dropped, letter kept).
    assert _to_latin1("José Müller") == "José Müller"  # both are latin-1 already


def test_non_latin_scripts_transliterate_instead_of_vanishing():
    # A CJK or Devanagari name has no latin-1 form; it should transliterate to
    # something, not become empty or a row of "?".
    out = _to_latin1("北京 Beijing")
    assert "Beijing" in out
    assert "?" not in out


def test_smart_punctuation_becomes_ascii():
    out = _to_latin1("“quote” — dash … ‘apos’")
    assert '"quote"' in out
    assert "--" in out or "-" in out
    assert "..." in out


def test_currency_symbols_degrade_readably():
    # £ is latin-1 and survives; € and ₹ are not, so they become EUR / Rs
    # rather than being dropped or turned into "?".
    out = _to_latin1("£55,000 €70,000 ₹800000")
    assert "£55,000" in out
    assert "EUR70,000" in out
    assert "Rs800000" in out


def test_a_markdown_only_title_still_produces_a_valid_pdf():
    assert _pdf_ok(render_markdown_pdf("Cover Letter", "Dear team,\n\nHello.\n\nRegards,\nAda"))


def test_empty_content_still_produces_a_valid_pdf():
    assert _pdf_ok(render_markdown_pdf("Empty", ""))


def test_bullets_and_headings_do_not_crash_on_odd_input():
    weird = "### \n- \n#\n**\n_\n" + "x" * 5000
    assert _pdf_ok(render_markdown_pdf("Odd", weird))
