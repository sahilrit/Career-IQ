"""Models for the LLM gateway: what a task is, what a provider reports about
itself, and what one completed call looks like.

The gateway's job is to keep CareerOS business logic (resume tailoring, job
analysis, question answering, review) from ever naming a vendor. Business
logic asks for a ``LLMTask``; the gateway decides which provider serves it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class LLMTask(StrEnum):
    """What the caller is asking for, not which model should do it.

    Routing maps these to providers/models (see ``LLMConfig``), so swapping a
    cheap model in for classification is a config change, never a code change.
    """

    #: Short, mechanical, high-volume — tier/keyword classification.
    CLASSIFY = "classify"
    #: Pull structured fields out of a posting. Fast model is fine.
    EXTRACT = "extract"
    #: Read a job/company and reason about fit. Mid tier.
    ANALYZE = "analyze"
    #: Candidate-facing prose that gets read by a human. Best model.
    WRITE = "write"
    #: Answer a specific application question truthfully. Best model.
    ANSWER = "answer"
    #: Independently check someone else's draft. Deliberately routed to a
    #: DIFFERENT provider than WRITE when more than one is configured, so the
    #: reviewer does not inherit the drafter's blind spots.
    REVIEW = "review"


class FailureKind(StrEnum):
    """Why a provider call failed, at the granularity that changes behaviour.

    The distinction that matters is RETRYABLE vs not. Retrying a timeout is
    reasonable; retrying "you are not logged in" is a loop that burns the
    user's time and tells them nothing. ``is_retryable`` is the only question
    callers ask of this, and it is asked about retrying the SAME provider —
    moving on to a *different* provider is always allowed regardless, because
    a different provider does not share the failure.
    """

    #: The call did not finish in time. Trying again can genuinely work.
    TIMEOUT = "timeout"
    #: Connection reset, DNS, 5xx. Transient by nature.
    NETWORK = "network"
    #: The provider answered, but not in the shape the caller requires. A
    #: retry with a stricter instruction is the standard, effective fix.
    MALFORMED = "malformed"
    #: The provider is up but declined to serve right now.
    UNAVAILABLE = "unavailable"
    #: The executable/endpoint does not exist here. Nothing to retry.
    NOT_INSTALLED = "not_installed"
    #: Present but not logged in / key rejected. The user must act.
    NOT_AUTHENTICATED = "not_authenticated"
    #: Quota or rate limit hit. An immediate retry hits the same wall, so it
    #: is NOT retryable here — the fallback chain (a different provider) is
    #: the correct response, not a tighter loop against the same one.
    RATE_LIMITED = "rate_limited"
    #: The configuration itself is wrong (unknown model, bad base URL).
    INVALID_CONFIG = "invalid_config"
    #: The task cannot be completed without information only a human has.
    NEEDS_HUMAN = "needs_human"
    #: Unclassified. Treated as non-retryable on purpose: an unrecognised
    #: failure repeated three times is three times the damage if it is not
    #: actually transient.
    UNKNOWN = "unknown"

    @property
    def is_retryable(self) -> bool:
        return self in _RETRYABLE_KINDS


_RETRYABLE_KINDS = frozenset(
    {
        FailureKind.TIMEOUT,
        FailureKind.NETWORK,
        FailureKind.MALFORMED,
        FailureKind.UNAVAILABLE,
    }
)


#: Substrings that identify a failure kind from a provider's own error text.
#: Ordered most-specific first: "invalid api key" must classify as an auth
#: problem, not as a generic "invalid" configuration one.
_KIND_MARKERS: tuple[tuple[str, FailureKind], ...] = (
    ("not logged in", FailureKind.NOT_AUTHENTICATED),
    ("please run /login", FailureKind.NOT_AUTHENTICATED),
    ("please set an auth method", FailureKind.NOT_AUTHENTICATED),
    ("no auth method", FailureKind.NOT_AUTHENTICATED),
    ("authentication required", FailureKind.NOT_AUTHENTICATED),
    ("unauthorized", FailureKind.NOT_AUTHENTICATED),
    ("invalid api key", FailureKind.NOT_AUTHENTICATED),
    ("api key not found", FailureKind.NOT_AUTHENTICATED),
    ("api key was rejected", FailureKind.NOT_AUTHENTICATED),
    ("no api key", FailureKind.NOT_AUTHENTICATED),
    ("quota exceeded", FailureKind.RATE_LIMITED),
    ("rate limit", FailureKind.RATE_LIMITED),
    ("usage limit reached", FailureKind.RATE_LIMITED),
    ("too many requests", FailureKind.RATE_LIMITED),
    ("is not installed", FailureKind.NOT_INSTALLED),
    ("command not found", FailureKind.NOT_INSTALLED),
    ("executable not found", FailureKind.NOT_INSTALLED),
    ("no such file or directory", FailureKind.NOT_INSTALLED),
    ("timed out", FailureKind.TIMEOUT),
    ("timeout", FailureKind.TIMEOUT),
    ("connection reset", FailureKind.NETWORK),
    ("connection refused", FailureKind.NETWORK),
    ("connection aborted", FailureKind.NETWORK),
    ("temporarily unavailable", FailureKind.NETWORK),
    ("network", FailureKind.NETWORK),
    ("bad gateway", FailureKind.NETWORK),
    ("service unavailable", FailureKind.NETWORK),
    ("unknown model", FailureKind.INVALID_CONFIG),
    ("model not found", FailureKind.INVALID_CONFIG),
    ("unsupported model", FailureKind.INVALID_CONFIG),
)


def classify_failure(message: str) -> FailureKind:
    """The failure kind a provider's error message describes.

    Providers report failures as prose (an HTTP body, a CLI banner), so this
    is pattern matching by necessity. It is deliberately conservative: an
    unrecognised message is UNKNOWN, which is non-retryable, so a
    misclassification costs a fallback rather than a retry storm.
    """
    lowered = (message or "").lower()
    for marker, kind in _KIND_MARKERS:
        if marker in lowered:
            return kind
    return FailureKind.UNKNOWN


class ProviderStatus(StrEnum):
    """What a provider can actually do for us right now.

    These are deliberately specific. A single generic "failed" was the thing
    that made an unauthenticated CLI indistinguishable from an uninstalled
    one, and left the user with nothing to act on.

    "Installed" and "authenticated" are FACTS about a provider, not statuses —
    they live on ``ProviderHealth`` as booleans, because a provider can be
    installed and still unusable, and knowing both is what makes the message
    actionable.
    """

    #: Present, authenticated, and answered a probe. The only usable state.
    AVAILABLE = "available"
    #: Back-compat alias of AVAILABLE (this is what it always meant).
    HEALTHY = "available"
    #: The executable/endpoint does not exist on this machine.
    NOT_INSTALLED = "not_installed"
    #: Back-compat alias: for a CLI provider, ABSENT always meant not installed.
    ABSENT = "not_installed"
    #: Nothing configured at all — no API key, no credentials. Not an error.
    NOT_CONFIGURED = "not_configured"
    #: Installed/configured, but the user has not logged in or the key was
    #: rejected. One command away from working, and we know which one.
    NOT_AUTHENTICATED = "not_authenticated"
    #: Authenticated but out of quota right now.
    RATE_LIMITED = "rate_limited"
    #: Present and, as far as we can tell, authenticated — but it did not
    #: answer. Transient: worth trying again later.
    UNAVAILABLE = "unavailable"
    #: The health check itself broke. That is a CareerOS bug, not a user
    #: problem, and must never be reported as "you are not logged in".
    ERROR = "error"


#: How a failure kind surfaces as a provider status.
_STATUS_FOR_KIND: dict[FailureKind, ProviderStatus] = {
    FailureKind.NOT_INSTALLED: ProviderStatus.NOT_INSTALLED,
    FailureKind.NOT_AUTHENTICATED: ProviderStatus.NOT_AUTHENTICATED,
    FailureKind.RATE_LIMITED: ProviderStatus.RATE_LIMITED,
    FailureKind.INVALID_CONFIG: ProviderStatus.ERROR,
    FailureKind.TIMEOUT: ProviderStatus.UNAVAILABLE,
    FailureKind.NETWORK: ProviderStatus.UNAVAILABLE,
    FailureKind.UNAVAILABLE: ProviderStatus.UNAVAILABLE,
    FailureKind.MALFORMED: ProviderStatus.UNAVAILABLE,
    FailureKind.NEEDS_HUMAN: ProviderStatus.ERROR,
    FailureKind.UNKNOWN: ProviderStatus.UNAVAILABLE,
}


def status_for_failure(kind: FailureKind) -> ProviderStatus:
    return _STATUS_FOR_KIND.get(kind, ProviderStatus.UNAVAILABLE)


class ProviderHealth(BaseModel):
    provider_id: str
    status: ProviderStatus
    #: Human-readable and ACTIONABLE — "run `claude /login`", not "error".
    detail: str = ""
    model: str = ""
    #: Is the underlying thing present here at all? None where the question
    #: does not apply (a hosted HTTP API is never "installed").
    installed: bool | None = None
    #: Did credentials work? None when we could not get far enough to tell —
    #: which is itself information, and different from a definite False.
    authenticated: bool | None = None
    #: The exact command or setting that would fix it, when there is one.
    remedy: str = ""
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def usable(self) -> bool:
        return self.status is ProviderStatus.AVAILABLE

    @property
    def needs_user_action(self) -> bool:
        """Whether a human could make this provider work, as opposed to
        waiting (UNAVAILABLE) or nothing at all (NOT_INSTALLED with no
        install path offered)."""
        return self.status in (
            ProviderStatus.NOT_AUTHENTICATED,
            ProviderStatus.NOT_CONFIGURED,
        )

    def describe(self) -> str:
        """The multi-line form the health dashboard prints.

        Says installed/authenticated/usable separately and gives the reason,
        because collapsing them is exactly the failure this model exists to
        prevent.
        """
        lines = [self.provider_id]
        if self.installed is not None:
            lines.append(f"  installed: {'yes' if self.installed else 'no'}")
        if self.authenticated is not None:
            lines.append(f"  authenticated: {'yes' if self.authenticated else 'no'}")
        lines.append(f"  usable: {'yes' if self.usable else 'no'}")
        if self.detail:
            lines.append(f"  reason: {self.detail}")
        if self.remedy:
            lines.append(f"  fix: {self.remedy}")
        return "\n".join(lines)


class LLMRun(BaseModel):
    """One completed (or failed) gateway call — the observability record.

    Stored alongside an application attempt so a bad generated answer can be
    traced back to the exact provider and model that produced it. Prompts are
    NOT stored here: they contain the candidate's profile.
    """

    task: LLMTask
    provider_id: str
    model: str
    succeeded: bool
    #: Providers tried and rejected before this one, with the reason.
    fallbacks: list[str] = Field(default_factory=list)
    duration_ms: int = 0
    error: str = ""
    #: Length only — never the text itself.
    response_chars: int = 0
    #: How many times the SAME provider was re-asked (malformed output). Zero
    #: on the normal path; a non-zero value here is the signal that a model is
    #: struggling with a schema.
    retries: int = 0
    ran_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
