"""careeros_application_runner: turns an ApplicationPackage into an
actual browser form submission — form fill, validation, upload,
screenshots, and retries, all against the BrowserSession abstraction
(Phase 13), site-agnostic via FormFieldMapping.
"""

from careeros_application_runner.form_handler import (
    fill_application_form,
    submit_application_form,
)
from careeros_application_runner.models import FormFieldMapping, QuestionField
from careeros_application_runner.retry import retry
from careeros_application_runner.runner import ApplicationRunner, SubmissionResult
from careeros_application_runner.validator import ValidationResult, validate_submission

__all__ = [
    "ApplicationRunner",
    "FormFieldMapping",
    "QuestionField",
    "SubmissionResult",
    "ValidationResult",
    "fill_application_form",
    "retry",
    "submit_application_form",
    "validate_submission",
]
