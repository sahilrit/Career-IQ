"""Tests for the AISkillMarketplace facade."""

from __future__ import annotations

import pytest

from careeros_skill_marketplace import AISkillCategory, AISkillMarketplace, SkillNotFoundError


def test_list_skills_returns_everything_with_no_filter(skills):
    marketplace = AISkillMarketplace(skills)
    assert len(marketplace.list_skills()) == len(skills)


def test_list_skills_filters_by_category(skills):
    marketplace = AISkillMarketplace(skills)
    resume_skills = marketplace.list_skills(category=AISkillCategory.RESUME_OPTIMIZATION)
    assert len(resume_skills) == 1
    assert resume_skills[0].skill_id == "resume-optimization"


def test_available_skills_excludes_unimplemented_ones(skills):
    marketplace = AISkillMarketplace(skills)
    available_ids = {skill.skill_id for skill in marketplace.available_skills()}
    assert "linkedin-optimization" not in available_ids
    assert "resume-optimization" in available_ids


def test_search_matches_name(skills):
    marketplace = AISkillMarketplace(skills)
    results = marketplace.search("shopify")
    assert any(skill.skill_id == "shopify-cro-audit" for skill in results)


def test_get_returns_the_matching_skill(skills):
    marketplace = AISkillMarketplace(skills)
    assert marketplace.get("career-strategy").name == "Career Strategy"


def test_get_raises_for_an_unknown_id(skills):
    marketplace = AISkillMarketplace(skills)
    with pytest.raises(SkillNotFoundError):
        marketplace.get("not-a-real-skill")
