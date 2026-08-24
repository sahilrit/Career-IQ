"""Tests for the Adzuna provider. No real network calls."""

from __future__ import annotations

import pytest

from careeros_adzuna_provider import (
    ADZUNA_APP_ID_ENV_VAR,
    ADZUNA_APP_KEY_ENV_VAR,
    AdzunaProvider,
    country_for_locations,
    is_job_entry,
    parse_job_entry,
)
from careeros_job_providers import EmploymentType, HealthStatus, JobSearchQuery


@pytest.fixture(autouse=True)
def credentials(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(ADZUNA_APP_ID_ENV_VAR, "test-app-id")
    monkeypatch.setenv(ADZUNA_APP_KEY_ENV_VAR, "test-app-key")


# --- entry mapping -----------------------------------------------------------


def test_a_result_without_an_id_is_not_usable():
    assert is_job_entry({"title": "x", "redirect_url": "https://example.com"}) is False


def test_a_result_without_a_link_is_not_usable():
    assert is_job_entry({"id": "1", "title": "x"}) is False


def test_parse_maps_the_core_fields(result_salaried):
    posting = parse_job_entry(result_salaried)
    assert posting.source_provider == "adzuna"
    assert posting.external_id == "4200001"
    assert posting.company_name == "Acme Corp"
    assert posting.url == "https://www.adzuna.co.uk/details/4200001"
    assert posting.location == "London, UK"


def test_parse_strips_the_markup_adzuna_puts_in_titles(result_salaried):
    """Adzuna bolds the matched terms in the title with real HTML tags."""
    assert parse_job_entry(result_salaried).title == "Performance Marketing Manager"


def test_parse_reads_a_stated_salary(result_salaried):
    salary = parse_job_entry(result_salaried).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount) == (55000, 70000)


def test_a_predicted_salary_is_not_treated_as_a_stated_one(result_predicted):
    """salary_is_predicted=1 means Adzuna guessed. Passing that off as a real
    figure would let a guess satisfy the user's minimum-salary filter."""
    assert parse_job_entry(result_predicted).salary is None


def test_parse_reads_the_created_date(result_salaried):
    posted = parse_job_entry(result_salaried).posted_at
    assert posted is not None
    assert (posted.year, posted.month, posted.day) == (2026, 8, 12)


def test_parse_maps_the_contract_time(result_salaried, result_predicted):
    assert parse_job_entry(result_salaried).employment_type is EmploymentType.FULL_TIME
    assert parse_job_entry(result_predicted).employment_type is EmploymentType.PART_TIME


def test_remote_is_detected_from_the_location(result_predicted, result_salaried):
    assert parse_job_entry(result_predicted).remote is True
    assert parse_job_entry(result_salaried).remote is False


def test_the_category_becomes_a_tag(result_salaried):
    assert "pr, advertising & marketing jobs" in parse_job_entry(result_salaried).tags


def test_a_sparse_result_still_parses(result_minimal):
    posting = parse_job_entry(result_minimal)
    assert posting.title == "Coordinator"
    assert posting.salary is None
    assert posting.posted_at is None


# --- country routing ---------------------------------------------------------


def test_country_defaults_to_great_britain_when_nothing_is_stated():
    assert country_for_locations([]) == "gb"


def test_country_is_derived_from_the_requested_location():
    assert country_for_locations(["Bengaluru, India"]) == "in"
    assert country_for_locations(["New York"]) == "us"
    assert country_for_locations(["Berlin, Germany"]) == "de"


def test_an_unrecognised_location_falls_back_rather_than_failing():
    assert country_for_locations(["Atlantis"]) == "gb"


# --- provider ----------------------------------------------------------------


def test_provider_id_is_adzuna(fake_transport_cls):
    assert AdzunaProvider(fake_transport_cls()).provider_id == "adzuna"


def test_search_returns_the_usable_results(fake_transport_cls):
    result = AdzunaProvider(fake_transport_cls()).search(JobSearchQuery())
    assert {p.external_id for p in result.postings} == {"4200001", "4200002", "4200003"}


def test_search_joins_the_keywords_into_one_query(fake_transport_cls):
    transport = fake_transport_cls()
    AdzunaProvider(transport).search(JobSearchQuery(keywords=["performance marketing", "ppc"]))
    assert transport.calls[0]["what"] == "performance marketing ppc"


def test_search_routes_to_the_right_country(fake_transport_cls):
    transport = fake_transport_cls()
    AdzunaProvider(transport).search(JobSearchQuery(locations=["Mumbai, India"]))
    assert transport.calls[0]["country"] == "in"


def test_search_stops_when_a_page_comes_back_empty(fake_transport_cls):
    transport = fake_transport_cls()
    AdzunaProvider(transport).search(JobSearchQuery(limit=500))
    assert len(transport.calls) == 2


def test_search_respects_the_limit(fake_transport_cls):
    result = AdzunaProvider(fake_transport_cls()).search(JobSearchQuery(limit=1))
    assert len(result.postings) == 1


def test_search_does_not_refilter_what_adzuna_already_matched(fake_transport_cls):
    result = AdzunaProvider(fake_transport_cls()).search(
        JobSearchQuery(keywords=["nothing will match this"])
    )
    assert len(result.postings) == 3


def test_search_still_applies_the_salary_floor(fake_transport_cls):
    result = AdzunaProvider(fake_transport_cls()).search(JobSearchQuery(min_salary=60_000))
    assert {p.external_id for p in result.postings} == {"4200001"}


# --- credentials -------------------------------------------------------------


def test_without_credentials_the_provider_reports_itself_down(
    fake_transport_cls, monkeypatch: pytest.MonkeyPatch
):
    """Adzuna needs a free developer key. Without one the provider must say so
    rather than raise on every search."""
    monkeypatch.delenv(ADZUNA_APP_ID_ENV_VAR, raising=False)
    monkeypatch.delenv(ADZUNA_APP_KEY_ENV_VAR, raising=False)
    health = AdzunaProvider(fake_transport_cls()).health_check()
    assert health.status == HealthStatus.DOWN
    assert "ADZUNA_APP_ID" in health.detail


def test_without_credentials_search_returns_nothing_instead_of_raising(
    fake_transport_cls, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv(ADZUNA_APP_ID_ENV_VAR, raising=False)
    monkeypatch.delenv(ADZUNA_APP_KEY_ENV_VAR, raising=False)
    transport = fake_transport_cls()
    assert AdzunaProvider(transport).search(JobSearchQuery()).postings == []
    assert transport.calls == []


def test_health_check_is_healthy_with_credentials_and_a_live_api(fake_transport_cls):
    assert AdzunaProvider(fake_transport_cls()).health_check().status == HealthStatus.HEALTHY


def test_health_check_is_down_when_the_api_fails(fake_transport_cls):
    provider = AdzunaProvider(fake_transport_cls(raise_error=RuntimeError("401 unauthorized")))
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "401" in health.detail


def test_health_check_asks_for_a_single_result(fake_transport_cls):
    transport = fake_transport_cls()
    AdzunaProvider(transport).health_check()
    assert transport.calls[0]["results_per_page"] == 1
