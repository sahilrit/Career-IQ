"""Tests for record_outcome."""

from __future__ import annotations

import pytest

from careeros_application_intelligence import record_outcome
from careeros_career_brain import (
    Application,
    ApplicationStatus,
    CareerBrainRepository,
    InvalidStatusTransitionError,
)
from careeros_common import DocumentStore
from careeros_event_bus import EventBus


@pytest.fixture
def repository():
    with DocumentStore() as store:
        yield CareerBrainRepository(store)


@pytest.fixture
def event_bus():
    return EventBus()


def _applied_application() -> Application:
    app = Application(job_title="Engineer", company_name="Acme")
    app.transition_to(ApplicationStatus.QUALIFIED)
    app.transition_to(ApplicationStatus.APPLIED)
    return app


def test_record_outcome_transitions_status_and_persists(repository, event_bus, brain_factory):
    application = _applied_application()
    brain = brain_factory(applications=[application])
    repository.save(brain)

    record_outcome(
        repository, event_bus, brain, application, ApplicationStatus.REJECTED, reason="no fit"
    )

    reloaded = repository.load(brain.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.REJECTED
    assert reloaded.applications[0].history[-1].note == "no fit"


def test_record_outcome_publishes_an_event(repository, event_bus, brain_factory):
    application = _applied_application()
    application.transition_to(ApplicationStatus.IN_REVIEW)
    application.transition_to(ApplicationStatus.INTERVIEWING)
    brain = brain_factory(applications=[application])
    repository.save(brain)

    record_outcome(repository, event_bus, brain, application, ApplicationStatus.OFFER)

    events = [e for e in event_bus.history() if e.event_type == "outcome.recorded"]
    assert len(events) == 1
    assert events[0].payload["final_status"] == "offer"
    assert events[0].payload["company_name"] == "Acme"


def test_record_outcome_rejects_invalid_transitions(repository, event_bus, brain_factory):
    application = Application(job_title="Engineer", company_name="Acme")  # still DISCOVERED
    brain = brain_factory(applications=[application])
    repository.save(brain)

    with pytest.raises(InvalidStatusTransitionError):
        record_outcome(repository, event_bus, brain, application, ApplicationStatus.ACCEPTED)
