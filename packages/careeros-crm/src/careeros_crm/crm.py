"""RelationshipCRM: the facade tying contacts and their relationship
timelines together.
"""

from __future__ import annotations

from careeros_crm.contact import Contact, ContactRepository, ContactRole
from careeros_crm.events import wire_crm
from careeros_crm.timeline import RelationshipStage, RelationshipTimeline, TimelineRepository
from careeros_event_bus import EventBus


class RelationshipCRM:
    def __init__(
        self, contact_repository: ContactRepository, timeline_repository: TimelineRepository
    ) -> None:
        self._contacts = contact_repository
        self._timelines = timeline_repository

    @staticmethod
    def wire_events(bus: EventBus, timeline_repository: TimelineRepository) -> None:
        wire_crm(bus, timeline_repository)

    def add_contact(self, contact: Contact) -> None:
        self._contacts.save(contact)

    def get_contact(self, contact_id: str) -> Contact | None:
        return self._contacts.load_or_none(contact_id)

    def list_contacts(self, role: ContactRole | None = None) -> list[Contact]:
        if role is None:
            return self._contacts.list_all()
        return self._contacts.list_by_role(role)

    def record_engagement(
        self, contact_id: str, stage: RelationshipStage, detail: str = ""
    ) -> RelationshipTimeline:
        return self._timelines.record(contact_id, stage, detail)

    def timeline_for(self, contact_id: str) -> RelationshipTimeline:
        return self._timelines.load(contact_id)

    def contacts_at_stage(self, stage: RelationshipStage) -> list[Contact]:
        return [
            contact
            for contact in self._contacts.list_all()
            if self._timelines.load(contact.id).current_stage == stage
        ]
