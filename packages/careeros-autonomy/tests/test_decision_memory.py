"""Tests for DecisionMemory."""

from __future__ import annotations

import pytest

from careeros_autonomy import (
    ActionRequest,
    AuthorizationDecision,
    AutonomyMode,
    DecisionMemory,
    RiskLevel,
)
from careeros_common import DocumentStore


@pytest.fixture
def memory():
    with DocumentStore() as store:
        yield DecisionMemory(store)


def _decision(approved: bool) -> AuthorizationDecision:
    return AuthorizationDecision(
        approved=approved, requires_human=not approved, risk_level=RiskLevel.LOW, reason="x"
    )


def test_record_then_all_returns_it(memory):
    request = ActionRequest(action_type="submit_application", subject_id="app-1")
    memory.record(request, _decision(True), AutonomyMode.FULL_AUTONOMOUS)

    records = memory.all()
    assert len(records) == 1
    assert records[0].action_type == "submit_application"
    assert records[0].approved is True


def test_for_action_type_filters(memory):
    memory.record(
        ActionRequest(action_type="submit_application", subject_id="a"),
        _decision(True),
        AutonomyMode.FULL_AUTONOMOUS,
    )
    memory.record(
        ActionRequest(action_type="accept_offer", subject_id="b"),
        _decision(False),
        AutonomyMode.FULL_AUTONOMOUS,
    )

    assert len(memory.for_action_type("submit_application")) == 1
    assert len(memory.for_action_type("accept_offer")) == 1


def test_approval_rate_with_no_records_is_zero(memory):
    assert memory.approval_rate() == 0.0


def test_approval_rate_computes_correctly(memory):
    for approved in [True, True, False, False]:
        memory.record(
            ActionRequest(action_type="submit_application", subject_id="x"),
            _decision(approved),
            AutonomyMode.FULL_AUTONOMOUS,
        )
    assert memory.approval_rate() == 0.5
    assert memory.approval_rate("submit_application") == 0.5
    assert memory.approval_rate("accept_offer") == 0.0
