"""Tests for classify_client_lifecycle_stage."""

from __future__ import annotations

from datetime import date

from careeros_client_success import ClientLifecycleStage, Contract, ContractStatus
from careeros_client_success.lifecycle import classify_client_lifecycle_stage


def _contract(status: ContractStatus) -> Contract:
    return Contract(client_id="client-1", title="Work", start_date=date(2026, 1, 1), status=status)


def test_no_completed_contracts_and_no_referrals_is_none():
    contracts = [_contract(ContractStatus.ACTIVE)]
    assert classify_client_lifecycle_stage(contracts) is None


def test_one_completed_contract_is_one_time():
    contracts = [_contract(ContractStatus.COMPLETED)]
    assert classify_client_lifecycle_stage(contracts) == ClientLifecycleStage.ONE_TIME


def test_two_completed_contracts_is_repeat():
    contracts = [_contract(ContractStatus.COMPLETED), _contract(ContractStatus.COMPLETED)]
    assert classify_client_lifecycle_stage(contracts) == ClientLifecycleStage.REPEAT


def test_four_completed_contracts_is_long_term():
    contracts = [_contract(ContractStatus.COMPLETED) for _ in range(4)]
    assert classify_client_lifecycle_stage(contracts) == ClientLifecycleStage.LONG_TERM


def test_any_referral_is_referral_source_regardless_of_contract_count():
    contracts = [_contract(ContractStatus.COMPLETED)]
    assert (
        classify_client_lifecycle_stage(contracts, referral_count=1)
        == ClientLifecycleStage.REFERRAL_SOURCE
    )


def test_terminated_contracts_do_not_count_as_completed():
    contracts = [_contract(ContractStatus.TERMINATED), _contract(ContractStatus.TERMINATED)]
    assert classify_client_lifecycle_stage(contracts) is None
