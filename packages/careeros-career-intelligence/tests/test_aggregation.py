"""Tests for rank_subjects / rank_by_category."""

from __future__ import annotations

from careeros_career_intelligence import RecommendationCategory, SignalInput
from careeros_career_intelligence.aggregation import rank_by_category, rank_subjects


def _signal(subject: str, score: float, source: str = "test") -> SignalInput:
    return SignalInput(
        category=RecommendationCategory.ROLE, subject=subject, score=score, source=source
    )


def test_ranks_higher_score_first():
    signals = [_signal("Engineer", 30), _signal("Manager", 80)]
    ranked = rank_subjects(signals)
    assert [r.subject for r in ranked] == ["Manager", "Engineer"]


def test_combines_multiple_signals_for_the_same_subject():
    signals = [_signal("Engineer", 30, source="a"), _signal("Engineer", 20, source="b")]
    ranked = rank_subjects(signals)
    assert ranked[0].combined_score == 50
    assert ranked[0].supporting_signal_count == 2
    assert ranked[0].sources == ["a", "b"]


def test_combined_score_caps_at_100():
    signals = [_signal("Engineer", 60, source="a"), _signal("Engineer", 60, source="b")]
    ranked = rank_subjects(signals)
    assert ranked[0].combined_score == 100.0


def test_empty_input_returns_empty():
    assert rank_subjects([]) == []


def test_rank_by_category_filters_first():
    role = _signal("Engineer", 50)
    skill = SignalInput(
        category=RecommendationCategory.SKILL, subject="Python", score=90, source="test"
    )
    ranked = rank_by_category([role, skill], RecommendationCategory.ROLE)
    assert [r.subject for r in ranked] == ["Engineer"]
