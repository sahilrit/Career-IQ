"""Tests for the unified score_opportunity heuristic."""

from __future__ import annotations

import pytest

from careeros_career_brain import Preferences, Skill
from careeros_opportunity_intelligence import Opportunity, OpportunityKind, score_opportunity


def _opportunity(**overrides) -> Opportunity:
    defaults = {
        "kind": OpportunityKind.EMPLOYMENT,
        "source_provider": "remoteok",
        "external_id": "1",
        "title": "Backend Engineer",
        "organization_name": "Acme",
        "url": "https://example.com/1",
        "tags": ["python"],
    }
    defaults.update(overrides)
    return Opportunity(**defaults)


def test_full_skill_overlap_scores_higher_than_none(brain_factory):
    brain = brain_factory(skills=[Skill(name="Python", proficiency=5)])
    matching = _opportunity(tags=["python"])
    non_matching = _opportunity(tags=["rust"])
    assert score_opportunity(matching, brain) > score_opportunity(non_matching, brain)


def test_employment_title_preference_affects_score(brain_factory):
    brain = brain_factory(
        skills=[Skill(name="Python", proficiency=5)],
        preferences=Preferences(desired_titles=["Backend Engineer"]),
    )
    matching_title = _opportunity(title="Backend Engineer")
    other_title = _opportunity(title="Completely Unrelated Role")
    assert score_opportunity(matching_title, brain) > score_opportunity(other_title, brain)


def test_freelance_kind_ignores_title_preference(brain_factory):
    brain = brain_factory(
        skills=[Skill(name="Python", proficiency=5)],
        preferences=Preferences(desired_titles=["Backend Engineer"]),
    )
    matching_title = _opportunity(kind=OpportunityKind.FREELANCE, title="Backend Engineer")
    mismatched_title = _opportunity(kind=OpportunityKind.FREELANCE, title="Anything At All")

    # Title mismatch must not penalize a freelance opportunity the way it
    # would an employment one: both score identically here.
    assert score_opportunity(matching_title, brain) == pytest.approx(
        score_opportunity(mismatched_title, brain)
    )


def test_score_is_between_zero_and_one(brain_factory):
    brain = brain_factory()
    opportunity = _opportunity(tags=[])
    score = score_opportunity(opportunity, brain)
    assert 0.0 <= score <= 1.0
