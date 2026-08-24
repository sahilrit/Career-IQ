"""Tests for fill_application_form / submit_application_form."""

from __future__ import annotations

from careeros_application_runner import fill_application_form, submit_application_form
from careeros_application_runner.models import FormFieldMapping


def test_fills_name_email_and_phone(session, package):
    mapping = FormFieldMapping(
        full_name_selector="#name",
        email_selector="#email",
        phone_selector="#phone",
        submit_selector="#submit",
        success_selector="#success",
    )

    fill_application_form(session, package, mapping)

    assert session.field_value("#name") == "Ada Lovelace"
    assert session.field_value("#email") == "ada@example.com"
    assert session.field_value("#phone") == "+1-555-0100"


def test_uploads_resume_when_selector_and_path_given(session, package):
    mapping = FormFieldMapping(
        resume_upload_selector="#resume", submit_selector="#submit", success_selector="#success"
    )

    fill_application_form(session, package, mapping, resume_file_path="/tmp/resume.pdf")

    assert session.uploaded_files["#resume"] == "/tmp/resume.pdf"


def test_skips_resume_upload_without_a_path(session, package):
    mapping = FormFieldMapping(
        resume_upload_selector="#resume", submit_selector="#submit", success_selector="#success"
    )

    fill_application_form(session, package, mapping, resume_file_path=None)

    assert session.uploaded_files == {}


def test_fills_cover_letter_field(session, package):
    mapping = FormFieldMapping(
        cover_letter_selector="#cover", submit_selector="#submit", success_selector="#success"
    )

    fill_application_form(session, package, mapping)

    assert session.field_value("#cover") == package.cover_letter


def test_cover_letter_fill_failure_does_not_abort_the_application(package):
    """A file-input cover-letter field (can't be typed into) must not sink the
    whole submission — the résumé and core fields still go in."""
    from careeros_browser import FakeBrowserSession

    class PickySession(FakeBrowserSession):
        def fill(self, selector, value):
            if selector == "#cover_letter":
                raise RuntimeError('Input of type "file" cannot be filled')
            super().fill(selector, value)

    session = PickySession()
    mapping = FormFieldMapping(
        email_selector="#email",
        resume_upload_selector="#resume",
        cover_letter_selector="#cover_letter",  # turns out to be a file input
        submit_selector="#submit",
        success_selector="#success",
    )

    # Does not raise, and the core fields are still filled/uploaded.
    fill_application_form(session, package, mapping, resume_file_path="/tmp/resume.pdf")
    assert session.field_value("#email") == "ada@example.com"
    assert session.uploaded_files["#resume"] == "/tmp/resume.pdf"
    assert session.field_value("#cover_letter") is None


def test_submit_clicks_the_submit_selector(session):
    mapping = FormFieldMapping(submit_selector="#submit", success_selector="#success")
    submit_application_form(session, mapping)
    assert session.clicked_selectors == ["#submit"]
