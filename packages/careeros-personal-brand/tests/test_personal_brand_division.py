"""Tests for the PersonalBrandDivision facade."""

from __future__ import annotations

import pytest

from careeros_personal_brand import ContentStage, PersonalBrandDivision, Testimonial


@pytest.fixture
def division(progress_repository, testimonial_repository):
    return PersonalBrandDivision(progress_repository, testimonial_repository)


def test_generate_case_study_marks_case_study_stage(division, brain, project):
    division.generate_case_study(brain, project)
    assert division.progress_for(project.id).current_stage == ContentStage.CASE_STUDY


def test_full_chain_advances_progress_to_final_stage(division, brain, project):
    case_study = division.generate_case_study(brain, project)
    division.generate_portfolio_page(case_study, project)
    division.generate_linkedin_post(case_study)
    division.generate_x_thread(case_study)
    division.generate_blog_post(case_study)
    division.generate_resume_achievement(case_study, project)
    assert division.progress_for(project.id).current_stage == ContentStage.RESUME_ACHIEVEMENT


def test_add_and_list_testimonials(division, project):
    testimonial = Testimonial(author_name="Jane", quote="Excellent work.", project_id=project.id)
    division.add_testimonial(testimonial)
    assert division.testimonials_for(project.id) == [testimonial]
