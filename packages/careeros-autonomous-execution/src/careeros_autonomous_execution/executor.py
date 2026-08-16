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

from careeros_application_engine import build_application_package
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
LiveFormMappingResolver = Callable[[BrowserSession, Application], FormFieldMapping | None]


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
    ) -> None:
        self._repository = repository
        self._autonomy = autonomy_policy
        self._runner = application_runner
        self._bus = event_bus
        self._resolve_posting = resolve_posting
        self._resolve_form_mapping = resolve_form_mapping
        self._prepare_page = prepare_page
        self._resolve_form_mapping_live = resolve_form_mapping_live

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

        if self._prepare_page is not None:
            preparation_error = self._prepare_page(session, posting)
            if preparation_error is not None:
                return ExecutionOutcome(
                    application.id,
                    submitted=False,
                    reason=f"Could not reach an application form: {preparation_error}",
                )

        problem = run_detectors(session, detectors)
        if problem is not None:
            handoff.request_takeover(problem)
            return ExecutionOutcome(
                application.id,
                submitted=False,
                reason=f"Handed off to a human: {problem.description}",
            )

        mapping = None
        if self._resolve_form_mapping_live is not None:
            mapping = self._resolve_form_mapping_live(session, application)
        if mapping is None:
            mapping = self._resolve_form_mapping(application)
        if mapping is None:
            return ExecutionOutcome(
                application.id,
                submitted=False,
                reason="No form mapping known for this posting's site.",
            )

        package = build_application_package(brain, posting)
        result = self._runner.submit(
            session,
            package,
            mapping,
            application_id=application.id,
            resume_file_path=resume_file_path,
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
