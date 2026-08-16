"""Tests for filter_postings/matches_query."""

from __future__ import annotations

from careeros_job_providers import EmploymentType, JobSearchQuery, Salary, matches_query


def test_remote_only_excludes_non_remote_postings(posting_factory):
    posting = posting_factory(remote=False)
    assert not matches_query(posting, JobSearchQuery(remote_only=True))


def test_remote_only_includes_remote_postings(posting_factory):
    posting = posting_factory(remote=True)
    assert matches_query(posting, JobSearchQuery(remote_only=True))


def test_min_salary_excludes_postings_below_threshold(posting_factory):
    posting = posting_factory(salary=Salary(min_amount=80_000, max_amount=90_000))
    assert not matches_query(posting, JobSearchQuery(min_salary=100_000))


def test_min_salary_excludes_postings_with_no_salary_listed(posting_factory):
    posting = posting_factory(salary=None)
    assert not matches_query(posting, JobSearchQuery(min_salary=100_000))


def test_min_salary_includes_postings_at_or_above_threshold(posting_factory):
    posting = posting_factory(salary=Salary(min_amount=100_000, max_amount=140_000))
    assert matches_query(posting, JobSearchQuery(min_salary=100_000))


def test_employment_type_filter(posting_factory):
    contract = posting_factory(employment_type=EmploymentType.CONTRACT)
    assert matches_query(contract, JobSearchQuery(employment_types=[EmploymentType.CONTRACT]))
    assert not matches_query(contract, JobSearchQuery(employment_types=[EmploymentType.FULL_TIME]))


def test_keyword_filter_matches_title_or_description(posting_factory):
    posting = posting_factory(title="Senior Python Engineer", description="Django experience")
    assert matches_query(posting, JobSearchQuery(keywords=["python"]))
    assert matches_query(posting, JobSearchQuery(keywords=["django"]))
    assert not matches_query(posting, JobSearchQuery(keywords=["rust"]))


def test_location_filter_requires_a_substring_match(posting_factory):
    posting = posting_factory(location="Berlin, Germany")
    assert matches_query(posting, JobSearchQuery(locations=["berlin"]))
    assert not matches_query(posting, JobSearchQuery(locations=["paris"]))


def test_location_filter_excludes_postings_with_no_location(posting_factory):
    posting = posting_factory(location=None)
    assert not matches_query(posting, JobSearchQuery(locations=["berlin"]))


def test_empty_query_matches_everything(posting_factory):
    posting = posting_factory()
    assert matches_query(posting, JobSearchQuery())


def test_keyword_matches_whole_words_only(posting_factory):
    posting = posting_factory(
        title="Field Technician", description="Work across teams on site equipment."
    )
    assert not matches_query(posting, JobSearchQuery(keywords=["cro"]))


def test_keyword_matches_word_regardless_of_case(posting_factory):
    posting = posting_factory(title="CRO Specialist", description="")
    assert matches_query(posting, JobSearchQuery(keywords=["cro"]))


def test_multi_word_keyword_matches_phrase(posting_factory):
    posting = posting_factory(title="Meta Ads Specialist", description="")
    assert matches_query(posting, JobSearchQuery(keywords=["meta ads"]))


def test_keyword_found_in_tags(posting_factory):
    posting = posting_factory(title="Growth Role", description="", tags=["ppc", "marketing"])
    assert matches_query(posting, JobSearchQuery(keywords=["ppc"]))
