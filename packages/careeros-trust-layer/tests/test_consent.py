"""Tests for consent grant/revoke/has_active_consent."""

from __future__ import annotations

from careeros_trust_layer import (
    ConsentRepository,
    ConsentType,
    grant_consent,
    has_active_consent,
    revoke_consent,
)


def test_no_consent_record_is_not_active(store):
    repository = ConsentRepository(store)
    assert has_active_consent(repository, "user-1", ConsentType.DATA_PROCESSING) is False


def test_granting_consent_makes_it_active(store):
    repository = ConsentRepository(store)
    grant_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    assert has_active_consent(repository, "user-1", ConsentType.DATA_PROCESSING) is True


def test_revoking_consent_makes_it_inactive(store):
    repository = ConsentRepository(store)
    grant_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    revoke_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    assert has_active_consent(repository, "user-1", ConsentType.DATA_PROCESSING) is False


def test_regranting_after_revocation_is_active_again(store):
    repository = ConsentRepository(store)
    grant_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    revoke_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    grant_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    assert has_active_consent(repository, "user-1", ConsentType.DATA_PROCESSING) is True


def test_consent_is_scoped_per_type(store):
    repository = ConsentRepository(store)
    grant_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    assert has_active_consent(repository, "user-1", ConsentType.MARKETING_COMMUNICATIONS) is False


def test_consent_is_scoped_per_user(store):
    repository = ConsentRepository(store)
    grant_consent(repository, "user-1", ConsentType.DATA_PROCESSING)
    assert has_active_consent(repository, "user-2", ConsentType.DATA_PROCESSING) is False


def test_network_intelligence_sharing_consent_behaves_like_any_other_type(store):
    repository = ConsentRepository(store)
    assert (
        has_active_consent(repository, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING) is False
    )
    grant_consent(repository, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING)
    assert (
        has_active_consent(repository, "user-1", ConsentType.NETWORK_INTELLIGENCE_SHARING) is True
    )
