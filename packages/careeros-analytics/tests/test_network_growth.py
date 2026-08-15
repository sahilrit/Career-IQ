"""Tests for compute_network_growth."""

from __future__ import annotations

from careeros_analytics import compute_network_growth
from careeros_crm import Contact, ContactRole, RelationshipStage, TimelineRepository


def test_contact_count_is_every_contact(store):
    contacts = [Contact(name="Jane", role=ContactRole.RECRUITER)]
    metrics = compute_network_growth(contacts, TimelineRepository(store))
    assert metrics.contact_count == 1
    assert metrics.connected_count == 0


def test_stage_counts_reflect_real_interactions(store):
    contact = Contact(name="Jane", role=ContactRole.RECRUITER)
    timeline_repository = TimelineRepository(store)
    timeline_repository.record(contact.id, RelationshipStage.CONNECTED)
    timeline_repository.record(contact.id, RelationshipStage.MESSAGED)

    metrics = compute_network_growth([contact], timeline_repository)
    assert metrics.connected_count == 1
    assert metrics.messaged_count == 1
    assert metrics.conversation_count == 0
