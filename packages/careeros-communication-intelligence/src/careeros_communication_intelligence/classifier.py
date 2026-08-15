"""EmailClassifier: turns incoming email into a structured career
communication category, using deterministic keyword/pattern heuristics —
zero-cost, no paid AI required. A future AI Skill (Phase 49) can plug in
a richer classifier behind the same ``classify()`` signature.
"""

from __future__ import annotations

import re
from enum import StrEnum


class CommunicationCategory(StrEnum):
    OFFER = "offer"
    REJECTION = "rejection"
    INTERVIEW = "interview"
    CONTRACT = "contract"
    PAYMENT = "payment"
    RECRUITER_MESSAGE = "recruiter_message"
    CLIENT_INQUIRY = "client_inquiry"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


# Order matters: outcomes (offer/rejection) are checked before process
# signals (interview) so "...unfortunately, after your interview..."
# classifies as REJECTION, not INTERVIEW.
_PATTERNS: list[tuple[CommunicationCategory, re.Pattern[str]]] = [
    (
        CommunicationCategory.OFFER,
        re.compile(r"\b(offer letter|pleased to offer|job offer|excited to offer)\b", re.I),
    ),
    (
        CommunicationCategory.REJECTION,
        re.compile(
            r"\b(unfortunately|not moving forward|other candidates|"
            r"decided not to proceed|regret to inform)\b",
            re.I,
        ),
    ),
    (
        CommunicationCategory.INTERVIEW,
        re.compile(
            r"\b(interview|schedule a call|meet the team|technical screen|phone screen)\b", re.I
        ),
    ),
    (
        CommunicationCategory.CONTRACT,
        re.compile(r"\b(contract|statement of work|\bsow\b|agreement attached)\b", re.I),
    ),
    (
        CommunicationCategory.PAYMENT,
        re.compile(r"\b(invoice|payment (received|sent|due)|wire transfer|remittance)\b", re.I),
    ),
    (
        CommunicationCategory.RECRUITER_MESSAGE,
        re.compile(
            r"\b(recruiter|talent acquisition|came across your profile|"
            r"reaching out about a role)\b",
            re.I,
        ),
    ),
    (
        CommunicationCategory.CLIENT_INQUIRY,
        re.compile(
            r"\b(interested in your services|looking for a freelancer|"
            r"project inquiry|quote for)\b",
            re.I,
        ),
    ),
    (
        CommunicationCategory.FOLLOW_UP,
        re.compile(r"\b(following up|just checking in|any update|circling back)\b", re.I),
    ),
]


def classify(subject: str, body: str) -> CommunicationCategory:
    text = f"{subject}\n{body}"
    for category, pattern in _PATTERNS:
        if pattern.search(text):
            return category
    return CommunicationCategory.OTHER
