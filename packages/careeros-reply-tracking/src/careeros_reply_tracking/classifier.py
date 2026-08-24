"""Classify a recruiter email into the application stage it signals.

Deliberately conservative rules over the message text. A wrong automatic
status change erodes trust in the whole feature — a candidate who sees
"Rejected" on a job that just invited them to interview stops believing
any of it — so anything the rules are unsure about produces no signal and
the application is left where the human put it.

Outcome ordering matters: a rejection or an offer routinely quotes the
earlier interview ("following your interview, we regret…"), so the final
outcome is checked before the interview invitation.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from careeros_career_brain import ApplicationStatus


class ReplySignal(BaseModel):
    """What an email was read to mean. ``target`` is None for "nothing to do"."""

    target: ApplicationStatus | None
    evidence: str = ""

    def __bool__(self) -> bool:
        return self.target is not None


# Phrases are matched as substrings of the normalised (lower-cased,
# whitespace-collapsed) text. Ordered lists so the first hit can be reported
# as evidence. Kept close to how recruiters actually write, not exhaustive —
# the LLM classifier (optional) is what catches the long tail.

_REJECTION_PHRASES = (
    "won't be progressing",
    "will not be progressing",
    "not be progressing",
    "won't be moving forward",
    "will not be moving forward",
    "not be moving forward with your",
    "decided to move forward with other",
    "move forward with other candidates",
    "not to move forward",
    "regret to inform",
    "you were not selected",
    "not been successful",
    "unsuccessful on this occasion",
    "pursue other candidates",
    "will not be taking your application further",
    "won't be taking your application further",
    "not be taking your application further",
    "no longer under consideration",
)

_OFFER_PHRASES = (
    "offer you the position",
    "offer you the role",
    "extend an offer",
    "offer of employment",
    "pleased to offer",
    "delighted to offer",
    "happy to offer",
    "formal offer",
    "job offer",
)

_INTERVIEW_PHRASES = (
    "invite you to an interview",
    "invite you to interview",
    "invite you for an interview",
    "like to interview",
    "schedule an interview",
    "schedule a call",
    "schedule a time",
    "set up a call",
    "available for a call",
    "available for a chat",
    "book a time",
    "first-round interview",
    "first round interview",
    "next stage",
    "next round",
    "move you to the next",
    "move forward to the next",
    "phone screen",
    "technical screen",
    "meet the team",
    "hop on a call",
)

# Ordered by precedence: the outcome states win over an interview invitation.
_RULES: tuple[tuple[ApplicationStatus, tuple[str, ...]], ...] = (
    (ApplicationStatus.REJECTED, _REJECTION_PHRASES),
    (ApplicationStatus.OFFER, _OFFER_PHRASES),
    (ApplicationStatus.INTERVIEWING, _INTERVIEW_PHRASES),
)

_WS_RE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    return _WS_RE.sub(" ", text).strip().lower()


def classify_email(*, subject: str, body: str) -> ReplySignal:
    """Read one email; return the stage it signals, or a null signal."""
    haystack = _normalise(f"{subject} {body}")
    if not haystack:
        return ReplySignal(target=None)

    for target, phrases in _RULES:
        for phrase in phrases:
            if phrase in haystack:
                return ReplySignal(target=target, evidence=phrase)

    return ReplySignal(target=None)
