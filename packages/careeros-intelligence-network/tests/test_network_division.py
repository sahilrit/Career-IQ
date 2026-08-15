"""Tests for the IntelligenceNetworkDivision facade."""

from __future__ import annotations

import pytest

from careeros_intelligence_network import (
    ConsentRequiredError,
    IntelligenceNetworkDivision,
    SignalCategory,
)
from careeros_trust_layer import ConsentRepository, ConsentType, grant_consent


def test_contribute_without_consent_raises(store):
    division = IntelligenceNetworkDivision(store)
    with pytest.raises(ConsentRequiredError):
        division.contribute(user_id="user-1", category=SignalCategory.SKILL_DEMAND, label="python")


def test_contribute_then_insight_reflects_it(store):
    grant_consent(ConsentRepository(store), "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING)
    division = IntelligenceNetworkDivision(store)

    division.contribute(user_id="user-1", category=SignalCategory.SKILL_DEMAND, label="python")
    insight = division.insights_for_category(SignalCategory.SKILL_DEMAND)

    assert insight.total_contributions == 1
    assert insight.rankings[0].label == "python"


def test_insight_from_multiple_consented_users_never_carries_their_identity(store):
    consent = ConsentRepository(store)
    grant_consent(consent, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING)
    grant_consent(consent, "user-2", ConsentType.NETWORK_INTELLIGENCE_SHARING)
    division = IntelligenceNetworkDivision(store)

    division.contribute(user_id="user-1", category=SignalCategory.SKILL_DEMAND, label="python")
    division.contribute(user_id="user-2", category=SignalCategory.SKILL_DEMAND, label="python")

    insight = division.insights_for_category(SignalCategory.SKILL_DEMAND)
    assert insight.total_contributions == 2
    assert "user-1" not in insight.model_dump_json()
    assert "user-2" not in insight.model_dump_json()
