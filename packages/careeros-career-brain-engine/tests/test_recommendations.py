"""Tests for rule-based recommendations."""

from __future__ import annotations

from datetime import date

from careeros_career_brain import Achievement, Experience, Identity, Preferences, Skill
from careeros_career_brain_engine import generate_recommendations


def test_empty_brain_flags_every_completeness_issue(brain_factory):
    brain = brain_factory()
    codes = {r.code for r in generate_recommendations(brain)}
    assert {"missing_headline", "no_skills", "no_current_experience", "no_desired_titles"} <= codes


def test_complete_brain_has_no_completeness_recommendations(brain_factory):
    brain = brain_factory(
        identity=Identity(full_name="Ada", email="ada@example.com", headline="Backend Engineer"),
        skills=[Skill(name="Python")],
        preferences=Preferences(desired_titles=["Backend Engineer"]),
        experiences=[
            Experience(
                company_name="Acme",
                title="Backend Engineer",
                start_date=date(2020, 1, 1),
                achievements=[Achievement(description="Shipped feature", metric="+10% signups")],
            )
        ],
    )
    codes = {r.code for r in generate_recommendations(brain)}
    assert codes == set()


def test_achievement_without_metric_is_flagged(brain_factory):
    brain = brain_factory(
        identity=Identity(full_name="Ada", email="ada@example.com", headline="Engineer"),
        skills=[Skill(name="Python")],
        preferences=Preferences(desired_titles=["Engineer"]),
        experiences=[
            Experience(
                company_name="Acme",
                title="Engineer",
                start_date=date(2020, 1, 1),
                achievements=[Achievement(description="Did a thing")],
            )
        ],
    )
    codes = {r.code for r in generate_recommendations(brain)}
    assert "achievements_without_metrics" in codes


def test_experience_gap_is_flagged(brain_factory):
    brain = brain_factory(
        identity=Identity(full_name="Ada", email="ada@example.com", headline="Engineer"),
        skills=[Skill(name="Python")],
        preferences=Preferences(desired_titles=["Engineer"]),
        experiences=[
            Experience(
                company_name="Old",
                title="Engineer",
                start_date=date(2015, 1, 1),
                end_date=date(2016, 1, 1),
            ),
            Experience(company_name="New", title="Engineer", start_date=date(2020, 1, 1)),
        ],
    )
    codes = {r.code for r in generate_recommendations(brain)}
    assert "experience_gaps" in codes
