"""ApplicationRunner: turns an ApplicationPackage into an actual browser
form submission, with validation, screenshots, and retries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from careeros_application_engine import ApplicationPackage
from careeros_application_runner.form_handler import (
    fill_application_form,
    submit_application_form,
)
from careeros_application_runner.models import FormFieldMapping
from careeros_application_runner.retry import retry
from careeros_application_runner.validator import validate_submission
from careeros_browser import BrowserHealth, BrowserSession, check_browser_health


@dataclass
class SubmissionResult:
    success: bool
    attempts: int
    screenshots: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


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

        def attempt() -> None:
            nonlocal attempts
            attempts += 1
            fill_application_form(
                session,
                package,
                mapping,
                resume_file_path=resume_file_path,
                question_answers=question_answers,
            )
            screenshots.append(
                self._screenshot(session, f"{application_id}-before-submit-{attempts}")
            )
            submit_application_form(session, mapping)
            session.wait_for_selector(mapping.success_selector)

        try:
            retry(attempt, max_attempts=self._max_attempts)
        except Exception as exc:
            screenshots.append(self._screenshot(session, f"{application_id}-error"))
            return SubmissionResult(
                success=False, attempts=attempts, screenshots=screenshots, errors=[str(exc)]
            )

        screenshots.append(self._screenshot(session, f"{application_id}-success"))
        return SubmissionResult(success=True, attempts=attempts, screenshots=screenshots)

    def prepare(
        self,
        session: BrowserSession,
        package: ApplicationPackage,
        mapping: FormFieldMapping,
        *,
        resume_file_path: str | None = None,
        question_answers: dict[str, str] | None = None,
        application_id: str = "application",
    ) -> Path:
        """Fill the form but never submit — for prepare-and-review, where a
        human solves the captcha and clicks submit. Returns a screenshot of the
        filled form. Filling is best-effort: a field that rejects input is
        skipped, since the human can finish it."""
        fill_application_form(
            session,
            package,
            mapping,
            resume_file_path=resume_file_path,
            question_answers=question_answers,
        )
        return self._screenshot(session, f"{application_id}-prepared")

    def _screenshot(self, session: BrowserSession, name: str) -> Path:
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        return session.screenshot(self._screenshot_dir / f"{name}.png")

    def health(self) -> BrowserHealth:
        return check_browser_health()
