"""careeros_career_brain_engine: makes Career Brain intelligent instead of
merely storage — profile matching, resume-relevant achievement ranking,
experience analysis, and rule-based recommendations.
"""

from careeros_career_brain_engine.achievement_matching import (
    RankedAchievement,
    rank_achievements_for_text,
)
from careeros_career_brain_engine.experience_analysis import (
    ExperienceGap,
    SeniorityLevel,
    detect_experience_gaps,
    seniority_level,
    total_years_of_experience,
)
from careeros_career_brain_engine.profile_matching import ProfileMatch, match_profile_to_posting
from careeros_career_brain_engine.recommendations import Recommendation, generate_recommendations
from careeros_career_brain_engine.skill_matching import (
    SkillMatchResult,
    match_skills,
    skills_by_category,
)

__all__ = [
    "ExperienceGap",
    "ProfileMatch",
    "RankedAchievement",
    "Recommendation",
    "SeniorityLevel",
    "SkillMatchResult",
    "detect_experience_gaps",
    "generate_recommendations",
    "match_profile_to_posting",
    "match_skills",
    "rank_achievements_for_text",
    "seniority_level",
    "skills_by_category",
    "total_years_of_experience",
]
