"""Tests for FiverrProvider, entirely against a fake transport."""

from __future__ import annotations

from careeros_fiverr_provider import FiverrProvider
from careeros_freelance_providers import GigSearchQuery, HealthStatus


class FakeTransport:
    def __init__(
        self, entries: list[dict] | None = None, *, raise_error: Exception | None = None
    ) -> None:
        self._entries = entries if entries is not None else []
        self._raise_error = raise_error
        self.fetch_calls = 0

    def fetch_listings(self, query: GigSearchQuery) -> list[dict]:
        self.fetch_calls += 1
        if self._raise_error is not None:
            raise self._raise_error
        return self._entries


def test_provider_id_is_fiverr():
    assert FiverrProvider(FakeTransport()).provider_id == "fiverr"


def test_search_normalizes_and_filters_out_malformed_entries():
    entries = [
        {"title": "Shopify redesign", "seller": "ada_dev", "price": "$500", "url": "https://x/1"},
        {"seller": "no-title", "url": "https://x/2"},  # missing title: dropped
    ]
    provider = FiverrProvider(FakeTransport(entries))

    result = provider.search(GigSearchQuery())

    assert len(result.postings) == 1
    assert result.postings[0].title == "Shopify redesign"


def test_search_respects_the_limit():
    entries = [{"title": f"Gig {i}", "seller": "x", "url": f"https://x/{i}"} for i in range(5)]
    provider = FiverrProvider(FakeTransport(entries))

    result = provider.search(GigSearchQuery(limit=2))

    assert len(result.postings) == 2


def test_health_check_reports_healthy_on_success():
    provider = FiverrProvider(FakeTransport())
    assert provider.health_check().status == HealthStatus.HEALTHY


def test_health_check_reports_down_when_transport_raises():
    provider = FiverrProvider(FakeTransport(raise_error=RuntimeError("navigation timeout")))
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "navigation timeout" in health.detail
