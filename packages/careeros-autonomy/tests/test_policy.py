"""Tests for AutonomyPolicy: the full evaluate() orchestration."""

from __future__ import annotations

import pytest

from careeros_autonomy import (
    ActionRequest,
    AuthorizationEngine,
    AutonomyMode,
    AutonomyPolicy,
    DecisionMemory,
    PacingLimiter,
)
from careeros_common import DocumentStore
from careeros_event_bus import EventBus


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock():
    return _FakeClock()


@pytest.fixture
def policy(clock):
    with DocumentStore() as store:
        yield AutonomyPolicy(
            mode=AutonomyMode.FULL_AUTONOMOUS,
            engine=AuthorizationEngine(),
            pacing=PacingLimiter(10.0, clock=clock),
            decision_memory=DecisionMemory(store),
            event_bus=EventBus(),
        )


def test_qualified_application_is_approved_and_recorded(policy):
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
    )
    decision = policy.evaluate(request)

    assert decision.approved is True
    assert policy.decision_memory.approval_rate() == 1.0


def test_a_second_action_too_soon_is_rate_limited(policy, clock):
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
    )
    first = policy.evaluate(request)
    second = policy.evaluate(request)

    assert first.approved is True
    assert second.approved is False
    assert "Rate-limited" in second.reason


def test_pacing_allows_a_new_action_after_the_interval(policy, clock):
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
    )
    policy.evaluate(request)
    clock.advance(10.0)
    second = policy.evaluate(request)

    assert second.approved is True


def test_high_risk_action_is_never_approved_even_in_full_autonomous(policy):
    request = ActionRequest(action_type="accept_offer", subject_id="app-1")
    decision = policy.evaluate(request)
    assert decision.approved is False
    assert decision.requires_human is True


def test_evaluate_publishes_an_authorization_decided_event():
    with DocumentStore() as store:
        bus = EventBus()
        policy = AutonomyPolicy(
            mode=AutonomyMode.FULL_AUTONOMOUS,
            engine=AuthorizationEngine(),
            pacing=PacingLimiter(0.0, clock=_FakeClock()),
            decision_memory=DecisionMemory(store),
            event_bus=bus,
        )
        request = ActionRequest(
            action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
        )

        policy.evaluate(request)

        events = [e for e in bus.history() if e.event_type == "authorization.decided"]
        assert len(events) == 1
        assert events[0].payload["approved"] is True


def test_manual_mode_never_auto_approves_anything():
    with DocumentStore() as store:
        policy = AutonomyPolicy(
            mode=AutonomyMode.MANUAL,
            engine=AuthorizationEngine(),
            pacing=PacingLimiter(0.0, clock=_FakeClock()),
            decision_memory=DecisionMemory(store),
            event_bus=EventBus(),
        )
        request = ActionRequest(
            action_type="submit_application", subject_id="app-1", payload={"match_score": 0.99}
        )
        decision = policy.evaluate(request)
        assert decision.approved is False
