"""Tests for AllocationPlanRepository."""

from __future__ import annotations

from careeros_ceo_agent import allocate_resources


def test_list_all_returns_saved_plans(plan_repository):
    plan = allocate_resources([])
    plan_repository.save(plan)
    assert plan_repository.list_all() == [plan]


def test_list_all_is_chronologically_sorted(plan_repository):
    first = allocate_resources([])
    second = allocate_resources([])
    plan_repository.save(second)
    plan_repository.save(first)
    plans = plan_repository.list_all()
    assert [p.generated_at for p in plans] == sorted(p.generated_at for p in plans)
