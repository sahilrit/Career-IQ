"""Tests for AuthorizationEngine: the hard risk/mode decision matrix."""

from __future__ import annotations

import pytest

from careeros_autonomy import ActionRequest, AuthorizationEngine, AutonomyMode


@pytest.fixture
def engine():
    return AuthorizationEngine()


@pytest.mark.parametrize("mode", list(AutonomyMode))
def test_high_risk_action_always_requires_a_human_in_every_mode(engine, mode):
    request = ActionRequest(action_type="accept_offer", subject_id="app-1")
    decision = engine.authorize(request, mode)
    assert decision.approved is False
    assert decision.requires_human is True


def test_manual_mode_requires_human_even_for_low_risk(engine):
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
    )
    decision = engine.authorize(request, AutonomyMode.MANUAL)
    assert decision.approved is False
    assert decision.requires_human is True


def test_supervised_mode_auto_approves_low_risk(engine):
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
    )
    decision = engine.authorize(request, AutonomyMode.SUPERVISED)
    assert decision.approved is True
    assert decision.requires_human is False


def test_supervised_mode_requires_human_for_medium_risk(engine):
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.3}
    )
    decision = engine.authorize(request, AutonomyMode.SUPERVISED)
    assert decision.approved is False
    assert decision.requires_human is True


def test_full_autonomous_mode_auto_approves_low_and_medium_risk(engine):
    low = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
    )
    medium = ActionRequest(
        action_type="submit_application", subject_id="app-2", payload={"match_score": 0.3}
    )
    assert engine.authorize(low, AutonomyMode.FULL_AUTONOMOUS).approved is True
    assert engine.authorize(medium, AutonomyMode.FULL_AUTONOMOUS).approved is True


def test_full_autonomous_mode_still_blocks_high_risk(engine):
    request = ActionRequest(action_type="change_identity_credentials", subject_id="app-1")
    decision = engine.authorize(request, AutonomyMode.FULL_AUTONOMOUS)
    assert decision.approved is False
    assert decision.requires_human is True


def test_custom_risk_classifier_is_honored():
    from careeros_autonomy import RiskLevel

    always_low = AuthorizationEngine(risk_classifier=lambda request: RiskLevel.LOW)
    request = ActionRequest(action_type="anything", subject_id="app-1")
    decision = always_low.authorize(request, AutonomyMode.SUPERVISED)
    assert decision.approved is True
