"""Tests for the CEOAgentDivision facade."""

from __future__ import annotations

import pytest

from careeros_ceo_agent import CEOAgentDivision, PerformanceInput, ResourceCategory


@pytest.fixture
def division(performance_repository, plan_repository):
    return CEOAgentDivision(performance_repository, plan_repository)


def test_compute_allocation_saves_to_history(division):
    division.record_performance(
        PerformanceInput(
            category=ResourceCategory.EMPLOYMENT, metric_name="score", value=50, source="t"
        )
    )
    plan = division.compute_allocation()
    assert division.allocation_history() == [plan]


def test_latest_allocation_returns_none_with_no_history(division):
    assert division.latest_allocation() is None


def test_latest_allocation_returns_the_most_recent_plan(division):
    division.compute_allocation()
    second = division.compute_allocation()
    assert division.latest_allocation() == second


def test_record_performance_influences_the_next_allocation(division):
    division.record_performance(
        PerformanceInput(
            category=ResourceCategory.PERSONAL_BRAND, metric_name="score", value=100, source="t"
        )
    )
    plan = division.compute_allocation(shift_weight=1.0)
    assert plan.allocations[ResourceCategory.PERSONAL_BRAND] == pytest.approx(100.0)
