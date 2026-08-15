"""Tests for generate_career_direction_summary."""

from __future__ import annotations

from careeros_career_intelligence import RecommendationCategory, SignalInput
from careeros_career_intelligence.career_direction import generate_career_direction_summary


def test_no_signals_says_not_enough_signal():
    summary = generate_career_direction_summary([])
    assert summary == "Not enough signal yet to recommend a direction."


def test_mentions_the_top_role():
    signals = [
        SignalInput(
            category=RecommendationCategory.ROLE, subject="Backend Engineer", score=80, source="t"
        )
    ]
    summary = generate_career_direction_summary(signals)
    assert "Backend Engineer" in summary


def test_mentions_top_role_industry_and_skill_together():
    signals = [
        SignalInput(category=RecommendationCategory.ROLE, subject="Engineer", score=80, source="t"),
        SignalInput(
            category=RecommendationCategory.INDUSTRY, subject="Fintech", score=70, source="t"
        ),
        SignalInput(category=RecommendationCategory.SKILL, subject="Python", score=90, source="t"),
    ]
    summary = generate_career_direction_summary(signals)
    assert "Engineer" in summary
    assert "Fintech" in summary
    assert "Python" in summary


def test_picks_the_highest_ranked_when_multiple_exist():
    signals = [
        SignalInput(category=RecommendationCategory.ROLE, subject="Engineer", score=20, source="t"),
        SignalInput(category=RecommendationCategory.ROLE, subject="Manager", score=90, source="t"),
    ]
    summary = generate_career_direction_summary(signals)
    assert "Manager" in summary
    assert "Engineer" not in summary
