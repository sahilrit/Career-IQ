"""Tests for AutonomousApplicationExecutor: the full autonomous loop."""

from __future__ import annotations

from careeros_autonomous_execution import AutonomousApplicationExecutor
from careeros_autonomy import (
    AuthorizationEngine,
    AutonomyMode,
    AutonomyPolicy,
    DecisionMemory,
    PacingLimiter,
)
from careeros_career_brain import ApplicationStatus
from careeros_human_in_the_loop import SelectorAppearsDetector


def _executor(
    repository, autonomy_policy, application_runner, event_bus, posting, form_mapping
) -> AutonomousApplicationExecutor:
    return AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: posting,
        resolve_form_mapping=lambda application: form_mapping,
    )


def test_qualified_application_is_submitted_and_transitioned_to_applied(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    session.set_visible(form_mapping.submit_selector)
    session.set_visible(form_mapping.success_selector)
    executor = _executor(
        repository, autonomy_policy, application_runner, event_bus, posting, form_mapping
    )

    run = executor.run_for_identity(brain_with_qualified_application.identity.id, session)

    assert run.submitted_count == 1
    reloaded = repository.load(brain_with_qualified_application.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.APPLIED


def test_submission_publishes_the_autonomously_submitted_event(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    session.set_visible(form_mapping.submit_selector)
    session.set_visible(form_mapping.success_selector)
    executor = _executor(
        repository, autonomy_policy, application_runner, event_bus, posting, form_mapping
    )

    executor.run_for_identity(brain_with_qualified_application.identity.id, session)

    event_type = "application.autonomously_submitted"
    events = [e for e in event_bus.history() if e.event_type == event_type]
    assert len(events) == 1


def test_manual_mode_never_submits_anything(
    repository,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    store,
    brain_with_qualified_application,
):
    manual_policy = AutonomyPolicy(
        mode=AutonomyMode.MANUAL,
        engine=AuthorizationEngine(),
        pacing=PacingLimiter(0.0),
        decision_memory=DecisionMemory(store),
        event_bus=event_bus,
    )
    session.set_visible(form_mapping.submit_selector)
    session.set_visible(form_mapping.success_selector)
    executor = _executor(
        repository, manual_policy, application_runner, event_bus, posting, form_mapping
    )

    run = executor.run_for_identity(brain_with_qualified_application.identity.id, session)

    assert run.submitted_count == 0
    assert session.clicked_selectors == []
    reloaded = repository.load(brain_with_qualified_application.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_missing_posting_is_reported_and_nothing_is_submitted(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    form_mapping,
    brain_with_qualified_application,
):
    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: None,
        resolve_form_mapping=lambda application: form_mapping,
    )

    run = executor.run_for_identity(brain_with_qualified_application.identity.id, session)

    assert run.submitted_count == 0
    assert "No original posting" in run.outcomes[0].reason


def test_missing_form_mapping_is_reported_and_nothing_is_submitted(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    brain_with_qualified_application,
):
    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: posting,
        resolve_form_mapping=lambda application: None,
    )

    run = executor.run_for_identity(brain_with_qualified_application.identity.id, session)

    assert run.submitted_count == 0
    assert "No form mapping" in run.outcomes[0].reason


def test_detected_problem_hands_off_instead_of_submitting(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    session.set_visible("#captcha")
    session.set_visible(form_mapping.submit_selector)
    executor = _executor(
        repository, autonomy_policy, application_runner, event_bus, posting, form_mapping
    )
    detectors = [SelectorAppearsDetector("#captcha", kind="captcha")]

    run = executor.run_for_identity(
        brain_with_qualified_application.identity.id, session, detectors=detectors
    )

    assert run.submitted_count == 0
    assert "Handed off" in run.outcomes[0].reason
    assert session.clicked_selectors == []


def test_submission_failure_hands_off_and_leaves_application_qualified(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    session.set_visible(form_mapping.submit_selector)
    # success_selector never becomes visible: ApplicationRunner retries then fails
    executor = _executor(
        repository, autonomy_policy, application_runner, event_bus, posting, form_mapping
    )

    run = executor.run_for_identity(brain_with_qualified_application.identity.id, session)

    assert run.submitted_count == 0
    assert "handed off" in run.outcomes[0].reason.lower()
    reloaded = repository.load(brain_with_qualified_application.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_no_arbitrary_cap_processes_every_qualified_application_in_one_run(
    repository, autonomy_policy, application_runner, event_bus, session
):
    from careeros_application_runner import FormFieldMapping
    from careeros_career_brain import Application, ApplicationStatus, CareerBrain, Identity
    from careeros_job_providers import JobPosting

    def make_application(**overrides):
        application = Application(match_score=0.9, **overrides)
        application.transition_to(ApplicationStatus.QUALIFIED)
        return application

    applications = [
        make_application(
            job_title=f"Engineer {i}",
            company_name=f"Company {i}",
            job_url=f"https://example.com/jobs/{i}",
        )
        for i in range(5)
    ]
    brain = CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
        applications=applications,
    )
    repository.save(brain)

    postings_by_url = {
        app.job_url: JobPosting(
            source_provider="remoteok",
            external_id=str(i),
            title=app.job_title,
            company_name=app.company_name,
            url=app.job_url,
        )
        for i, app in enumerate(applications)
    }
    mapping = FormFieldMapping(submit_selector="#submit", success_selector="#success")
    session.set_visible(mapping.submit_selector)
    session.set_visible(mapping.success_selector)

    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: postings_by_url[application.job_url],
        resolve_form_mapping=lambda application: mapping,
    )

    run = executor.run_for_identity(brain.identity.id, session)

    assert run.submitted_count == 5
