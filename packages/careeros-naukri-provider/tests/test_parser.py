"""Tests for parsing the Naukri jobapi/v3/search response and its rows."""

from __future__ import annotations

import pytest

from careeros_naukri_provider.parser import (
    is_job_entry,
    make_search_url,
    parse_job_entry,
    parse_search_response,
)

# --- URL building --------------------------------------------------------


def test_make_search_url_with_no_location():
    url = make_search_url(keyword="performance marketing")
    assert (
        url == "https://www.naukri.com/performance-marketing-jobs?k=performance+marketing&jobAge=7"
    )


def test_make_search_url_with_a_location():
    url = make_search_url(keyword="growth lead", location="Bengaluru")
    assert "growth-lead-jobs-in-bengaluru" in url
    assert "l=Bengaluru" in url


def test_make_search_url_slugifies_special_characters():
    url = make_search_url(keyword="C++ Developer / Backend")
    assert "/c-developer-backend-jobs" in url.split("?")[0]


def test_make_search_url_respects_freshness():
    url = make_search_url(keyword="growth", freshness="30")
    assert "jobAge=30" in url


def test_make_search_url_defaults_freshness_to_seven_days():
    assert "jobAge=7" in make_search_url(keyword="growth")


# --- response parsing -----------------------------------------------------


def test_parse_search_response_extracts_job_details(search_response_body):
    rows = parse_search_response(search_response_body)
    assert len(rows) == 2
    assert rows[0]["jobId"] == "1"


def test_parse_search_response_handles_a_malformed_body():
    assert parse_search_response("not json at all") == []


def test_parse_search_response_handles_a_missing_jobDetails_key():
    assert parse_search_response('{"totalCount": 0}') == []


def test_parse_search_response_handles_an_empty_string():
    assert parse_search_response("") == []


# --- row usability ----------------------------------------------------------


def test_a_row_without_jdurl_is_not_usable(row_unusable):
    assert is_job_entry(row_unusable) is False


def test_a_row_with_jdurl_and_title_is_usable(row_full):
    assert is_job_entry(row_full) is True


# --- row -> JobPosting ------------------------------------------------------


def test_parse_maps_the_core_fields(row_full):
    posting = parse_job_entry(row_full)
    assert posting.source_provider == "naukri"
    assert posting.external_id == "250824012345"
    assert posting.title == "Senior Marketing Manager"
    assert posting.company_name == "Acme Corp"


def test_parse_makes_a_relative_jdurl_absolute(row_full):
    posting = parse_job_entry(row_full)
    assert posting.url.startswith("https://www.naukri.com/")
    assert "senior-marketing-manager-acme" in posting.url


def test_parse_leaves_an_already_absolute_jdurl_unchanged(row_minimal):
    posting = parse_job_entry(row_minimal)
    assert posting.url == "https://www.naukri.com/job-listings-growth-lead-widgetco-240824099999"


def test_parse_reads_the_location_from_placeholders(row_full):
    assert parse_job_entry(row_full).location == "Bengaluru"


def test_parse_reads_a_stated_salary(row_full):
    salary = parse_job_entry(row_full).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount, salary.currency) == (
        1200000,
        1800000,
        "INR",
    )


def test_hidden_salary_is_not_exposed(row_minimal):
    """salaryDetail.hideSalary=true means the employer chose not to disclose
    it — showing a figure anyway would be inventing data Naukri itself
    withheld."""
    assert parse_job_entry(row_minimal).salary is None


def test_parse_reads_the_created_date(row_full):
    posted = parse_job_entry(row_full).posted_at
    assert posted is not None
    assert (posted.year, posted.month, posted.day) == (2026, 8, 20)


def test_parse_reads_tags_from_tagsandskills(row_full):
    tags = parse_job_entry(row_full).tags
    assert set(tags) == {"google ads", "meta ads", "sql"}


def test_a_sparse_row_still_parses(row_minimal):
    posting = parse_job_entry(row_minimal)
    assert posting.title == "Growth Lead"
    assert posting.salary is None
    assert posting.tags == []


def test_remote_placeholder_location_sets_remote_true(row_minimal):
    assert parse_job_entry(row_minimal).remote is True


def test_a_city_location_is_not_remote(row_full):
    assert parse_job_entry(row_full).remote is False


def test_description_is_included_when_present(row_full):
    assert "paid-acquisition" in parse_job_entry(row_full).description


@pytest.mark.parametrize("field", ["jobId", "jdURL", "title", "companyName"])
def test_parse_never_raises_on_a_missing_field(field, row_full):
    row = dict(row_full)
    row.pop(field, None)
    # Must not raise, even for a row missing something normally present.
    parse_job_entry(row)
