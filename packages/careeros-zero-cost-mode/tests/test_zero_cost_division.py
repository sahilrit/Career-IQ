"""Tests for the ZeroCostDivision facade."""

from __future__ import annotations

from pathlib import Path

import pytest

from careeros_zero_cost_mode import (
    CostTier,
    ProviderDeclaration,
    ZeroCostDivision,
    ZeroCostRegistry,
    ZeroCostViolationError,
)


def test_default_division_is_seeded_with_platform_declarations():
    division = ZeroCostDivision()
    report = division.verify(["find_jobs", "find_gigs"])
    assert report.is_fully_zero_cost is True


def test_register_provider_adds_to_the_registry():
    division = ZeroCostDivision(ZeroCostRegistry())
    division.register_provider(
        ProviderDeclaration(capability_name="new_thing", provider_name="a", cost_tier=CostTier.FREE)
    )
    assert division.verify(["new_thing"]).is_fully_zero_cost is True


def test_enforce_raises_on_a_paid_only_capability():
    division = ZeroCostDivision(ZeroCostRegistry())
    division.register_provider(
        ProviderDeclaration(capability_name="new_thing", provider_name="a", cost_tier=CostTier.PAID)
    )
    with pytest.raises(ZeroCostViolationError):
        division.enforce(["new_thing"])


def test_audit_workspace_dependencies_against_the_real_repo():
    division = ZeroCostDivision()
    packages_dir = Path(__file__).resolve().parents[2]
    assert division.audit_workspace_dependencies(packages_dir) == {}
