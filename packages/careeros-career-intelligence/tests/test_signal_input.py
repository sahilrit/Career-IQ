"""Tests for SignalInput / SignalInputRepository."""

from __future__ import annotations

from careeros_career_intelligence import RecommendationCategory, SignalInput


def test_list_all_returns_every_saved_signal(signal_repository):
    signal = SignalInput(
        category=RecommendationCategory.ROLE, subject="Backend Engineer", score=80, source="test"
    )
    signal_repository.save(signal)
    assert signal_repository.list_all() == [signal]


def test_list_by_category_filters(signal_repository):
    role_signal = SignalInput(
        category=RecommendationCategory.ROLE, subject="Backend Engineer", score=80, source="test"
    )
    skill_signal = SignalInput(
        category=RecommendationCategory.SKILL, subject="Python", score=60, source="test"
    )
    signal_repository.save(role_signal)
    signal_repository.save(skill_signal)
    assert signal_repository.list_by_category(RecommendationCategory.ROLE) == [role_signal]
