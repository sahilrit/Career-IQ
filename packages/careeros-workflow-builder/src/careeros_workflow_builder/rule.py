"""Rule: one no-code WHEN/THEN automation — WHEN an event matches
``event_type`` and (optionally) ``condition``, THEN run ``actions`` in
order. The engine (see ``engine.py``) is what actually dispatches
these; this module is just the declarative shape a user builds without
code.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from careeros_common import DocumentStore
from careeros_workflow_builder.condition import Condition

_ENTITY_TYPE = "workflow_rule"


class Rule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    event_type: str
    condition: Condition | None = None
    actions: list[str] = Field(default_factory=list)
    enabled: bool = True


class RuleRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, rule: Rule) -> None:
        self._store.put(_ENTITY_TYPE, rule.id, rule.model_dump(mode="json"))

    def load(self, rule_id: str) -> Rule:
        return Rule.model_validate(self._store.get(_ENTITY_TYPE, rule_id))

    def list_all(self) -> list[Rule]:
        return [Rule.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def list_enabled(self) -> list[Rule]:
        return [rule for rule in self.list_all() if rule.enabled]
