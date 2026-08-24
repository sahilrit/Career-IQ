"""careeros_reply_tracking: post-application reply tracking.

Connect a mailbox and CareerOS reads recruiter replies for you — an
interview invitation moves the application to Interviewing, a "we won't
be progressing" moves it to Rejected — so the pipeline board reflects
reality without anyone updating it by hand.

The classifier is deterministic and conservative by design; the sync loop
walks the same status-transition rules a human is held to, and never
forces an illegal jump.
"""

from careeros_reply_tracking.classifier import ReplySignal, classify_email
from careeros_reply_tracking.sync import (
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_MAX_MESSAGES,
    EmailMessage,
    Mailbox,
    ReplySyncSummary,
    sync_replies,
)

__all__ = [
    "DEFAULT_LOOKBACK_DAYS",
    "DEFAULT_MAX_MESSAGES",
    "EmailMessage",
    "Mailbox",
    "ReplySignal",
    "ReplySyncSummary",
    "classify_email",
    "sync_replies",
]
