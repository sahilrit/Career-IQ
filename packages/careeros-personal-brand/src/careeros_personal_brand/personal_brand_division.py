"""PersonalBrandDivision: the facade turning one Project into the full
chain of public assets, tracking progress per project.
"""

from __future__ import annotations

from careeros_career_brain import Achievement, CareerBrain, Project
from careeros_personal_brand.case_study import CaseStudy, generate_case_study
from careeros_personal_brand.pipeline_stage import (
    ContentProgress,
    ContentProgressRepository,
    ContentStage,
)
from careeros_personal_brand.portfolio_page import render_portfolio_page
from careeros_personal_brand.resume_achievement import derive_resume_achievement
from careeros_personal_brand.social_content import (
    render_blog_post,
    render_linkedin_post,
    render_x_thread,
)
from careeros_personal_brand.testimonials import Testimonial, TestimonialRepository


class PersonalBrandDivision:
    def __init__(
        self,
        progress_repository: ContentProgressRepository,
        testimonial_repository: TestimonialRepository,
    ) -> None:
        self._progress = progress_repository
        self._testimonials = testimonial_repository

    def generate_case_study(self, brain: CareerBrain, project: Project) -> CaseStudy:
        case_study = generate_case_study(brain, project)
        self._progress.mark_complete(project.id, ContentStage.CASE_STUDY)
        return case_study

    def generate_portfolio_page(self, case_study: CaseStudy, project: Project) -> str:
        page = render_portfolio_page(case_study, project)
        self._progress.mark_complete(project.id, ContentStage.PORTFOLIO)
        return page

    def generate_linkedin_post(self, case_study: CaseStudy) -> str:
        post = render_linkedin_post(case_study)
        self._progress.mark_complete(case_study.project_id, ContentStage.LINKEDIN_POST)
        return post

    def generate_x_thread(self, case_study: CaseStudy) -> list[str]:
        thread = render_x_thread(case_study)
        self._progress.mark_complete(case_study.project_id, ContentStage.X_THREAD)
        return thread

    def generate_blog_post(self, case_study: CaseStudy) -> str:
        post = render_blog_post(case_study)
        self._progress.mark_complete(case_study.project_id, ContentStage.BLOG)
        return post

    def generate_resume_achievement(self, case_study: CaseStudy, project: Project) -> Achievement:
        achievement = derive_resume_achievement(case_study, project)
        self._progress.mark_complete(project.id, ContentStage.RESUME_ACHIEVEMENT)
        return achievement

    def add_testimonial(self, testimonial: Testimonial) -> None:
        self._testimonials.save(testimonial)

    def testimonials_for(self, project_id: str) -> list[Testimonial]:
        return self._testimonials.list_for_project(project_id)

    def progress_for(self, project_id: str) -> ContentProgress:
        return self._progress.load(project_id)
