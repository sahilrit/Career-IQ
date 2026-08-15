"""Tests for build_application_package: the full bundle."""

from __future__ import annotations

from careeros_application_engine import build_application_package


def test_package_bundles_every_artifact(brain, posting):
    package = build_application_package(brain, posting)

    assert "Ada Lovelace" in package.resume_text
    assert package.resume_markdown.startswith("# Ada Lovelace")
    assert "<h1>Ada Lovelace</h1>" in package.resume_html
    assert "Widget Co" in package.cover_letter
    assert "why_this_role" in package.answers
    assert package.ats_report.coverage_ratio > 0


def test_custom_cover_letter_generator_is_used(brain, posting):
    class FakeCoverLetterGenerator:
        def generate(self, brain, posting) -> str:
            return "FAKE LETTER"

    package = build_application_package(
        brain, posting, cover_letter_generator=FakeCoverLetterGenerator()
    )

    assert package.cover_letter == "FAKE LETTER"


def test_ats_report_reflects_the_generated_resume_text(brain, posting):
    package = build_application_package(brain, posting)
    assert "python" in package.ats_report.covered_keywords
