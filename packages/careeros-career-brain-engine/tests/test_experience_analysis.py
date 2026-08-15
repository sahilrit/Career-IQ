"""Tests for experience analysis: tenure, seniority, gaps."""

from __future__ import annotations

from datetime import date

from careeros_career_brain import Experience
from careeros_career_brain_engine import (
    SeniorityLevel,
    detect_experience_gaps,
    seniority_level,
    total_years_of_experience,
)


def test_total_years_sums_closed_roles(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(
                company_name="A",
                title="Engineer",
                start_date=date(2018, 1, 1),
                end_date=date(2020, 1, 1),
            ),
            Experience(
                company_name="B",
                title="Engineer",
                start_date=date(2020, 1, 1),
                end_date=date(2022, 1, 1),
            ),
        ]
    )
    assert total_years_of_experience(brain) == 4.0


def test_total_years_counts_current_role_up_to_as_of(brain_factory):
    brain = brain_factory(
        experiences=[Experience(company_name="A", title="Engineer", start_date=date(2020, 1, 1))]
    )
    years = total_years_of_experience(brain, as_of=date(2022, 1, 1))
    assert years == 2.0


def test_seniority_level_detects_lead_keywords(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(company_name="A", title="Engineering Director", start_date=date(2020, 1, 1))
        ]
    )
    assert seniority_level(brain) == SeniorityLevel.LEAD


def test_seniority_level_detects_senior_keywords(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(
                company_name="A", title="Senior Backend Engineer", start_date=date(2020, 1, 1)
            )
        ]
    )
    assert seniority_level(brain) == SeniorityLevel.SENIOR


def test_seniority_level_detects_junior_keywords(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(company_name="A", title="Junior Developer", start_date=date(2020, 1, 1))
        ]
    )
    assert seniority_level(brain) == SeniorityLevel.ENTRY


def test_seniority_level_falls_back_to_tenure_when_no_keywords(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(
                company_name="A",
                title="Engineer",
                start_date=date(2010, 1, 1),
                end_date=date(2020, 1, 1),
            )
        ]
    )
    assert seniority_level(brain) == SeniorityLevel.LEAD


def test_seniority_level_with_no_experience_is_entry(brain_factory):
    brain = brain_factory()
    assert seniority_level(brain) == SeniorityLevel.ENTRY


def test_detect_experience_gaps_finds_a_long_gap(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(
                company_name="A",
                title="Engineer",
                start_date=date(2018, 1, 1),
                end_date=date(2019, 1, 1),
            ),
            Experience(
                company_name="B",
                title="Engineer",
                start_date=date(2019, 8, 1),  # ~7 months later
            ),
        ]
    )
    gaps = detect_experience_gaps(brain, min_gap_days=90)
    assert len(gaps) == 1
    assert gaps[0].gap_days > 90


def test_no_gap_when_roles_are_adjacent(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(
                company_name="A",
                title="Engineer",
                start_date=date(2018, 1, 1),
                end_date=date(2019, 1, 1),
            ),
            Experience(company_name="B", title="Engineer", start_date=date(2019, 1, 5)),
        ]
    )
    assert detect_experience_gaps(brain, min_gap_days=90) == []


def test_current_role_never_produces_a_trailing_gap(brain_factory):
    brain = brain_factory(
        experiences=[Experience(company_name="A", title="Engineer", start_date=date(2018, 1, 1))]
    )
    assert detect_experience_gaps(brain) == []
