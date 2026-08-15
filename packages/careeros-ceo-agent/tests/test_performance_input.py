"""Tests for PerformanceInput / PerformanceInputRepository."""

from __future__ import annotations

from careeros_ceo_agent import PerformanceInput, ResourceCategory


def test_list_all_returns_every_saved_input(performance_repository):
    performance_input = PerformanceInput(
        category=ResourceCategory.EMPLOYMENT, metric_name="response_rate", value=40, source="t"
    )
    performance_repository.save(performance_input)
    assert performance_repository.list_all() == [performance_input]
