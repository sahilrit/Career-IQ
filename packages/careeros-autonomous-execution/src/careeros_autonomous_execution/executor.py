"""AutonomousApplicationExecutor: connects the autonomous decision system
(Phase 21) to the real browser application engine (Phases 12-14, 17),
completing the loop:

    Career Brain -> Opportunity Engine -> Scoring -> Application Builder
    -> Autonomy Policy -> Application Execution -> Browser -> Verification
    -> CRM / Memory -> Learning

No arbitrary cap on how many qualified opportunities one run processes —
Phase 21's pacing, not a count limit, governs how fast it moves.
CareerOS must not fabricate anything about the user (every application
package still comes straight from Career Brain, per Phase 12), and any
step this executor can't get authorized or can't complete cleanly falls
back to a human via Phase 17's handoff — it never silently skips a
problem or a HIGH-risk step.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from careeros_application_engine import (
    ApplicationPackage,
    CoverLetterGenerator,
    QuestionAnswerer,
    build_application_package,
    disqualifying_requirement,
)
from careeros_application_intelligence import record_outcome
from careeros_application_runner import ApplicationRunner, FormFieldMapping
from careeros_autonomy import ActionRequest, AutonomyPolicy
from careeros_browser import BrowserSession
from careeros_career_brain import (
    Application,
    ApplicationStatus,
    CareerBrain,
    CareerBrainRepository,
)
from careeros_event_bus import Event, EventBus
from careeros_human_in_the_loop import HandoffSession, Problem, ProblemDetector, run_detectors
from careeros_job_providers import JobPosting

PostingResolver = Callable[[Application], JobPosting | None]
FormMappingResolver = Callable[[Application], FormFieldMapping | None]
# Navigates the session to the posting's live application form; returns an
# error reason, or None when the form page is loaded and ready.
PagePreparer = Callable[[BrowserSession, JobPosting], str | None]
# Inspects the live page (post-navigation) to build a mapping on the fly.
#
# May return either a bare ``FormFieldMapping`` or an object carrying both a
# mapping and the session its selectors belong to (``.session``/``.mapping``).
# The second form exists because a selector only reaches ONE document: when the
# form is inside an iframe, the mapping is meaningless against the page session
# and must travel with the frame session it was resolved against.
LiveFormMappingResolver = Callable[[BrowserSession, Application], object | None]


@dataclass
class ExecutionOutcome:
    application_id: str
    submitted: bool
    reason: str


@dataclass
class ExecutionRun:
    identity_id: str
    outcomes: list[ExecutionOutcome] = field(default_factory=list)

    @property
    def submitted_count(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.submitted)


class AutonomousApplicationExecutor:
    def __init__(
        self,
        *,
        repository: CareerBrainRepository,
        autonomy_policy: AutonomyPolicy,
        application_runner: ApplicationRunner,
        event_bus: EventBus,
        resolve_posting: PostingResolver,
        resolve_form_mapping: FormMappingResolver,
        prepare_page: PagePreparer | None = None,
        resolve_form_mapping_live: LiveFormMappingResolver | None = None,
        cover_letter_generator: CoverLetterGenerator | None = None,
        submit_enabled: bool = True,
        prepare_only: bool = False,
        assist_captcha: bool = False,
        question_ai_client: object | None = None,
        on_prepared: Callable[[Application, JobPosting, ApplicationPackage], None] | None = None,
    ) -> None:
        self._repository = repository
        self._autonomy = autonomy_policy
        self._runner = application_runner
        self._bus = event_bus
        self._resolve_posting = resolve_posting
        self._resolve_form_mapping = resolve_form_mapping
        self._prepare_page = prepare_page
        self._resolve_form_mapping_live = resolve_form_mapping_live
        # None -> build_application_package uses its template generator.
        self._cover_letter_generator = cover_letter_generator
        # False -> reach + map the form but never click submit (dry run).
        self._submit_enabled = submit_enabled
        # True -> fill the form (incl. captcha-gated ones) but never submit;
        # a human reviews, solves any captcha, and submits. on_prepared is
        # called with (application, posting, package) once the form is filled.
        self._prepare_only = prepare_only
        # True -> auto-submit clean forms, but when a captcha is present, fill
        # and hand off to the human (solve captcha + submit) instead of holding.
        self._assist_captcha = assist_captcha
        # Raw AI client used to answer custom form questions the rules can't.
        self._question_ai_client = question_ai_client
        self._on_prepared = on_prepared

    def run_for_identity(
        self,
        identity_id: str,
        session: BrowserSession,
        *,
        detectors: list[ProblemDetector] | None = None,
        resume_file_path: str | None = None,
    ) -> ExecutionRun:
        """Process every QUALIFIED application for this identity.

        Continues through all of them in one pass — no arbitrary cap —
        bounded only by Phase 21's authorization/pacing checks.
        """
        brain = self._repository.load(identity_id)
        qualified = [a for a in brain.applications if a.status == ApplicationStatus.QUALIFIED]
        handoff = HandoffSession(identity_id, self._bus)
        detectors = detectors or []

        outcomes = [
            self._process_one(
                brain, application, session, handoff, detectors, resume_file_path=resume_file_path
            )
            for application in qualified
        ]
        return ExecutionRun(identity_id=identity_id, outcomes=outcomes)

    def _process_one(
        self,
        brain: CareerBrain,
        application: Application,
        session: BrowserSession,
        handoff: HandoffSession,
        detectors: list[ProblemDetector],
        *,
        resume_file_path: str | None = None,
    ) -> ExecutionOutcome:
        decision = self._autonomy.evaluate(
            ActionRequest(
                action_type="submit_application",
                subject_id=application.id,
                payload={"match_score": application.match_score},
            )
        )
        if not decision.approved:
            return ExecutionOutcome(application.id, submitted=False, reason=decision.reason)

        posting = self._resolve_posting(application)
        if posting is None:
            return ExecutionOutcome(
                application.id,
                submitted=False,
                reason="No original posting found for this application.",
            )

        # Eligibility gate (from the posting text, before we even open a
        # browser): if the job explicitly requires something the candidate
        # can't meet — US work authorization, sponsorship it won't give,
        # US-only location — skip it and move on rather than prepare a form
        # they'd be rejected from.
        blocker = disqualifying_requirement(
            brain, posting.title, getattr(posting, "description", None)
        )
        if blocker is not None:
            return ExecutionOutcome(application.id, submitted=False, reason=f"Skipped — {blocker}.")

        if self._prepare_page is not None:
            preparation_error = self._prepare_page(session, posting)
            if preparation_error is not None:
                return ExecutionOutcome(
                    application.id,
                    submitted=False,
                    reason=f"Could not reach an application form: {preparation_error}",
                )

        # NOTE: we deliberately do NOT re-run the eligibility gate against the
        # loaded page's full body text. Nearly every US company's page carries
        # boilerplate EEO legalese ("must be authorized to work in the US")
        # that is NOT the role's actual requirement — scanning the whole body
        # skipped fillable forms wholesale. The structured-description check
        # above (posting title/description) is the only eligibility gate.

        problem = run_detectors(session, detectors)
        if problem is not None:
            # Prepare-and-review and assist-on-captcha both WANT captcha-gated
            # forms: fill what we can and let the human solve the captcha +
            # submit. A login wall means there's no fillable form — still hand
            # off. (Assist auto-submits clean forms; only captchas pause here.)
            handle_here = (self._prepare_only or self._assist_captcha) and (
                problem.kind != "login_required"
            )
            if not handle_here:
                handoff.request_takeover(problem)
                return ExecutionOutcome(
                    application.id,
                    submitted=False,
                    reason=f"Handed off to a human: {problem.description}",
                )

        mapping = None
        # The session the form's selectors actually resolve against. It is the
        # page for every ATS that renders its form inline, and a FRAME session
        # for the ones that render it in an iframe — where filling against the
        # page would silently write nothing.
        form_session = session
        if self._resolve_form_mapping_live is not None:
            located = self._resolve_form_mapping_live(session, application)
            if located is not None and hasattr(located, "mapping"):
                mapping = located.mapping
                form_session = getattr(located, "session", session)
            else:
                mapping = located
        if mapping is None:
            mapping = self._resolve_form_mapping(application)
        if mapping is None:
            return ExecutionOutcome(
                application.id,
                submitted=False,
                reason="No form mapping known for this posting's site.",
            )

        package = build_application_package(
            brain, posting, cover_letter_generator=self._cover_letter_generator
        )

        # Answer any additional questions on the form, truthfully from the
        # Career Brain; unanswerable ones are left blank for a human.
        question_answers: dict[str, str] = {}
        if mapping.question_fields:
            answerer = QuestionAnswerer(brain, posting, ai_client=self._question_ai_client)
            for field in mapping.question_fields:
                answer = answerer.answer(field.question)
                if answer.answerable and answer.text:
                    question_answers[field.selector] = answer.text

        # Pause for a human in review mode AND in assist mode. Blind auto-submit
        # can't be verified (job forms carry "thank you"/"submitted" boilerplate
        # that false-positives success, and captchas/anti-bot silently reject the
        # submit), so assist now fills every form and hands it to the human to
        # verify and submit — nothing goes out unseen.
        pause_for_human = self._prepare_only or self._assist_captcha
        if pause_for_human:
            # Fill the form (best-effort) but never submit. A human solves any
            # captcha and clicks submit. Stays QUALIFIED.
            self._runner.prepare(
                form_session,
                package,
                mapping,
                application_id=application.id,
                resume_file_path=resume_file_path,
                question_answers=question_answers,
            )
            if self._on_prepared is not None:
                self._on_prepared(application, posting, package)
            return ExecutionOutcome(
                application.id,
                submitted=False,
                reason="Prepared for review — form filled; solve the captcha and submit",
            )

        if not self._submit_enabled:
            # Dry run: we reached a fillable form and built the mapping/package,
            # which is the whole point of validation — just don't click submit.
            return ExecutionOutcome(
                application.id,
                submitted=False,
                reason="DRY RUN — reached a fillable form; would submit",
            )

        result = self._runner.submit(
            form_session,
            package,
            mapping,
            application_id=application.id,
            resume_file_path=resume_file_path,
            question_answers=question_answers,
        )

        if not result.success:
            handoff.request_takeover(
                Problem(
                    kind="submission_failed",
                    description="; ".join(result.errors) or "Submission failed",
                )
            )
            return ExecutionOutcome(
                application.id,
                submitted=False,
                reason="Submission failed after retries; handed off to a human.",
            )

        record_outcome(
            self._repository,
            self._bus,
            brain,
            application,
            ApplicationStatus.APPLIED,
            reason="Autonomously submitted",
        )
        self._bus.publish(
            Event(
                event_type="application.autonomously_submitted",
                source="autonomous-execution",
                payload={"subject_id": application.id, "company_name": application.company_name},
            )
        )
        return ExecutionOutcome(application.id, submitted=True, reason="Submitted successfully")
