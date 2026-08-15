"""Shared fixtures for client success tests."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_client_success import (
    Contract,
    ContractRepository,
    ContractStatus,
    DeliverableRepository,
    InvoiceRepository,
    MeetingNoteRepository,
    ReferralRepository,
)
from careeros_common import DocumentStore


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def contract_repository(store):
    return ContractRepository(store)


@pytest.fixture
def deliverable_repository(store):
    return DeliverableRepository(store)


@pytest.fixture
def meeting_note_repository(store):
    return MeetingNoteRepository(store)


@pytest.fixture
def invoice_repository(store):
    return InvoiceRepository(store)


@pytest.fixture
def referral_repository(store):
    return ReferralRepository(store)


@pytest.fixture
def contract():
    return Contract(
        client_id="client-1",
        title="Website Redesign",
        start_date=date(2026, 1, 1),
        status=ContractStatus.ACTIVE,
    )
