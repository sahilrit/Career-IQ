"""Tests for CapabilityMarketplace: discovery, ranking, fallback, parallel execution."""

from __future__ import annotations

import pytest

from careeros_capability_marketplace import (
    CapabilityMarketplace,
    NoProviderAvailableError,
    ProviderRecord,
)


@pytest.fixture
def marketplace():
    return CapabilityMarketplace()


def test_discover_returns_every_registered_provider(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("remoteok", "provider-a"))
    marketplace.register("FIND_JOBS", ProviderRecord("wellfound", "provider-b"))
    assert len(marketplace.discover("FIND_JOBS")) == 2


def test_discover_filters_by_version_constraint(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("remoteok", "a", version="1.5.0"))
    marketplace.register("FIND_JOBS", ProviderRecord("wellfound", "b", version="2.0.0"))
    matching = marketplace.discover("FIND_JOBS", version_constraint="^1.0.0")
    assert [r.provider_id for r in matching] == ["remoteok"]


def test_ranked_excludes_unhealthy_providers(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("remoteok", "a", health_check=lambda: True))
    marketplace.register("FIND_JOBS", ProviderRecord("broken", "b", health_check=lambda: False))
    ranked = marketplace.ranked("FIND_JOBS")
    assert [r.provider_id for r in ranked] == ["remoteok"]


def test_ranked_orders_by_priority_descending(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("low", "a", priority=1))
    marketplace.register("FIND_JOBS", ProviderRecord("high", "b", priority=10))
    ranked = marketplace.ranked("FIND_JOBS")
    assert [r.provider_id for r in ranked] == ["high", "low"]


def test_health_check_that_raises_is_treated_as_unhealthy(marketplace):
    def broken_check():
        raise RuntimeError("boom")

    marketplace.register("FIND_JOBS", ProviderRecord("broken", "a", health_check=broken_check))
    assert marketplace.ranked("FIND_JOBS") == []


def test_call_with_fallback_uses_the_first_healthy_provider(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("remoteok", "provider-a", priority=1))
    result = marketplace.call_with_fallback("FIND_JOBS", lambda provider: f"called {provider}")
    assert result == "called provider-a"


def test_call_with_fallback_skips_a_failing_provider(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("broken", "a", priority=10))
    marketplace.register("FIND_JOBS", ProviderRecord("works", "b", priority=1))

    def invoke(provider):
        if provider == "a":
            raise RuntimeError("provider a is down")
        return f"result from {provider}"

    result = marketplace.call_with_fallback("FIND_JOBS", invoke)
    assert result == "result from b"


def test_call_with_fallback_raises_no_provider_available_when_none_registered(marketplace):
    with pytest.raises(NoProviderAvailableError):
        marketplace.call_with_fallback("FIND_JOBS", lambda provider: provider)


def test_call_with_fallback_raises_last_error_when_all_fail(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("a", "a"))
    marketplace.register("FIND_JOBS", ProviderRecord("b", "b"))

    def always_fails(provider):
        raise RuntimeError(f"{provider} failed")

    with pytest.raises(RuntimeError):
        marketplace.call_with_fallback("FIND_JOBS", always_fails)


def test_call_all_parallel_collects_every_successful_result(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("a", "provider-a"))
    marketplace.register("FIND_JOBS", ProviderRecord("b", "provider-b"))
    marketplace.register("FIND_JOBS", ProviderRecord("c", "provider-c"))

    results = marketplace.call_all_parallel("FIND_JOBS", lambda provider: provider)

    assert set(results) == {"provider-a", "provider-b", "provider-c"}


def test_call_all_parallel_skips_failures_without_raising(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("broken", "broken"))
    marketplace.register("FIND_JOBS", ProviderRecord("works", "works"))

    def invoke(provider):
        if provider == "broken":
            raise RuntimeError("down")
        return provider

    results = marketplace.call_all_parallel("FIND_JOBS", invoke)

    assert results == ["works"]


def test_call_all_parallel_with_no_providers_returns_empty_list(marketplace):
    assert marketplace.call_all_parallel("FIND_JOBS", lambda provider: provider) == []


def test_unregister_removes_a_provider(marketplace):
    marketplace.register("FIND_JOBS", ProviderRecord("a", "a"))
    marketplace.unregister("FIND_JOBS", "a")
    assert marketplace.discover("FIND_JOBS") == []
