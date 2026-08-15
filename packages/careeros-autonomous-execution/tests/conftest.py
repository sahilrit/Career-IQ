"""Shared fixtures for autonomous execution tests."""

from __future__ import annotations

import pytest

from careeros_application_runner import ApplicationRunner, FormFieldMapping
from careeros_autonomy import (
    AuthorizationEngine,
    AutonomyMode,
    AutonomyPolicy,
    DecisionMemory,
    PacingLimiter,
)
from careeros_browser import FakeBrowserSession
from careeros_career_brain import (
    Application,
    ApplicationStatus,
    CareerBrain,
    CareerBrainRepository,
    Identity,
)
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_job_providers import JobPosting


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def repository(store):
    return CareerBrainRepository(store)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def autonomy_policy(store, event_bus):
    return AutonomyPolicy(
        mode=AutonomyMode.FULL_AUTONOMOUS,
        engine=AuthorizationEngine(),
        pacing=PacingLimiter(0.0),
        decision_memory=DecisionMemory(store),
        event_bus=event_bus,
    )


@pytest.fixture
def application_runner():
    return ApplicationRunner(screenshot_dir="/tmp/careeros-autonomous-execution-tests")


@pytest.fixture
def session():
    return FakeBrowserSession()


def make_qualified_application(**overrides) -> Application:
    defaults = {
        "job_title": "Backend Engineer",
        "company_name": "Acme",
        "job_url": "https://example.com/jobs/1",
        "match_score": 0.9,
    }
    defaults.update(overrides)
    application = Application(**defaults)
    application.transition_to(ApplicationStatus.QUALIFIED)
    return application


@pytest.fixture
def qualified_application():
    return make_qualified_application()


@pytest.fixture
def brain_with_qualified_application(repository, qualified_application):
    brain = CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
        applications=[qualified_application],
    )
    repository.save(brain)
    return brain


def make_posting(**overrides) -> JobPosting:
    defaults = {
        "source_provider": "remoteok",
        "external_id": "1",
        "title": "Backend Engineer",
        "company_name": "Acme",
        "url": "https://example.com/jobs/1",
        "tags": ["python"],
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


@pytest.fixture
def posting():
    return make_posting()


@pytest.fixture
def form_mapping():
    return FormFieldMapping(submit_selector="#submit", success_selector="#success")
