"""ApplicationRunner: turns an ApplicationPackage into an actual browser
form submission, with validation, screenshots, and retries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from careeros_application_engine import ApplicationPackage
from careeros_application_runner.fill import fill_application_form, submit_application_form
from careeros_application_runner.fill_report import FillReport
from careeros_application_runner.models import FormFieldMapping
from careeros_application_runner.retry import TerminalError, retry
from careeros_application_runner.validator import validate_submission
from careeros_browser import BrowserHealth, BrowserSession, check_browser_health


class IncompleteFormError(TerminalError):
    """A required field did not take, so the form was never submitted.

    Terminal on purpose: the form will be exactly as incomplete on the third
    attempt, and each retry re-fills everything — which on a real ATS means
    re-uploading the résumé twice more for nothing.
    """


@dataclass
class PreparedApplication:
    """A form filled and left for a human to review and submit."""

    screenshot: Path
    fill_report: FillReport

    @property
    def is_ready(self) -> bool:
        """Nothing required is missing — a human can submit as-is."""
        return self.fill_report.is_submittable

    def what_you_must_finish(self) -> list[str]:
        """The specific fields a human still has to handle, with the reason."""
        return [f"{r.field}: {r.detail}" for r in self.fill_report.blocking]


@dataclass
class SubmissionResult:
    success: bool
    attempts: int
    screenshots: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    #: Per-field evidence for the last fill attempt. Present even on failure -
    #: it is usually the only thing that explains one.
    fill_report: FillReport | None = None


class ApplicationRunner:
    def __init__(
        self,
        *,
        max_attempts: int = 3,
        screenshot_dir: str | Path = ".careeros/screenshots",
    ) -> None:
        self._max_attempts = max_attempts
        self._screenshot_dir = Path(screenshot_dir)

    def submit(
        self,
        session: BrowserSession,
        package: ApplicationPackage,
        mapping: FormFieldMapping,
        *,
        resume_file_path: str | None = None,
        question_answers: dict[str, str] | None = None,
        application_id: str = "application",
    ) -> SubmissionResult:
        validation = validate_submission(
            session, package, mapping, resume_file_path=resume_file_path
        )
        if not validation.is_valid:
            return SubmissionResult(success=False, attempts=0, errors=validation.errors)

        screenshots: list[Path] = []
        attempts = 0

        report_holder: list[FillReport] = []

        def attempt() -> None:
            nonlocal attempts
            attempts += 1
            report = fill_application_form(
                session,
                package,
                mapping,
                resume_file_path=resume_file_path,
                question_answers=question_answers,
            )
            report_holder.append(report)
            screenshots.append(
                self._screenshot(session, f"{application_id}-before-submit-{attempts}")
            )
            # Submitting a form we know is incomplete burns the application:
            # most ATSes reject it and some record the attempt. If a required
            # field did not take, stop here and say which one, rather than
            # clicking submit and reading the failure off an error page.
            if not report.is_submittable:
                blocking = "; ".join(f"{r.field} ({r.detail})" for r in report.blocking)
                failed = "; ".join(f"{r.field} ({r.detail})" for r in report.failures)
                raise IncompleteFormError(
                    "the form is not ready to submit — "
                    + (f"missing required: {blocking}. " if blocking else "")
                    + (f"failed to fill: {failed}" if failed else "")
                )
            submit_application_form(session, mapping)
            session.wait_for_selector(mapping.success_selector)

        try:
            retry(attempt, max_attempts=self._max_attempts)
        except Exception as exc:
            screenshots.append(self._screenshot(session, f"{application_id}-error"))
            return SubmissionResult(
                success=False,
                attempts=attempts,
                screenshots=screenshots,
                errors=[str(exc)],
                fill_report=report_holder[-1] if report_holder else None,
            )

        screenshots.append(self._screenshot(session, f"{application_id}-success"))
        return SubmissionResult(
            success=True,
            attempts=attempts,
            screenshots=screenshots,
            fill_report=report_holder[-1] if report_holder else None,
        )

    def prepare(
        self,
        session: BrowserSession,
        package: ApplicationPackage,
        mapping: FormFieldMapping,
        *,
        resume_file_path: str | None = None,
        question_answers: dict[str, str] | None = None,
        application_id: str = "application",
    ) -> PreparedApplication:
        """Fill the form and stop, for prepare-and-review — the mode where a
        human checks the result, answers anything left open, and clicks submit.

        Unlike ``submit``, an incomplete form is a normal outcome here: the
        point is to get as far as truthfully possible and hand over a precise
        list of what remains. The report says which fields those are, so the
        human is not left comparing a screenshot against their own CV.
        """
        report = fill_application_form(
            session,
            package,
            mapping,
            resume_file_path=resume_file_path,
            question_answers=question_answers,
        )
        screenshot = self._screenshot(session, f"{application_id}-prepared")
        return PreparedApplication(screenshot=screenshot, fill_report=report)

    def _screenshot(self, session: BrowserSession, name: str) -> Path:
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        return session.screenshot(self._screenshot_dir / f"{name}.png")

    def health(self) -> BrowserHealth:
        return check_browser_health()
