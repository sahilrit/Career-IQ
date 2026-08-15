"""Tests for generate_case_study."""

from __future__ import annotations

from careeros_career_brain import CareerBrain, Identity, Project
from careeros_personal_brand import generate_case_study


def test_case_study_uses_project_description_as_problem(brain, project):
    case_study = generate_case_study(brain, project)
    assert case_study.problem == project.description


def test_case_study_approach_mentions_skills(brain, project):
    case_study = generate_case_study(brain, project)
    assert "Python" in case_study.approach
    assert "CLI design" in case_study.approach


def test_case_study_result_uses_the_real_ranked_achievement(brain, project):
    case_study = generate_case_study(brain, project)
    assert "saved 3 hours/week" in case_study.result


def test_case_study_falls_back_when_no_relevant_achievement_exists():
    brain = CareerBrain(identity=Identity(full_name="Ada", email="ada@example.com"))
    project = Project(name="Unrelated Project", description="Something with zero overlap.")
    case_study = generate_case_study(brain, project)
    assert case_study.result == "Shipped and in active use."
