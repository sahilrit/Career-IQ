"""Tests for verify_zero_cost_mode / enforce_zero_cost_mode."""

from __future__ import annotations

import pytest

from careeros_zero_cost_mode import (
    CostTier,
    ProviderDeclaration,
    ZeroCostRegistry,
    ZeroCostViolationError,
    enforce_zero_cost_mode,
    verify_zero_cost_mode,
)


def test_report_is_fully_zero_cost_when_every_capability_has_a_free_path():
    registry = ZeroCostRegistry()
    registry.register(
        ProviderDeclaration(capability_name="find_jobs", provider_name="a", cost_tier=CostTier.FREE)
    )
    report = verify_zero_cost_mode(registry, ["find_jobs"])
    assert report.is_fully_zero_cost is True
    assert report.violations == []


def test_report_flags_capabilities_with_no_free_path():
    registry = ZeroCostRegistry()
    registry.register(
        ProviderDeclaration(capability_name="find_jobs", provider_name="a", cost_tier=CostTier.PAID)
    )
    report = verify_zero_cost_mode(registry, ["find_jobs"])
    assert report.is_fully_zero_cost is False
    assert [v.capability_name for v in report.violations] == ["find_jobs"]


def test_report_flags_capabilities_with_no_registered_provider_at_all():
    registry = ZeroCostRegistry()
    report = verify_zero_cost_mode(registry, ["find_jobs"])
    assert report.violations[0].provider_count == 0


def test_enforce_raises_on_violation():
    registry = ZeroCostRegistry()
    with pytest.raises(ZeroCostViolationError):
        enforce_zero_cost_mode(registry, ["find_jobs"])


def test_enforce_does_not_raise_when_clean():
    registry = ZeroCostRegistry()
    registry.register(
        ProviderDeclaration(capability_name="find_jobs", provider_name="a", cost_tier=CostTier.FREE)
    )
    enforce_zero_cost_mode(registry, ["find_jobs"])
