"""Freelance proposal generation, mirroring careeros_application_engine's
cover-letter pattern (Phase 12) but for a GigPosting instead of a
JobPosting. Deterministic and template-based — no LLM required, nothing
fabricated.
"""

from __future__ import annotations

from typing import Protocol

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine import (
    RankedAchievement,
    SkillMatchResult,
    match_skills,
    rank_achievements_for_text,
)
from careeros_freelance_providers import GigPosting

_TEMPLATE = """Hi,

I'd like to propose working on "{title}". {opening}

{body}

{closing}

Best,
{full_name}
"""


class ProposalGenerator(Protocol):
    def generate(self, brain: CareerBrain, posting: GigPosting) -> str: ...


class TemplateProposalGenerator:
    """Deterministic, template-based proposal — no LLM required."""

    def generate(self, brain: CareerBrain, posting: GigPosting) -> str:
        skill_result = match_skills(brain, posting.skills_required)
        text = f"{posting.title} {posting.description}"
        top_achievements = rank_achievements_for_text(brain, text, top_k=2)

        rendered = _TEMPLATE.format(
            title=posting.title,
            opening=self._opening(skill_result),
            body=self._body(top_achievements),
            closing=self._closing(),
            full_name=brain.identity.full_name,
        )
        return rendered.strip() + "\n"

    def _opening(self, skill_result: SkillMatchResult) -> str:
        if skill_result.matched_skills:
            skills = ", ".join(skill_result.matched_skills)
            return f"My experience with {skills} lines up well with what you need."
        return "I'd love to help bring this project to life."

    def _body(self, top_achievements: list[RankedAchievement]) -> str:
        if not top_achievements:
            return "I focus on clear communication and delivering measurable results."
        sentences = []
        for ranked in top_achievements:
            sentence = ranked.achievement.description
            if ranked.achievement.metric:
                sentence += f" ({ranked.achievement.metric})"
            sentences.append(sentence + ".")
        return " ".join(sentences)

    def _closing(self) -> str:
        return "Happy to hop on a call to discuss details and timeline."
