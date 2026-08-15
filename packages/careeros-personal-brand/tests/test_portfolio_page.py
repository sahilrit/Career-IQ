"""Tests for render_portfolio_page."""

from __future__ import annotations

from careeros_personal_brand import generate_case_study, render_portfolio_page


def test_page_includes_all_sections(brain, project):
    case_study = generate_case_study(brain, project)
    page = render_portfolio_page(case_study, project)
    assert "## Problem" in page
    assert "## Approach" in page
    assert "## Result" in page
    assert case_study.problem in page


def test_page_includes_project_url_when_present(brain, project):
    case_study = generate_case_study(brain, project)
    page = render_portfolio_page(case_study, project)
    assert project.url in page


def test_page_omits_url_link_when_absent(brain, project):
    project_no_url = project.model_copy(update={"url": None})
    case_study = generate_case_study(brain, project_no_url)
    page = render_portfolio_page(case_study, project_no_url)
    assert "View project" not in page
