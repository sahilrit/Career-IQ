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

import re

from careeros_application_engine import ApplicationPackage
from careeros_application_runner.fill_report import FieldOutcome, FieldResult, FillReport
from careeros_application_runner.form_semantics import ControlKind, classify_control
from careeros_application_runner.models import FormFieldMapping
from careeros_application_runner.retry import TerminalError
from careeros_browser import BrowserSession, best_option_index

#: Some fields cannot be read back by design, and that is not a failure:
#: ``input_value`` is meaningless for a file input, and a contenteditable
#: rich-text box is not an <input> at all.
_UNVERIFIABLE_KINDS = frozenset({"file", "richtext"})


_DIGITS_RE = re.compile(r"\D+")


def _same_number(written: str, actual: str) -> bool:
    """Whether two strings are the same number under different formatting.

    Phone inputs mask what you type. Workable rewrites "+91 91298 32709" to
    "091298 32709" — the country code becomes a local trunk prefix. Reading
    that back and calling it a failed fill blocked otherwise-complete
    applications on a field that was, in fact, correctly filled.

    Compared on the last nine digits rather than as a suffix of one another,
    because the country code is often SUBSTITUTED rather than dropped: "+91 …"
    becomes "0…", so neither string is a suffix of the other while the national
    number is identical. Nine digits is long enough that two genuinely
    different numbers cannot collide, and both sides must reach that length —
    so a short code or an extension never matches by coincidence.
    """
    written_digits = _DIGITS_RE.sub("", written)
    actual_digits = _DIGITS_RE.sub("", actual)
    core = 9
    if len(written_digits) < core or len(actual_digits) < core:
        return False
    return written_digits[-core:] == actual_digits[-core:]


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
    if _same_number(expected, actual):
        # Same number, different formatting — the field's own mask. Filled.
        return True, ""
    return False, f"the field holds {actual[:60]!r} rather than the value written"


def _choose_one(
    session: BrowserSession,
    *,
    field: str,
    value: str,
    required: bool,
    option_selectors: dict[str, str],
) -> FieldResult:
    """Tick the option in a radio/checkbox group that matches ``value``.

    A choice group is answered by clicking the right control, not by writing
    to one — ``fill`` on a radio raises. And the option must actually exist:
    if the answer does not match any of them we leave the group alone rather
    than tick the nearest thing, because a wrong EEO or work-authorization
    answer is worse than an unanswered one.
    """
    options = list(option_selectors)
    index = best_option_index(options, value)
    if index is None:
        return FieldResult(
            field=field,
            selector=next(iter(option_selectors.values()), ""),
            outcome=FieldOutcome.NEEDS_HUMAN,
            detail=(
                f"the answer {value[:40]!r} matches none of this question's options "
                f"({', '.join(options[:5])})"
            ),
            required=required,
        )
    selector = option_selectors[options[index]]
    try:
        session.choose(selector)
    except Exception as exc:
        return FieldResult(
            field=field,
            selector=selector,
            outcome=FieldOutcome.FAILED,
            detail=str(exc)[:200],
            required=required,
        )
    try:
        ticked = session.is_checked(selector)
    except Exception as exc:
        return FieldResult(
            field=field,
            selector=selector,
            outcome=FieldOutcome.UNVERIFIED,
            detail=f"could not confirm the option was selected: {exc}"[:200],
            required=required,
        )
    if not ticked:
        # Clicked, nothing ticked. A custom widget intercepted it — which
        # looks identical to success without this check.
        return FieldResult(
            field=field,
            selector=selector,
            outcome=FieldOutcome.FAILED,
            detail="the option did not become selected after clicking it",
            required=required,
        )
    return FieldResult(
        field=field, selector=selector, outcome=FieldOutcome.FILLED, required=required
    )


def _fill_one(
    session: BrowserSession,
    *,
    field: str,
    selector: str | None,
    value: str | None,
    required: bool = False,
    kind: str = "text",
    option_selectors: dict[str, str] | None = None,
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

    if kind == "choice":
        return _choose_one(
            session,
            field=field,
            value=value,
            required=required,
            option_selectors=option_selectors or {},
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
                option_selectors=getattr(question_field, "option_selectors", None),
            )
        )

    return report


class UnsafeSubmitError(TerminalError):
    """The control we were about to click is not the one that submits.

    Raised instead of clicking. Clicking the wrong control is not a failed
    attempt that can be retried — by then a file dialog is open, a draft is
    saved, or a half-filled application has been sent to the employer.
    """


def submit_application_form(
    session: BrowserSession,
    mapping: FormFieldMapping,
    *,
    verify: bool = True,
) -> None:
    """Click the submit control, after confirming it IS the submit control.

    The final click is the one irreversible action in the whole pipeline, so
    it gets re-verified at the moment it happens rather than trusting a
    selector resolved earlier: a multi-step form re-renders between detection
    and submission, and the element that selector now points at may be a
    different button entirely.

    ``verify=False`` exists only for callers that have already classified the
    control themselves. It is not a way to skip the check.
    """
    selector = mapping.submit_selector
    if verify:
        problem = _why_unsafe_to_submit(session, selector)
        if problem is not None:
            raise UnsafeSubmitError(problem)
    session.click(selector)


def _why_unsafe_to_submit(session: BrowserSession, selector: str) -> str | None:
    """Why clicking ``selector`` would not be a submission, or None if it is.

    Silent on pages whose DOM cannot be inspected: an unverifiable control is
    the situation we were always in before, and refusing to submit at all
    there would break every form that works today.
    """
    try:
        buttons = session.detect_buttons()
    except Exception:
        return None
    if not buttons:
        return None

    match = next((b for b in buttons if (b.get("selector") or "") == selector), None)
    if match is None:
        return (
            f"the submit control {selector!r} is no longer on the page — the form has "
            "changed since it was detected"
        )
    if match.get("disabled"):
        return (
            f"the submit control {selector!r} is disabled — the form still considers "
            "itself incomplete"
        )
    kind = classify_control(match)
    if kind is not ControlKind.SUBMIT_APPLICATION:
        label = (match.get("accessible_name") or match.get("text") or "").strip()
        return (
            f"{selector!r} is a {kind.value} control ({label!r}), not the button that "
            "submits the application"
        )
    return None
