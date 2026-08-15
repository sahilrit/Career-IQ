"""Tests for career_brain_actions.py."""

from __future__ import annotations

from datetime import date

from careeros_career_brain import CareerBrainRepository
from careeros_dashboard.career_brain_actions import (
    add_achievement,
    add_award,
    add_certification,
    add_education,
    add_experience,
    add_goal,
    add_language,
    add_project,
    add_skill,
    get_or_create_brain,
    update_preferences,
    update_summary,
)


def test_get_or_create_brain_creates_when_store_is_empty(store):
    brain = get_or_create_brain(store, full_name="Ada Lovelace", email="ada@example.com")
    assert brain.identity.full_name == "Ada Lovelace"
    assert CareerBrainRepository(store).list_all() == [brain]


def test_get_or_create_brain_returns_the_existing_brain(store):
    first = get_or_create_brain(store, full_name="Ada Lovelace", email="ada@example.com")
    second = get_or_create_brain(store, full_name="Someone Else", email="other@example.com")
    assert second.identity.id == first.identity.id


def test_add_skill_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_skill(store, brain, "Python", 5)
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.skills[0].name == "Python"


def test_add_project_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_project(store, brain, name="Open Source Tool", skills_used=["Python"])
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.projects[0].name == "Open Source Tool"


def test_add_goal_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_goal(store, brain, "Land a staff engineer role")
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.goals[0].description == "Land a staff engineer role"


def test_add_experience_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_experience(
        store, brain, company_name="Acme", title="Backend Engineer", start_date=date(2020, 1, 1)
    )
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.experiences[0].company_name == "Acme"


def test_add_achievement_attaches_to_the_right_experience(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_experience(
        store, brain, company_name="Acme", title="Backend Engineer", start_date=date(2020, 1, 1)
    )
    experience_id = brain.experiences[0].id
    brain = add_achievement(
        store, brain, experience_id, description="Shipped a feature", metric="+10% signups"
    )
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.experiences[0].achievements[0].description == "Shipped a feature"


def test_update_preferences_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = update_preferences(store, brain, desired_titles=["Staff Engineer"], remote_only=True)
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.preferences.desired_titles == ["Staff Engineer"]
    assert reloaded.preferences.remote_only is True


def test_update_summary_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = update_summary(store, brain, "Results-driven engineer.")
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.identity.summary == "Results-driven engineer."


def test_add_education_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_education(store, brain, institution="Axis College", credential="BCA")
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.education[0].institution == "Axis College"


def test_add_certification_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_certification(store, brain, name="Digital Marketing", issuer="HubSpot Academy")
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.certifications[0].name == "Digital Marketing"
    assert reloaded.certifications[0].issuer == "HubSpot Academy"


def test_add_language_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_language(store, brain, "Spanish", "fluent")
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.languages[0].name == "Spanish"
    assert reloaded.languages[0].proficiency == "fluent"


def test_add_award_persists(store):
    brain = get_or_create_brain(store, full_name="Ada", email="ada@example.com")
    brain = add_award(store, brain, title="Employee of the Year", issuer="Acme")
    reloaded = CareerBrainRepository(store).load(brain.identity.id)
    assert reloaded.awards[0].title == "Employee of the Year"
