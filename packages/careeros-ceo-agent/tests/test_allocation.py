"""Tests for allocate_resources."""

from __future__ import annotations

import pytest

from careeros_ceo_agent import DISCLAIMER, PerformanceInput, ResourceCategory, allocate_resources


def _input(category: ResourceCategory, value: float) -> PerformanceInput:
    return PerformanceInput(category=category, metric_name="score", value=value, source="t")


def test_no_evidence_returns_the_baseline():
    plan = allocate_resources([])
    for value in plan.allocations.values():
        assert value == pytest.approx(25.0)


def test_allocations_always_sum_to_100():
    inputs = [_input(ResourceCategory.EMPLOYMENT, 80), _input(ResourceCategory.FREELANCE, 20)]
    plan = allocate_resources(inputs)
    assert sum(plan.allocations.values()) == pytest.approx(100.0)


def test_stronger_performance_raises_that_categorys_share():
    inputs = [_input(ResourceCategory.EMPLOYMENT, 90), _input(ResourceCategory.FREELANCE, 10)]
    plan = allocate_resources(inputs)
    assert (
        plan.allocations[ResourceCategory.EMPLOYMENT] > plan.allocations[ResourceCategory.FREELANCE]
    )


def test_shift_weight_of_zero_ignores_performance_entirely():
    inputs = [_input(ResourceCategory.EMPLOYMENT, 100)]
    plan = allocate_resources(inputs, shift_weight=0.0)
    for value in plan.allocations.values():
        assert value == pytest.approx(25.0)


def test_shift_weight_of_one_ignores_the_baseline_entirely():
    inputs = [_input(ResourceCategory.EMPLOYMENT, 100)]
    plan = allocate_resources(inputs, shift_weight=1.0)
    assert plan.allocations[ResourceCategory.EMPLOYMENT] == pytest.approx(100.0)
    assert plan.allocations[ResourceCategory.FREELANCE] == pytest.approx(0.0)


def test_custom_baseline_is_respected_with_no_evidence():
    custom_baseline = {
        ResourceCategory.EMPLOYMENT: 40.0,
        ResourceCategory.FREELANCE: 35.0,
        ResourceCategory.NETWORKING: 15.0,
        ResourceCategory.PERSONAL_BRAND: 10.0,
    }
    plan = allocate_resources([], baseline=custom_baseline)
    assert plan.allocations == custom_baseline


def test_disclaimer_is_present():
    plan = allocate_resources([])
    assert plan.disclaimer == DISCLAIMER
