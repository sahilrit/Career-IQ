"""Experience analysis: tenure, seniority signal, and gap detection.

Deterministic arithmetic and keyword heuristics over Career Brain data —
no ML, fully explainable. This is the seed for Phase 40's broader Career
Intelligence Engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from itertools import pairwise

from careeros_career_brain import CareerBrain, Experience

_LEAD_KEYWORDS = ("lead", "head", "director", "vp", "chief", "principal")
_SENIOR_KEYWORDS = ("senior", "staff")
_JUNIOR_KEYWORDS = ("junior", "intern", "associate", "entry")


class SeniorityLevel(StrEnum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


@dataclass
class ExperienceGap:
    after: Experience
    before: Experience
    gap_days: int


def total_years_of_experience(brain: CareerBrain, *, as_of: date | None = None) -> float:
    """Sum of each role's own duration in years (tenure, not calendar coverage)."""
    as_of = as_of or date.today()
    total_days = 0
    for exp in brain.experiences:
        end = exp.end_date or as_of
        total_days += max((end - exp.start_date).days, 0)
    return round(total_days / 365.25, 1)


def seniority_level(brain: CareerBrain) -> SeniorityLevel:
    """A simple, explainable seniority signal: title keywords first, tenure as fallback."""
    titles = " ".join(exp.title.lower() for exp in brain.experiences)

    if any(keyword in titles for keyword in _LEAD_KEYWORDS):
        return SeniorityLevel.LEAD
    if any(keyword in titles for keyword in _SENIOR_KEYWORDS):
        return SeniorityLevel.SENIOR
    if any(keyword in titles for keyword in _JUNIOR_KEYWORDS):
        return SeniorityLevel.ENTRY

    years = total_years_of_experience(brain)
    if years < 2:
        return SeniorityLevel.ENTRY
    if years < 5:
        return SeniorityLevel.MID
    if years < 9:
        return SeniorityLevel.SENIOR
    return SeniorityLevel.LEAD


def detect_experience_gaps(brain: CareerBrain, *, min_gap_days: int = 90) -> list[ExperienceGap]:
    """Gaps of at least ``min_gap_days`` between consecutive roles, chronologically."""
    ordered = sorted(brain.experiences, key=lambda e: e.start_date)
    gaps = []
    for earlier, later in pairwise(ordered):
        if earlier.end_date is None:
            continue  # still current: no gap possible after it
        gap_days = (later.start_date - earlier.end_date).days
        if gap_days >= min_gap_days:
            gaps.append(ExperienceGap(after=earlier, before=later, gap_days=gap_days))
    return gaps
