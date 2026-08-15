"""Tests for the ClientSuccessDivision facade."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_client_success import (
    ClientLifecycleStage,
    ClientSuccessDivision,
    Deliverable,
    DeliverableStatus,
    Invoice,
    InvoiceStatus,
    MeetingNote,
    ReferralRecord,
)


@pytest.fixture
def division(
    contract_repository,
    deliverable_repository,
    meeting_note_repository,
    invoice_repository,
    referral_repository,
):
    return ClientSuccessDivision(
        contract_repository,
        deliverable_repository,
        meeting_note_repository,
        invoice_repository,
        referral_repository,
    )


def test_outstanding_balance_for_contract(division, contract):
    division.add_contract(contract)
    division.add_invoice(
        Invoice(
            contract_id=contract.id,
            amount=2_000,
            issued_date=date(2026, 1, 1),
            due_date=date(2026, 1, 31),
            status=InvoiceStatus.SENT,
        )
    )
    assert division.outstanding_balance_for_contract(contract.id) == 2_000


def test_lifecycle_stage_for_client_with_no_contracts(division):
    assert division.lifecycle_stage_for("client-1") is None


def test_lifecycle_stage_for_client_with_a_referral(division, contract):
    division.add_contract(contract)
    division.record_referral(ReferralRecord(client_id=contract.client_id, referred_name="New Co"))
    assert division.lifecycle_stage_for(contract.client_id) == ClientLifecycleStage.REFERRAL_SOURCE


def test_renewal_reminder_delegates(division, contract):
    division.add_contract(contract)
    reminder = division.renewal_reminder(contract.id)
    assert contract.title in reminder


def test_upsell_suggestion_delegates(division, contract):
    division.add_contract(contract)
    division.add_deliverable(
        Deliverable(contract_id=contract.id, title="Homepage", status=DeliverableStatus.APPROVED)
    )
    suggestion = division.upsell_suggestion(contract.id)
    assert contract.title in suggestion


def test_add_meeting_note(division, contract):
    note = MeetingNote(client_id=contract.client_id, summary="Kickoff")
    division.add_meeting_note(note)
