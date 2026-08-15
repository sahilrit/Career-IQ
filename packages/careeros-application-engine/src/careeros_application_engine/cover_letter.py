"""Cover letter generation.

A ``CoverLetterGenerator`` protocol lets a future AI-backed plugin
generate richer prose; ``TemplateCoverLetterGenerator`` is the default,
zero-cost implementation — a template filled entirely from Career Brain
and posting data, never fabricated content.
"""

from __future__ import annotations

from typing import Protocol

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine import ProfileMatch, match_profile_to_posting
from careeros_job_providers import JobPosting

_TEMPLATE = """Dear Hiring Team at {company},

I'm writing to apply for the {title} role. {opening}

{body}

{closing}

Sincerely,
{full_name}
"""


class CoverLetterGenerator(Protocol):
    def generate(self, brain: CareerBrain, posting: JobPosting) -> str: ...


class TemplateCoverLetterGenerator:
    """Deterministic, template-based cover letter — no LLM required."""

    def generate(self, brain: CareerBrain, posting: JobPosting) -> str:
        match = match_profile_to_posting(brain, posting)
        rendered = _TEMPLATE.format(
            company=posting.company_name,
            title=posting.title,
            opening=self._opening(brain),
            body=self._body(match),
            closing=self._closing(),
            full_name=brain.identity.full_name,
        )
        return rendered.strip() + "\n"

    def _opening(self, brain: CareerBrain) -> str:
        current = brain.current_experience
        if current is not None:
            return (
                f"As {current.title} at {current.company_name}, I've built directly "
                "relevant experience for this position."
            )
        return "I believe my background makes me a strong fit for this position."

    def _body(self, match: ProfileMatch) -> str:
        sentences = []
        if match.skill_match.matched_skills:
            skills = ", ".join(match.skill_match.matched_skills)
            sentences.append(f"My skills include {skills}.")
        for ranked in match.top_achievements:
            sentence = ranked.achievement.description
            if ranked.achievement.metric:
                sentence += f" ({ranked.achievement.metric})"
            sentences.append(sentence + ".")
        if not sentences:
            return "I'm eager to bring my experience to your team."
        return " ".join(sentences)

    def _closing(self) -> str:
        return (
            "I'd welcome the chance to discuss how I can contribute. "
            "Thank you for your time and consideration."
        )
