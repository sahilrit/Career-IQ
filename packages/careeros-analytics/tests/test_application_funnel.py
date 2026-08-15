"""Tests for compute_application_funnel."""

from __future__ import annotations

from careeros_analytics import compute_application_funnel
from careeros_career_brain import Application, ApplicationStatus, StatusChange


def _application(*history_statuses: ApplicationStatus) -> Application:
    application = Application(job_title="Engineer", company_name="Acme")
    for status in history_statuses:
        application.history.append(StatusChange(status=status))
    application.status = history_statuses[-1] if history_statuses else ApplicationStatus.DISCOVERED
    return application


def test_empty_list_gives_zero_counts_and_none_rates():
    metrics = compute_application_funnel([])
    assert metrics.discovered_count == 0
    assert metrics.response_rate is None


def test_discovered_only_application_counts_toward_discovered_but_not_applied():
    metrics = compute_application_funnel([_application(ApplicationStatus.DISCOVERED)])
    assert metrics.discovered_count == 1
    assert metrics.applied_count == 0


def test_rejected_after_interview_still_counts_as_reaching_interview():
    application = _application(
        ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEWING, ApplicationStatus.REJECTED
    )
    metrics = compute_application_funnel([application])
    assert metrics.applied_count == 1
    assert metrics.interview_count == 1
    assert metrics.interview_rate == 1.0


def test_rates_divide_by_applied_count_not_discovered_count():
    applications = [
        _application(ApplicationStatus.DISCOVERED),
        _application(ApplicationStatus.APPLIED),
        _application(ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEWING),
    ]
    metrics = compute_application_funnel(applications)
    assert metrics.discovered_count == 3
    assert metrics.applied_count == 2
    assert metrics.interview_rate == 0.5


def test_full_funnel_counts_each_stage():
    application = _application(
        ApplicationStatus.APPLIED,
        ApplicationStatus.IN_REVIEW,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.OFFER,
        ApplicationStatus.ACCEPTED,
    )
    metrics = compute_application_funnel([application])
    assert metrics.response_count == 1
    assert metrics.interview_count == 1
    assert metrics.offer_count == 1
    assert metrics.accepted_count == 1
    assert metrics.acceptance_rate == 1.0
