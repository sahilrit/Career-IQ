"""Tests for the platform's own default declarations."""

from __future__ import annotations

from careeros_zero_cost_mode import DEFAULT_PLATFORM_DECLARATIONS, CostTier, load_default_registry


def test_every_default_declaration_is_free():
    assert all(d.cost_tier == CostTier.FREE for d in DEFAULT_PLATFORM_DECLARATIONS)


def test_default_registry_has_a_free_path_for_every_declared_capability():
    registry = load_default_registry()
    for capability in registry.capabilities():
        assert registry.has_free_path(capability) is True


def test_default_registry_covers_find_jobs_and_find_gigs():
    registry = load_default_registry()
    assert {"find_jobs", "find_gigs"} <= registry.capabilities()
