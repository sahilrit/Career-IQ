"""Tests for validate_submission."""

from __future__ import annotations

from careeros_application_runner import FormFieldMapping, validate_submission


def test_valid_when_submit_visible_and_no_extra_requirements(session, package):
    mapping = FormFieldMapping(submit_selector="#submit", success_selector="#success")
    session.set_visible("#submit")

    result = validate_submission(session, package, mapping, resume_file_path=None)

    assert result.is_valid
    assert result.errors == []


def test_invalid_when_submit_button_is_not_visible(session, package):
    mapping = FormFieldMapping(submit_selector="#submit", success_selector="#success")

    result = validate_submission(session, package, mapping, resume_file_path=None)

    assert not result.is_valid
    assert any("not visible" in error for error in result.errors)


def test_invalid_when_resume_required_but_no_path_given(session, package):
    mapping = FormFieldMapping(
        resume_upload_selector="#resume",
        submit_selector="#submit",
        success_selector="#success",
    )
    session.set_visible("#submit")

    result = validate_submission(session, package, mapping, resume_file_path=None)

    assert not result.is_valid
    assert any("resume" in error.lower() for error in result.errors)


def test_valid_when_resume_required_and_path_given(session, package):
    mapping = FormFieldMapping(
        resume_upload_selector="#resume",
        submit_selector="#submit",
        success_selector="#success",
    )
    session.set_visible("#submit")

    result = validate_submission(session, package, mapping, resume_file_path="/tmp/resume.pdf")

    assert result.is_valid
