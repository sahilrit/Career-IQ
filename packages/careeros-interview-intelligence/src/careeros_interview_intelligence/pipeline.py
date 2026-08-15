"""Orchestrates the full timed briefing pipeline against every upcoming
calendar event with a scheduled interview.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from careeros_calendar_assistant import CalendarEventRepository, EventWorkspaceRepository
from careeros_career_brain import CareerBrain
from careeros_event_bus import Event, EventBus
from careeros_interview_intelligence.briefing import (
    BriefingStage,
    generate_one_page_briefing,
    generate_research_checklist,
)
from careeros_interview_intelligence.questions import generate_questions
from careeros_interview_intelligence.research import CompanyResearchProvider
from careeros_interview_intelligence.schedule import (
    BriefingMilestone,
    due_milestones,
    stage_for_milestone,
)
from careeros_interview_intelligence.tracker import BriefingTracker


@dataclass
class GeneratedBriefing:
    calendar_event_id: str
    milestone: BriefingMilestone
    stage: BriefingStage
    content: Any


def run_due_briefings(
    brain: CareerBrain,
    calendar_repo: CalendarEventRepository,
    workspace_repo: EventWorkspaceRepository,
    research_provider: CompanyResearchProvider,
    tracker: BriefingTracker,
    event_bus: EventBus,
    *,
    now: datetime | None = None,
) -> list[GeneratedBriefing]:
    now = now or datetime.now(UTC)
    generated: list[GeneratedBriefing] = []

    for event in calendar_repo.list_all():
        fired = tracker.fired_milestones(event.id)
        milestones = due_milestones(event, now=now, already_fired=fired)
        if not milestones:
            continue

        application = brain.find_application(event.application_id) if event.application_id else None
        company_name = application.company_name if application else "Unknown Company"
        job_title = application.job_title if application else event.title

        research = research_provider.get(event.id)
        workspace = workspace_repo.for_calendar_event(event.id)
        job_description = workspace.job_description if workspace else ""

        for milestone in milestones:
            stage = stage_for_milestone(milestone)
            if stage == BriefingStage.RESEARCH_CHECKLIST:
                content = generate_research_checklist(company_name, research)
            elif stage == BriefingStage.QUESTION_PREP:
                content = generate_questions(
                    brain,
                    job_title=job_title,
                    company_name=company_name,
                    job_description=job_description,
                    research=research,
                )
            else:
                content = generate_one_page_briefing(
                    brain,
                    job_title=job_title,
                    company_name=company_name,
                    job_description=job_description,
                    research=research,
                    min_salary=brain.preferences.min_salary,
                )

            tracker.mark_fired(event.id, milestone)
            generated.append(GeneratedBriefing(event.id, milestone, stage, content))
            event_bus.publish(
                Event(
                    event_type="interview.briefing_generated",
                    source="interview-intelligence",
                    payload={
                        "subject_id": event.id,
                        "milestone": milestone.value,
                        "stage": stage.value,
                    },
                )
            )

    return generated
