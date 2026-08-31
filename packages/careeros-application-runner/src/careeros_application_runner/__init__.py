"""careeros_application_runner: turns an ApplicationPackage into an actual
browser form submission — form fill, verification, validation, upload,
screenshots, and retries, all against the BrowserSession abstraction and
site-agnostic via FormFieldMapping.

Every fill returns a ``FillReport``: what was written, what was verified, what
was left for a human and why. A form is never reported as filled on the
strength of having called ``fill()``.
"""

from careeros_application_runner.fill import (
    UnsafeSubmitError,
    fill_application_form,
    submit_application_form,
)
from careeros_application_runner.fill_report import FieldOutcome, FieldResult, FillReport
from careeros_application_runner.form_semantics import (
    ControlKind,
    FieldPurpose,
    MappedField,
    SubmitCandidate,
    classify_control,
    classify_field,
    find_submit_control,
    map_fields,
    normalize_label,
)
from careeros_application_runner.models import FormFieldMapping, QuestionField
from careeros_application_runner.retry import TerminalError, retry
from careeros_application_runner.runner import (
    ApplicationRunner,
    IncompleteFormError,
    PreparedApplication,
    SubmissionResult,
)
from careeros_application_runner.validator import ValidationResult, validate_submission

__all__ = [
    "ApplicationRunner",
    "ControlKind",
    "FieldOutcome",
    "FieldPurpose",
    "FieldResult",
    "FillReport",
    "FormFieldMapping",
    "IncompleteFormError",
    "MappedField",
    "PreparedApplication",
    "QuestionField",
    "SubmissionResult",
    "SubmitCandidate",
    "TerminalError",
    "UnsafeSubmitError",
    "ValidationResult",
    "classify_control",
    "classify_field",
    "fill_application_form",
    "find_submit_control",
    "map_fields",
    "normalize_label",
    "retry",
    "submit_application_form",
    "validate_submission",
]
