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
from enum import StrEnum

from careeros_ai import AIClient
from careeros_career_brain import CareerBrain
from careeros_job_providers import JobPosting


class Confidence(StrEnum):
    """How much a given answer should be trusted before it goes to an employer.

    This is not decoration. "Sahil" for First Name and a generated paragraph
    for "Why do you want to work here?" are both answers, but only one of them
    is a fact — and a human reviewing a filled form needs to know which is
    which without re-reading everything.
    """

    #: Copied from a verified profile fact. Nothing to review.
    HIGH = "high"
    #: Derived or generated from profile facts. True, but worth a glance.
    MEDIUM = "medium"
    #: A defensible default rather than a known fact ("Immediately / 2 weeks'
    #: notice", "Open / negotiable"). Must be reviewed before sending.
    LOW = "low"
    #: Cannot be answered truthfully from what we know. Never sent.
    UNKNOWN = "unknown"

    @property
    def needs_review(self) -> bool:
        return self is not Confidence.HIGH


@dataclass(frozen=True)
class Answer:
    text: str
    answerable: bool = True
    # For yes/no/choice questions, the normalized option to select.
    choice: str | None = None
    #: How far this answer is from a verified fact. Defaults to HIGH because
    #: every rule-matched answer is a straight profile read; the builders that
    #: derive or generate say so explicitly.
    confidence: Confidence = Confidence.HIGH
    #: Why it could not be answered. Set only when ``answerable`` is False —
    #: an unanswered question with no reason is not actionable, and "left for
    #: a human" without saying why is what made these invisible.
    reason: str = ""
    #: What information would answer it, phrased as something the user can
    #: actually supply.
    needs: str = ""

    @property
    def needs_user_input(self) -> bool:
        """The question must go back to the user rather than be guessed.

        The whole point: an application question CareerOS cannot answer from
        verified data is returned as a question, never as an invention.
        """
        return not self.answerable or self.confidence is Confidence.UNKNOWN


def unknown(reason: str, needs: str) -> Answer:
    """An honest non-answer: what we could not answer, and what would fix it."""
    return Answer("", answerable=False, confidence=Confidence.UNKNOWN, reason=reason, needs=needs)


