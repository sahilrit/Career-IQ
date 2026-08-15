"""Recruiter outreach: a templated message to a recruiter about a
specific opportunity, mirroring careeros_application_engine's
cover-letter pattern (Phase 12). Deterministic, sourced only from real
Career Brain data.
"""

from __future__ import annotations

from typing import Protocol

from careeros_career_brain import CareerBrain, Recruiter
from careeros_career_brain_engine import match_skills
from careeros_job_providers import JobPosting

_TEMPLATE = """Hi {recruiter_name},

I saw the {title} opening at {company} and wanted to reach out directly. {opening}

I'd welcome the chance to talk about the role.

Best,
{full_name}
"""


class RecruiterOutreachGenerator(Protocol):
    def generate(self, brain: CareerBrain, recruiter: Recruiter, posting: JobPosting) -> str: ...


class TemplateRecruiterOutreachGenerator:
    def generate(self, brain: CareerBrain, recruiter: Recruiter, posting: JobPosting) -> str:
        skill_result = match_skills(brain, posting.tags)
        # match_skills echoes the posting's own tag casing (often
        # lowercase); resolve back to the user's own skill casing rather
        # than quoting the posting verbatim in outreach copy.
        matched_lower = {name.lower() for name in skill_result.matched_skills}
        properly_cased = [
            skill.name for skill in brain.skills if skill.name.lower() in matched_lower
        ]
        if properly_cased:
            skills = ", ".join(properly_cased)
            opening = f"My background in {skills} lines up well with what you're looking for."
        else:
            opening = "I think my background could be a strong fit."

        rendered = _TEMPLATE.format(
            recruiter_name=recruiter.full_name,
            title=posting.title,
            company=posting.company_name,
            opening=opening,
            full_name=brain.identity.full_name,
        )
        return rendered.strip() + "\n"
