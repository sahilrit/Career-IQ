"""Tests for the seed skills' honesty guarantees."""

from __future__ import annotations

from careeros_skill_marketplace import SEED_SKILLS, AISkillCategory


def test_every_available_skill_names_a_real_source_package():
    for skill in SEED_SKILLS:
        if skill.is_available:
            assert skill.source_package.startswith("careeros-")


def test_unavailable_skills_say_not_yet_implemented():
    for skill in SEED_SKILLS:
        if not skill.is_available:
            assert "not yet implemented" in skill.description.lower()


def test_linkedin_optimization_is_the_only_unavailable_skill():
    unavailable_ids = {skill.skill_id for skill in SEED_SKILLS if not skill.is_available}
    assert unavailable_ids == {"linkedin-optimization"}


def test_every_skill_has_a_unique_id():
    ids = [skill.skill_id for skill in SEED_SKILLS]
    assert len(ids) == len(set(ids))


def test_every_category_is_represented():
    categories = {skill.category for skill in SEED_SKILLS}
    assert categories == set(AISkillCategory)