@dataclass(frozen=True)
class UnansweredQuestion:
    """A question handed back to the user, with everything they need to act.

    ``question``, ``why``, ``needs`` — the three things a "we could not answer
    this" message has to carry to be worth showing at all.
    """

    question: str
    why: str
    needs: str
    selector: str = ""

    def describe(self) -> str:
        return f"{self.question}\n  why: {self.why}\n  needs: {self.needs}"


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
                Answer(identity.phone)
                if identity.phone
                else unknown(
                    "the profile has no phone number",
                    "add a phone number to your Career Brain identity",
                ),
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
                # A defensible default, NOT something the profile states.
                Answer("Immediately / 2 weeks' notice", confidence=Confidence.LOW),
            ),
            (
                # Word-bound city/country so they don't match inside words like
                # "ethni-CITY" (which must fall through to the demographics rule).
                # "located" as well as "location"/"based": "Where are you
                # currently located?" is one of the most common phrasings on a
                # real form — it came back as NEEDS_USER_INPUT on a live Ashby
                # posting purely because the word was missing here.
                re.compile(
                    r"location|where.*(based|located)|\bcity\b|\bcountry\b|time ?zone", re.I
                ),
                Answer(identity.location)
                if identity.location
                else unknown(
                    "the profile records no location",
                    "set your location in your Career Brain identity",
                ),
            ),
            (
                re.compile(r"remote|work from home", re.I),
                # An assumption about preference, not a recorded fact.
                Answer("Yes", choice="yes", confidence=Confidence.LOW),
            ),
            (
                re.compile(r"how did you (hear|find)|referral source", re.I),
                Answer(
                    f"Found the {self._role_name()} posting online.",
                    confidence=Confidence.MEDIUM,
                ),
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
                # Deliberately never inferred from a name or anything else.
                Answer(
                    "Prefer not to say",
                    choice="prefer not to say",
                    confidence=Confidence.MEDIUM,
                ),
            ),
        ]

    # -- answer builders -------------------------------------------------

    def _url_answer(self, *keys: str) -> Answer:
        url = _link(self._brain, *keys)
        if url:
            return Answer(url)
        wanted = keys[0] if keys else "link"
        return unknown(
            f"the profile has no {wanted} link",
            f"add your {wanted} URL to the links on your Career Brain identity",
        )

    def _current_company(self) -> Answer:
        experiences = self._brain.experiences
        if experiences:
            current = next((e for e in experiences if e.is_current), experiences[0])
            return Answer(current.company_name)
        return unknown(
            "the profile records no employment history",
            "add at least one role to your Career Brain",
        )

    def _current_title(self) -> Answer:
        experiences = self._brain.experiences
        if experiences:
            current = next((e for e in experiences if e.is_current), experiences[0])
            return Answer(current.title)
        return unknown(
            "the profile records no employment history",
            "add at least one role to your Career Brain",
        )

    def _years(self) -> Answer:
        years = _total_years_experience(self._brain)
        if years is not None:
            return Answer(str(years))
        return unknown(
            "no skill in the profile records years of experience, so a total cannot be derived",
            "set years of experience on your skills in the Career Brain",
        )

    def _salary(self) -> Answer:
        minimum = self._brain.preferences.min_salary
        currency = self._brain.preferences.salary_currency
        if minimum:
            return Answer(f"{currency} {minimum:,}+")
        # A placeholder, not a stated expectation — always worth a look.
        return Answer("Open / negotiable", confidence=Confidence.LOW)

    def _work_auth(self) -> Answer:
        # Use the user's stored, truthful answer (set once). Never guess: if
        # unknown, defer to a human. (Most of these ask about the US.)
        authorized = self._brain.preferences.us_work_authorized
        if authorized is True:
            return Answer("Yes", choice="yes")
        if authorized is False:
            return Answer("No", choice="no")
        return unknown(
            "your work-authorization status is not recorded, and guessing it "
            "would be a false statement on an application",
            "set 'authorized to work in the US' in your Career Brain preferences",
        )

    def _sponsorship(self) -> Answer:
        # The user's stored answer — never a guess.
        needs = self._brain.preferences.needs_visa_sponsorship
        if needs is True:
            return Answer("Yes", choice="yes")
        if needs is False:
            return Answer("No", choice="no")
        return unknown(
            "whether you need visa sponsorship is not recorded, and guessing "
            "it would be a false statement on an application",
            "set 'needs visa sponsorship' in your Career Brain preferences",
        )

    def _stored_answer(self, question: str) -> Answer | None:
        """A "learned" answer the user saved for a matching question, if any."""
        lowered = question.lower()
        for key, value in self._brain.preferences.screening_answers.items():
            if key.lower() in lowered and value:
                return Answer(value)
        return None

    def _why(self) -> Answer:
        if self._posting is None:
            return unknown(
                "there is no job posting in context to answer 'why this role' against",
                "run this from an application rather than standalone",
            )
        from careeros_application_engine.answers import answer_why_this_role

        # Composed from profile facts, but it is prose about motivation —
        # true, and still the kind of thing a human should read before it goes.
        return Answer(
            answer_why_this_role(self._brain, self._posting), confidence=Confidence.MEDIUM
        )

    def _cover(self) -> Answer:
        if self._posting is None:
            summary = self._brain.identity.summary
            if summary:
                return Answer(summary, confidence=Confidence.MEDIUM)
            return unknown(
                "the profile has no summary and there is no posting to write against",
                "add a summary to your Career Brain identity",
            )
        from careeros_application_engine.cover_letter import TemplateCoverLetterGenerator

        return Answer(
            TemplateCoverLetterGenerator().generate(self._brain, self._posting),
            confidence=Confidence.MEDIUM,
        )

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
            return unknown(
                "no rule recognises this question and no AI provider is available "
                "to draft an answer from your profile",
                "answer it yourself once and CareerOS will reuse it, or connect an "
                "AI provider (see Settings → AI)",
            )
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
        except Exception as exc:
            return unknown(
                f"the AI provider could not answer it ({type(exc).__name__})",
                "answer it yourself, or check your AI provider in Settings → AI",
            )
        if not text or text.upper().startswith("UNKNOWN"):
            # The model doing the right thing: refusing rather than inventing.
            return unknown(
                "the model judged that your profile does not contain a truthful "
                "answer, and declined to invent one",
                "answer it yourself, or add the missing detail to your Career Brain",
            )
        # Generated prose grounded in profile facts — true, and still the kind
        # of thing that goes to an employer, so it is never HIGH.
        return Answer(text, confidence=Confidence.MEDIUM)

    # -- public API ------------------------------------------------------

    def answer(self, question: str) -> Answer:
        """Best truthful answer for a free-text question label."""
        # A "learned" answer the user saved wins over everything else.
        stored = self._stored_answer(question)
        if stored is not None:
            return stored
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

    def answer_all(self, questions: list[str]) -> tuple[dict[str, str], list[UnansweredQuestion]]:
        """Answer a whole form: what we can fill, and what must go back.

        Returns the answers to write and an explicit list of the questions
        CareerOS refused to answer, each with a reason and what would fix it.
        Callers get both halves in one call so it is not possible to fill a
        form and quietly lose track of what was skipped — which is how
        unanswered questions became invisible in the first place.
        """
        answers: dict[str, str] = {}
        unanswered: list[UnansweredQuestion] = []
        for question in questions:
            result = self.answer(question)
            if result.needs_user_input or not result.text:
                unanswered.append(
                    UnansweredQuestion(
                        question=question,
                        why=result.reason or "no truthful answer could be derived",
                        needs=result.needs or "an answer from you",
                    )
                )
            else:
                answers[question] = result.text
        return answers, unanswered


#: Screening answers are stored against a lowercased key and matched by
#: substring, so the key must be the distinctive part of the question rather
#: than the whole sentence (which would never match a reworded version).
_STOPWORDS = frozenset(
    {"do", "you", "have", "are", "is", "the", "a", "an", "to", "of", "in", "for", "what", "your"}
)


def memory_key_for(question: str) -> str:
    """The key a user's answer is remembered under.

    Content words only, so "Do you have experience with Google Ads?" and
    "Experience with Google Ads" resolve to the same memory instead of being
    asked twice.
    """
    words = re.findall(r"[a-z0-9+#.]+", (question or "").lower())
    kept = [w for w in words if w not in _STOPWORDS]
    return " ".join(kept[:8])


def remember_answer(brain: CareerBrain, question: str, answer: str) -> str:
    """Store a user-supplied answer so the same question is never asked twice.

    Mutates ``brain.preferences.screening_answers``; persisting the brain is
    the caller's job. Returns the key it was stored under.
    """
    key = memory_key_for(question)
    if key and answer:
        brain.preferences.screening_answers[key] = answer
    return key
