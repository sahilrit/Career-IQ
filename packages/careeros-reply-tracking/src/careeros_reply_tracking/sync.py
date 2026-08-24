"""The reply-tracking sync loop.

Reads recent recruiter email, matches each message to an open application
by company, and moves the application to the stage the message signals.
It never invents a jump: the domain's transition rules are the same ones
a human is held to, so an interview email on a freshly-applied job walks
APPLIED -> IN_REVIEW -> INTERVIEWING one legal step at a time, and a
rejection on an already-accepted offer is refused.

The mailbox is a protocol so the whole loop runs against fixtures with no
Gmail account. The API layer supplies a real Gmail-backed implementation.
"""

from __future__ import annotations

from collections import deque
from typing import Protocol

from pydantic import BaseModel, Field

from careeros_career_brain import (
    ALLOWED_STATUS_TRANSITIONS,
    Application,
    ApplicationStatus,
    CareerBrain,
    CareerBrainRepository,
)
from careeros_common import DocumentStore, get_logger
from careeros_event_bus import Event, EventBus
from careeros_reply_tracking.classifier import ReplySignal, classify_email

logger = get_logger(__name__)

DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_MAX_MESSAGES = 100

# Suffixes stripped from a company name before matching it against an email,
# so "Acme Corp" and "acme" line up.
_COMPANY_NOISE = (
    "inc",
    "inc.",
    "llc",
    "ltd",
    "ltd.",
    "limited",
    "corp",
    "corp.",
    "corporation",
    "co",
    "co.",
    "company",
    "gmbh",
    "plc",
    "technologies",
    "technology",
    "labs",
    "group",
    "holdings",
)


class EmailMessage(BaseModel):
    id: str
    sender: str
    subject: str
    body: str


class Mailbox(Protocol):
    def recent_messages(self, *, days: int, max_messages: int) -> list[EmailMessage]: ...


class ReplySyncSummary(BaseModel):
    scanned: int = 0
    transitioned: int = 0
    already_seen: int = 0
    skipped_illegal: int = 0
    unmatched: int = 0


class _SeenState(BaseModel):
    """Message ids already acted on, so a scheduled re-scan is idempotent."""

    message_ids: list[str] = Field(default_factory=list)


_SEEN_ENTITY = "reply_tracking_seen"


def _company_key(name: str) -> str:
    tokens = "".join(c if c.isalnum() else " " for c in name.lower()).split()
    meaningful = [t for t in tokens if t not in _COMPANY_NOISE]
    return "".join(meaningful or tokens)


def _email_mentions_company(message: EmailMessage, company_key: str) -> bool:
    if not company_key:
        return False
    haystack = _company_key(f"{message.sender} {message.subject}")
    return company_key in haystack


def _transition_path(
    start: ApplicationStatus, target: ApplicationStatus
) -> list[ApplicationStatus] | None:
    """The shortest legal sequence of stages from ``start`` to ``target``.

    A recruiter's "you're through to interview" can arrive while we still
    have the job at APPLIED, several legal hops short of INTERVIEWING.
    Rather than force the jump — which would bypass the very rules that keep
    status honest — we walk the transition graph and take every intermediate
    step, or give up if no legal path exists.
    """
    if start == target:
        return []
    queue: deque[tuple[ApplicationStatus, list[ApplicationStatus]]] = deque([(start, [])])
    seen = {start}
    while queue:
        state, path = queue.popleft()
        for nxt in ALLOWED_STATUS_TRANSITIONS[state]:
            if nxt in seen:
                continue
            new_path = [*path, nxt]
            if nxt == target:
                return new_path
            seen.add(nxt)
            queue.append((nxt, new_path))
    return None


def _matching_applications(brain: CareerBrain, message: EmailMessage) -> list[Application]:
    """Every application whose company this email mentions.

    A person may have applied to two roles at the same company, so this can
    return more than one; the caller prefers whichever can legally take the
    signalled stage.
    """
    return [
        application
        for application in brain.applications
        if _email_mentions_company(message, _company_key(application.company_name))
    ]


def _walk(application: Application, signal: ReplySignal) -> None:
    """Move the application through every legal step to the signalled stage.

    The caller has already confirmed a legal path exists, so this only has to
    replay it.
    """
    assert signal.target is not None
    path = _transition_path(application.status, signal.target) or []
    note = (
        f"auto: recruiter email ({signal.evidence})" if signal.evidence else "auto: recruiter email"
    )
    for step in path:
        application.transition_to(step, note=note)


def sync_replies(
    store: DocumentStore,
    identity_id: str,
    mailbox: Mailbox,
    *,
    event_bus: EventBus,
    days: int = DEFAULT_LOOKBACK_DAYS,
    max_messages: int = DEFAULT_MAX_MESSAGES,
) -> ReplySyncSummary:
    """Read recent email and advance any application a recruiter has replied to."""
    repository = CareerBrainRepository(store)
    brain = repository.load(identity_id)

    seen_raw = store.get_or_none(_SEEN_ENTITY, identity_id)
    seen = _SeenState.model_validate(seen_raw) if seen_raw else _SeenState()
    seen_ids = set(seen.message_ids)

    summary = ReplySyncSummary()
    changed = False

    for message in mailbox.recent_messages(days=days, max_messages=max_messages):
        summary.scanned += 1
        if message.id in seen_ids:
            summary.already_seen += 1
            continue

        signal = classify_email(subject=message.subject, body=message.body)
        # Record every message we have examined, signal or not, so a neutral
        # email is not re-classified on every run.
        seen_ids.add(message.id)

        if not signal:
            continue

        candidates = _matching_applications(brain, message)
        if not candidates:
            summary.unmatched += 1
            continue

        # Prefer an application that can legally take this signal; a job that
        # is still open beats one that is already decided.
        movable = [
            application
            for application in candidates
            if _transition_path(application.status, signal.target)
        ]
        if not movable:
            # The company matched, but no matching application can legally move
            # — e.g. a rejection email for an offer we already accepted.
            summary.skipped_illegal += 1
            continue

        application = movable[0]
        previous = application.status
        _walk(application, signal)
        summary.transitioned += 1
        changed = True
        event_bus.publish(
            Event(
                event_type="application.status_changed",
                source="reply-tracking",
                payload={
                    "subject_id": application.id,
                    "previous_status": previous.value,
                    "new_status": application.status.value,
                    "evidence": signal.evidence,
                    "message_id": message.id,
                },
            )
        )

    if changed:
        repository.save(brain)
    store.put(_SEEN_ENTITY, identity_id, _SeenState(message_ids=sorted(seen_ids)).model_dump())

    return summary
