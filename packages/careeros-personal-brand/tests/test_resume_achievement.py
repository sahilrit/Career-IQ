"""Tests for derive_resume_achievement."""

from __future__ import annotations

from careeros_personal_brand import derive_resume_achievement, generate_case_study


def test_derived_achievement_mentions_approach_and_result(brain, project):
    case_study = generate_case_study(brain, project)
    achievement = derive_resume_achievement(case_study, project)
    assert case_study.result in achievement.description


def test_derived_achievement_carries_project_skills(brain, project):
    case_study = generate_case_study(brain, project)
    achievement = derive_resume_achievement(case_study, project)
    assert achievement.skills_demonstrated == project.skills_used
