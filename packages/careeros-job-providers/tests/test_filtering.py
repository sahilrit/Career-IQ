"""Tests for filter_postings/matches_query."""

from __future__ import annotations

import pytest

from careeros_job_providers import (
    EmploymentType,
    JobSearchQuery,
    Salary,
    filter_postings,
    matches_query,
)


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


def test_keyword_filter_matches_the_title(posting_factory):
    posting = posting_factory(title="Senior Python Engineer", description="Django experience")
    assert matches_query(posting, JobSearchQuery(keywords=["python"]))
    assert not matches_query(posting, JobSearchQuery(keywords=["rust"]))


def test_keyword_filter_matches_tags(posting_factory):
    posting = posting_factory(title="Senior Engineer", tags=["golang", "backend"])
    assert matches_query(posting, JobSearchQuery(keywords=["golang"]))


def test_a_single_word_in_the_body_alone_is_not_a_match(posting_factory):
    """The noise rule, measured against 2,170 live Lever postings.

    Matching any keyword anywhere in a description kept 987 of them, including
    retail roles whose body mentions "performance" once in boilerplate. A bare
    word in a long body is not evidence the role is about that word.
    """
    posting = posting_factory(
        title="Liquor Store Associate",
        description="You will be evaluated on performance during quarterly reviews.",
    )
    assert not matches_query(posting, JobSearchQuery(keywords=["performance"]))


def test_a_multi_word_phrase_in_the_body_is_a_match(posting_factory):
    """A phrase in the body really is about the role, so it is trusted where a
    single generic word is not — this recovers genuine matches whose title is
    vague without readmitting the noise above."""
    posting = posting_factory(
        title="Senior Manager, Digital",
        description="You will own the performance marketing programme end to end.",
    )
    assert matches_query(posting, JobSearchQuery(keywords=["performance marketing"]))


def test_keyword_matching_stays_whole_word(posting_factory):
    posting = posting_factory(title="Across the board Engineer", description="")
    assert not matches_query(posting, JobSearchQuery(keywords=["cro"]))


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


# --- server-side filters -----------------------------------------------------
# Some providers (LinkedIn, Indeed, Adzuna) apply keyword and location matching
# inside their own query. Re-applying it here drops valid results, because our
# haystack is only what we managed to parse — a posting whose description has
# not been fetched yet has almost nothing to match against.


def test_keywords_can_be_marked_as_already_applied(posting_factory):
    posting = posting_factory(title="Senior Manager, Growth", description="", tags=[])
    query = JobSearchQuery(keywords=["performance marketing"])
    assert matches_query(posting, query) is False
    assert matches_query(posting, query, applied_server_side={"keywords"}) is True


def test_locations_can_be_marked_as_already_applied(posting_factory):
    posting = posting_factory(title="Engineer", location="Karnataka, India")
    query = JobSearchQuery(locations=["Bengaluru"])
    assert matches_query(posting, query) is False
    assert matches_query(posting, query, applied_server_side={"locations"}) is True


def test_marking_keywords_applied_does_not_disable_the_other_filters(posting_factory):
    posting = posting_factory(title="Anything", remote=False)
    query = JobSearchQuery(keywords=["whatever"], remote_only=True)
    assert matches_query(posting, query, applied_server_side={"keywords"}) is False


def test_filter_postings_passes_the_flag_through(posting_factory):
    postings = [posting_factory(title="Senior Manager, Growth", description="", tags=[])]
    query = JobSearchQuery(keywords=["performance marketing"])
    assert filter_postings(postings, query) == []
    assert filter_postings(postings, query, applied_server_side={"keywords"}) == postings


def test_unknown_server_side_field_is_rejected(posting_factory):
    with pytest.raises(ValueError, match="not a filterable field"):
        matches_query(posting_factory(), JobSearchQuery(), applied_server_side={"salary"})
