"""Career direction: a one-paragraph synthesis referencing only the
top-ranked subject in each of role/industry/skill — never a prediction
beyond what the aggregated signals actually rank highest.
"""

from __future__ import annotations

from careeros_career_intelligence.aggregation import rank_by_category
from careeros_career_intelligence.signal_input import RecommendationCategory, SignalInput

_NO_SIGNAL_MESSAGE = "Not enough signal yet to recommend a direction."


def generate_career_direction_summary(signals: list[SignalInput]) -> str:
    top_role = _top_subject(signals, RecommendationCategory.ROLE)
    top_industry = _top_subject(signals, RecommendationCategory.INDUSTRY)
    top_skill = _top_subject(signals, RecommendationCategory.SKILL)

    parts = []
    if top_role:
        parts.append(f"lean toward {top_role} roles")
    if top_industry:
        parts.append(f"in the {top_industry} industry")
    if top_skill:
        parts.append(f"leaning on your strongest signal: {top_skill}")

    if not parts:
        return _NO_SIGNAL_MESSAGE

    return "Based on the signals collected so far, " + ", ".join(parts) + "."


def _top_subject(signals: list[SignalInput], category: RecommendationCategory) -> str | None:
    ranked = rank_by_category(signals, category)
    return ranked[0].subject if ranked else None
