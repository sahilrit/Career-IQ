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


class ProviderStatus(StrEnum):
    #: Configured, reachable, and answered a probe.
    HEALTHY = "healthy"
    #: Present but cannot serve a call right now (not logged in, no key, rate
    #: limited). Distinguished from DOWN because the fix is usually one command.
    UNAVAILABLE = "unavailable"
    #: Not installed / not configured at all. Never an error, just absent.
    ABSENT = "absent"


class ProviderHealth(BaseModel):
    provider_id: str
    status: ProviderStatus
    #: Human-readable and ACTIONABLE — "run `claude /login`", not "error".
    detail: str = ""
    model: str = ""
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def usable(self) -> bool:
        return self.status is ProviderStatus.HEALTHY


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
    ran_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
