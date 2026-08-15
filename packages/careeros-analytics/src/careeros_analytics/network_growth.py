"""Network growth: how many contacts (Phase 33) have actually reached
each relationship stage — "LinkedIn outreach" maps to Messaged, which
is the real stage a CRM interaction gets recorded under.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_crm import Contact, RelationshipStage, TimelineRepository


class NetworkGrowthMetrics(BaseModel):
    contact_count: int
    connected_count: int
    messaged_count: int
    conversation_count: int


def compute_network_growth(
    contacts: list[Contact], timeline_repository: TimelineRepository
) -> NetworkGrowthMetrics:
    def reached(contact: Contact, stage: RelationshipStage) -> bool:
        timeline = timeline_repository.load(contact.id)
        return any(interaction.stage == stage for interaction in timeline.interactions)

    return NetworkGrowthMetrics(
        contact_count=len(contacts),
        connected_count=sum(1 for c in contacts if reached(c, RelationshipStage.CONNECTED)),
        messaged_count=sum(1 for c in contacts if reached(c, RelationshipStage.MESSAGED)),
        conversation_count=sum(1 for c in contacts if reached(c, RelationshipStage.CONVERSATION)),
    )
