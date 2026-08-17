"""ATS keyword coverage: a real, zero-cost approximation of what an
Applicant Tracking System keyword scan checks — is a target keyword's
text present anywhere in the generated resume?
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from careeros_job_providers import JobPosting

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class ATSReport:
    covered_keywords: list[str]
    missing_keywords: list[str]

    @property
    def coverage_ratio(self) -> float:
        total = len(self.covered_keywords) + len(self.missing_keywords)
        return len(self.covered_keywords) / total if total else 1.0


def ats_keyword_coverage(resume_text: str, posting: JobPosting) -> ATSReport:
    # Normalise the resume to a single, space-padded token stream so multi-word
    # keywords ("google ads") match as phrases, not just as single tokens.
    resume_norm = f" {' '.join(_TOKEN_RE.findall(resume_text.lower()))} "
    covered = []
    missing = []
    for keyword in posting.tags:
        phrase = " ".join(_TOKEN_RE.findall(keyword.lower()))
        if phrase and f" {phrase} " in resume_norm:
            covered.append(keyword)
        else:
            missing.append(keyword)
    return ATSReport(covered_keywords=covered, missing_keywords=missing)
