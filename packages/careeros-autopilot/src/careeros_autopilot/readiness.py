"""How close one application actually is to being sendable — and why not.

"Application failed." is the message this module exists to delete. It tells the
user nothing about what worked, nothing about what is left, and nothing about
whether they can do anything. Every attempt now produces a readiness record
that answers four questions:

    what happened · why · what was completed · what remains, and by whom

A percentage on its own would be no better than "failed" — so the number is
always accompanied by the per-stage checklist it was computed from, and the
checklist is what a human actually reads.

The evidence record is the other half. A failed application that cannot be
reproduced is a bug report with no repro steps, so every attempt keeps the
posting URL, the application URL, the ATS, the fields detected and mapped, the
validation outcome and any screenshot. It deliberately keeps NO credentials,
cookies or profile values — evidence has to be safe to attach to a bug report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from careeros_application_engine import UnansweredQuestion
from careeros_application_runner import FieldOutcome, FillReport, FormFieldMapping
from careeros_autopilot.page_analysis import ApplicationRoute


class CheckState(StrEnum):
    PASS = "pass"
    #: Done, but a human should look. Never blocks.
    WARN = "warn"
    FAIL = "fail"
    #: Not applicable to this form (no cover-letter field, no questions).
    #: Scored as neither a success nor a failure.
    SKIPPED = "skipped"

    @property
    def mark(self) -> str:
        return {"pass": "✓", "warn": "⚠", "fail": "✗", "skipped": "-"}[self.value]


@dataclass
class ReadinessCheck:
    name: str
    state: CheckState
    detail: str = ""

    def line(self) -> str:
        suffix = f" — {self.detail}" if self.detail else ""
        return f"{self.state.mark} {self.name}{suffix}"


#: The stages, in the order they happen. Order is fixed so two runs are
#: comparable at a glance.
STAGES = (
    "Job identified",
    "Application URL found",
    "ATS detected",
    "Resume ready",
    "Cover letter ready",
    "Profile fields available",
    "Application fields mapped",
    "Required fields filled",
    "Validation passed",
    "Questions answered",
)


@dataclass
class Evidence:
    """Everything needed to reproduce one attempt. No secrets, ever.

    Field VALUES are deliberately absent: the names of the fields that were
    detected, mapped and left unmapped are what explain a failure, and the
    values are the candidate's personal data. Storing them would make every
    debug log a copy of the user's profile.
    """

    job_url: str = ""
    application_url: str = ""
    ats: str = ""
    route: str = ""
    #: Field NAMES only.
    detected_fields: list[str] = field(default_factory=list)
    mapped_fields: list[str] = field(default_factory=list)
    unmapped_fields: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    screenshot: str = ""
    error: str = ""
    final_state: str = ""
    #: Where the form was found — the page, or an iframe. Without it, "the
    #: field was not filled" cannot be told from "not filled in the document
    #: we were looking at".
    form_context: str = "the page itself"
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def as_dict(self) -> dict:
        return {
            "job_url": self.job_url,
            "application_url": self.application_url,
            "ats": self.ats,
            "route": self.route,
            "detected_fields": list(self.detected_fields),
            "mapped_fields": list(self.mapped_fields),
            "unmapped_fields": list(self.unmapped_fields),
            "validation": list(self.validation),
            "screenshot": self.screenshot,
            "error": self.error,
            "final_state": self.final_state,
            "form_context": self.form_context,
            "captured_at": self.captured_at.isoformat(),
        }


class ApplicationRecommendation(StrEnum):
    """What to DO about this application — a different question from whether
    the form can be filled in.

    These were the same field, and that was dangerous. A job can be perfectly
    fillable and still one the candidate must not apply to: OpenAI's posting
    reached SUBMISSION_READY at 83% while explicitly restricted to US-based
    candidates. Both facts were reported, but a human skimming the status — or
    any automation keying off "submission ready" — could act on the technical
    verdict and miss the disqualification entirely.

    Technical readiness is retained unchanged underneath (``score``,
    ``is_submission_ready``). This is the layer above it, and it is the one a
    caller should read.
    """

    #: Fillable, and nothing rules the candidate out. The only state in which
    #: submitting is appropriate.
    READY_TO_APPLY = "ready_to_apply"
    #: The form could be completed — but the employer has explicitly ruled this
    #: candidate out. DO NOT APPLY. Kept distinct from BLOCKED because the
    #: technical work succeeded; it is the job that says no.
    SUBMISSION_READY_BUT_DISQUALIFIED = "submission_ready_but_disqualified"
    #: Reached the form, but something required is missing and only the
    #: candidate can supply it.
    NEEDS_USER_INPUT = "needs_user_input"
    #: Could not complete the form at all — no form found, an anti-bot wall, a
    #: login required.
    BLOCKED = "blocked"

    @property
    def may_submit(self) -> bool:
        """Whether an automated caller may proceed to submit.

        The machine-readable half of this whole distinction. Checking
        ``is_submission_ready`` alone is exactly the mistake this enum exists
        to make impossible, so anything driving a submit button asks THIS.
        """
        return self is ApplicationRecommendation.READY_TO_APPLY

    @property
    def headline(self) -> str:
        return {
            ApplicationRecommendation.READY_TO_APPLY: "READY TO APPLY",
            ApplicationRecommendation.SUBMISSION_READY_BUT_DISQUALIFIED: (
                "DO NOT APPLY — JOB DISQUALIFICATION"
            ),
            ApplicationRecommendation.NEEDS_USER_INPUT: "NEEDS YOUR INPUT",
            ApplicationRecommendation.BLOCKED: "BLOCKED",
        }[self]


@dataclass
class ApplicationReadiness:
    checks: list[ReadinessCheck] = field(default_factory=list)
    unanswered: list[UnansweredQuestion] = field(default_factory=list)
    evidence: Evidence = field(default_factory=Evidence)
    #: Why the employer rules this candidate out, if they do — e.g. "role is
    #: restricted to US-based candidates". Empty when nothing does.
    disqualifier: str = ""
    #: True when the form was never reached or filled (no form, captcha, login
    #: wall), as opposed to reached-but-incomplete.
    unreachable: bool = False

    def _scored(self) -> list[ReadinessCheck]:
        """Checks that count. SKIPPED stages are not applicable to this form,
        and counting them as failures would punish a short form for being
        short."""
        return [c for c in self.checks if c.state is not CheckState.SKIPPED]

    @property
    def score(self) -> int:
        """0-100. A WARN is half credit: it is done, and a human should look."""
        scored = self._scored()
        if not scored:
            return 0
        weights = {CheckState.PASS: 1.0, CheckState.WARN: 0.5, CheckState.FAIL: 0.0}
        earned = sum(weights[c.state] for c in scored)
        return round(100 * earned / len(scored))

    @property
    def is_submission_ready(self) -> bool:
        """No stage failed. Warnings do not block — they are things to look at,
        not things that are missing."""
        return not any(c.state is CheckState.FAIL for c in self.checks)

    @property
    def is_disqualified(self) -> bool:
        return bool(self.disqualifier)

    @property
    def recommendation(self) -> ApplicationRecommendation:
        """What to do about this application.

        Order matters. BLOCKED wins over a disqualification because "we never
        reached the form" is the more immediate fact; the disqualification is
        still surfaced in the report either way. A disqualification then wins
        over technical readiness, because a fillable form the candidate is
        barred from is not an opportunity.
        """
        if self.unreachable:
            return ApplicationRecommendation.BLOCKED
        if not self.is_submission_ready:
            return ApplicationRecommendation.NEEDS_USER_INPUT
        if self.is_disqualified:
            return ApplicationRecommendation.SUBMISSION_READY_BUT_DISQUALIFIED
        return ApplicationRecommendation.READY_TO_APPLY

    @property
    def may_submit(self) -> bool:
        """The single question anything driving a submit button should ask."""
        return self.recommendation.may_submit

    @property
    def blockers(self) -> list[ReadinessCheck]:
        return [c for c in self.checks if c.state is CheckState.FAIL]

    @property
    def needs_review(self) -> list[ReadinessCheck]:
        return [c for c in self.checks if c.state is CheckState.WARN]

    def report(self) -> str:
        """The checklist a human reads. More useful than "application ready"
        because it says which parts are ready."""
        # The recommendation leads. Putting the percentage first is what let a
        # reader take "83%" as approval while a disqualification sat below it.
        lines = [self.recommendation.headline]
        if self.is_disqualified:
            lines.append(f"  {self.disqualifier}")
        lines += [f"Form readiness: {self.score}%", ""]
        lines += [check.line() for check in self.checks]
        if self.unanswered:
            lines.append("")
            lines.append(f"{len(self.unanswered)} question(s) need you:")
            for question in self.unanswered:
                lines.append(f"  • {question.question}")
                lines.append(f"      why: {question.why}")
                lines.append(f"      needs: {question.needs}")
        return "\n".join(lines)

    def failure_report(self, *, headline: str = "") -> str:
        """What happened, why, what was done, what remains, who must act.

        This is the whole message — a caller prints it and stops. Splitting it
        up is how "Application failed." happened in the first place.
        """
        recommendation = self.recommendation
        opening = {
            ApplicationRecommendation.READY_TO_APPLY: "Application ready for you to submit.",
            ApplicationRecommendation.SUBMISSION_READY_BUT_DISQUALIFIED: (
                "DO NOT APPLY — the employer rules you out for this role.\n"
                "The form itself was completed successfully, which is why the "
                "readiness score below is high. That is a statement about the "
                "form, not about whether you should send it."
            ),
            ApplicationRecommendation.NEEDS_USER_INPUT: "Application paused.",
            ApplicationRecommendation.BLOCKED: "Application blocked.",
        }[recommendation]
        ready = self.is_submission_ready
        lines = [opening, ""]
        if self.is_disqualified:
            lines += ["Disqualification:", f"  {self.disqualifier}", ""]
        reason = (
            headline
            or self.evidence.error
            or ("; ".join(f"{c.name}: {c.detail}" for c in self.blockers))
        )
        if reason:
            lines += ["Reason:", f"  {reason}", ""]
        lines.append("Status:")
        lines += [f"  {check.line()}" for check in self.checks]
        lines.append("")
        if recommendation is ApplicationRecommendation.SUBMISSION_READY_BUT_DISQUALIFIED:
            lines.append("Required action:")
            lines.append("  Do not submit this one. Move on to the next posting.")
        elif ready and not self.unanswered and not self.needs_review:
            lines.append("Required action:")
            lines.append("  Review and submit — nothing is missing.")
        else:
            lines.append("Required action:")
            for check in self.blockers:
                lines.append(f"  • {check.name}: {check.detail or 'needs you'}")
            for check in self.needs_review:
                lines.append(f"  • check {check.name}: {check.detail or 'worth a look'}")
            for question in self.unanswered:
                lines.append(f"  • answer: {question.question} ({question.needs})")
        lines.append("")
        lines.append("No application was submitted.")
        return "\n".join(lines)


def _resume_check(resume_file_path: str | None, has_upload_field: bool) -> ReadinessCheck:
    if not has_upload_field:
        return ReadinessCheck("Resume ready", CheckState.SKIPPED, "this form takes no upload")
    if not resume_file_path:
        return ReadinessCheck(
            "Resume ready", CheckState.FAIL, "no resume file was generated to upload"
        )
    return ReadinessCheck("Resume ready", CheckState.PASS)


def assess_readiness(
    *,
    posting_url: str = "",
    application_url: str = "",
    ats: str = "",
    route: ApplicationRoute | None = None,
    mapping: FormFieldMapping | None = None,
    fill_report: FillReport | None = None,
    resume_file_path: str | None = None,
    cover_letter: str = "",
    unanswered: list[UnansweredQuestion] | None = None,
    detected_field_count: int = 0,
    form_context: str = "the page itself",
    screenshot: str = "",
    error: str = "",
    disqualifier: str = "",
) -> ApplicationReadiness:
    """Turn one attempt into a readiness record.

    Every argument is optional because an attempt can stop at any stage, and a
    stage that was never reached must read as "not reached" rather than as a
    silent pass.
    """
    unanswered = list(unanswered or [])
    checks: list[ReadinessCheck] = []

    checks.append(
        ReadinessCheck(
            "Job identified",
            CheckState.PASS if posting_url else CheckState.FAIL,
            "" if posting_url else "no posting URL",
        )
    )
    if application_url:
        checks.append(ReadinessCheck("Application URL found", CheckState.PASS))
    elif route in (ApplicationRoute.EXTERNAL_UNSUPPORTED,):
        checks.append(
            ReadinessCheck(
                "Application URL found",
                CheckState.FAIL,
                "this employer takes applications on its own site, not through the ATS",
            )
        )
    else:
        checks.append(
            ReadinessCheck("Application URL found", CheckState.FAIL, "no application page reached")
        )

    checks.append(
        ReadinessCheck(
            "ATS detected",
            CheckState.PASS if ats else CheckState.WARN,
            "" if ats else "the ATS could not be identified",
        )
    )

    checks.append(_resume_check(resume_file_path, bool(mapping and mapping.resume_upload_selector)))

    if mapping is None or not mapping.cover_letter_selector:
        checks.append(
            ReadinessCheck(
                "Cover letter ready", CheckState.SKIPPED, "this form has no field for one"
            )
        )
    else:
        checks.append(
            ReadinessCheck(
                "Cover letter ready",
                CheckState.PASS if cover_letter.strip() else CheckState.FAIL,
                "" if cover_letter.strip() else "no cover letter was generated",
            )
        )

    if fill_report is None:
        checks.append(
            ReadinessCheck("Profile fields available", CheckState.FAIL, "the form was never filled")
        )
        checks.append(ReadinessCheck("Application fields mapped", CheckState.FAIL, "no mapping"))
        checks.append(ReadinessCheck("Required fields filled", CheckState.FAIL, "not attempted"))
        checks.append(ReadinessCheck("Validation passed", CheckState.FAIL, "nothing to validate"))
    else:
        missing_values = [r.field for r in fill_report.needs_human]
        checks.append(
            ReadinessCheck(
                "Profile fields available",
                CheckState.PASS if not missing_values else CheckState.WARN,
                "" if not missing_values else "no value for: " + ", ".join(missing_values[:4]),
            )
        )
        not_present = [
            r.field for r in fill_report.results if r.outcome is FieldOutcome.NOT_PRESENT
        ]
        checks.append(
            ReadinessCheck(
                "Application fields mapped",
                CheckState.PASS if mapping is not None else CheckState.FAIL,
                "" if not not_present else "not on this form: " + ", ".join(not_present[:4]),
            )
        )
        blocking = fill_report.blocking
        checks.append(
            ReadinessCheck(
                "Required fields filled",
                CheckState.PASS if not blocking else CheckState.FAIL,
                "" if not blocking else "; ".join(f"{r.field} ({r.detail})" for r in blocking[:3]),
            )
        )
        unverified = fill_report.unverified
        optional_failures = [r for r in fill_report.failures if not r.required]
        if fill_report.is_submittable and not unverified and not optional_failures:
            checks.append(ReadinessCheck("Validation passed", CheckState.PASS))
        elif fill_report.is_submittable:
            note = []
            if unverified:
                note.append(f"{len(unverified)} field(s) could not be read back")
            if optional_failures:
                note.append(f"{len(optional_failures)} optional field(s) did not take")
            checks.append(ReadinessCheck("Validation passed", CheckState.WARN, "; ".join(note)))
        else:
            checks.append(
                ReadinessCheck("Validation passed", CheckState.FAIL, "required fields are missing")
            )

    if not mapping or not mapping.question_fields:
        checks.append(
            ReadinessCheck("Questions answered", CheckState.SKIPPED, "this form asks none")
        )
    elif unanswered:
        # WARN, not FAIL: an unanswered OPTIONAL question does not stop a
        # human submitting, and calling it a failure would make every form
        # with an optional free-text box look broken.
        required_unanswered = [
            q
            for q in unanswered
            if any(f.required and f.question == q.question for f in mapping.question_fields)
        ]
        state = CheckState.FAIL if required_unanswered else CheckState.WARN
        checks.append(
            ReadinessCheck(
                "Questions answered",
                state,
                f"{len(unanswered)} left for you"
                + (f" ({len(required_unanswered)} required)" if required_unanswered else ""),
            )
        )
    else:
        checks.append(ReadinessCheck("Questions answered", CheckState.PASS))

    evidence = Evidence(
        job_url=posting_url,
        application_url=application_url,
        ats=ats,
        route=route.value if route is not None else "",
        detected_fields=[r.field for r in (fill_report.results if fill_report else [])],
        mapped_fields=[r.field for r in (fill_report.filled if fill_report else [])],
        unmapped_fields=[
            r.field
            for r in (fill_report.results if fill_report else [])
            if r.outcome is FieldOutcome.NOT_PRESENT
        ],
        validation=[f"{c.name}: {c.state.value}" for c in checks],
        screenshot=screenshot,
        error=error,
        form_context=form_context,
    )
    # detected_field_count comes from the DOM scan, which sees fields the
    # mapping never claimed; recorded so "we mapped 6 of 19" is visible.
    if detected_field_count:
        evidence.final_state = f"{detected_field_count} field(s) detected on the form"

    readiness = ApplicationReadiness(
        checks=checks,
        unanswered=unanswered,
        evidence=evidence,
        disqualifier=disqualifier,
        # No fill report means the form was never reached or never filled —
        # an anti-bot wall, a login page, no form at all. That is BLOCKED, and
        # it is a different thing from a form we filled but could not finish.
        unreachable=fill_report is None,
    )
    evidence.final_state = readiness.recommendation.value
    return readiness
