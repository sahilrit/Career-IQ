"""careeros_career_intelligence: the Career Intelligence Engine.

Combines signals already computed elsewhere in the platform — skill
matching, opportunity scoring, predicted demand, learning-lab winners —
into ranked recommendations across roles, companies, industries,
clients, countries, salary range, skills, platform, outreach strategy,
and resume variant, plus a synthesized career direction summary.
"""

from careeros_career_intelligence.aggregation import RankedSubject, rank_by_category, rank_subjects
from careeros_career_intelligence.career_direction import generate_career_direction_summary
from careeros_career_intelligence.career_intelligence_division import CareerIntelligenceDivision
from careeros_career_intelligence.exceptions import CareerIntelligenceError
from careeros_career_intelligence.signal_input import (
    RecommendationCategory,
    SignalInput,
    SignalInputRepository,
)

__all__ = [
    "CareerIntelligenceDivision",
    "CareerIntelligenceError",
    "RankedSubject",
    "RecommendationCategory",
    "SignalInput",
    "SignalInputRepository",
    "generate_career_direction_summary",
    "rank_by_category",
    "rank_subjects",
]
