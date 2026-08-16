"""careeros_application_engine: generates resumes, cover letters,
application answers, and ATS reports from Career Brain — every word
sourced from real data, nothing fabricated, no paid AI required.
"""

from careeros_application_engine.answers import (
    ANSWER_GENERATORS,
    answer_greatest_achievement,
    answer_why_this_role,
    answer_why_you,
    generate_answers,
)
from careeros_application_engine.ats import ATSReport, ats_keyword_coverage
from careeros_application_engine.cover_letter import (
    CoverLetterGenerator,
    TemplateCoverLetterGenerator,
)
from careeros_application_engine.package import ApplicationPackage, build_application_package
from careeros_application_engine.question_answering import Answer, QuestionAnswerer
from careeros_application_engine.resume import (
    ResumeContent,
    build_resume_content,
    render_resume_html,
    render_resume_markdown,
    render_resume_text,
)

__all__ = [
    "ANSWER_GENERATORS",
    "ATSReport",
    "Answer",
    "ApplicationPackage",
    "CoverLetterGenerator",
    "QuestionAnswerer",
    "ResumeContent",
    "TemplateCoverLetterGenerator",
    "answer_greatest_achievement",
    "answer_why_this_role",
    "answer_why_you",
    "ats_keyword_coverage",
    "build_application_package",
    "build_resume_content",
    "generate_answers",
    "render_resume_html",
    "render_resume_markdown",
    "render_resume_text",
]
