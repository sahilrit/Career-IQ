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

from careeros_career_brain import CareerBrain, ClaimStatus


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


def _figures_in(text: str) -> set[str]:
    """The metric tokens in ``text``, normalised for comparison.

    Extracted as whole tokens rather than substring-searched. A plain
    ``"3x" in draft`` matches inside "12.33x", so the disputed ~3x delivered
    ROAS flagged a draft quoting the verified 12.33x best month — the same
    substring trap that mapped "ethni-CITY" to a location field.
    """
    return {m.group(0).strip().lower().replace(" ", "") for m in _METRIC_RE.finditer(text or "")}


def _explained_elsewhere(brain: CareerBrain) -> set[str]:
    """Figures ``check_disputed_claims`` will report with a better message.

    Without this, a disputed figure produces TWO findings for the same number:
    a generic "does not appear anywhere in the career profile" from
    ``check_metrics`` and the specific "recorded as DISPUTED between two
    values" from the provenance check. Both are true; only the second tells the
    user what to do, and a duplicate makes the review harder to read.
    """
    supported: set[str] = set()
    unsafe: set[str] = set()
    for experience in brain.experiences:
        for achievement in experience.achievements:
            target = supported if achievement.is_publishable else unsafe
            target |= _figures_in(achievement.metric or "")
    return unsafe - supported


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
    """Everything the profile SUPPORTS, lowercased, for substring checks.

    Deliberately not "everything the profile contains". This function is what
    ``check_metrics`` measures a draft against, so any figure present here is
    treated as true — which means an unsupported or disputed number stored in
    the brain would *launder* itself: the checker built to catch it would see
    it as corroboration and wave the draft through.

    Claims marked CONFLICTING or UNSUPPORTED are therefore excluded, so a draft
    quoting one is flagged as an unsupported metric exactly like an invented
    one. That is the correct treatment: from the employer's side there is no
    difference between a number the candidate made up and one his own records
    contradict.
    """
    parts: list[str] = [brain.identity.summary or "", brain.identity.headline or ""]
    for experience in brain.experiences:
        parts += [experience.company_name, experience.title, experience.description]
        supported = [a for a in experience.achievements if a.is_publishable]
        parts += [a.description for a in supported]
        parts += [a.metric or "" for a in supported]
        parts += [a.qualifier or "" for a in supported]
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
    explained = _explained_elsewhere(brain)
    findings: list[ReviewFinding] = []
    seen: set[str] = set()
    for match in _METRIC_RE.finditer(draft):
        figure = match.group(0).strip()
        normalized = figure.lower().replace(" ", "")
        if normalized in seen or normalized in explained:
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


def check_disputed_claims(draft: str, brain: CareerBrain) -> list[ReviewFinding]:
    """Figures the profile itself records as disputed or unsupported.

    ``check_metrics`` already catches these — they are excluded from
    ``_known_text``, so they read as unsupported. This check exists to say
    something more useful than "we cannot find this figure": it can say *which*
    claim it came from and *why* it is not safe, which is the difference
    between a finding the user can act on and one they have to investigate.
    """
    findings: list[ReviewFinding] = []
    seen: set[str] = set()
    draft_figures = _figures_in(draft)

    # The same figure can be unsupported in one place and verified in another.
    # $420K is misattributed on the consulting role AND correctly recorded as
    # Presha's peak month; flagging it purely because the bad copy exists would
    # make the legitimate, properly qualified use unusable. Where a figure is
    # supported somewhere, qualification — not existence — is the question, and
    # ``check_unqualified_figures`` is what answers it.
    supported: set[str] = set()
    for experience in brain.experiences:
        for achievement in experience.achievements:
            if not achievement.is_publishable:
                continue
            for figure in _METRIC_RE.finditer(achievement.metric or ""):
                supported.add(figure.group(0).strip().lower().replace(" ", ""))

    for experience in brain.experiences:
        for achievement in experience.achievements:
            if achievement.is_publishable:
                continue
            for figure in _METRIC_RE.finditer(achievement.metric or ""):
                token = figure.group(0).strip()
                normalized = token.lower().replace(" ", "")
                if not normalized or normalized in seen or normalized in supported:
                    continue
                if normalized not in draft_figures:
                    continue
                seen.add(normalized)
                reason = (
                    "the profile records this figure as DISPUTED between two different values"
                    if achievement.status is ClaimStatus.CONFLICTING
                    else "the profile records this figure as UNSUPPORTED by any source"
                )
                findings.append(
                    ReviewFinding(
                        severity=Severity.FABRICATION,
                        category=f"{achievement.status.value} claim",
                        detail=(
                            f"{reason}"
                            + (f" — {achievement.evidence}" if achievement.evidence else "")
                            + ". It must not be sent to an employer until it is verified."
                        ),
                        evidence=token,
                    )
                )
    return findings


