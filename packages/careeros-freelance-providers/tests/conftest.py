"""Shared fixtures for freelance provider framework tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from careeros_freelance_providers import (
    FreelanceProvider,
    GigPosting,
    GigSearchQuery,
    GigSearchResult,
    HealthStatus,
    ProviderHealth,
)


class FakeProvider(FreelanceProvider):
    def __init__(
        self,
        provider_id: str,
        postings: list[GigPosting] | None = None,
        *,
        health: HealthStatus = HealthStatus.HEALTHY,
        raise_on_search: bool = False,
    ) -> None:
        self._provider_id = provider_id
        self._postings = postings or []
        self._health = health
        self._raise_on_search = raise_on_search
        self.search_calls = 0

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def search(self, query: GigSearchQuery) -> GigSearchResult:
        self.search_calls += 1
        if self._raise_on_search:
            raise RuntimeError("provider is on fire")
        return GigSearchResult(postings=list(self._postings))

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(status=self._health)


def make_posting(
    source_provider: str = "fake",
    external_id: str = "1",
    title: str = "Shopify Storefront Redesign",
    **overrides: object,
) -> GigPosting:
    defaults = {
        "source_provider": source_provider,
        "external_id": external_id,
        "title": title,
        "client_name": "Acme Co",
        "url": f"https://example.com/gigs/{external_id}",
    }
    defaults.update(overrides)
    return GigPosting(**defaults)


@pytest.fixture
def posting_factory() -> Callable[..., GigPosting]:
    return make_posting


@pytest.fixture
def fake_provider_cls() -> type[FakeProvider]:
    return FakeProvider
