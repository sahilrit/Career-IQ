"""Tests for consent-gated, identity-free signal contribution."""

from __future__ import annotations

import pytest

from careeros_intelligence_network import (
    ConsentRequiredError,
    SignalCategory,
    SignalContributionRepository,
    contribute_signal,
)
from careeros_trust_layer import ConsentRepository, ConsentType, grant_consent, revoke_consent


def test_contribute_without_consent_raises(store):
    signals = SignalContributionRepository(store)
    consent = ConsentRepository(store)
    with pytest.raises(ConsentRequiredError):
        contribute_signal(
            signals,
            consent,
            user_id="user-1",
            category=SignalCategory.SKILL_DEMAND,
            label="python",
        )


def test_contribute_with_consent_saves_an_anonymous_record(store):
    signals = SignalContributionRepository(store)
    consent = ConsentRepository(store)
    grant_consent(consent, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING)

    contribution = contribute_signal(
        signals,
        consent,
        user_id="user-1",
        category=SignalCategory.SKILL_DEMAND,
        label="python",
        weight=2.0,
    )

    assert contribution.category == SignalCategory.SKILL_DEMAND
    assert contribution.label == "python"
    assert contribution.weight == 2.0
    assert not hasattr(contribution, "user_id")
    assert "user_id" not in contribution.model_dump()
    assert "user-1" not in contribution.model_dump_json()


def test_contributions_are_retrievable_by_category(store):
    signals = SignalContributionRepository(store)
    consent = ConsentRepository(store)
    grant_consent(consent, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING)
    contribute_signal(
        signals, consent, user_id="user-1", category=SignalCategory.SKILL_DEMAND, label="python"
    )
    contribute_signal(
        signals,
        consent,
        user_id="user-1",
        category=SignalCategory.OUTREACH_PATTERN,
        label="cold_email",
    )

    skill_signals = signals.list_for_category(SignalCategory.SKILL_DEMAND)
    assert len(skill_signals) == 1
    assert skill_signals[0].label == "python"


def test_revoked_consent_blocks_further_contribution(store):
    signals = SignalContributionRepository(store)
    consent = ConsentRepository(store)
    grant_consent(consent, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING)
    revoke_consent(consent, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING)

    with pytest.raises(ConsentRequiredError):
        contribute_signal(
            signals, consent, user_id="user-1", category=SignalCategory.SKILL_DEMAND, label="rust"
        )
