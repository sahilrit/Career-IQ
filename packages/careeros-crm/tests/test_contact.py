"""Tests for Contact / ContactRepository."""

from __future__ import annotations

from careeros_crm import Contact, ContactRole


def test_save_and_load_round_trips(contact_repository, contact):
    contact_repository.save(contact)
    loaded = contact_repository.load(contact.id)
    assert loaded == contact


def test_load_or_none_returns_none_when_missing(contact_repository):
    assert contact_repository.load_or_none("missing") is None


def test_list_all_returns_every_saved_contact(contact_repository, contact):
    contact_repository.save(contact)
    assert contact_repository.list_all() == [contact]


def test_list_by_role_filters(contact_repository, contact):
    other = Contact(name="Founder Co", role=ContactRole.FOUNDER)
    contact_repository.save(contact)
    contact_repository.save(other)
    assert contact_repository.list_by_role(ContactRole.FOUNDER) == [other]
