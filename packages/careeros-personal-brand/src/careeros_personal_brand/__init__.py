"""careeros_personal_brand: the Personal Brand Division.

Turns career activity into public assets:

    Project -> Case Study -> Portfolio -> LinkedIn Post -> X Thread
      -> Blog -> Resume Achievement
"""

from careeros_personal_brand.case_study import CaseStudy, generate_case_study
from careeros_personal_brand.exceptions import PersonalBrandError
from careeros_personal_brand.personal_brand_division import PersonalBrandDivision
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

__all__ = [
    "CaseStudy",
    "ContentProgress",
    "ContentProgressRepository",
    "ContentStage",
    "PersonalBrandDivision",
    "PersonalBrandError",
    "Testimonial",
    "TestimonialRepository",
    "derive_resume_achievement",
    "generate_case_study",
    "render_blog_post",
    "render_linkedin_post",
    "render_portfolio_page",
    "render_x_thread",
]
