"""Pre-submission validation: is there enough information, on both the
application package and the live page, to attempt a submission at all?
"""

from __future__ import annotations

from dataclasses import dataclass, field

from careeros_application_engine import ApplicationPackage
from careeros_application_runner.models import FormFieldMapping
from careeros_browser import BrowserSession


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


def validate_submission(
    session: BrowserSession,
    package: ApplicationPackage,
    mapping: FormFieldMapping,
    *,
    resume_file_path: str | None,
) -> ValidationResult:
    errors: list[str] = []

    if mapping.resume_upload_selector and not resume_file_path:
        errors.append("Form requires a resume upload but no resume_file_path was provided.")

    if mapping.cover_letter_selector and not package.cover_letter:
        errors.append("Form has a cover letter field but the application package has none.")

    if not session.is_visible(mapping.submit_selector):
        errors.append(f"Submit selector {mapping.submit_selector!r} is not visible.")

    return ValidationResult(is_valid=not errors, errors=errors)
