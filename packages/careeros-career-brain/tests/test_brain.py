"""Tests for the CareerBrain aggregate."""

from __future__ import annotations

from datetime import date

from careeros_career_brain import Application, CareerBrain, Experience, Identity, Skill


def _brain(**overrides) -> CareerBrain:
    defaults = {"identity": Identity(full_name="Ada Lovelace", email="ada@example.com")}
    defaults.update(overrides)
    return CareerBrain(**defaults)


def test_current_experience_returns_the_role_with_no_end_date():
    brain = _brain(
        experiences=[
            Experience(
                company_name="Old Co",
                title="Junior Engineer",
                start_date=date(2018, 1, 1),
                end_date=date(2020, 1, 1),
            ),
            Experience(company_name="New Co", title="Senior Engineer", start_date=date(2020, 1, 2)),
        ]
    )
    assert brain.current_experience.company_name == "New Co"


def test_current_experience_is_none_when_no_current_role():
    brain = _brain(
        experiences=[
            Experience(
                company_name="Old Co",
                title="Junior Engineer",
                start_date=date(2018, 1, 1),
                end_date=date(2020, 1, 1),
            )
        ]
    )
    assert brain.current_experience is None


def test_skill_names_are_lowercased():
    brain = _brain(skills=[Skill(name="Python"), Skill(name="SQL")])
    assert brain.skill_names() == {"python", "sql"}


def test_find_application_by_job_url():
    app = Application(job_title="Engineer", company_name="Acme", job_url="https://acme.example/1")
    brain = _brain(applications=[app])
    assert brain.find_application_by_job_url("https://acme.example/1") is app
    assert brain.find_application_by_job_url("https://nope.example") is None
