"""Tests for proficiency-weighted skill matching."""

from __future__ import annotations

from careeros_career_brain import Skill
from careeros_career_brain_engine import match_skills, skills_by_category


def test_empty_required_skills_scores_perfectly(brain_factory):
    brain = brain_factory()
    result = match_skills(brain, [])
    assert result.score == 1.0
    assert result.matched_skills == []


def test_full_proficiency_match_scores_one(brain_factory):
    brain = brain_factory(skills=[Skill(name="Python", proficiency=5)])
    result = match_skills(brain, ["Python"])
    assert result.score == 1.0
    assert result.matched_skills == ["Python"]


def test_low_proficiency_scores_lower_than_high_proficiency(brain_factory):
    low = brain_factory(skills=[Skill(name="Python", proficiency=1)])
    high = brain_factory(skills=[Skill(name="Python", proficiency=5)])
    assert match_skills(low, ["Python"]).score < match_skills(high, ["Python"]).score


def test_missing_skill_is_reported(brain_factory):
    brain = brain_factory(skills=[Skill(name="Python", proficiency=5)])
    result = match_skills(brain, ["Python", "Rust"])
    assert result.missing_skills == ["Rust"]
    assert result.matched_skills == ["Python"]
    assert result.score == 0.5


def test_matching_is_case_insensitive(brain_factory):
    brain = brain_factory(skills=[Skill(name="python", proficiency=5)])
    result = match_skills(brain, ["Python"])
    assert result.matched_skills == ["Python"]


def test_skills_by_category_groups_by_category(brain_factory):
    brain = brain_factory(
        skills=[
            Skill(name="Python", category="language"),
            Skill(name="Django", category="framework"),
            Skill(name="SQL", category="language"),
        ]
    )
    grouped = skills_by_category(brain)
    assert set(grouped["language"]) == {"Python", "SQL"}
    assert grouped["framework"] == ["Django"]
