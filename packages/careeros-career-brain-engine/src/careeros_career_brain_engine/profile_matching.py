"""Full profile match: skills, seniority signal, and top relevant
achievements combined into one explainable report against a specific
opportunity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine.achievement_matching import (
    RankedAchievement,
    rank_achievements_for_text,
)
from careeros_career_brain_engine.experience_analysis import SeniorityLevel, seniority_level
from careeros_career_brain_engine.skill_matching import SkillMatchResult, match_skills
from careeros_job_providers import JobPosting


@dataclass
class ProfileMatch:
    skill_match: SkillMatchResult
    seniority: SeniorityLevel
    top_achievements: list[RankedAchievement] = field(default_factory=list)


def match_profile_to_posting(
    brain: CareerBrain, posting: JobPosting, *, top_k_achievements: int = 3
) -> ProfileMatch:
    skill_match = match_skills(brain, posting.tags)
    text = f"{posting.title} {posting.description}"
    top_achievements = rank_achievements_for_text(brain, text, top_k=top_k_achievements)
    return ProfileMatch(
        skill_match=skill_match,
        seniority=seniority_level(brain),
        top_achievements=top_achievements,
    )
