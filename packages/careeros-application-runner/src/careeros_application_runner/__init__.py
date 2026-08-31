"""careeros_application_runner: turns an ApplicationPackage into an actual
browser form submission — form fill, verification, validation, upload,
screenshots, and retries, all against the BrowserSession abstraction and
site-agnostic via FormFieldMapping.

Every fill returns a ``FillReport``: what was written, what was verified, what
was left for a human and why. A form is never reported as filled on the
strength of having called ``fill()``.
"""

from careeros_application_runner.fill import fill_application_form, submit_application_form
from careeros_application_runner.fill_report import FieldOutcome, FieldResult, FillReport
from careeros_application_runner.models import FormFieldMapping, QuestionField
from careeros_application_runner.retry import retry
from careeros_application_runner.runner import (
    ApplicationRunner,
    IncompleteFormError,
    PreparedApplication,
    SubmissionResult,
)
from careeros_application_runner.validator import ValidationResult, validate_submission

__all__ = [
    "ApplicationRunner",
    "FieldOutcome",
    "FieldResult",
    "FillReport",
    "FormFieldMapping",
    "IncompleteFormError",
    "PreparedApplication",
    "QuestionField",
    "SubmissionResult",
    "ValidationResult",
    "fill_application_form",
    "retry",
    "submit_application_form",
    "validate_submission",
]
