"""Tests for Career Brain domain models and domain rules."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from careeros_career_brain import (
    Application,
    ApplicationStatus,
    Certification,
    Education,
    Experience,
    InvalidStatusTransitionError,
    Preferences,
    Skill,
)


def test_experience_rejects_end_date_before_start_date():
    with pytest.raises(ValidationError):
        Experience(
            company_name="Acme",
            title="Engineer",
            start_date=date(2024, 1, 1),
            end_date=date(2023, 1, 1),
        )


def test_experience_with_no_end_date_is_current():
    exp = Experience(company_name="Acme", title="Engineer", start_date=date(2024, 1, 1))
    assert exp.is_current is True


def test_experience_with_end_date_is_not_current():
    exp = Experience(
        company_name="Acme",
        title="Engineer",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 1, 1),
    )
    assert exp.is_current is False


def test_skill_proficiency_must_be_in_range():
    with pytest.raises(ValidationError):
        Skill(name="Python", proficiency=6)


def test_preferences_rejects_negative_min_salary():
    with pytest.raises(ValidationError):
        Preferences(min_salary=-1)


def test_application_starts_discovered_with_seeded_history():
    app = Application(job_title="Backend Engineer", company_name="Acme")
    assert app.status == ApplicationStatus.DISCOVERED
    assert len(app.history) == 1
    assert app.history[0].status == ApplicationStatus.DISCOVERED


def test_application_valid_transition_updates_status_and_history():
    app = Application(job_title="Backend Engineer", company_name="Acme")
    app.transition_to(ApplicationStatus.QUALIFIED, note="matches skills")
    assert app.status == ApplicationStatus.QUALIFIED
    assert len(app.history) == 2
    assert app.history[-1].note == "matches skills"


def test_application_rejects_skipping_states():
    app = Application(job_title="Backend Engineer", company_name="Acme")
    with pytest.raises(InvalidStatusTransitionError):
        app.transition_to(ApplicationStatus.OFFER)


def test_application_terminal_states_have_no_outgoing_transitions():
    app = Application(job_title="Backend Engineer", company_name="Acme")
    app.transition_to(ApplicationStatus.QUALIFIED)
    app.transition_to(ApplicationStatus.APPLIED)
    app.transition_to(ApplicationStatus.REJECTED)
    with pytest.raises(InvalidStatusTransitionError):
        app.transition_to(ApplicationStatus.APPLIED)


def test_education_rejects_end_date_before_start_date():
    with pytest.raises(ValidationError):
        Education(
            institution="Axis College",
            credential="BCA",
            start_date=date(2023, 1, 1),
            end_date=date(2020, 1, 1),
        )


def test_education_with_no_dates_is_valid():
    education = Education(institution="Axis College", credential="BCA")
    assert education.end_date is None


def test_certification_rejects_expiration_before_issued_date():
    with pytest.raises(ValidationError):
        Certification(
            name="Digital Marketing",
            issued_date=date(2023, 1, 1),
            expiration_date=date(2020, 1, 1),
        )
