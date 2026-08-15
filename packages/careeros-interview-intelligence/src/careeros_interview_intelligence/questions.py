"""Generates interview questions to prepare for — role-specific,
technical, company-specific, and STAR prompts tied to real achievements
from Career Brain. Deterministic templates, not a fabricated Q&A bank —
every STAR prompt points back to something genuinely in the user's
record.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine import rank_achievements_for_text
from careeros_interview_intelligence.research import CompanyResearch

_ROLE_SPECIFIC_TEMPLATES = [
    "Why are you interested in this role?",
    "What does a typical day in this role look like to you, and how does your "
    "background prepare you for it?",
    "Where do you see this role fitting into your longer-term goals?",
]

_TECHNICAL_TEMPLATE = "Walk me through how you've used {skill} in a real project."

_COMPANY_SPECIFIC_TEMPLATES = [
    "Why do you want to work at {company}?",
    "What do you think {company} could be doing better?",
]

_STAR_PROMPT_TEMPLATE = "Tell me about a time you {description}"


@dataclass
class STARPrompt:
    question: str
    achievement_description: str
    metric: str | None


@dataclass
class InterviewQuestions:
    role_specific: list[str] = field(default_factory=list)
    technical: list[str] = field(default_factory=list)
    company_specific: list[str] = field(default_factory=list)
    star_prompts: list[STARPrompt] = field(default_factory=list)


def _lowercase_first(text: str) -> str:
    return text[0].lower() + text[1:] if text else text


def generate_questions(
    brain: CareerBrain,
    *,
    job_title: str,
    company_name: str,
    job_description: str = "",
    research: CompanyResearch | None = None,
    top_skills: int = 3,
    top_achievements: int = 3,
) -> InterviewQuestions:
    top_skill_names = [
        skill.name
        for skill in sorted(brain.skills, key=lambda s: s.proficiency, reverse=True)[:top_skills]
    ]
    technical = [_TECHNICAL_TEMPLATE.format(skill=skill) for skill in top_skill_names]

    company_specific = [
        template.format(company=company_name) for template in _COMPANY_SPECIFIC_TEMPLATES
    ]
    if research is not None and research.competitors:
        company_specific.append(
            f"How do you see {company_name} differentiating from {research.competitors[0]}?"
        )

    achievements = rank_achievements_for_text(
        brain, f"{job_title} {job_description}", top_k=top_achievements
    )
    star_prompts = [
        STARPrompt(
            question=_STAR_PROMPT_TEMPLATE.format(
                description=_lowercase_first(ranked.achievement.description)
            ),
            achievement_description=ranked.achievement.description,
            metric=ranked.achievement.metric,
        )
        for ranked in achievements
    ]

    return InterviewQuestions(
        role_specific=list(_ROLE_SPECIFIC_TEMPLATES),
        technical=technical,
        company_specific=company_specific,
        star_prompts=star_prompts,
    )
