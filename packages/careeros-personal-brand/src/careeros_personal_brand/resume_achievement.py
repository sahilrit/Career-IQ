"""Closes the content loop: a case study becomes a candidate resume
Achievement. Returned for the user to review and add to their Career
Brain themselves — this package never writes to the Career Brain
directly, since deciding what counts as a resume-worthy achievement is
the user's call, not something to apply silently.
"""

from __future__ import annotations

from careeros_career_brain import Achievement, Project
from careeros_personal_brand.case_study import CaseStudy


def derive_resume_achievement(case_study: CaseStudy, project: Project) -> Achievement:
    return Achievement(
        description=f"{case_study.approach} {case_study.result}".strip(),
        metric=None,
        skills_demonstrated=list(project.skills_used),
    )
