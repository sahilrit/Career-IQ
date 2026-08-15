"""Application package: resume (all formats) + cover letter + answers +
ATS report, bundled for one Career Brain against one posting.
"""

from __future__ import annotations

from dataclasses import dataclass

from careeros_application_engine.answers import generate_answers
from careeros_application_engine.ats import ATSReport, ats_keyword_coverage
from careeros_application_engine.cover_letter import (
    CoverLetterGenerator,
    TemplateCoverLetterGenerator,
)
from careeros_application_engine.resume import (
    ResumeContent,
    build_resume_content,
    render_resume_html,
    render_resume_markdown,
    render_resume_text,
)
from careeros_career_brain import CareerBrain
from careeros_job_providers import JobPosting


@dataclass
class ApplicationPackage:
    resume_content: ResumeContent
    resume_text: str
    resume_markdown: str
    resume_html: str
    cover_letter: str
    answers: dict[str, str]
    ats_report: ATSReport


def build_application_package(
    brain: CareerBrain,
    posting: JobPosting,
    *,
    cover_letter_generator: CoverLetterGenerator | None = None,
) -> ApplicationPackage:
    generator = cover_letter_generator or TemplateCoverLetterGenerator()
    resume_content = build_resume_content(brain, posting)
    resume_text = render_resume_text(resume_content)
    return ApplicationPackage(
        resume_content=resume_content,
        resume_text=resume_text,
        resume_markdown=render_resume_markdown(resume_content),
        resume_html=render_resume_html(resume_content),
        cover_letter=generator.generate(brain, posting),
        answers=generate_answers(brain, posting),
        ats_report=ats_keyword_coverage(resume_text, posting),
    )
