"""Tests for Contract / ContractRepository."""

from __future__ import annotations

from datetime import date

from careeros_client_success import Contract


def test_save_and_load_round_trips(contract_repository, contract):
    contract_repository.save(contract)
    assert contract_repository.load(contract.id) == contract


def test_load_or_none_returns_none_when_missing(contract_repository):
    assert contract_repository.load_or_none("missing") is None


def test_list_for_client_filters(contract_repository, contract):
    other = Contract(client_id="client-2", title="Other", start_date=date(2026, 1, 1))
    contract_repository.save(contract)
    contract_repository.save(other)
    assert contract_repository.list_for_client("client-1") == [contract]
