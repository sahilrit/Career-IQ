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


def test_includes_education_certifications_and_languages(brain_factory):
    from careeros_career_brain import Certification, Education, Language

    brain = brain_factory(
        education=[Education(institution="Axis College", credential="BCA")],
        certifications=[Certification(name="Digital Marketing", issuer="HubSpot Academy")],
        languages=[Language(name="Spanish", proficiency="fluent")],
    )
    summary = build_portfolio_summary(brain)
    text = render_portfolio_summary(summary)
    assert "EDUCATION" in text
    assert "BCA, Axis College" in text
    assert "CERTIFICATIONS" in text
    assert "Digital Marketing — HubSpot Academy" in text
    assert "LANGUAGES" in text
    assert "Spanish (fluent)" in text


def test_render_with_no_education_omits_that_section(brain_factory):
    brain = brain_factory(education=[])
    summary = build_portfolio_summary(brain)
    text = render_portfolio_summary(summary)
    assert "EDUCATION" not in text


def test_render_includes_summary_when_present(brain_factory):
    from careeros_career_brain import Identity

    brain = brain_factory(
        identity=Identity(
            full_name="Ada Lovelace",
            email="ada@example.com",
            headline="Engineer",
            summary="Results-driven engineer.",
        )
    )
    summary = build_portfolio_summary(brain)
    text = render_portfolio_summary(summary)
    assert "Results-driven engineer." in text


def test_render_with_no_summary_omits_it(brain):
    summary = build_portfolio_summary(brain)
    text = render_portfolio_summary(summary)
    lines = [line for line in text.splitlines() if line.strip()]
    # name + headline are the only lines before PROJECTS when summary is empty
    assert lines[2] == "PROJECTS"
