"""Tests for run_due_briefings: the full timed pipeline end-to-end."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from careeros_calendar_assistant import (
    CalendarEventRepository,
    EventWorkspace,
    EventWorkspaceRepository,
    InterviewDetails,
    build_calendar_event,
)
from careeros_career_brain import Application
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_interview_intelligence import (
    BriefingMilestone,
    BriefingStage,
    BriefingTracker,
    ManualCompanyResearchProvider,
    run_due_briefings,
)

_INTERVIEW_AT = datetime(2026, 1, 10, 14, 0, tzinfo=UTC)


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def repos(store):
    return (
        CalendarEventRepository(store),
        EventWorkspaceRepository(store),
        ManualCompanyResearchProvider(store),
        BriefingTracker(store),
    )


def _seed_event(
    brain_factory, calendar_repo, workspace_repo, *, application_id: str | None = "app-1"
):
    brain = brain_factory(
        applications=[
            Application(id="app-1", job_title="Backend Engineer", company_name="Widget Co")
        ]
    )
    details = InterviewDetails(scheduled_at=_INTERVIEW_AT)
    event = build_calendar_event("Technical interview", details, application_id=application_id)
    calendar_repo.save(event)
    # Job description shares vocabulary with the seeded achievement so
    # rank_achievements_for_text's TF-IDF matching has something to find —
    # it only ranks by shared terms, not semantic understanding.
    workspace_repo.save(
        EventWorkspace(
            calendar_event_id=event.id,
            job_description="Own our Shopify checkout experience end to end.",
        )
    )
    return brain, event


def test_no_briefings_generated_far_before_the_interview(brain_factory, repos):
    calendar_repo, workspace_repo, research_provider, tracker = repos
    brain, _event = _seed_event(brain_factory, calendar_repo, workspace_repo)
    bus = EventBus()

    now = _INTERVIEW_AT - timedelta(hours=72)
    result = run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )

    assert result == []


def test_48h_briefing_uses_the_real_company_and_job_title_from_the_application(
    brain_factory, repos
):
    calendar_repo, workspace_repo, research_provider, tracker = repos
    brain, _event = _seed_event(brain_factory, calendar_repo, workspace_repo)
    bus = EventBus()

    now = _INTERVIEW_AT - timedelta(hours=48)
    result = run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )

    assert len(result) == 1
    assert result[0].stage == BriefingStage.RESEARCH_CHECKLIST
    assert result[0].content.company_name == "Widget Co"


def test_all_three_stages_fire_in_order_just_before_the_interview(brain_factory, repos):
    calendar_repo, workspace_repo, research_provider, tracker = repos
    brain, _event = _seed_event(brain_factory, calendar_repo, workspace_repo)
    bus = EventBus()

    now = _INTERVIEW_AT - timedelta(hours=1)
    result = run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )

    stages = [r.stage for r in result]
    assert stages == [
        BriefingStage.RESEARCH_CHECKLIST,
        BriefingStage.QUESTION_PREP,
        BriefingStage.ONE_PAGE_BRIEFING,
    ]


def test_one_page_briefing_uses_the_real_achievement(brain_factory, repos):
    calendar_repo, workspace_repo, research_provider, tracker = repos
    brain, _event = _seed_event(brain_factory, calendar_repo, workspace_repo)
    bus = EventBus()

    now = _INTERVIEW_AT - timedelta(hours=1)
    result = run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )

    one_pager = next(r for r in result if r.stage == BriefingStage.ONE_PAGE_BRIEFING)
    assert any("Shopify checkout" in item for item in one_pager.content.strongest_achievements)


def test_a_milestone_never_fires_twice(brain_factory, repos):
    calendar_repo, workspace_repo, research_provider, tracker = repos
    brain, _event = _seed_event(brain_factory, calendar_repo, workspace_repo)
    bus = EventBus()

    now = _INTERVIEW_AT - timedelta(hours=48)
    first = run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )
    second = run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )

    assert len(first) == 1
    assert second == []


def test_events_are_published_for_every_generated_briefing(brain_factory, repos):
    calendar_repo, workspace_repo, research_provider, tracker = repos
    brain, _event = _seed_event(brain_factory, calendar_repo, workspace_repo)
    bus = EventBus()

    now = _INTERVIEW_AT - timedelta(hours=1)
    run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )

    events = [e for e in bus.history() if e.event_type == "interview.briefing_generated"]
    assert len(events) == 3
    assert {e.payload["milestone"] for e in events} == {"48h", "24h", "2h"}


def test_event_without_an_application_falls_back_to_the_calendar_event_title(brain_factory, repos):
    calendar_repo, workspace_repo, research_provider, tracker = repos
    brain, _event = _seed_event(brain_factory, calendar_repo, workspace_repo, application_id=None)
    bus = EventBus()

    now = _INTERVIEW_AT - timedelta(hours=48)
    result = run_due_briefings(
        brain, calendar_repo, workspace_repo, research_provider, tracker, bus, now=now
    )

    assert result[0].content.company_name == "Unknown Company"


def test_milestone_enum_values_are_stable():
    assert BriefingMilestone.H48.value == "48h"
    assert BriefingMilestone.H24.value == "24h"
    assert BriefingMilestone.H2.value == "2h"
