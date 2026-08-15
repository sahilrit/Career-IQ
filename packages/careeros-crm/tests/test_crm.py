"""Tests for the RelationshipCRM facade."""

from __future__ import annotations

import pytest

from careeros_crm import Contact, ContactRole, RelationshipCRM, RelationshipStage
from careeros_event_bus import Event, EventBus


@pytest.fixture
def crm(contact_repository, timeline_repository):
    return RelationshipCRM(contact_repository, timeline_repository)


def test_add_and_get_contact(crm, contact):
    crm.add_contact(contact)
    assert crm.get_contact(contact.id) == contact


def test_get_contact_returns_none_when_missing(crm):
    assert crm.get_contact("missing") is None


def test_list_contacts_filters_by_role(crm, contact):
    crm.add_contact(contact)
    founder = Contact(name="Founder Co", role=ContactRole.FOUNDER)
    crm.add_contact(founder)
    assert crm.list_contacts(ContactRole.FOUNDER) == [founder]
    assert len(crm.list_contacts()) == 2


def test_record_engagement_and_timeline_for(crm, contact):
    crm.add_contact(contact)
    crm.record_engagement(contact.id, RelationshipStage.VIEWED)
    crm.record_engagement(contact.id, RelationshipStage.CONNECTED)
    timeline = crm.timeline_for(contact.id)
    assert timeline.current_stage == RelationshipStage.CONNECTED


def test_contacts_at_stage(crm, contact):
    crm.add_contact(contact)
    other = Contact(name="Other", role=ContactRole.PROSPECT)
    crm.add_contact(other)
    crm.record_engagement(contact.id, RelationshipStage.CONNECTED)
    assert crm.contacts_at_stage(RelationshipStage.CONNECTED) == [contact]
    assert crm.contacts_at_stage(RelationshipStage.VIEWED) == []


def test_wire_events_hooks_the_shared_timeline_repository(crm, timeline_repository, contact):
    crm.add_contact(contact)
    bus = EventBus()
    RelationshipCRM.wire_events(bus, timeline_repository)
    bus.publish(Event(event_type="company.qualified", payload={"subject_id": contact.id}))
    assert crm.timeline_for(contact.id).current_stage == RelationshipStage.OPPORTUNITY
