"""Skill matching: proficiency-weighted overlap with explanation.

Richer than a plain set intersection — a skill the user rates 5/5 counts
more than one they rate 1/5, and the result explains *which* skills
matched and which were missing rather than returning a bare number.
"""

from __future__ import annotations

from dataclasses import dataclass

from careeros_career_brain import CareerBrain


@dataclass
class SkillMatchResult:
    score: float
    matched_skills: list[str]
    missing_skills: list[str]


def match_skills(brain: CareerBrain, required_skills: list[str]) -> SkillMatchResult:
    """Score how well ``brain``'s skills cover ``required_skills``, weighted by proficiency."""
    if not required_skills:
        return SkillMatchResult(score=1.0, matched_skills=[], missing_skills=[])

    proficiency_by_name = {skill.name.lower(): skill.proficiency for skill in brain.skills}

    matched: list[str] = []
    missing: list[str] = []
    weight_sum = 0.0
    for required in required_skills:
        proficiency = proficiency_by_name.get(required.lower())
        if proficiency is None:
            missing.append(required)
            continue
        matched.append(required)
        weight_sum += proficiency / 5.0

    score = weight_sum / len(required_skills)
    return SkillMatchResult(score=round(score, 3), matched_skills=matched, missing_skills=missing)


def skills_by_category(brain: CareerBrain) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for skill in brain.skills:
        grouped.setdefault(skill.category, []).append(skill.name)
    return grouped
