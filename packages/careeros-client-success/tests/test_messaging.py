"""Tests for render_renewal_reminder / render_upsell_suggestion."""

from __future__ import annotations

from careeros_client_success import Deliverable, DeliverableStatus
from careeros_client_success.messaging import render_renewal_reminder, render_upsell_suggestion


def test_renewal_reminder_mentions_contract_title(contract):
    reminder = render_renewal_reminder(contract)
    assert contract.title in reminder


def test_upsell_suggestion_with_no_approved_deliverables(contract):
    suggestion = render_upsell_suggestion(contract, [])
    assert contract.title in suggestion


def test_upsell_suggestion_mentions_approved_deliverable_count(contract):
    deliverables = [
        Deliverable(contract_id=contract.id, title="Homepage", status=DeliverableStatus.APPROVED),
        Deliverable(contract_id=contract.id, title="Checkout", status=DeliverableStatus.PENDING),
    ]
    suggestion = render_upsell_suggestion(contract, deliverables)
    assert "1 deliverable" in suggestion
