"""The reviewer half of the drafter → reviewer pair.

A model asked to write a cover letter will, given a thin profile, fill the gaps
plausibly: an employer that sounds right, a metric that fits the story, a
degree the candidate never finished. That is the single worst failure mode this
product has, because it is invisible in the output and catastrophic in an
interview.

Reviewing happens in two layers, and the order matters:

1. **Deterministic checks.** Named entities in the draft — employers, job
   titles, degrees, numbers — are checked back against the Career Brain, which
   is the only authority on what is true. These run with no AI configured at
   all, they cannot hallucinate, and they are the checks that actually catch
   fabrication.
2. **An AI reviewer**, routed as ``LLMTask.REVIEW`` so it prefers a different
   provider than the drafter and does not inherit its blind spots. It is asked
   to find problems, never to approve: "looks good" is not an accepted answer,
   and a reviewer that returns nothing is treated as having found nothing
   rather than as having endorsed the draft.

Layer 1 is trusted; layer 2 is advisory. An AI reviewer being unavailable
degrades the review, it does not disable it.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_career_brain import CareerBrain


class Severity(StrEnum):
    #: A factual claim the profile does not support. Never send this out.
    FABRICATION = "fabrication"
    #: Wrong or self-contradictory, but not invented.
    ERROR = "error"
    #: Worth a human's attention before sending.
    WARNING = "warning"


class ReviewFinding(BaseModel):
    severity: Severity
    category: str
    detail: str
    #: The exact text that triggered it, so a human can find it in the draft.
    evidence: str = ""

    def __str__(self) -> str:
        where = f" — {self.evidence!r}" if self.evidence else ""
        return f"[{self.severity.value}] {self.category}: {self.detail}{where}"


class ApplicationReview(BaseModel):
    findings: list[ReviewFinding] = Field(default_factory=list)
    #: False when no AI reviewer ran, so a caller can tell "reviewed and clean"
    #: from "only the deterministic half ran".
    ai_reviewed: bool = False
    reviewer_model: str = ""

    @property
    def fabrications(self) -> list[ReviewFinding]:
        return [f for f in self.findings if f.severity is Severity.FABRICATION]

    @property
    def is_safe_to_send(self) -> bool:
        """No fabricated claim survived. Warnings do not block."""
        return not self.fabrications

    def summary(self) -> str:
        if not self.findings:
            return "no issues found" + ("" if self.ai_reviewed else " (deterministic checks only)")
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
        return ", ".join(f"{count} {name}" for name, count in counts.items())


# ── Layer 1: deterministic fabrication checks ──────────────────────────────

#: Sentences that attach a number to an achievement are where invented metrics
#: live ("grew revenue 340%", "managed $2M in spend").
_METRIC_RE = re.compile(
    r"(?:[£$€]\s?[\d,.]+\s?(?:k|m|bn|million|billion)?|\b\d[\d,.]*\s?%|\b\d[\d,.]*x\b)",
    re.I,
)

#: "at Acme", "with Acme", "for Acme" — how a letter names an employer.
#: The preposition is matched case-INSENSITIVELY (a sentence can open with
#: "At Globex…"), while the company itself must stay capitalised — that
#: capitalisation is the only thing separating a company name from an ordinary
#: prepositional phrase. Hence the scoped (?i:…) rather than a re.I on the
#: whole pattern, which would have matched "at scale" as an employer.
#: Continuation words must be 2+ characters so the pronoun "I" is not swallowed
#: into the name — "At Globex Corporation I led…" must yield "Globex
#: Corporation", not "Globex Corporation I".
_EMPLOYER_RE = re.compile(
    r"\b(?i:at|with|for|joined|from)\s+([A-Z][\w&.'-]*(?:\s+[A-Z][\w&.'-]+){0,3})"
)

_CREDENTIAL_RE = re.compile(
    r"\b(?:BSc|BA|BS|MSc|MA|MBA|PhD|Bachelor(?:'s)?|Master(?:'s)?|Doctorate)\b", re.I
)

#: Words that follow "at" without naming a company.
_NOT_A_COMPANY = frozenset(
    {
        "the",
        "this",
        "that",
        "your",
        "our",
        "my",
        "a",
        "an",
        "i",
        "you",
        "scale",
        "speed",
        "least",
        "once",
        "all",
        "any",
        "some",
        "every",
        "work",
        "working",
        "home",
        "present",
        "time",
        "times",
        "first",
        "last",
        "best",
        "heart",
        "core",
        "hand",
        "will",
        "which",
        "when",
        "where",
    }
)


def _known_companies(brain: CareerBrain) -> set[str]:
    names = {e.company_name.strip().lower() for e in brain.experiences if e.company_name}
    for project in getattr(brain, "projects", None) or []:
        if project.name:
            names.add(project.name.strip().lower())
    for education in getattr(brain, "education", None) or []:
        if education.institution:
            names.add(education.institution.strip().lower())
    return {n for n in names if n}


def _known_text(brain: CareerBrain) -> str:
    """Everything the profile actually says, lowercased, for substring checks."""
    parts: list[str] = [brain.identity.summary or "", brain.identity.headline or ""]
    for experience in brain.experiences:
        parts += [experience.company_name, experience.title, experience.description]
        parts += [a.description for a in experience.achievements]
        parts += [a.metric or "" for a in experience.achievements]
    for project in getattr(brain, "projects", None) or []:
        parts += [project.name, project.description]
    for education in getattr(brain, "education", None) or []:
        parts += [education.institution, education.credential, education.description]
    for certification in getattr(brain, "certifications", None) or []:
        parts.append(certification.name)
    return " ".join(p for p in parts if p).lower()


def check_employers(
    draft: str, brain: CareerBrain, *, allowed_extra: set[str] | None = None
) -> list[ReviewFinding]:
    """Employer-shaped names in the draft that the profile does not know.

    ``allowed_extra`` is how the company being applied to (and the candidate's
    own name) avoid being flagged — a cover letter naming its recipient is
    correct, not fabricated.
    """
    known = _known_companies(brain)
    allowed = {a.strip().lower() for a in (allowed_extra or set()) if a}
    findings: list[ReviewFinding] = []
    seen: set[str] = set()
    for match in _EMPLOYER_RE.finditer(draft):
        candidate = match.group(1).strip().rstrip(".,;:")
        lowered = candidate.lower()
        if lowered in seen or not lowered:
            continue
        # A single common word after "at" is a preposition, not an employer.
        if lowered.split()[0] in _NOT_A_COMPANY:
            continue
        seen.add(lowered)
        if any(lowered == k or lowered in k or k in lowered for k in known):
            continue
        if any(lowered == a or lowered in a or a in lowered for a in allowed):
            continue
        findings.append(
            ReviewFinding(
                severity=Severity.FABRICATION,
                category="unknown employer",
                detail=(
                    f"{candidate!r} is named as an organisation but appears nowhere in the "
                    "career profile"
                ),
                evidence=candidate,
            )
        )
    return findings


def check_metrics(draft: str, brain: CareerBrain) -> list[ReviewFinding]:
    """Numbers in the draft that the profile does not contain.

    A metric is the easiest thing for a model to invent and the hardest for a
    reader to spot, so any figure that is not already somewhere in the profile
    is surfaced.
    """
    known = _known_text(brain)
    findings: list[ReviewFinding] = []
    seen: set[str] = set()
    for match in _METRIC_RE.finditer(draft):
        figure = match.group(0).strip()
        normalized = figure.lower().replace(" ", "")
        if normalized in seen:
            continue
        seen.add(normalized)
        if normalized in known.replace(" ", ""):
            continue
        findings.append(
            ReviewFinding(
                severity=Severity.FABRICATION,
                category="unsupported metric",
                detail=(f"the figure {figure!r} does not appear anywhere in the career profile"),
                evidence=figure,
            )
        )
    return findings


def check_credentials(draft: str, brain: CareerBrain) -> list[ReviewFinding]:
    """Degrees claimed in the draft with no matching education record."""
    education = getattr(brain, "education", None) or []
    certifications = getattr(brain, "certifications", None) or []
    have_any = bool(education or certifications)
    known = _known_text(brain)
    findings: list[ReviewFinding] = []
    seen: set[str] = set()
    for match in _CREDENTIAL_RE.finditer(draft):
        credential = match.group(0)
        lowered = credential.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        if lowered in known:
            continue
        detail = (
            f"a {credential} is claimed but the profile records no matching qualification"
            if have_any
            else f"a {credential} is claimed but the profile records no education at all"
        )
        findings.append(
            ReviewFinding(
                severity=Severity.FABRICATION,
                category="unsupported credential",
                detail=detail,
                evidence=credential,
            )
        )
    return findings


def check_placeholders(draft: str) -> list[ReviewFinding]:
    """Template scaffolding that survived into the draft.

    Sending "[Company Name]" is not a fabrication, but it is the single most
    embarrassing thing an automated application can do.
    """
    findings = []
    for pattern, label in (
        (r"\[[A-Za-z _/]+\]", "square-bracket placeholder"),
        (r"\{\{?[A-Za-z_ ]+\}?\}", "template placeholder"),
        (r"\bXX+\b", "placeholder XX"),
        (r"\b(?:TBD|TODO|FIXME|LOREM IPSUM)\b", "unfinished marker"),
    ):
        for match in re.finditer(pattern, draft, re.I):
            findings.append(
                ReviewFinding(
                    severity=Severity.ERROR,
                    category=label,
                    detail="unreplaced placeholder text would be sent to the employer",
                    evidence=match.group(0),
                )
            )
    return findings


def deterministic_review(
    draft: str, brain: CareerBrain, *, allowed_extra: set[str] | None = None
) -> list[ReviewFinding]:
    """Every check that needs no AI. These are the trustworthy ones."""
    if not draft.strip():
        return [
            ReviewFinding(
                severity=Severity.ERROR,
                category="empty draft",
                detail="there is nothing to send",
            )
        ]
    return [
        *check_employers(draft, brain, allowed_extra=allowed_extra),
        *check_metrics(draft, brain),
        *check_credentials(draft, brain),
        *check_placeholders(draft),
    ]


# ── Layer 2: the AI reviewer ───────────────────────────────────────────────

_REVIEW_SYSTEM = (
    "You are an adversarial reviewer of a job application draft. Your job is to "
    "FIND PROBLEMS, not to approve. You are given the candidate's verified profile "
    "facts and a draft written by another model.\n\n"
    "Report every instance of:\n"
    "- a claim the profile facts do not support (employers, titles, dates, metrics, "
    "skills, degrees, certifications, clients)\n"
    "- a claim that contradicts the profile facts\n"
    "- ownership inflated beyond what the facts state (contributed vs owned/led)\n"
    "- a required detail the draft is missing for this role\n"
    "- placeholder or unfinished text\n"
    "- vague filler that says nothing specific\n\n"
    "Output one finding per line, in the form:\n"
    "SEVERITY|CATEGORY|what is wrong|the exact quoted text\n"
    "where SEVERITY is FABRICATION, ERROR or WARNING.\n"
    "Use FABRICATION only for a claim the facts do not support.\n"
    "If and only if you genuinely find nothing, output the single word NONE. "
    "Do not write praise, summaries, or preamble."
)

_SEVERITY_BY_NAME = {
    "FABRICATION": Severity.FABRICATION,
    "ERROR": Severity.ERROR,
    "WARNING": Severity.WARNING,
}


def parse_review_output(text: str) -> list[ReviewFinding]:
    """The reviewer's lines as findings.

    Deliberately tolerant of an extra sentence or a stray bullet, because a
    reviewer that formats badly has still found something real; and deliberately
    strict about NONE, so "looks good to me" is not silently read as approval —
    an unparseable response yields no findings, and the caller can see the
    review ran but produced nothing structured.
    """
    findings: list[ReviewFinding] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip().lstrip("-*• ").strip()
        if not line or line.upper() == "NONE":
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        severity = _SEVERITY_BY_NAME.get(parts[0].upper())
        if severity is None:
            continue
        findings.append(
            ReviewFinding(
                severity=severity,
                category=parts[1] or "unspecified",
                detail=parts[2],
                evidence=parts[3] if len(parts) > 3 else "",
            )
        )
    return findings


def profile_facts(brain: CareerBrain) -> str:
    """The verified facts a reviewer checks a draft against."""
    identity = brain.identity
    lines = [f"Name: {identity.full_name}"]
    if identity.headline:
        lines.append(f"Headline: {identity.headline}")
    if identity.location:
        lines.append(f"Location: {identity.location}")
    if identity.summary:
        lines.append(f"Summary: {identity.summary}")
    if brain.experiences:
        lines.append("Employment history (the ONLY employers that are real):")
        for experience in brain.experiences:
            end = experience.end_date or "present"
            lines.append(
                f"  - {experience.title} at {experience.company_name} "
                f"({experience.start_date} to {end})"
            )
            for achievement in experience.achievements:
                metric = f" [{achievement.metric}]" if achievement.metric else ""
                lines.append(f"      * {achievement.description}{metric}")
    else:
        lines.append("Employment history: NONE RECORDED. Any employer named is fabricated.")
    education = getattr(brain, "education", None) or []
    if education:
        lines.append("Education:")
        lines += [f"  - {e.credential} — {e.institution}" for e in education]
    else:
        lines.append("Education: NONE RECORDED. Any degree claimed is fabricated.")
    certifications = getattr(brain, "certifications", None) or []
    if certifications:
        lines.append("Certifications: " + ", ".join(c.name for c in certifications))
    if brain.skills:
        lines.append("Skills: " + ", ".join(s.name for s in brain.skills))
    return "\n".join(lines)


def review_application_draft(
    draft: str,
    brain: CareerBrain,
    *,
    ai_client=None,
    allowed_extra: set[str] | None = None,
    context: str = "",
) -> ApplicationReview:
    """Review one generated draft. The deterministic checks always run.

    ``ai_client`` is any ``AIClient``; pass one built for ``LLMTask.REVIEW`` so
    the reviewer prefers a different provider than the drafter. When it is
    absent or fails, the review still happens — with ``ai_reviewed=False``, so
    a caller can tell a full review from a partial one rather than reading
    "no findings" as an all-clear.
    """
    review = ApplicationReview(
        findings=deterministic_review(draft, brain, allowed_extra=allowed_extra)
    )
    if ai_client is None or not draft.strip():
        return review

    prompt = (
        f"VERIFIED PROFILE FACTS:\n{profile_facts(brain)}\n\n"
        + (f"ROLE CONTEXT:\n{context}\n\n" if context else "")
        + f"DRAFT TO REVIEW:\n{draft}\n\nFindings:"
    )
    try:
        raw = ai_client.complete(system=_REVIEW_SYSTEM, prompt=prompt)
    except Exception:
        return review

    review.ai_reviewed = True
    review.reviewer_model = getattr(getattr(ai_client, "last_run", None), "model", "")
    existing = {(f.category, f.evidence.lower()) for f in review.findings}
    for finding in parse_review_output(raw):
        if (finding.category, finding.evidence.lower()) not in existing:
            review.findings.append(finding)
    return review
