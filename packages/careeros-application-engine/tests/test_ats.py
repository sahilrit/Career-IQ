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
