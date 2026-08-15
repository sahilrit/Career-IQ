"""Tests for Deliverable / DeliverableRepository."""

from __future__ import annotations

from careeros_client_success import Deliverable


def test_save_and_load_round_trips(deliverable_repository, contract):
    deliverable = Deliverable(contract_id=contract.id, title="Homepage mockup")
    deliverable_repository.save(deliverable)
    assert deliverable_repository.load(deliverable.id) == deliverable


def test_list_for_contract_filters(deliverable_repository, contract):
    matching = Deliverable(contract_id=contract.id, title="Homepage mockup")
    other = Deliverable(contract_id="other-contract", title="Unrelated")
    deliverable_repository.save(matching)
    deliverable_repository.save(other)
    assert deliverable_repository.list_for_contract(contract.id) == [matching]
