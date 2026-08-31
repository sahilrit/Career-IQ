"""Filling a live application form, with every field verified and reported.

The contract is: write a value, read it back, and record what happened. A field
that rejects input is a reported failure, not a silence; a field with no
truthful value is a reported hand-off, not a guess.

Verification matters more than it sounds. A React-controlled input accepts a
programmatic ``fill`` and then re-renders its old value; a disabled field
ignores one entirely. Both leave the page looking filled and submit nothing.
Reading the value back is the only way to tell those apart from a real fill.
"""

from __future__ import annotations

from careeros_application_engine import ApplicationPackage
from careeros_application_runner.fill_report import FieldOutcome, FieldResult, FillReport
from careeros_application_runner.models import FormFieldMapping
from careeros_browser import BrowserSession

#: Some fields cannot be read back by design, and that is not a failure:
#: ``input_value`` is meaningless for a file input, and a contenteditable
#: rich-text box is not an <input> at all.
_UNVERIFIABLE_KINDS = frozenset({"file", "richtext"})


def _verify(session: BrowserSession, selector: str, expected: str) -> tuple[bool, str]:
    """Whether the field now holds ``expected``, and why not if it does not."""
    try:
        actual = session.input_value(selector)
    except Exception as exc:
        return False, f"could not read the field back: {exc}"
    if actual == expected:
        return True, ""
    if actual.strip() == expected.strip():
        return True, ""
    if not actual:
        # The dangerous case: no exception, no value. A React-controlled or
        # disabled input does exactly this.
        return False, "the field discarded the value (it is empty after filling)"
    # A field that normalizes what it stores (phone masks, trimmed selects) is
    # still filled; report the difference rather than calling it a failure.
    return False, f"the field holds {actual[:60]!r} rather than the value written"


def _fill_one(
    session: BrowserSession,
    *,
    field: str,
    selector: str | None,
    value: str | None,
    required: bool = False,
    kind: str = "text",
) -> FieldResult:
    if not selector:
        return FieldResult(
            field=field,
            selector="",
            outcome=FieldOutcome.NOT_PRESENT,
            detail="no selector for this field on this form",
            required=required,
        )
    if not value:
        return FieldResult(
            field=field,
            selector=selector,
            outcome=FieldOutcome.NEEDS_HUMAN,
            detail="no truthful value available from the profile",
            required=required,
        )

    try:
        if kind == "select":
            session.select_option(selector, value)
        elif kind == "combobox":
            session.select_combobox_option(selector, value)
        elif kind == "file":
            session.upload_file(selector, value)
        else:
            session.fill(selector, value)
    except Exception as exc:
        return FieldResult(
            field=field,
            selector=selector,
            outcome=FieldOutcome.FAILED,
            detail=str(exc)[:200],
            required=required,
        )

    if kind in _UNVERIFIABLE_KINDS:
        return FieldResult(
            field=field,
            selector=selector,
            outcome=FieldOutcome.UNVERIFIED,
            detail=f"a {kind} field cannot be read back; check it before submitting",
            required=required,
        )

    ok, why = _verify(session, selector, value)
    if ok:
        return FieldResult(
            field=field, selector=selector, outcome=FieldOutcome.FILLED, required=required
        )
    return FieldResult(
        field=field,
        selector=selector,
        outcome=FieldOutcome.FAILED,
        detail=why,
        required=required,
    )


def fill_application_form(
    session: BrowserSession,
    package: ApplicationPackage,
    mapping: FormFieldMapping,
    *,
    resume_file_path: str | None = None,
    question_answers: dict[str, str] | None = None,
) -> FillReport:
    """Fill every mapped field and report exactly what happened to each."""
    report = FillReport()
    content = package.resume_content
    answers = question_answers or {}

    if mapping.first_name_selector or mapping.last_name_selector:
        first_name, _, last_name = content.full_name.partition(" ")
        report.add(
            _fill_one(
                session,
                field="first_name",
                selector=mapping.first_name_selector,
                value=first_name,
                required=True,
            )
        )
        if mapping.last_name_selector:
            report.add(
                _fill_one(
                    session,
                    field="last_name",
                    selector=mapping.last_name_selector,
                    # A single-word legal name is real; falling back to the
                    # first name would submit a duplicate rather than a blank
                    # a human can correct.
                    value=last_name,
                    required=True,
                )
            )
    elif mapping.full_name_selector:
        report.add(
            _fill_one(
                session,
                field="full_name",
                selector=mapping.full_name_selector,
                value=content.full_name,
                required=True,
            )
        )

    report.add(
        _fill_one(
            session,
            field="email",
            selector=mapping.email_selector,
            value=content.email,
            required=True,
        )
    )
    report.add(
        _fill_one(session, field="phone", selector=mapping.phone_selector, value=content.phone)
    )

    if mapping.resume_upload_selector:
        report.add(
            _fill_one(
                session,
                field="resume",
                selector=mapping.resume_upload_selector,
                value=resume_file_path,
                required=True,
                kind="file",
            )
        )

    if mapping.cover_letter_selector:
        report.add(
            _fill_one(
                session,
                field="cover_letter",
                selector=mapping.cover_letter_selector,
                value=package.cover_letter,
            )
        )

    for question_field in mapping.question_fields:
        report.add(
            _fill_one(
                session,
                field=question_field.question,
                selector=question_field.selector,
                value=answers.get(question_field.selector),
                required=getattr(question_field, "required", False),
                kind=question_field.kind,
            )
        )

    return report


def submit_application_form(session: BrowserSession, mapping: FormFieldMapping) -> None:
    session.click(mapping.submit_selector)
