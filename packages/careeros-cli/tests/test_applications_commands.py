"""Tests for `careeros applications` command logic."""

from __future__ import annotations

from careeros_career_brain import Application, ApplicationStatus
from careeros_cli.commands.applications import filter_applications, format_applications


def _app(status: ApplicationStatus = ApplicationStatus.DISCOVERED, **overrides) -> Application:
    app = Application(job_title="Engineer", company_name="Acme", **overrides)
    if status != ApplicationStatus.DISCOVERED:
        app.transition_to(ApplicationStatus.QUALIFIED)
    return app


def test_filter_applications_with_no_status_returns_everything():
    apps = [_app(), _app(ApplicationStatus.QUALIFIED)]
    assert filter_applications(apps, None) == apps


def test_filter_applications_filters_by_status():
    discovered = _app()
    qualified = _app(ApplicationStatus.QUALIFIED)
    result = filter_applications([discovered, qualified], "qualified")
    assert result == [qualified]


def test_format_applications_includes_title_company_and_status():
    app = _app(match_score=0.87)
    formatted = format_applications([app])
    assert "Engineer @ Acme" in formatted
    assert "discovered" in formatted
    assert "0.87" in formatted


def test_format_applications_shows_dash_for_missing_score():
    app = _app()
    formatted = format_applications([app])
    assert "score=-" in formatted


def test_format_applications_with_empty_list_is_empty_string():
    assert format_applications([]) == ""
