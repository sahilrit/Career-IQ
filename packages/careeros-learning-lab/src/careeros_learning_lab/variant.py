"""Variant: one version of an experiment's content — the actual
resume/email/proposal text (or a reference to it) that real outcomes
get measured against.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "variant"


class Variant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    label: str
    content: str = ""


class VariantRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, variant: Variant) -> None:
        self._store.put(_ENTITY_TYPE, variant.id, variant.model_dump(mode="json"))

    def load(self, variant_id: str) -> Variant:
        return Variant.model_validate(self._store.get(_ENTITY_TYPE, variant_id))

    def list_for_experiment(self, experiment_id: str) -> list[Variant]:
        return [
            Variant.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("experiment_id") == experiment_id
        ]
