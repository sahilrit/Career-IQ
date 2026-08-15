"""Unified opportunity scoring: one heuristic for both employment and
freelance postings, reusing careeros_career_brain_engine's proficiency-
weighted skill matching (Phase 11) as the primary signal.
"""

from __future__ import annotations

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine import match_skills
from careeros_opportunity_intelligence.opportunity import Opportunity, OpportunityKind

_SKILL_WEIGHT = 0.7
_TITLE_WEIGHT = 0.3


def score_opportunity(opportunity: Opportunity, brain: CareerBrain) -> float:
    skill_result = match_skills(brain, opportunity.tags)

    title_score = 1.0
    if opportunity.kind == OpportunityKind.EMPLOYMENT and brain.preferences.desired_titles:
        title_lower = opportunity.title.lower()
        title_score = (
            1.0
            if any(title.lower() in title_lower for title in brain.preferences.desired_titles)
            else 0.0
        )

    return _SKILL_WEIGHT * skill_result.score + _TITLE_WEIGHT * title_score
