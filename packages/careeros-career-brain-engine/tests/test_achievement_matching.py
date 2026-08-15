"""Tests for achievement relevance ranking."""

from __future__ import annotations

from datetime import date

from careeros_career_brain import Achievement, Experience
from careeros_career_brain_engine import rank_achievements_for_text


def _experience_with(achievements: list[Achievement]) -> Experience:
    return Experience(
        company_name="Acme",
        title="Engineer",
        start_date=date(2020, 1, 1),
        achievements=achievements,
    )


def test_no_achievements_returns_empty_list(brain_factory):
    brain = brain_factory(experiences=[_experience_with([])])
    assert rank_achievements_for_text(brain, "shopify audit") == []


def test_relevant_achievement_ranks_above_irrelevant_one(brain_factory):
    relevant = Achievement(description="Led a Shopify storefront redesign, improving CRO")
    irrelevant = Achievement(description="Migrated an internal Java batch job to Kubernetes")
    brain = brain_factory(experiences=[_experience_with([relevant, irrelevant])])

    ranked = rank_achievements_for_text(brain, "shopify ecommerce store redesign")

    assert ranked[0].achievement.id == relevant.id


def test_top_k_limits_results(brain_factory):
    achievements = [Achievement(description="shopify ecommerce store work") for _ in range(10)]
    brain = brain_factory(experiences=[_experience_with(achievements)])

    ranked = rank_achievements_for_text(brain, "shopify", top_k=3)

    assert len(ranked) == 3


def test_achievements_across_multiple_experiences_are_all_considered(brain_factory):
    first = Achievement(description="Shopify storefront work")
    second = Achievement(description="Unrelated aerospace project")
    brain = brain_factory(experiences=[_experience_with([first]), _experience_with([second])])

    ranked = rank_achievements_for_text(brain, "shopify")

    assert len(ranked) >= 1
    assert ranked[0].achievement.id == first.id
