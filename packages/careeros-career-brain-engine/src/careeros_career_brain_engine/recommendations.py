"""Rule-based career recommendations from Career Brain completeness checks.

Plain, explainable rules — not ML — flagging gaps the user can act on.
Each recommendation names *why* it fired so it stays useful as more rules
are added later.
"""

from __future__ import annotations

from dataclasses import dataclass

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine.experience_analysis import detect_experience_gaps


@dataclass
class Recommendation:
    code: str
    message: str


def generate_recommendations(brain: CareerBrain) -> list[Recommendation]:
    recommendations: list[Recommendation] = []

    if not brain.identity.headline:
        recommendations.append(
            Recommendation("missing_headline", "Add a professional headline to your identity.")
        )

    if not brain.skills:
        recommendations.append(
            Recommendation("no_skills", "No skills listed — add skills so matching can work.")
        )

    if brain.current_experience is None:
        recommendations.append(
            Recommendation(
                "no_current_experience",
                "No current role on file — add your most recent experience.",
            )
        )

    if not brain.preferences.desired_titles:
        recommendations.append(
            Recommendation(
                "no_desired_titles", "No desired titles set — this weakens job matching."
            )
        )

    missing_metrics = [
        achievement
        for experience in brain.experiences
        for achievement in experience.achievements
        if not achievement.metric
    ]
    if missing_metrics:
        recommendations.append(
            Recommendation(
                "achievements_without_metrics",
                f"{len(missing_metrics)} achievement(s) have no measurable metric "
                "(e.g. '+32% conversion') — add one to make them more persuasive.",
            )
        )

    gaps = detect_experience_gaps(brain)
    if gaps:
        recommendations.append(
            Recommendation(
                "experience_gaps",
                f"{len(gaps)} employment gap(s) of 90+ days detected — "
                "consider adding context (education, freelance work, etc.).",
            )
        )

    return recommendations
