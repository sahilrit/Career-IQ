"""Tests for default_risk_classifier."""

from __future__ import annotations

import pytest

from careeros_autonomy import (
    HARD_HIGH_RISK_ACTION_TYPES,
    ActionRequest,
    RiskLevel,
    default_risk_classifier,
)


@pytest.mark.parametrize("action_type", sorted(HARD_HIGH_RISK_ACTION_TYPES))
def test_hard_high_risk_actions_are_always_high(action_type):
    request = ActionRequest(action_type=action_type, subject_id="app-1")
    assert default_risk_classifier(request) == RiskLevel.HIGH


def test_submit_application_with_high_score_is_low_risk():
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.9}
    )
    assert default_risk_classifier(request) == RiskLevel.LOW


def test_submit_application_with_low_score_is_medium_risk():
    request = ActionRequest(
        action_type="submit_application", subject_id="app-1", payload={"match_score": 0.3}
    )
    assert default_risk_classifier(request) == RiskLevel.MEDIUM


def test_submit_application_without_a_score_is_medium_risk():
    request = ActionRequest(action_type="submit_application", subject_id="app-1")
    assert default_risk_classifier(request) == RiskLevel.MEDIUM


def test_unknown_action_type_defaults_to_medium():
    request = ActionRequest(action_type="something_new", subject_id="app-1")
    assert default_risk_classifier(request) == RiskLevel.MEDIUM
