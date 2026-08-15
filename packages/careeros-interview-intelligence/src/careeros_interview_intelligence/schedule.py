"""BriefingMilestone: computes which timed briefing (48h/24h/2h before an
interview) is due right now.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

from careeros_calendar_assistant import CalendarEvent
from careeros_interview_intelligence.briefing import BriefingStage


class BriefingMilestone(StrEnum):
    H48 = "48h"
    H24 = "24h"
    H2 = "2h"


_MILESTONE_ORDER = [BriefingMilestone.H48, BriefingMilestone.H24, BriefingMilestone.H2]

_MILESTONE_OFFSETS: dict[BriefingMilestone, timedelta] = {
    BriefingMilestone.H48: timedelta(hours=48),
    BriefingMilestone.H24: timedelta(hours=24),
    BriefingMilestone.H2: timedelta(hours=2),
}

_MILESTONE_STAGE: dict[BriefingMilestone, BriefingStage] = {
    BriefingMilestone.H48: BriefingStage.RESEARCH_CHECKLIST,
    BriefingMilestone.H24: BriefingStage.QUESTION_PREP,
    BriefingMilestone.H2: BriefingStage.ONE_PAGE_BRIEFING,
}


def stage_for_milestone(milestone: BriefingMilestone) -> BriefingStage:
    return _MILESTONE_STAGE[milestone]


def due_milestones(
    event: CalendarEvent, *, now: datetime, already_fired: set[BriefingMilestone]
) -> list[BriefingMilestone]:
    """Milestones whose trigger time has passed and haven't fired yet,
    ordered earliest-offset (48h) first.
    """
    if event.scheduled_at is None:
        return []

    due = []
    for milestone, offset in _MILESTONE_OFFSETS.items():
        if milestone in already_fired:
            continue
        trigger_at = event.scheduled_at - offset
        if now >= trigger_at:
            due.append(milestone)
    return sorted(due, key=_MILESTONE_ORDER.index)
