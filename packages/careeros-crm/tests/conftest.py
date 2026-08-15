"""Shared fixtures for CRM tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_crm import Contact, ContactRepository, ContactRole, TimelineRepository


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def contact_repository(store):
    return ContactRepository(store)


@pytest.fixture
def timeline_repository(store):
    return TimelineRepository(store)


@pytest.fixture
def contact():
    return Contact(name="Jane Smith", role=ContactRole.RECRUITER, organization_name="Acme")
