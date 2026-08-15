"""Tests for the CareerIntelligenceDivision facade."""

from __future__ import annotations

import pytest

from careeros_career_intelligence import (
    CareerIntelligenceDivision,
    RecommendationCategory,
    SignalInput,
)


@pytest.fixture
def division(signal_repository):
    return CareerIntelligenceDivision(signal_repository)


def test_recommendations_for_ranks_saved_signals(division):
    division.record_signal(
        SignalInput(category=RecommendationCategory.SKILL, subject="Python", score=90, source="t")
    )
    division.record_signal(
        SignalInput(category=RecommendationCategory.SKILL, subject="Rust", score=30, source="t")
    )
    ranked = division.recommendations_for(RecommendationCategory.SKILL)
    assert [r.subject for r in ranked] == ["Python", "Rust"]


def test_recommendations_for_respects_top_k(division):
    for i in range(10):
        division.record_signal(
            SignalInput(
                category=RecommendationCategory.SKILL, subject=f"Skill {i}", score=i, source="t"
            )
        )
    assert len(division.recommendations_for(RecommendationCategory.SKILL, top_k=3)) == 3


def test_all_recommendations_covers_every_category(division):
    division.record_signal(
        SignalInput(category=RecommendationCategory.ROLE, subject="Engineer", score=50, source="t")
    )
    all_recs = division.all_recommendations()
    assert set(all_recs) == set(RecommendationCategory)


def test_career_direction_summary_delegates(division):
    division.record_signal(
        SignalInput(category=RecommendationCategory.ROLE, subject="Engineer", score=50, source="t")
    )
    assert "Engineer" in division.career_direction_summary()
