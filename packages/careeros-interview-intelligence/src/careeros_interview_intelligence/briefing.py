"""Timed interview briefings: 48h (research checklist), 24h (question
prep), 2h (one-page briefing) before the interview.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from careeros_career_brain import CareerBrain
from careeros_career_brain_engine import rank_achievements_for_text
from careeros_interview_intelligence.research import CompanyResearch


class BriefingStage(StrEnum):
    RESEARCH_CHECKLIST = "research_checklist"  # 48h
    QUESTION_PREP = "question_prep"  # 24h
    ONE_PAGE_BRIEFING = "one_page_briefing"  # 2h


_RESEARCH_CHECKLIST_ITEMS = [
    "Business model",
    "Products",
    "Competitors",
    "Recent developments (funding, launches, news)",
    "Marketing / brand positioning",
    "Website / product experience",
    "Interviewer backgrounds",
]


@dataclass
class ResearchChecklist:
    company_name: str
    items: list[str]
    completed_items: list[str]

    @property
    def is_complete(self) -> bool:
        return set(self.items) <= set(self.completed_items)


def generate_research_checklist(
    company_name: str, research: CompanyResearch | None
) -> ResearchChecklist:
    completed = []
    if research is not None:
        if research.business_model:
            completed.append("Business model")
        if research.products:
            completed.append("Products")
        if research.competitors:
            completed.append("Competitors")
        if research.recent_developments:
            completed.append("Recent developments (funding, launches, news)")
        if research.marketing_notes:
            completed.append("Marketing / brand positioning")
        if research.website_notes:
            completed.append("Website / product experience")
        if research.interviewer_backgrounds:
            completed.append("Interviewer backgrounds")
    return ResearchChecklist(
        company_name=company_name, items=list(_RESEARCH_CHECKLIST_ITEMS), completed_items=completed
    )


@dataclass
class OnePageBriefing:
    company_name: str
    job_title: str
    strongest_achievements: list[str] = field(default_factory=list)
    questions_to_ask: list[str] = field(default_factory=list)
    compensation_strategy: str = ""
    things_to_avoid: list[str] = field(default_factory=list)


_THINGS_TO_AVOID = [
    "Do not claim experience, skills, or achievements that aren't in your real record.",
    "Avoid badmouthing previous employers.",
    "Don't guess on technical questions you don't know — say how you'd find out instead.",
    "Avoid discussing compensation before the interviewer raises it, unless asked directly.",
]

_DEFAULT_QUESTIONS_TO_ASK = [
    "What does success look like in this role after the first 90 days?",
    "What's the biggest challenge facing the team right now?",
    "How is performance evaluated here?",
]


def generate_one_page_briefing(
    brain: CareerBrain,
    *,
    job_title: str,
    company_name: str,
    job_description: str = "",
    research: CompanyResearch | None = None,
    min_salary: int | None = None,
) -> OnePageBriefing:
    achievements = rank_achievements_for_text(brain, f"{job_title} {job_description}", top_k=3)
    strongest = []
    for ranked in achievements:
        text = ranked.achievement.description
        if ranked.achievement.metric:
            text += f" ({ranked.achievement.metric})"
        strongest.append(text)

    questions_to_ask = list(_DEFAULT_QUESTIONS_TO_ASK)
    if research is not None and research.recent_developments:
        questions_to_ask.append(
            f"I saw {research.recent_developments[0]} — how has that shaped the team's priorities?"
        )

    if min_salary is not None:
        compensation_strategy = (
            f"Your stated minimum is ${min_salary:,}. Let the interviewer name a number "
            "first if possible; if pressed, give a range anchored above your minimum."
        )
    else:
        compensation_strategy = (
            "No minimum salary set in your preferences — set one before your next interview."
        )

    return OnePageBriefing(
        company_name=company_name,
        job_title=job_title,
        strongest_achievements=strongest,
        questions_to_ask=questions_to_ask,
        compensation_strategy=compensation_strategy,
        things_to_avoid=list(_THINGS_TO_AVOID),
    )


def render_one_page_briefing(briefing: OnePageBriefing) -> str:
    lines = [f"{briefing.job_title} at {briefing.company_name}", ""]
    lines.append("STRONGEST ACHIEVEMENTS TO MENTION")
    lines.extend(f"- {item}" for item in briefing.strongest_achievements)
    lines.append("")
    lines.append("QUESTIONS TO ASK")
    lines.extend(f"- {item}" for item in briefing.questions_to_ask)
    lines.append("")
    lines.append("COMPENSATION STRATEGY")
    lines.append(briefing.compensation_strategy)
    lines.append("")
    lines.append("THINGS TO AVOID")
    lines.extend(f"- {item}" for item in briefing.things_to_avoid)
    return "\n".join(lines) + "\n"
