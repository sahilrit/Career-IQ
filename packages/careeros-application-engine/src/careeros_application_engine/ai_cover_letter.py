"""AICoverLetterGenerator: same CoverLetterGenerator seam as the template
one, but the prose comes from an AIClient, grounded strictly in Career Brain."""

from __future__ import annotations

from careeros_ai import AIClient
from careeros_career_brain import CareerBrain
from careeros_job_providers import JobPosting

_SYSTEM = (
    "You write concise, specific cover letters. Use ONLY the facts provided "
    "about the candidate and role. Never invent employers, job titles, metrics, "
    "skills, or achievements. 180-260 words, professional, no placeholders."
)


class AICoverLetterGenerator:
    def __init__(self, client: AIClient) -> None:
        self._client = client

    def generate(self, brain: CareerBrain, posting: JobPosting) -> str:
        prompt = self._prompt(brain, posting)
        return self._client.complete(system=_SYSTEM, prompt=prompt).strip() + "\n"

    def _prompt(self, brain: CareerBrain, posting: JobPosting) -> str:
        identity = brain.identity
        skills = ", ".join(skill.name for skill in brain.skills) or "(none listed)"
        experiences = (
            "\n".join(f"- {exp.title} at {exp.company_name}" for exp in brain.experiences)
            or "(none listed)"
        )
        return (
            f"Candidate: {identity.full_name}\n"
            f"Headline: {identity.headline}\n"
            f"Summary: {identity.summary}\n"
            f"Skills: {skills}\n"
            f"Experience:\n{experiences}\n\n"
            f"Role: {posting.title} at {posting.company_name}\n"
            f"Job description:\n{posting.description}\n\n"
            f"Write the cover letter, signed '{identity.full_name}'."
        )
