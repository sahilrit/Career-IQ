"""careeros_application_engine: generates resumes, cover letters,
application answers, and ATS reports from Career Brain — every word
sourced from real data, nothing fabricated, no paid AI required.
"""

from careeros_application_engine.ai_cover_letter import AICoverLetterGenerator
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
from careeros_application_engine.eligibility import disqualifying_requirement
from careeros_application_engine.package import ApplicationPackage, build_application_package
from careeros_application_engine.question_answering import (
    Answer,
    Confidence,
    QuestionAnswerer,
    UnansweredQuestion,
    memory_key_for,
    remember_answer,
)
from careeros_application_engine.resume import (
    ResumeContent,
    build_resume_content,
    render_resume_html,
    render_resume_markdown,
    render_resume_text,
)
from careeros_application_engine.review import (
    AiReviewReport,
    ApplicationReview,
    ReviewFinding,
    Severity,
    check_disputed_claims,
    check_unqualified_figures,
    deterministic_review,
    parse_review_output,
    profile_facts,
    review_application_draft,
)

__all__ = [
    "ANSWER_GENERATORS",
    "AICoverLetterGenerator",
    "ATSReport",
    "AiReviewReport",
    "Answer",
    "ApplicationPackage",
    "ApplicationReview",
    "Confidence",
    "CoverLetterGenerator",
    "QuestionAnswerer",
    "ResumeContent",
    "ReviewFinding",
    "Severity",
    "TemplateCoverLetterGenerator",
    "UnansweredQuestion",
    "answer_greatest_achievement",
    "answer_why_this_role",
    "answer_why_you",
    "ats_keyword_coverage",
    "build_application_package",
    "build_resume_content",
    "check_disputed_claims",
    "check_unqualified_figures",
    "deterministic_review",
    "disqualifying_requirement",
    "generate_answers",
    "memory_key_for",
    "parse_review_output",
    "profile_facts",
    "remember_answer",
    "render_resume_html",
    "render_resume_markdown",
    "render_resume_text",
    "review_application_draft",
]
