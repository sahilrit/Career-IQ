"""Tests for portfolio summary generation."""

from __future__ import annotations

from careeros_employment_division import build_portfolio_summary, render_portfolio_summary


def test_includes_projects_and_achievements(brain):
    summary = build_portfolio_summary(brain)
    assert summary.projects[0].name == "Open Source Tool"
    assert any("Shipped a feature" in item for item in summary.highlighted_achievements)


def test_achievement_includes_its_metric(brain):
    summary = build_portfolio_summary(brain)
    assert any("+10% signups" in item for item in summary.highlighted_achievements)


def test_max_achievements_limits_the_list(brain_factory):
    from datetime import date

    from careeros_career_brain import Achievement, Experience

    brain = brain_factory(
        experiences=[
            Experience(
                company_name="Acme",
                title="Engineer",
                start_date=date(2020, 1, 1),
                achievements=[Achievement(description=f"Achievement {i}") for i in range(10)],
            )
        ]
    )
    summary = build_portfolio_summary(brain, max_achievements=3)
    assert len(summary.highlighted_achievements) == 3


def test_render_includes_expected_sections(brain):
    summary = build_portfolio_summary(brain)
    text = render_portfolio_summary(summary)
    assert "PROJECTS" in text
    assert "HIGHLIGHTED ACHIEVEMENTS" in text
    assert "Ada Lovelace" in text


def test_render_with_no_projects_omits_that_section(brain_factory):
    brain = brain_factory(projects=[])
    summary = build_portfolio_summary(brain)
    text = render_portfolio_summary(summary)
    assert "PROJECTS" not in text
