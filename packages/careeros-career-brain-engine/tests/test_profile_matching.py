"""Tests for the combined profile-to-posting match report."""

from __future__ import annotations

from datetime import date

from careeros_career_brain import Achievement, Experience, Skill
from careeros_career_brain_engine import SeniorityLevel, match_profile_to_posting
from careeros_job_providers import JobPosting


def _posting(**overrides) -> JobPosting:
    defaults = {
        "source_provider": "remoteok",
        "external_id": "1",
        "title": "Senior Python Engineer",
        "company_name": "Acme",
        "url": "https://example.com/1",
        "tags": ["python", "django"],
        "description": "Own our Shopify integration and checkout flow.",
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


def test_combines_skill_match_seniority_and_achievements(brain_factory):
    brain = brain_factory(
        skills=[Skill(name="Python", proficiency=5), Skill(name="Django", proficiency=4)],
        experiences=[
            Experience(
                company_name="Acme",
                title="Senior Backend Engineer",
                start_date=date(2020, 1, 1),
                achievements=[
                    Achievement(description="Rebuilt our Shopify checkout flow"),
                    Achievement(description="Unrelated internal tooling work"),
                ],
            )
        ],
    )

    result = match_profile_to_posting(brain, _posting())

    assert result.skill_match.matched_skills == ["python", "django"]
    assert result.seniority == SeniorityLevel.SENIOR
    assert len(result.top_achievements) >= 1
    assert "Shopify" in result.top_achievements[0].achievement.description


def test_empty_brain_still_returns_a_result_without_erroring(brain_factory):
    brain = brain_factory()
    result = match_profile_to_posting(brain, _posting())
    assert result.skill_match.matched_skills == []
    assert result.top_achievements == []
