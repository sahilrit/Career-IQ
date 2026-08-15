"""Tests for the EmploymentDivision facade."""

from __future__ import annotations

import pytest

from careeros_career_brain import Application, Recruiter
from careeros_employment_division import (
    EmploymentDivision,
    PipelineProgressRepository,
    PipelineStage,
)
from careeros_event_bus import Event, EventBus


@pytest.fixture
def division(store):
    return EmploymentDivision(PipelineProgressRepository(store))


def test_build_portfolio_delegates_to_the_generator(division, brain):
    summary = division.build_portfolio(brain)
    assert summary.full_name == "Ada Lovelace"


def test_draft_recruiter_outreach_delegates_to_the_generator(division, brain, posting):
    message = division.draft_recruiter_outreach(brain, Recruiter(full_name="Jane Smith"), posting)
    assert "Jane Smith" in message


def test_draft_follow_up_delegates_to_the_generator(division):
    application = Application(job_title="Engineer", company_name="Acme")
    message = division.draft_follow_up(application, days_since_applied=3)
    assert "3 days" in message


def test_mark_methods_advance_progress(division):
    division.mark_research_done("app-1")
    division.mark_resume_done("app-1")
    progress = division.progress_for("app-1")
    assert progress.current_stage == PipelineStage.RESUME


def test_wire_events_hooks_the_facades_own_repository(store):
    progress_repository = PipelineProgressRepository(store)
    division = EmploymentDivision(progress_repository)
    bus = EventBus()

    EmploymentDivision.wire_events(bus, progress_repository)
    bus.publish(Event(event_type="application.created", payload={"subject_id": "app-1"}))

    assert division.progress_for("app-1").current_stage == PipelineStage.DISCOVERY
