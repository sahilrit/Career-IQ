"""Templated answers to common application questions, filled from Career
Brain and a target posting — no fabricated content, no LLM required.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine import match_profile_to_posting
from careeros_job_providers import JobPosting


def answer_why_this_role(brain: CareerBrain, posting: JobPosting) -> str:
    match = match_profile_to_posting(brain, posting)
    if match.skill_match.matched_skills:
        return (
            f"I'm drawn to the {posting.title} role at {posting.company_name} because it "
            f"lines up with my experience in {', '.join(match.skill_match.matched_skills)}."
        )
    return f"I'm drawn to the {posting.title} role at {posting.company_name}."


def answer_greatest_achievement(brain: CareerBrain, posting: JobPosting) -> str:
    match = match_profile_to_posting(brain, posting, top_k_achievements=1)
    if match.top_achievements:
        achievement = match.top_achievements[0].achievement
        text = achievement.description
        if achievement.metric:
            text += f" ({achievement.metric})"
        return text
    return "I'm proud of the consistent, measurable impact I've had across my roles."


def answer_why_you(brain: CareerBrain, posting: JobPosting) -> str:
    match = match_profile_to_posting(brain, posting)
    headline = brain.identity.headline or "a professional in this field"
    return (
        f"With a background as {headline}, I bring {match.seniority.value}-level "
        "experience directly relevant to this role."
    )


ANSWER_GENERATORS: dict[str, Callable[[CareerBrain, JobPosting], str]] = {
    "why_this_role": answer_why_this_role,
    "greatest_achievement": answer_greatest_achievement,
    "why_you": answer_why_you,
}


def generate_answers(brain: CareerBrain, posting: JobPosting) -> dict[str, str]:
    return {key: fn(brain, posting) for key, fn in ANSWER_GENERATORS.items()}
