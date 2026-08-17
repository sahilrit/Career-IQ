"""Tests for ATS keyword coverage."""

from __future__ import annotations

from careeros_application_engine import ats_keyword_coverage


def test_covered_and_missing_keywords_are_split_correctly(posting_factory):
    posting = posting_factory(tags=["python", "django", "rust"])
    report = ats_keyword_coverage("Experienced Python and Django engineer.", posting)
    assert report.covered_keywords == ["python", "django"]
    assert report.missing_keywords == ["rust"]


def test_coverage_ratio_reflects_the_split(posting_factory):
    posting = posting_factory(tags=["python", "django", "rust", "erlang"])
    report = ats_keyword_coverage("Python and Django background.", posting)
    assert report.coverage_ratio == 0.5


def test_no_tags_yields_full_coverage(posting_factory):
    posting = posting_factory(tags=[])
    report = ats_keyword_coverage("Anything at all.", posting)
    assert report.coverage_ratio == 1.0


def test_matching_is_case_insensitive(posting_factory):
    posting = posting_factory(tags=["Python"])
    report = ats_keyword_coverage("experienced python engineer", posting)
    assert report.covered_keywords == ["Python"]


# --- Regression: multi-word keywords must match as phrases --------------------


def test_multiword_keywords_match_as_phrases(posting_factory):
    posting = posting_factory(tags=["Google Ads", "growth marketing", "SQL"])
    resume = "SKILLS\nGoogle Ads, growth marketing, SQL"
    report = ats_keyword_coverage(resume, posting)
    assert report.covered_keywords == ["Google Ads", "growth marketing", "SQL"]
    assert report.missing_keywords == []


def test_multiword_keyword_absent_is_missing(posting_factory):
    posting = posting_factory(tags=["Google Ads", "growth marketing"])
    report = ats_keyword_coverage("Ran Google campaigns and did some marketing.", posting)
    # neither exact phrase is present, so both are missing (no false positives)
    assert report.covered_keywords == []
    assert set(report.missing_keywords) == {"Google Ads", "growth marketing"}
