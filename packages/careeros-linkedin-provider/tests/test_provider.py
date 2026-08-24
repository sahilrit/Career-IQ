"""Tests for LinkedInProvider, entirely against a fake transport."""

from __future__ import annotations

from careeros_job_providers import HealthStatus, JobSearchQuery
from careeros_linkedin_provider import LinkedInProvider


def test_provider_id_is_linkedin(fake_transport_cls):
    assert LinkedInProvider(transport=fake_transport_cls()).provider_id == "linkedin"


def test_search_returns_the_usable_cards(fake_transport_cls):
    provider = LinkedInProvider(transport=fake_transport_cls(), fetch_descriptions=False)
    result = provider.search(JobSearchQuery(keywords=["performance marketing"]))
    assert {p.external_id for p in result.postings} == {"4438071583", "4400000001"}


def test_search_sends_the_keywords_and_location_through(fake_transport_cls):
    transport = fake_transport_cls()
    provider = LinkedInProvider(transport=transport, fetch_descriptions=False)
    provider.search(JobSearchQuery(keywords=["growth"], locations=["India"]))
    assert transport.search_calls[0]["keywords"] == "growth"
    assert transport.search_calls[0]["location"] == "India"


def test_search_stops_paging_when_a_page_returns_nothing(fake_transport_cls):
    transport = fake_transport_cls()
    provider = LinkedInProvider(transport=transport, fetch_descriptions=False)
    provider.search(JobSearchQuery(keywords=["growth"], limit=100))
    # Page 1 had cards, page 2 was empty -> stop. No third request.
    assert len(transport.search_calls) == 2


def test_search_respects_the_limit(fake_transport_cls):
    provider = LinkedInProvider(transport=fake_transport_cls(), fetch_descriptions=False)
    result = provider.search(JobSearchQuery(keywords=["growth"], limit=1))
    assert len(result.postings) == 1


def test_each_keyword_is_searched_separately(fake_transport_cls):
    transport = fake_transport_cls(pages=[])
    provider = LinkedInProvider(transport=transport, fetch_descriptions=False)
    provider.search(JobSearchQuery(keywords=["growth", "paid media"]))
    assert [call["keywords"] for call in transport.search_calls] == ["growth", "paid media"]


def test_the_same_job_from_two_keywords_is_only_returned_once(fake_transport_cls, one_card_html):
    transport = fake_transport_cls(pages=[one_card_html, "", one_card_html, ""])
    provider = LinkedInProvider(transport=transport, fetch_descriptions=False)
    result = provider.search(JobSearchQuery(keywords=["growth", "paid media"]))
    assert len(result.postings) == 1


def test_descriptions_are_fetched_when_enabled(fake_transport_cls):
    transport = fake_transport_cls()
    provider = LinkedInProvider(transport=transport, fetch_descriptions=True)
    result = provider.search(JobSearchQuery(keywords=["growth"]))
    assert transport.description_calls
    assert all("paid acquisition" in p.description for p in result.postings)


def test_descriptions_are_capped(fake_transport_cls):
    transport = fake_transport_cls()
    provider = LinkedInProvider(transport=transport, fetch_descriptions=True, max_descriptions=1)
    provider.search(JobSearchQuery(keywords=["growth"]))
    assert len(transport.description_calls) == 1


def test_a_failing_description_does_not_lose_the_posting(fake_transport_cls):
    class FlakyTransport(fake_transport_cls):  # type: ignore[misc, valid-type]
        def fetch_job_page(self, job_id: str) -> str:
            raise RuntimeError("429 rate limited")

    provider = LinkedInProvider(transport=FlakyTransport(), fetch_descriptions=True)
    result = provider.search(JobSearchQuery(keywords=["growth"]))
    assert len(result.postings) == 2
    assert all(p.description == "" for p in result.postings)


def test_remote_only_query_filters_out_onsite_roles(fake_transport_cls):
    provider = LinkedInProvider(transport=fake_transport_cls(), fetch_descriptions=False)
    result = provider.search(JobSearchQuery(keywords=["growth"], remote_only=True))
    assert {p.external_id for p in result.postings} == {"4400000001"}


def test_health_check_is_healthy_when_the_endpoint_answers(fake_transport_cls):
    provider = LinkedInProvider(transport=fake_transport_cls())
    assert provider.health_check().status == HealthStatus.HEALTHY


def test_health_check_is_down_when_the_endpoint_raises(fake_transport_cls):
    provider = LinkedInProvider(
        transport=fake_transport_cls(raise_error=RuntimeError("999 blocked"))
    )
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "999" in health.detail


def test_health_check_makes_one_cheap_request(fake_transport_cls):
    transport = fake_transport_cls()
    LinkedInProvider(transport=transport).health_check()
    assert len(transport.search_calls) == 1
