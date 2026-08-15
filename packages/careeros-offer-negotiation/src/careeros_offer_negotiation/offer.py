"""Offer: everything about a job or contract offer worth analyzing
beyond the headline salary figure. Every field is either a hard number
the offer actually states, or a 1-5 rating the user themselves assigns
— nothing here is inferred or fabricated.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "offer"


class Offer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    job_title: str
    base_salary: float
    bonus: float = 0.0
    equity_value: float = Field(
        default=0.0, description="Annualized, user-estimated dollar value of any equity grant."
    )
    benefits_value: float = Field(
        default=0.0, description="User-estimated annual dollar value of benefits."
    )
    pto_days: int = 0
    remote_policy: str = ""
    timezone_overlap_hours: int | None = None
    stability_score: int | None = Field(
        default=None, description="1 (high risk) - 5 (very stable), user's own judgment."
    )
    growth_score: int | None = Field(
        default=None, description="1 (little growth) - 5 (high growth), user's own judgment."
    )
    reputation_score: int | None = Field(
        default=None, description="1 (poor reputation) - 5 (excellent), user's own judgment."
    )
    notes: str = ""


class OfferRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, offer: Offer) -> None:
        self._store.put(_ENTITY_TYPE, offer.id, offer.model_dump(mode="json"))

    def load(self, offer_id: str) -> Offer:
        return Offer.model_validate(self._store.get(_ENTITY_TYPE, offer_id))

    def load_or_none(self, offer_id: str) -> Offer | None:
        data = self._store.get_or_none(_ENTITY_TYPE, offer_id)
        return Offer.model_validate(data) if data is not None else None

    def list_all(self) -> list[Offer]:
        return [Offer.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
