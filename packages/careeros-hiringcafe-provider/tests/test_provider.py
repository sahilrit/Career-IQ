"""Tests for the Hiring Cafe provider and its SSR payload parsing."""

from __future__ import annotations

import pytest

from careeros_hiringcafe_provider import (
    HiringCafeChallengeError,
    HiringCafeProvider,
    build_search_state,
    is_job_entry,
    parse_job_entry,
    parse_ssr_page,
)
from careeros_job_providers import EmploymentType, HealthStatus, JobProviderError, JobSearchQuery

# --- payload parsing ---------------------------------------------------------


def test_parse_ssr_page_reads_hits_and_paging(page_builder, hit_remote):
    page = parse_ssr_page(page_builder([hit_remote], page=2, total=551, is_last=False))
    assert len(page.hits) == 1
    assert page.page == 2
    assert page.total_count == 551
    assert page.is_last_page is False


def test_parse_ssr_page_raises_on_a_cloudflare_challenge(challenge_html):
    with pytest.raises(HiringCafeChallengeError):
        parse_ssr_page(challenge_html)


def test_parse_ssr_page_raises_when_the_payload_is_missing():
    with pytest.raises(JobProviderError):
        parse_ssr_page("<html><body>no next data here</body></html>")


# --- entry mapping -----------------------------------------------------------


def test_expired_hits_are_not_job_entries():
    assert is_job_entry({"is_expired": True, "id": "x", "job_information": {"title": "t"}}) is False


def test_a_hit_without_an_apply_url_is_not_usable():
    assert is_job_entry({"id": "x", "job_information": {"title": "t"}}) is False


def test_parse_maps_the_core_fields(hit_remote):
    posting = parse_job_entry(hit_remote)
    assert posting.source_provider == "hiringcafe"
    assert posting.external_id == "greenhouse___acme___4400001"
    assert posting.title == "Performance Marketing Manager"
    assert posting.company_name == "Acme Corp"
    assert posting.url == "https://boards.greenhouse.io/acme/jobs/4400001"
    assert posting.location == "Remote, United States"


def test_remote_workplace_type_sets_the_flag(hit_remote, hit_onsite):
    assert parse_job_entry(hit_remote).remote is True
    assert parse_job_entry(hit_onsite).remote is False


def test_parse_reads_the_compensation_range(hit_remote):
    salary = parse_job_entry(hit_remote).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount) == (120000, 150000)
    assert salary.currency == "USD"


def test_no_compensation_means_no_salary(hit_onsite):
    assert parse_job_entry(hit_onsite).salary is None


def test_parse_maps_the_commitment_to_an_employment_type(hit_remote, hit_onsite):
    assert parse_job_entry(hit_remote).employment_type is EmploymentType.FULL_TIME
    assert parse_job_entry(hit_onsite).employment_type is EmploymentType.INTERNSHIP


def test_parse_reads_the_estimated_publish_date(hit_remote):
    posted = parse_job_entry(hit_remote).posted_at
    assert posted is not None
    assert (posted.year, posted.month, posted.day) == (2026, 7, 24)


def test_tools_and_category_become_tags(hit_remote):
    tags = parse_job_entry(hit_remote).tags
    assert "google ads" in tags
    assert "marketing" in tags


def test_description_is_built_from_the_structured_fields(hit_remote):
    """Search hits carry no job description, but Hiring Cafe's own extraction
    does — and the scorer needs text to match skills against."""
    description = parse_job_entry(hit_remote).description
    assert "5+ years running paid acquisition" in description
    assert "owning budget" in description
    assert "Google Ads" in description


# --- search state ------------------------------------------------------------


def test_search_state_carries_the_keywords():
    state = build_search_state(JobSearchQuery(keywords=["performance marketing", "growth"]))
    assert state["searchQuery"] == "performance marketing growth"


def test_remote_only_query_asks_the_source_for_remote_roles():
    state = build_search_state(JobSearchQuery(remote_only=True))
    assert state["workplaceTypes"] == ["Remote"]


def test_locations_are_passed_through_as_a_query_hint():
    state = build_search_state(JobSearchQuery(locations=["India"]))
    assert "India" in state["searchQuery"]


# --- provider ----------------------------------------------------------------


def test_provider_id_is_hiringcafe(fake_transport_cls):
    assert HiringCafeProvider(fake_transport_cls()).provider_id == "hiringcafe"


def test_search_returns_the_usable_hits(fake_transport_cls):
    result = HiringCafeProvider(fake_transport_cls()).search(JobSearchQuery())
    assert len(result.postings) == 2


def test_search_drops_expired_hits(fake_transport_cls):
    result = HiringCafeProvider(fake_transport_cls()).search(JobSearchQuery())
    assert "lever___oldco___1" not in {p.external_id for p in result.postings}


def test_search_stops_at_the_last_page(fake_transport_cls):
    transport = fake_transport_cls()
    HiringCafeProvider(transport).search(JobSearchQuery(limit=500))
    assert len(transport.calls) == 2


def test_each_keyword_is_searched_separately(fake_transport_cls):
    # Hiring Cafe free-text is effectively AND, so one blob of many keywords
    # matches nothing. We issue a search per keyword instead.
    transport = fake_transport_cls()
    HiringCafeProvider(transport).search(JobSearchQuery(keywords=["meta ads", "ppc"], limit=500))
    queries = [call["search_state"]["searchQuery"] for call in transport.calls]
    assert "meta ads" in queries
    assert "ppc" in queries


def test_search_respects_the_limit(fake_transport_cls):
    result = HiringCafeProvider(fake_transport_cls()).search(JobSearchQuery(limit=1))
    assert len(result.postings) == 1


def test_search_does_not_refilter_the_keywords(fake_transport_cls):
    """Hiring Cafe matched against the full job text; our copy has only the
    structured summary, so re-checking would throw away real matches."""
    result = HiringCafeProvider(fake_transport_cls()).search(
        JobSearchQuery(keywords=["nonexistent phrase"])
    )
    assert len(result.postings) == 2


def test_search_still_applies_the_salary_floor(fake_transport_cls):
    result = HiringCafeProvider(fake_transport_cls()).search(JobSearchQuery(min_salary=130_000))
    assert {p.external_id for p in result.postings} == {"greenhouse___acme___4400001"}


def test_a_challenge_surfaces_as_a_provider_error(fake_transport_cls, challenge_html):
    provider = HiringCafeProvider(fake_transport_cls(pages=[challenge_html]))
    with pytest.raises(HiringCafeChallengeError):
        provider.search(JobSearchQuery())


def test_health_check_is_healthy_when_the_page_parses(fake_transport_cls):
    assert HiringCafeProvider(fake_transport_cls()).health_check().status == HealthStatus.HEALTHY


def test_health_check_is_down_behind_a_challenge(fake_transport_cls, challenge_html):
    provider = HiringCafeProvider(fake_transport_cls(pages=[challenge_html]))
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "challenge" in health.detail.lower()


def test_health_check_is_down_when_the_request_fails(fake_transport_cls):
    provider = HiringCafeProvider(fake_transport_cls(raise_error=RuntimeError("timeout")))
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "timeout" in health.detail
