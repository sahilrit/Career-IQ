"""Tests for the generic CapabilityRegistry."""

from __future__ import annotations

from careeros_core import CapabilityRegistry


def test_register_then_get():
    registry = CapabilityRegistry()
    registry.register("FIND_JOBS", "remoteok", "remoteok-provider-instance")
    assert registry.get("FIND_JOBS", "remoteok") == "remoteok-provider-instance"


def test_get_missing_returns_none():
    registry = CapabilityRegistry()
    assert registry.get("FIND_JOBS", "does-not-exist") is None


def test_list_providers_for_a_capability():
    registry = CapabilityRegistry()
    registry.register("FIND_JOBS", "remoteok", "a")
    registry.register("FIND_JOBS", "wellfound", "b")
    registry.register("FIND_GIGS", "fiverr", "c")
    assert set(registry.list_providers("FIND_JOBS")) == {"a", "b"}


def test_list_capabilities():
    registry = CapabilityRegistry()
    registry.register("FIND_JOBS", "remoteok", "a")
    registry.register("FIND_GIGS", "fiverr", "c")
    assert set(registry.list_capabilities()) == {"FIND_JOBS", "FIND_GIGS"}


def test_unregister_removes_only_that_provider():
    registry = CapabilityRegistry()
    registry.register("FIND_JOBS", "remoteok", "a")
    registry.register("FIND_JOBS", "wellfound", "b")
    registry.unregister("FIND_JOBS", "remoteok")
    assert registry.list_providers("FIND_JOBS") == ["b"]


def test_capabilities_are_isolated_by_provider_id():
    registry = CapabilityRegistry()
    registry.register("FIND_JOBS", "shared-id", "job-provider")
    registry.register("FIND_GIGS", "shared-id", "gig-provider")
    assert registry.get("FIND_JOBS", "shared-id") == "job-provider"
    assert registry.get("FIND_GIGS", "shared-id") == "gig-provider"
