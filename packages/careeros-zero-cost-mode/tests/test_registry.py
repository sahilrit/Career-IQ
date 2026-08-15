"""Tests for ZeroCostRegistry."""

from __future__ import annotations

from careeros_zero_cost_mode import CostTier, ProviderDeclaration, ZeroCostRegistry


def _declaration(capability: str, tier: CostTier, provider: str = "test") -> ProviderDeclaration:
    return ProviderDeclaration(capability_name=capability, provider_name=provider, cost_tier=tier)


def test_unknown_capability_has_no_free_path():
    registry = ZeroCostRegistry()
    assert registry.has_free_path("find_jobs") is False


def test_free_provider_gives_a_free_path():
    registry = ZeroCostRegistry()
    registry.register(_declaration("find_jobs", CostTier.FREE))
    assert registry.has_free_path("find_jobs") is True


def test_freemium_counts_as_a_free_path():
    registry = ZeroCostRegistry()
    registry.register(_declaration("find_jobs", CostTier.FREEMIUM))
    assert registry.has_free_path("find_jobs") is True


def test_paid_only_provider_has_no_free_path():
    registry = ZeroCostRegistry()
    registry.register(_declaration("find_jobs", CostTier.PAID))
    assert registry.has_free_path("find_jobs") is False


def test_a_free_provider_among_paid_ones_still_counts():
    registry = ZeroCostRegistry()
    registry.register(_declaration("find_jobs", CostTier.PAID, provider="paid-one"))
    registry.register(_declaration("find_jobs", CostTier.FREE, provider="free-one"))
    assert registry.has_free_path("find_jobs") is True


def test_capabilities_lists_every_registered_capability():
    registry = ZeroCostRegistry()
    registry.register(_declaration("find_jobs", CostTier.FREE))
    registry.register(_declaration("find_gigs", CostTier.FREE))
    assert registry.capabilities() == {"find_jobs", "find_gigs"}
