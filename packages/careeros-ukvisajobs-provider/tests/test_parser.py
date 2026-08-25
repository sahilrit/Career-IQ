"""Tests for parsing the UK Visa Jobs fetch-jobs-data response and its rows."""

from __future__ import annotations

import pytest

from careeros_ukvisajobs_provider.parser import (
    build_search_form_fields,
    is_auth_error,
    is_job_entry,
    parse_job_entry,
    parse_search_response,
)

# --- form fields ------------------------------------------------------------


def test_build_search_form_fields_shape():
    fields = build_search_form_fields(page_no=1, search_keyword=None, token="tok-123")
    assert fields["pageNo"] == "1"
    assert fields["token"] == "tok-123"
    assert fields["searchKeyword"] == "null"


def test_build_search_form_fields_with_a_keyword():
    fields = build_search_form_fields(page_no=2, search_keyword="growth", token="tok")
    assert fields["pageNo"] == "2"
    assert fields["searchKeyword"] == "growth"


# --- response parsing ---------------------------------------------------


def test_parse_search_response_extracts_status_total_and_jobs(search_response_body):
    parsed = parse_search_response(search_response_body)
    assert parsed["status"] == 1
    assert parsed["total_jobs"] == 2
    assert len(parsed["jobs"]) == 2
    assert parsed["jobs"][0]["id"] == "1"


def test_parse_search_response_handles_a_malformed_body():
    parsed = parse_search_response("not json at all")
    assert parsed == {"status": 0, "total_jobs": 0, "jobs": []}


def test_parse_search_response_handles_a_missing_jobs_key():
    parsed = parse_search_response('{"status": 1, "totalJobs": 0}')
    assert parsed["jobs"] == []


def test_parse_search_response_handles_an_empty_string():
    assert parse_search_response("") == {"status": 0, "total_jobs": 0, "jobs": []}


# --- row usability ------------------------------------------------------


def test_a_row_without_job_link_is_not_usable(row_unusable):
    assert is_job_entry(row_unusable) is False


def test_a_row_with_id_and_job_link_is_usable(row_full):
    assert is_job_entry(row_full) is True


# --- auth-error detection ------------------------------------------------


@pytest.mark.parametrize("status", [401, 403])
def test_401_and_403_are_auth_errors(status):
    assert is_auth_error(status, "") is True


def test_400_with_expired_errortype_is_an_auth_error():
    assert is_auth_error(400, '{"errorType": "expired", "message": "token expired"}') is True


def test_400_with_expired_in_plain_text_is_an_auth_error():
    assert is_auth_error(400, "your session has expired") is True


def test_400_without_expired_is_not_an_auth_error():
    assert is_auth_error(400, '{"errorType": "validation"}') is False


def test_200_is_never_an_auth_error():
    assert is_auth_error(200, "") is False


# --- row -> JobPosting ----------------------------------------------------


def test_parse_maps_the_core_fields(row_full):
    posting = parse_job_entry(row_full)
    assert posting.source_provider == "ukvisajobs"
    assert posting.external_id == "88123"
    assert posting.title == "Graduate Software Engineer"
    assert posting.company_name == "Acme UK Ltd"
    assert posting.url == "https://my.ukvisajobs.com/job/graduate-software-engineer-88123"


def test_parse_reads_the_city_as_location(row_full):
    assert parse_job_entry(row_full).location == "London"


def test_remote_city_sets_remote_true(row_minimal):
    assert parse_job_entry(row_minimal).remote is True


def test_a_named_city_is_not_remote(row_full):
    assert parse_job_entry(row_full).remote is False


def test_parse_reads_a_stated_salary(row_full):
    salary = parse_job_entry(row_full).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount, salary.currency) == (32000, 38000, "GBP")


def test_a_row_without_salary_fields_has_no_salary(row_minimal):
    assert parse_job_entry(row_minimal).salary is None


def test_description_is_used_when_present(row_full):
    assert "platform team" in parse_job_entry(row_full).description


def test_a_sparse_row_synthesises_a_description_from_visa_fields():
    row = {
        "id": "1",
        "title": "X",
        "company_name": "Y",
        "job_link": "https://my.ukvisajobs.com/job/1",
        "likely_to_sponsor": "Yes",
    }
    description = parse_job_entry(row).description
    assert "sponsor" in description.lower()


def test_a_sparse_row_still_parses(row_minimal):
    posting = parse_job_entry(row_minimal)
    assert posting.title == "Remote Data Analyst"
    assert posting.salary is None
    assert posting.tags == []


def test_parse_reads_tags_from_industry_type_and_level(row_full):
    tags = parse_job_entry(row_full).tags
    assert set(tags) == {"software engineering", "full-time", "graduate"}


@pytest.mark.parametrize("field", ["id", "title", "company_name", "job_link"])
def test_parse_never_raises_on_a_missing_field(field, row_full):
    row = dict(row_full)
    row.pop(field, None)
    # Must not raise, even for a row missing something normally present.
    parse_job_entry(row)
