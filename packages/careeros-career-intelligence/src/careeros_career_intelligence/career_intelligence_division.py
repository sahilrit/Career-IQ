"""CareerIntelligenceDivision: the facade recording signals from
across the platform and answering the roadmap's question — which
roles, companies, industries, clients, countries, salary range, skills,
platform, outreach strategy, resume should I pursue?
"""

from __future__ import annotations

from careeros_career_intelligence.aggregation import RankedSubject, rank_subjects
from careeros_career_intelligence.career_direction import generate_career_direction_summary
from careeros_career_intelligence.signal_input import (
    RecommendationCategory,
    SignalInput,
    SignalInputRepository,
)


class CareerIntelligenceDivision:
    def __init__(self, signal_repository: SignalInputRepository) -> None:
        self._signals = signal_repository

    def record_signal(self, signal: SignalInput) -> None:
        self._signals.save(signal)

    def recommendations_for(
        self, category: RecommendationCategory, *, top_k: int = 5
    ) -> list[RankedSubject]:
        return rank_subjects(self._signals.list_by_category(category))[:top_k]

    def all_recommendations(
        self, *, top_k: int = 5
    ) -> dict[RecommendationCategory, list[RankedSubject]]:
        return {
            category: self.recommendations_for(category, top_k=top_k)
            for category in RecommendationCategory
        }

    def career_direction_summary(self) -> str:
        return generate_career_direction_summary(self._signals.list_all())
