"""Aggregation: combines every signal recorded for the same subject
into one ranked score. More independent supporting evidence for a
subject raises its combined score, capped rather than allowed to run
away — the same pattern used for opportunity/demand scoring elsewhere
in the platform.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_career_intelligence.signal_input import RecommendationCategory, SignalInput

_MAX_SCORE = 100.0


class RankedSubject(BaseModel):
    subject: str
    combined_score: float
    supporting_signal_count: int
    sources: list[str]


def rank_subjects(signals: list[SignalInput]) -> list[RankedSubject]:
    grouped: dict[str, list[SignalInput]] = {}
    for signal in signals:
        grouped.setdefault(signal.subject, []).append(signal)

    ranked = [
        RankedSubject(
            subject=subject,
            combined_score=min(_MAX_SCORE, sum(s.score for s in group)),
            supporting_signal_count=len(group),
            sources=[s.source for s in group],
        )
        for subject, group in grouped.items()
    ]
    ranked.sort(key=lambda r: r.combined_score, reverse=True)
    return ranked


def rank_by_category(
    signals: list[SignalInput], category: RecommendationCategory
) -> list[RankedSubject]:
    return rank_subjects([signal for signal in signals if signal.category == category])
