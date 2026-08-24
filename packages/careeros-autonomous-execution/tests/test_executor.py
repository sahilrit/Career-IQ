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


def test_dry_run_reaches_the_form_but_never_submits(
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
    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: posting,
        resolve_form_mapping=lambda application: form_mapping,
        submit_enabled=False,
    )

    run = executor.run_for_identity(brain_with_qualified_application.identity.id, session)

    assert run.submitted_count == 0
    assert "DRY RUN" in run.outcomes[0].reason
    # Nothing was clicked, and the application stays QUALIFIED (not APPLIED).
    assert session.clicked_selectors == []
    reloaded = repository.load(brain_with_qualified_application.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_prepare_only_fills_a_captcha_gated_form_and_hands_off(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    # A captcha is present, and the form is reachable/fillable.
    session.set_visible("iframe[src*='recaptcha']")
    prepared: list[str] = []
    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: posting,
        resolve_form_mapping=lambda application: form_mapping,
        prepare_only=True,
        on_prepared=lambda application, post, package: prepared.append(application.id),
    )

    run = executor.run_for_identity(
        brain_with_qualified_application.identity.id,
        session,
        detectors=[SelectorAppearsDetector("iframe[src*='recaptcha']", kind="captcha")],
    )

    # The captcha did NOT block preparation — we filled and handed off.
    assert run.submitted_count == 0
    assert "Prepared for review" in run.outcomes[0].reason
    assert len(prepared) == 1
    assert session.clicked_selectors == []  # never submitted
    reloaded = repository.load(brain_with_qualified_application.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_assist_fills_and_pauses_even_on_a_clean_form(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    # No captcha, but assist no longer blind-submits — it fills and hands off,
    # because an auto-submit can't be verified. Nothing goes out unseen.
    session.set_visible(form_mapping.submit_selector)
    session.set_visible(form_mapping.success_selector)
    prepared: list[str] = []
    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: posting,
        resolve_form_mapping=lambda application: form_mapping,
        assist_captcha=True,
        on_prepared=lambda application, post, package: prepared.append(application.id),
    )

    run = executor.run_for_identity(
        brain_with_qualified_application.identity.id,
        session,
        detectors=[SelectorAppearsDetector("iframe[src*='api2/anchor']", kind="captcha")],
    )

    assert run.submitted_count == 0
    assert len(prepared) == 1  # filled and handed to the human
    assert session.clicked_selectors == []  # never auto-clicked submit
    reloaded = repository.load(brain_with_qualified_application.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_assist_pauses_on_a_captcha_instead_of_submitting(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    session.set_visible("iframe[src*='recaptcha']")
    session.set_visible(form_mapping.submit_selector)
    prepared: list[str] = []
    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: posting,
        resolve_form_mapping=lambda application: form_mapping,
        assist_captcha=True,
        on_prepared=lambda application, post, package: prepared.append(application.id),
    )

    run = executor.run_for_identity(
        brain_with_qualified_application.identity.id,
        session,
        detectors=[SelectorAppearsDetector("iframe[src*='recaptcha']", kind="captcha")],
    )

    assert run.submitted_count == 0
    assert "Prepared for review" in run.outcomes[0].reason
    assert len(prepared) == 1
    assert session.clicked_selectors == []  # never auto-submitted the captcha form
    reloaded = repository.load(brain_with_qualified_application.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_prepare_only_still_hands_off_a_login_wall(
    repository,
    autonomy_policy,
    application_runner,
    event_bus,
    session,
    posting,
    form_mapping,
    brain_with_qualified_application,
):
    # A login wall means there is no fillable form to prepare — still hand off.
    session.set_visible("input[type='password']")
    prepared: list[str] = []
    executor = AutonomousApplicationExecutor(
        repository=repository,
        autonomy_policy=autonomy_policy,
        application_runner=application_runner,
        event_bus=event_bus,
        resolve_posting=lambda application: posting,
        resolve_form_mapping=lambda application: form_mapping,
        prepare_only=True,
        on_prepared=lambda application, post, package: prepared.append(application.id),
    )

    run = executor.run_for_identity(
        brain_with_qualified_application.identity.id,
        session,
        detectors=[SelectorAppearsDetector("input[type='password']", kind="login_required")],
    )

    assert run.submitted_count == 0
    assert "Handed off" in run.outcomes[0].reason
    assert prepared == []


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
