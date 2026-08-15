"""Tests for the Career Brain analytics helpers."""

from __future__ import annotations

from careeros_career_brain import Application, ApplicationStatus, CareerBrain, Identity
from careeros_memory import applications_by_status, interview_rate, offer_rate, response_rate


def _brain_with(applications: list[Application]) -> CareerBrain:
    return CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
        applications=applications,
    )


def _applied_app() -> Application:
    app = Application(job_title="Engineer", company_name="Acme")
    app.transition_to(ApplicationStatus.QUALIFIED)
    app.transition_to(ApplicationStatus.APPLIED)
    return app


def test_applications_by_status_counts_current_status_only():
    app = _applied_app()
    brain = _brain_with([app])
    counts = applications_by_status(brain)
    assert counts[ApplicationStatus.APPLIED.value] == 1
    assert counts[ApplicationStatus.DISCOVERED.value] == 0


def test_rates_are_zero_with_no_applications():
    brain = _brain_with([])
    assert response_rate(brain) == 0.0
    assert interview_rate(brain) == 0.0
    assert offer_rate(brain) == 0.0


def test_response_rate_counts_applications_that_reached_review():
    reviewed = _applied_app()
    reviewed.transition_to(ApplicationStatus.IN_REVIEW)
    not_yet_reviewed = _applied_app()

    brain = _brain_with([reviewed, not_yet_reviewed])
    assert response_rate(brain) == 0.5


def test_interview_and_offer_rate_follow_the_funnel():
    got_offer = _applied_app()
    got_offer.transition_to(ApplicationStatus.IN_REVIEW)
    got_offer.transition_to(ApplicationStatus.INTERVIEWING)
    got_offer.transition_to(ApplicationStatus.OFFER)

    only_interviewed = _applied_app()
    only_interviewed.transition_to(ApplicationStatus.IN_REVIEW)
    only_interviewed.transition_to(ApplicationStatus.INTERVIEWING)
    only_interviewed.transition_to(ApplicationStatus.REJECTED)

    brain = _brain_with([got_offer, only_interviewed])
    assert interview_rate(brain) == 1.0
    assert offer_rate(brain) == 0.5


def test_discovered_only_applications_do_not_count_as_applied():
    discovered = Application(job_title="Engineer", company_name="Acme")
    brain = _brain_with([discovered])
    assert response_rate(brain) == 0.0
