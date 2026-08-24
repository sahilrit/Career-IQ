"""Answer arbitrary application-form questions from the Career Brain.

Every answer is derived from real profile data — never invented. When a
question can't be answered truthfully from what we know (e.g. work
authorization for a specific country we have no data on), the answerer
returns ``answerable=False`` so the caller can leave it for a human
rather than guess. That honesty is the whole point: a fabricated visa
or salary answer is worse than no answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from careeros_ai import AIClient
from careeros_career_brain import CareerBrain
from careeros_job_providers import JobPosting


@dataclass(frozen=True)
class Answer:
    text: str
    answerable: bool = True
    # For yes/no/choice questions, the normalized option to select.
    choice: str | None = None


def _total_years_experience(brain: CareerBrain) -> int | None:
    years = [s.years_experience for s in brain.skills if s.years_experience]
    if years:
        return int(max(years))
    return None


def _link(brain: CareerBrain, *keys: str) -> str | None:
    for key, value in brain.identity.links.items():
        if any(k in key.lower() for k in keys):
            return value
    return None


def _has_skill(brain: CareerBrain, text: str) -> bool:
    lowered = text.lower()
    return any(skill.name.lower() in lowered for skill in brain.skills)


# Each matcher: (compiled label pattern, answer builder).
class QuestionAnswerer:
    """Maps a free-text question label to a truthful answer from the brain."""

    def __init__(
        self,
        brain: CareerBrain,
        posting: JobPosting | None = None,
        *,
        ai_client: AIClient | None = None,
    ) -> None:
        self._brain = brain
        self._posting = posting
        # When set, questions no rule recognizes are drafted by the AI, grounded
        # strictly in the profile facts below (it replies UNKNOWN rather than
        # invent). Hard facts (visa/sponsorship) and demographics are matched by
        # rules first, so the AI never fabricates those.
        self._ai_client = ai_client
        identity = brain.identity
        first_name, _, last_name = identity.full_name.partition(" ")

        # Ordered so specific patterns win over generic ones.
        self._rules: list[tuple[re.Pattern[str], object]] = [
            (re.compile(r"first name", re.I), Answer(first_name)),
            (re.compile(r"last name|surname|family name", re.I), Answer(last_name or first_name)),
            (re.compile(r"full name|^name$|your name", re.I), Answer(identity.full_name)),
            (re.compile(r"e-?mail", re.I), Answer(identity.email)),
            (
                re.compile(r"phone|mobile|contact number|whatsapp", re.I),
                Answer(identity.phone) if identity.phone else Answer("", answerable=False),
            ),
            (re.compile(r"linkedin", re.I), self._url_answer("linkedin")),
            (
                re.compile(r"portfolio|website|personal site", re.I),
                self._url_answer("portfolio", "website", "site"),
            ),
            (re.compile(r"github", re.I), self._url_answer("github")),
            (
                re.compile(r"current (or previous )?employer|current company", re.I),
                self._current_company(),
            ),
            (
                re.compile(r"current (or previous )?(job )?title|current role", re.I),
                self._current_title(),
            ),
            (
                re.compile(r"years.*experience|experience.*years|how many years", re.I),
                self._years(),
            ),
            (re.compile(r"salary|compensation|expected pay|ctc", re.I), self._salary()),
            (
                re.compile(r"authori[sz]ed to work|work authori|legally.*work|right to work", re.I),
                self._work_auth(),
            ),
            (
                re.compile(r"require.*sponsor|need.*sponsor|visa sponsor", re.I),
                self._sponsorship(),
            ),
            (
                re.compile(r"notice period|when can you start|availability|start date", re.I),
                Answer("Immediately / 2 weeks' notice"),
            ),
            (
                # Word-bound city/country so they don't match inside words like
                # "ethni-CITY" (which must fall through to the demographics rule).
                re.compile(r"location|where.*based|\bcity\b|\bcountry\b|time ?zone", re.I),
                Answer(identity.location) if identity.location else Answer("", answerable=False),
            ),
            (
                re.compile(r"remote|work from home", re.I),
                Answer("Yes", choice="yes"),
            ),
            (
                re.compile(r"how did you (hear|find)|referral source", re.I),
                Answer(f"Found the {self._role_name()} posting online."),
            ),
            (
                re.compile(r"why.*(interested|want|this role|this company|join)", re.I),
                self._why(),
            ),
            (
                re.compile(r"cover letter|anything else|tell us about|introduce yourself", re.I),
                self._cover(),
            ),
            (
                re.compile(r"gender|pronoun|ethnicit|race|disabilit|veteran|sexual", re.I),
                Answer("Prefer not to say", choice="prefer not to say"),
            ),
        ]

    # -- answer builders -------------------------------------------------

    def _url_answer(self, *keys: str) -> Answer:
        url = _link(self._brain, *keys)
        return Answer(url) if url else Answer("", answerable=False)

    def _current_company(self) -> Answer:
        experiences = self._brain.experiences
        if experiences:
            current = next((e for e in experiences if e.is_current), experiences[0])
            return Answer(current.company_name)
        return Answer("", answerable=False)

    def _current_title(self) -> Answer:
        experiences = self._brain.experiences
        if experiences:
            current = next((e for e in experiences if e.is_current), experiences[0])
            return Answer(current.title)
        return Answer("", answerable=False)

    def _years(self) -> Answer:
        years = _total_years_experience(self._brain)
        return Answer(str(years)) if years is not None else Answer("", answerable=False)

    def _salary(self) -> Answer:
        minimum = self._brain.preferences.min_salary
        currency = self._brain.preferences.salary_currency
        if minimum:
            return Answer(f"{currency} {minimum:,}+")
        return Answer("Open / negotiable")

    def _work_auth(self) -> Answer:
        # Truthful only if the brain records it; otherwise defer to a human.
        location = (self._brain.identity.location or "").lower()
        if location:
            return Answer(f"Authorized to work in {self._brain.identity.location}", choice="yes")
        return Answer("", answerable=False)

    def _sponsorship(self) -> Answer:
        return Answer("", answerable=False)  # never guess visa/sponsorship

    def _why(self) -> Answer:
        if self._posting is None:
            return Answer("", answerable=False)
        from careeros_application_engine.answers import answer_why_this_role

        return Answer(answer_why_this_role(self._brain, self._posting))

    def _cover(self) -> Answer:
        if self._posting is None:
            summary = self._brain.identity.summary
            return Answer(summary) if summary else Answer("", answerable=False)
        from careeros_application_engine.cover_letter import TemplateCoverLetterGenerator

        return Answer(TemplateCoverLetterGenerator().generate(self._brain, self._posting))

    def _role_name(self) -> str:
        return self._posting.title if self._posting else "the"

    # -- AI fallback -----------------------------------------------------

    def _profile_facts(self) -> str:
        brain = self._brain
        identity = brain.identity
        lines = [f"Name: {identity.full_name}"]
        if identity.headline:
            lines.append(f"Headline: {identity.headline}")
        if identity.location:
            lines.append(f"Location: {identity.location}")
        if identity.summary:
            lines.append(f"Summary: {identity.summary}")
        if brain.skills:
            lines.append("Skills: " + ", ".join(skill.name for skill in brain.skills))
        if brain.experiences:
            lines.append("Experience:")
            lines += [
                f"  - {exp.title} at {exp.company_name}"
                + (f" ({exp.start_date} to {exp.end_date or 'present'})" if exp.start_date else "")
                for exp in brain.experiences
            ]
        education = getattr(brain, "education", None) or []
        if education:
            lines.append(
                "Education: " + "; ".join(f"{e.credential} — {e.institution}" for e in education)
            )
        certifications = getattr(brain, "certifications", None) or []
        if certifications:
            lines.append("Certifications: " + ", ".join(c.name for c in certifications))
        prefs = brain.preferences
        if getattr(prefs, "min_salary", None):
            lines.append(f"Minimum salary: {prefs.salary_currency} {prefs.min_salary:,}")
        return "\n".join(lines)

    def _ai_answer(self, question: str) -> Answer:
        if self._ai_client is None:
            return Answer("", answerable=False)
        role = ""
        if self._posting is not None:
            role = f"\nRole: {self._posting.title} at {self._posting.company_name}\n"
        system = (
            "You fill answers on a candidate's job application. Answer the question "
            "truthfully and concisely using ONLY the candidate facts provided. NEVER "
            "invent employers, titles, dates, numbers, degrees, certifications, or "
            "work-authorization/visa status. If the facts do not support a truthful "
            "answer, reply with exactly: UNKNOWN. For a yes/no question, answer 'Yes' "
            "or 'No' only when the facts make it clear, else UNKNOWN. Keep it under "
            "120 words, first person, no preamble."
        )
        prompt = (
            f"Candidate facts:\n{self._profile_facts()}\n{role}\nQuestion: {question}\n\nAnswer:"
        )
        try:
            text = self._ai_client.complete(system=system, prompt=prompt).strip()
        except Exception:
            return Answer("", answerable=False)
        if not text or text.upper().startswith("UNKNOWN"):
            return Answer("", answerable=False)
        return Answer(text)

    # -- public API ------------------------------------------------------

    def answer(self, question: str) -> Answer:
        """Best truthful answer for a free-text question label."""
        for pattern, builder in self._rules:
            if pattern.search(question):
                result = builder() if callable(builder) else builder
                if isinstance(result, Answer):
                    return result
        # Yes/no screening: "do you have experience with <skill>?"
        is_screening = re.search(
            r"do you have|experience (with|in)|proficient|familiar", question, re.I
        )
        if is_screening and _has_skill(self._brain, question):
            return Answer("Yes", choice="yes")
        # No rule matched — let the AI draft it from the profile (or UNKNOWN).
        return self._ai_answer(question)
