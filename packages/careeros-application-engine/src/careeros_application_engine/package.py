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
from careeros_application_engine.review import ApplicationReview, review_application_draft
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
    #: The drafter → reviewer second pass over the cover letter. None only when
    #: review was explicitly switched off; a package generated normally always
    #: carries one, because an unreviewed draft is how a fabricated employer
    #: reaches an employer.
    review: ApplicationReview | None = None

    @property
    def is_safe_to_send(self) -> bool:
        """No fabricated claim survived review.

        A package that was never reviewed is NOT treated as safe: absence of
        findings and absence of checking must not look the same to a caller.
        """
        return self.review is not None and self.review.is_safe_to_send


def build_application_package(
    brain: CareerBrain,
    posting: JobPosting,
    *,
    cover_letter_generator: CoverLetterGenerator | None = None,
    reviewer_client=None,
    review: bool = True,
) -> ApplicationPackage:
    """Build the package and review the draft before handing it back.

    ``reviewer_client`` should be an AIClient routed to ``LLMTask.REVIEW`` so
    the reviewer prefers a different provider than whatever wrote the letter.
    Without one, the deterministic fabrication checks still run — those are the
    ones that catch invented employers, metrics and degrees, and they need no
    AI at all.
    """
    generator = cover_letter_generator or TemplateCoverLetterGenerator()
    resume_content = build_resume_content(brain, posting)
    resume_text = render_resume_text(resume_content)
    cover_letter = generator.generate(brain, posting)

    package_review = None
    if review:
        package_review = review_application_draft(
            cover_letter,
            brain,
            ai_client=reviewer_client,
            # The employer being applied to, and the candidate's own name, are
            # legitimately in the letter and must not read as fabrications.
            allowed_extra={posting.company_name, brain.identity.full_name},
            context=f"{posting.title} at {posting.company_name}",
        )

    return ApplicationPackage(
        resume_content=resume_content,
        resume_text=resume_text,
        resume_markdown=render_resume_markdown(resume_content),
        resume_html=render_resume_html(resume_content),
        cover_letter=cover_letter,
        answers=generate_answers(brain, posting),
        ats_report=ats_keyword_coverage(resume_text, posting),
        review=package_review,
    )
