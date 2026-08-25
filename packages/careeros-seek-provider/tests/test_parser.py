"""Tests for parsing Seek's search API response and its rows."""

from __future__ import annotations

import pytest

from careeros_job_providers import EmploymentType
from careeros_seek_provider.parser import (
    is_job_entry,
    make_job_url,
    parse_job_entry,
    parse_search_response,
)

# --- response parsing ---------------------------------------------------


def test_parse_search_response_extracts_total_and_rows(search_response_body):
    parsed = parse_search_response(search_response_body)
    assert parsed["total_count"] == 2
    assert len(parsed["jobs"]) == 2
    assert parsed["jobs"][0]["id"] == "1"


def test_parse_search_response_handles_a_malformed_body():
    assert parse_search_response("not json at all") == {"total_count": 0, "jobs": []}


def test_parse_search_response_handles_a_missing_data_key():
    assert parse_search_response('{"totalCount": 0}') == {"total_count": 0, "jobs": []}


def test_parse_search_response_handles_an_empty_string():
    assert parse_search_response("") == {"total_count": 0, "jobs": []}


# --- row usability --------------------------------------------------------


def test_a_row_without_id_or_title_is_not_usable(row_unusable):
    assert is_job_entry(row_unusable) is False


def test_a_row_with_id_and_title_is_usable(row_full):
    assert is_job_entry(row_full) is True


# --- job URL ---------------------------------------------------------------


def test_make_job_url():
    assert make_job_url("94152491") == "https://www.seek.com.au/job/94152491"


# --- row -> JobPosting ------------------------------------------------------


def test_parse_maps_the_core_fields(row_full):
    posting = parse_job_entry(row_full)
    assert posting.source_provider == "seek"
    assert posting.external_id == "94152491"
    assert posting.company_name == "Viabrand"
    assert posting.url == "https://www.seek.com.au/job/94152491"


def test_parse_strips_dash_and_bullet_junk_from_the_title(row_full):
    assert parse_job_entry(row_full).title == "Marketing & Studio Assistant - Part Time"


def test_parse_reads_the_location(row_full):
    assert parse_job_entry(row_full).location == "Brisbane QLD"


def test_remote_location_sets_remote_true(row_minimal):
    assert parse_job_entry(row_minimal).remote is True


def test_a_named_city_is_not_remote(row_full):
    assert parse_job_entry(row_full).remote is False


def test_parse_reads_an_hourly_salary_range(row_full):
    salary = parse_job_entry(row_full).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount, salary.currency, salary.period) == (
        28,
        32,
        "AUD",
        "hour",
    )


def test_a_row_without_a_salary_label_has_no_salary(row_minimal):
    assert parse_job_entry(row_minimal).salary is None


def test_a_non_numeric_salary_label_is_not_a_salary():
    row = {"id": "1", "title": "X", "companyName": "Y", "salaryLabel": "Competitive salary"}
    assert parse_job_entry(row).salary is None


def test_parse_reads_the_listing_date(row_full):
    posted = parse_job_entry(row_full).posted_at
    assert posted is not None
    assert (posted.year, posted.month, posted.day) == (2026, 8, 23)


def test_parse_reads_tags_from_classifications(row_full):
    tags = parse_job_entry(row_full).tags
    assert "marketing & communications" in tags
    assert "marketing assistants/coordinators" in tags


def test_part_time_maps_to_the_part_time_enum(row_full):
    assert parse_job_entry(row_full).employment_type is EmploymentType.PART_TIME


def test_full_time_maps_to_the_full_time_enum():
    row = {"id": "1", "title": "X", "companyName": "Y", "workTypes": ["Full time"]}
    assert parse_job_entry(row).employment_type is EmploymentType.FULL_TIME


def test_a_sparse_row_still_parses(row_minimal):
    posting = parse_job_entry(row_minimal)
    assert posting.title == "Remote Growth Marketer"
    assert posting.salary is None
    assert posting.tags == []
    assert posting.employment_type is None


def test_description_uses_the_teaser(row_full):
    assert "boutique agency" in parse_job_entry(row_full).description


@pytest.mark.parametrize("field", ["id", "title", "companyName"])
def test_parse_never_raises_on_a_missing_field(field, row_full):
    row = dict(row_full)
    row.pop(field, None)
    parse_job_entry(row)
