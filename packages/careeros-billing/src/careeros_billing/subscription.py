"""Subscription: which plan a workspace is on and its lifecycle state —
purely a state tracker. No card numbers, no charges, nothing that
touches real money; a real payment processor would update this state
via webhooks, kept entirely separate from this record.
"""

from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_billing.plan import PlanTier
from careeros_common import DocumentStore

_ENTITY_TYPE = "subscription"


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    plan_tier: PlanTier
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    current_period_end: date | None = None
    trial_ends_at: date | None = None


class SubscriptionRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, subscription: Subscription) -> None:
        self._store.put(
            _ENTITY_TYPE, subscription.workspace_id, subscription.model_dump(mode="json")
        )

    def load_or_none(self, workspace_id: str) -> Subscription | None:
        data = self._store.get_or_none(_ENTITY_TYPE, workspace_id)
        return Subscription.model_validate(data) if data is not None else None
