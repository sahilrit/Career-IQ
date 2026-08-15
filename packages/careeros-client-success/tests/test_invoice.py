"""Tests for Invoice / outstanding_balance."""

from __future__ import annotations

from datetime import date

from careeros_client_success import Invoice, InvoiceStatus, outstanding_balance


def _invoice(status: InvoiceStatus, amount: float = 1_000.0) -> Invoice:
    return Invoice(
        contract_id="contract-1",
        amount=amount,
        issued_date=date(2026, 1, 1),
        due_date=date(2026, 1, 31),
        status=status,
    )


def test_list_for_contract_filters(invoice_repository):
    matching = _invoice(InvoiceStatus.SENT)
    other = Invoice(
        contract_id="other-contract",
        amount=500.0,
        issued_date=date(2026, 1, 1),
        due_date=date(2026, 1, 31),
    )
    invoice_repository.save(matching)
    invoice_repository.save(other)
    assert invoice_repository.list_for_contract("contract-1") == [matching]


def test_outstanding_balance_includes_sent_and_overdue():
    invoices = [_invoice(InvoiceStatus.SENT, 1_000), _invoice(InvoiceStatus.OVERDUE, 500)]
    assert outstanding_balance(invoices) == 1_500


def test_outstanding_balance_excludes_paid_and_draft():
    invoices = [_invoice(InvoiceStatus.PAID, 1_000), _invoice(InvoiceStatus.DRAFT, 500)]
    assert outstanding_balance(invoices) == 0


def test_outstanding_balance_of_empty_list_is_zero():
    assert outstanding_balance([]) == 0
