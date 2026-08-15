"""PredictionSignal: one real, observed indicator that a company is
about to need help — funding, hiring velocity, a new product, expansion,
an executive hire, marketing/agency team growth, a new market, or a
technology change. Every signal here is something actually observed
(the caller supplies it, or it's computed from real platform data like
job posting counts — see hiring_velocity.py) — nothing is guessed.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "prediction_signal"


class SignalType(StrEnum):
    FUNDING = "funding"
    HIRING_VELOCITY = "hiring_velocity"
    NEW_PRODUCT = "new_product"
    EXPANSION = "expansion"
    EXECUTIVE_HIRE = "executive_hire"
    MARKETING_TEAM_GROWTH = "marketing_team_growth"
    AGENCY_EXPANSION = "agency_expansion"
    NEW_MARKET = "new_market"
    TECHNOLOGY_CHANGE = "technology_change"


class PredictionSignal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    signal_type: SignalType
    detail: str
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PredictionSignalRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, signal: PredictionSignal) -> None:
        self._store.put(_ENTITY_TYPE, signal.id, signal.model_dump(mode="json"))

    def list_for_company(self, company_id: str) -> list[PredictionSignal]:
        return [
            PredictionSignal.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("company_id") == company_id
        ]
