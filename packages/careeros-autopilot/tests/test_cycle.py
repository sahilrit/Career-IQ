"""End-to-end autopilot cycle tests on fakes: a submittable form gets
autonomously applied to; captchas and login walls hand off instead."""

from __future__ import annotations

import pytest

from careeros_autopilot import run_autopilot_cycle
from careeros_autopilot.cycle import RUN_ENTITY_TYPE
from careeros_browser import FakeBrowserSession
from careeros_career_brain import (
    ApplicationStatus,
    CareerBrain,
    CareerBrainRepository,
    Identity,
    Preferences,
    Skill,
)
from careeros_common import DocumentStore
from careeros_job_providers import (
    JobPosting,
    JobProvider,
    JobProviderRegistry,
    JobSearchQuery,
    JobSearchResult,
)

POSTING = JobPosting(
    source_provider="fake",
    external_id="1",
    title="Performance Marketing Manager",
    company_name="Acme DTC",
    url="https://jobs.example.com/pm-manager",
    remote=True,
    tags=["marketing"],
    description="Own performance marketing and Meta Ads.",
)


class FakeProvider(JobProvider):
    @property
    def provider_id(self) -> str:
        return "fake"

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        return JobSearchResult(postings=[POSTING])


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def registry():
    provider_registry = JobProviderRegistry()
    provider_registry.register(FakeProvider())
    return provider_registry


@pytest.fixture
def brain(store):
    career_brain = CareerBrain(
        identity=Identity(full_name="Sahil Sachdeva", email="sahil@example.com"),
        skills=[Skill(name="Marketing"), Skill(name="Meta Ads")],
        preferences=Preferences(desired_titles=["Marketing"], remote_only=True),
    )
    CareerBrainRepository(store).save(career_brain)
    return career_brain


def form_session() -> FakeBrowserSession:
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("input[autocomplete='name']")
    session.set_visible("button[type='submit']")
    from careeros_autopilot.page_analysis import GENERIC_SUCCESS_SELECTOR

    session.set_visible(GENERIC_SUCCESS_SELECTOR)
    return session


def run(store, registry, session, tmp_path):
    return run_autopilot_cycle(
        store,
        provider_registry=registry,
        keywords=["marketing"],
        seconds_between_actions=0,
        work_dir=tmp_path,
        browser_session=session,
    )


def test_autonomously_submits_a_qualified_application(store, registry, brain, tmp_path):
    session = form_session()
    report = run(store, registry, session, tmp_path)

    assert report["discovered"] == 1
    assert report["submitted"] == 1
    assert report["outcomes"][0]["submitted"] is True
    assert session.field_value("input[type='email']") == "sahil@example.com"
    assert session.field_value("input[autocomplete='name']") == "Sahil Sachdeva"
    assert "button[type='submit']" in session.clicked_selectors

    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.APPLIED


def test_run_report_is_persisted(store, registry, brain, tmp_path):
    run(store, registry, form_session(), tmp_path)
    runs = store.list(RUN_ENTITY_TYPE)
    assert len(runs) == 1
    assert runs[0]["submitted"] == 1


def test_captcha_hands_off_instead_of_submitting(store, registry, brain, tmp_path):
    session = form_session()
    session.set_visible("iframe[src*='recaptcha']")
    report = run(store, registry, session, tmp_path)

    assert report["submitted"] == 0
    assert "captcha" in report["outcomes"][0]["reason"].lower()
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_login_wall_hands_off_instead_of_submitting(store, registry, brain, tmp_path):
    session = form_session()
    session.set_visible("input[type='password']")
    report = run(store, registry, session, tmp_path)

    assert report["submitted"] == 0
    assert "password" in report["outcomes"][0]["reason"].lower()


def test_no_form_found_is_reported_not_submitted(store, registry, brain, tmp_path):
    report = run(store, registry, FakeBrowserSession(), tmp_path)
    assert report["submitted"] == 0
    assert "no application form" in report["outcomes"][0]["reason"]


def test_second_cycle_does_not_resubmit(store, registry, brain, tmp_path):
    run(store, registry, form_session(), tmp_path)
    second = run(store, registry, form_session(), tmp_path)
    assert second["submitted"] == 0
    assert second["qualified_total"] == 0
