"""Tests for ApplicationRunner.submit: the full validate -> fill ->
submit -> verify -> screenshot pipeline, against FakeBrowserSession.
"""

from __future__ import annotations

from careeros_application_runner import ApplicationRunner, FormFieldMapping


def test_successful_submission(session, package):
    mapping = FormFieldMapping(
        full_name_selector="#name", submit_selector="#submit", success_selector="#success"
    )
    session.set_visible("#submit")
    session.set_visible("#success")  # fake session has no dynamic page transitions

    runner = ApplicationRunner(screenshot_dir="/tmp/careeros-screenshots")
    result = runner.submit(session, package, mapping, application_id="job-1")

    assert result.success is True
    assert result.attempts == 1
    assert session.clicked_selectors == ["#submit"]
    assert len(result.screenshots) == 2  # before-submit + success


def test_validation_failure_short_circuits_before_any_attempt(session, package):
    mapping = FormFieldMapping(submit_selector="#submit", success_selector="#success")
    # submit button never made visible

    runner = ApplicationRunner()
    result = runner.submit(session, package, mapping)

    assert result.success is False
    assert result.attempts == 0
    assert session.clicked_selectors == []


def test_missing_success_indicator_retries_then_fails(session, package):
    mapping = FormFieldMapping(submit_selector="#submit", success_selector="#success")
    session.set_visible("#submit")
    # success selector never becomes visible

    runner = ApplicationRunner(max_attempts=2, screenshot_dir="/tmp/careeros-screenshots")
    result = runner.submit(session, package, mapping, application_id="job-2")

    assert result.success is False
    assert result.attempts == 2
    assert result.errors
    # before-submit screenshot per attempt (2) + one error screenshot
    assert len(result.screenshots) == 3


def test_resume_is_uploaded_when_mapping_requires_it(session, package):
    mapping = FormFieldMapping(
        resume_upload_selector="#resume", submit_selector="#submit", success_selector="#success"
    )
    session.set_visible("#submit")
    session.set_visible("#success")

    runner = ApplicationRunner(screenshot_dir="/tmp/careeros-screenshots")
    result = runner.submit(session, package, mapping, resume_file_path="/tmp/resume.pdf")

    assert result.success is True
    assert session.uploaded_files["#resume"] == "/tmp/resume.pdf"


def test_missing_resume_path_fails_validation_before_touching_the_page(session, package):
    mapping = FormFieldMapping(
        resume_upload_selector="#resume", submit_selector="#submit", success_selector="#success"
    )
    session.set_visible("#submit")

    runner = ApplicationRunner()
    result = runner.submit(session, package, mapping, resume_file_path=None)

    assert result.success is False
    assert session.uploaded_files == {}