def check_unqualified_figures(draft: str, brain: CareerBrain) -> list[ReviewFinding]:
    """Figures used WITHOUT the qualification that makes them true.

    The subtlest failure in this whole system. "$12M+ booked revenue" is
    accurate; "$12M+ in total revenue" is not — and both contain "$12M", so
    ``check_metrics`` sees the figure in the profile and waves it through. The
    number is real. The claim is not.

    That is exactly how a careful profile still produces a misleading letter,
    so the qualifying TERM is required, not merely suggested: if the draft uses
    the figure, it must also say the word that makes it honest.
    """
    findings: list[ReviewFinding] = []
    lowered = draft.lower()
    draft_figures = _figures_in(draft)
    seen: set[str] = set()

    for experience in brain.experiences:
        for achievement in experience.achievements:
            terms = getattr(achievement, "requires_terms", None) or []
            if not terms or not achievement.is_publishable:
                continue
            if any(term.lower() in lowered for term in terms):
                continue  # properly qualified
            for figure in _METRIC_RE.finditer(achievement.metric or ""):
                token = figure.group(0).strip()
                normalized = token.lower().replace(" ", "")
                if not normalized or normalized in seen:
                    continue
                if normalized not in draft_figures:
                    continue
                seen.add(normalized)
                findings.append(
                    ReviewFinding(
                        severity=Severity.FABRICATION,
                        category="unqualified figure",
                        detail=(
                            f"{token} is only true with its qualification "
                            f"({achievement.qualifier or ', '.join(terms)}). The draft states it "
                            f"without saying {' or '.join(repr(t) for t in terms)}, which changes "
                            "what is being claimed."
                        ),
                        evidence=token,
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
        *check_disputed_claims(draft, brain),
        *check_unqualified_figures(draft, brain),
        *check_placeholders(draft),
    ]


# ── Layer 2: the AI reviewer ───────────────────────────────────────────────

_REVIEW_SYSTEM = (
    "You are an adversarial reviewer of a job application draft. Your job is to "
    "FIND PROBLEMS, not to approve. You are given the candidate's verified profile "
    "facts and a draft written by another model.\n\n"
    "Check for every one of these, specifically:\n"
    "- FABRICATED CLAIMS: any employer, client, product or project not in the facts\n"
    "- UNSUPPORTED METRICS: any number, percentage or currency figure not in the facts\n"
    "- WRONG DATES: any date or duration that contradicts the employment history\n"
    "- WRONG EMPLOYER: a role attributed to the wrong company\n"
    "- WRONG TITLE: a job title the facts do not give the candidate\n"
    "- INCORRECT SKILLS: a skill or tool claimed that is not in the facts\n"
    "- CONTRADICTIONS: two statements in the draft that cannot both be true\n"
    "- INFLATED OWNERSHIP: 'led'/'owned' where the facts say contributed\n"
    "- MISSING REQUIREMENTS: a requirement of THIS role the draft never addresses\n"
    "- IRRELEVANT CLAIMS: content with no bearing on this role\n"
    "- GENERIC LANGUAGE: sentences that would fit any candidate and any job\n"
    "- PLACEHOLDERS: unreplaced template text\n\n"
    "Output one finding per line, in the form:\n"
    "SEVERITY|CATEGORY|what is wrong|the exact quoted text\n"
    "where SEVERITY is FABRICATION, ERROR or WARNING.\n"
    "Use FABRICATION only for a claim the facts do not support.\n"
    "If and only if you genuinely find nothing, output the single word NONE. "
    "Do not write praise, summaries, or preamble."
)

#: The same instruction, for the structured path. No output-format rules here:
#: the schema is enforced by validation, so restating it in prose only creates
#: something for the two to disagree about.
_STRUCTURED_REVIEW_SYSTEM = _REVIEW_SYSTEM.split("Output one finding per line")[0].rstrip() + (
    "\n\nReport ONLY problems you can point at in the draft. An empty findings "
    "list is a valid answer, but 'looks good' as a finding is not — do not "
    "invent a problem to fill the list, and do not report praise."
)


class AiFinding(BaseModel):
    """One problem the AI reviewer claims to have found.

    ``evidence`` is required, not optional: a finding that cannot quote the
    text it is about is unactionable, and it is also how a reviewer bluffs.
    """

    severity: Severity
    category: str = Field(min_length=1, max_length=80)
    detail: str = Field(min_length=1, max_length=600)
    evidence: str = Field(min_length=1, max_length=400)


class AiReviewReport(BaseModel):
    findings: list[AiFinding] = Field(default_factory=list, max_length=40)


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
    lines = [
        "Any line marked [CONFLICTING — NOT a usable fact] or [UNSUPPORTED — NOT a "
        "usable fact] is recorded in the profile but is NOT established. Treat a draft "
        "that states it as a FABRICATION.",
        "",
        f"Name: {identity.full_name}",
    ]
    # Contact details are facts the reviewer is asked to CHECK — the answers on
    # a form include the candidate's email, phone and profile links. Omitting
    # them meant the reviewer saw a correct email with nothing to verify it
    # against and reported it as a discrepancy: a false fabrication finding,
    # which is the most expensive kind, because it trains a user to ignore
    # findings.
    if identity.email:
        lines.append(f"Email: {identity.email}")
    if identity.phone:
        lines.append(f"Phone: {identity.phone}")
    for label, url in (identity.links or {}).items():
        lines.append(f"Link ({label}): {url}")
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
                if not achievement.is_publishable:
                    # Shown to the reviewer as explicitly NOT a fact, so it can
                    # flag a draft that uses it — rather than hidden, which
                    # would leave the reviewer unable to recognise the figure
                    # at all, or listed plainly, which would endorse it.
                    lines.append(
                        f"      * [{achievement.status.value.upper()} — NOT a usable fact] "
                        f"{achievement.description}{metric}"
                    )
                    continue
                qualifier = f" ({achievement.qualifier})" if achievement.qualifier else ""
                lines.append(f"      * {achievement.description}{metric}{qualifier}")
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


def _review_prompt(draft: str, brain: CareerBrain, context: str) -> str:
    return (
        f"VERIFIED PROFILE FACTS:\n{profile_facts(brain)}\n\n"
        + (f"ROLE CONTEXT:\n{context}\n\n" if context else "")
        + f"DRAFT TO REVIEW:\n{draft}\n\nFindings:"
    )


def review_application_draft(
    draft: str,
    brain: CareerBrain,
    *,
    ai_client=None,
    gateway=None,
    allowed_extra: set[str] | None = None,
    context: str = "",
    questions: dict[str, str] | None = None,
) -> ApplicationReview:
    """Review one generated draft. The deterministic checks always run.

    Order is deterministic → AI → final, and the order is the point. Layer 1
    is authoritative: it checks named entities against the Career Brain, which
    is the only authority on what is true, and it cannot hallucinate. Layer 2
    is an adversarial second opinion that catches what pattern matching
    cannot — a wrong date, an inflated "led", a paragraph that would fit any
    candidate. It can be wrong, so it never overrules layer 1 and never
    subtracts a finding.

    ``gateway`` is an ``LLMGateway``; when given, the AI review is taken
    through structured output so a malformed answer is retried and validated
    rather than silently parsed into nothing. ``ai_client`` is the older
    free-text path, kept for callers that hold a plain client.

    ``questions`` are the application answers to review alongside the letter —
    a wrong answer to a screening question is exactly as damaging as a wrong
    sentence in the cover letter, and used to go unchecked entirely.

    With neither, the review still happens — with ``ai_reviewed=False``, so a
    caller can tell a full review from a partial one rather than reading "no
    findings" as an all-clear.
    """
    review = ApplicationReview(
        findings=deterministic_review(draft, brain, allowed_extra=allowed_extra)
    )
    if not draft.strip():
        return review

    full_context = context
    if questions:
        rendered = "\n".join(f"  Q: {q}\n  A: {a}" for q, a in questions.items())
        full_context = (
            f"{context}\n\nAPPLICATION QUESTIONS AND THE ANSWERS GIVEN "
            f"(check these against the facts too):\n{rendered}"
        )
    prompt = _review_prompt(draft, brain, full_context)

    findings: list[ReviewFinding] | None = None
    model = ""
    if gateway is not None:
        findings, model = _structured_ai_review(gateway, prompt)
    if findings is None and ai_client is not None:
        findings, model = _free_text_ai_review(ai_client, prompt)
    if findings is None:
        return review

    review.ai_reviewed = True
    review.reviewer_model = model
    # The AI layer only ever ADDS. It cannot clear a deterministic finding,
    # because it is the layer that can be wrong.
    existing = {(f.category, f.evidence.lower()) for f in review.findings}
    for finding in findings:
        if (finding.category, finding.evidence.lower()) not in existing:
            review.findings.append(finding)
    return review


def _structured_ai_review(gateway, prompt: str) -> tuple[list[ReviewFinding] | None, str]:
    """The AI review through validated structured output.

    Returns (None, "") when no provider could serve it — distinct from
    (``[]``, model), which means a reviewer ran and found nothing.
    """
    from careeros_llm import LLMTask

    try:
        response = gateway.try_complete_structured(
            task=LLMTask.REVIEW,
            system=_STRUCTURED_REVIEW_SYSTEM,
            prompt=prompt,
            schema=AiReviewReport,
        )
    except Exception:
        return None, ""
    if response is None:
        return None, ""
    findings = [
        ReviewFinding(
            severity=f.severity,
            category=f.category,
            detail=f.detail,
            evidence=f.evidence,
        )
        for f in response.value.findings
    ]
    return findings, response.run.model


def _free_text_ai_review(ai_client, prompt: str) -> tuple[list[ReviewFinding] | None, str]:
    try:
        raw = ai_client.complete(system=_REVIEW_SYSTEM, prompt=prompt)
    except Exception:
        return None, ""
    model = getattr(getattr(ai_client, "last_run", None), "model", "")
    return parse_review_output(raw), model
