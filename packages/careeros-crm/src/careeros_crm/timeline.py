"""RelationshipTimeline: how far a relationship with a Contact has
progressed, using the roadmap's own engagement sequence:

    Viewed -> Liked -> Commented -> Connected -> Messaged -> Conversation
      -> Opportunity -> Client / Employer

Unlike Phase 30/31's pipeline progress (an ordered checklist of
required steps), a relationship can skip stages entirely — a cold email
can go straight to Conversation without a Like ever happening — so this
tracks a full ordered log of interactions, not just a completed-stages
set, while still exposing "furthest stage reached" the same way.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "relationship_timeline"


class RelationshipStage(StrEnum):
    VIEWED = "viewed"
    LIKED = "liked"
    COMMENTED = "commented"
    CONNECTED = "connected"
    MESSAGED = "messaged"
    CONVERSATION = "conversation"
    OPPORTUNITY = "opportunity"
    CLIENT_OR_EMPLOYER = "client_or_employer"


_STAGE_ORDER = list(RelationshipStage)


class Interaction(BaseModel):
    stage: RelationshipStage
    detail: str = ""
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RelationshipTimeline(BaseModel):
    contact_id: str
    interactions: list[Interaction] = Field(default_factory=list)

    @property
    def current_stage(self) -> RelationshipStage | None:
        current = None
        for stage in _STAGE_ORDER:
            if any(interaction.stage == stage for interaction in self.interactions):
                current = stage
        return current

    @property
    def next_stage(self) -> RelationshipStage | None:
        current = self.current_stage
        if current is None:
            return _STAGE_ORDER[0]
        index = _STAGE_ORDER.index(current)
        if index + 1 >= len(_STAGE_ORDER):
            return None
        return _STAGE_ORDER[index + 1]


class TimelineRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def load(self, contact_id: str) -> RelationshipTimeline:
        data = self._store.get_or_none(_ENTITY_TYPE, contact_id)
        if data is None:
            return RelationshipTimeline(contact_id=contact_id)
        return RelationshipTimeline.model_validate(data)

    def record(
        self, contact_id: str, stage: RelationshipStage, detail: str = ""
    ) -> RelationshipTimeline:
        timeline = self.load(contact_id)
        timeline.interactions.append(Interaction(stage=stage, detail=detail))
        self._store.put(_ENTITY_TYPE, contact_id, timeline.model_dump(mode="json"))
        return timeline
