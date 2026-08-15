"""Tests for CredentialVault: encrypted storage + permission checks + audit."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_credentials import (
    AccessDeniedError,
    CredentialAuditLog,
    CredentialVault,
    SecretCipher,
    SecretNotFoundError,
)


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


def _vault(store, *, permissions: frozenset[str] = frozenset({"credential:gmail"})):
    cipher = SecretCipher(SecretCipher.generate_key())
    audit_log = CredentialAuditLog(store)
    return CredentialVault(
        store, cipher, audit_log, lookup_permissions=lambda plugin_id: permissions
    ), audit_log


def test_store_then_get_roundtrips_when_authorized(store):
    vault, _audit = _vault(store)
    vault.store_secret("user-1", "gmail", "refresh-token-value", requester_id="gmail-plugin")
    assert vault.get_secret("user-1", "gmail", requester_id="gmail-plugin") == "refresh-token-value"


def test_secret_is_encrypted_at_rest(store):
    vault, _audit = _vault(store)
    vault.store_secret("user-1", "gmail", "refresh-token-value", requester_id="gmail-plugin")
    raw = store.get("encrypted_secret", "user-1:gmail")
    assert "refresh-token-value" not in raw["ciphertext"]


def test_get_without_declared_permission_raises_and_is_audited(store):
    vault, audit = _vault(store, permissions=frozenset())
    with pytest.raises(AccessDeniedError):
        vault.get_secret("user-1", "gmail", requester_id="untrusted-plugin")

    records = audit.for_identity("user-1")
    assert len(records) == 1
    assert records[0].success is False
    assert records[0].action == "retrieve"


def test_get_missing_secret_raises_and_is_audited(store):
    vault, audit = _vault(store)
    with pytest.raises(SecretNotFoundError):
        vault.get_secret("user-1", "gmail", requester_id="gmail-plugin")

    records = audit.for_identity("user-1")
    assert records[-1].success is False
    assert records[-1].detail == "not found"


def test_rotate_replaces_the_stored_value(store):
    vault, _audit = _vault(store)
    vault.store_secret("user-1", "gmail", "old-token", requester_id="gmail-plugin")
    vault.rotate_secret("user-1", "gmail", "new-token", requester_id="gmail-plugin")
    assert vault.get_secret("user-1", "gmail", requester_id="gmail-plugin") == "new-token"


def test_delete_removes_the_secret(store):
    vault, _audit = _vault(store)
    vault.store_secret("user-1", "gmail", "token", requester_id="gmail-plugin")
    vault.delete_secret("user-1", "gmail", requester_id="gmail-plugin")
    assert vault.has_secret("user-1", "gmail") is False


def test_has_secret_reflects_presence(store):
    vault, _audit = _vault(store)
    assert vault.has_secret("user-1", "gmail") is False
    vault.store_secret("user-1", "gmail", "token", requester_id="gmail-plugin")
    assert vault.has_secret("user-1", "gmail") is True


def test_every_successful_action_is_audited(store):
    vault, audit = _vault(store)
    vault.store_secret("user-1", "gmail", "token", requester_id="gmail-plugin")
    vault.get_secret("user-1", "gmail", requester_id="gmail-plugin")
    vault.rotate_secret("user-1", "gmail", "token-2", requester_id="gmail-plugin")
    vault.delete_secret("user-1", "gmail", requester_id="gmail-plugin")

    actions = [record.action for record in audit.for_identity("user-1")]
    assert actions == ["store", "retrieve", "rotate", "delete"]
    assert all(record.success for record in audit.for_identity("user-1"))


def test_secrets_for_different_identities_are_independent(store):
    vault, _audit = _vault(store)
    vault.store_secret("user-1", "gmail", "user-1-token", requester_id="gmail-plugin")
    vault.store_secret("user-2", "gmail", "user-2-token", requester_id="gmail-plugin")

    assert vault.get_secret("user-1", "gmail", requester_id="gmail-plugin") == "user-1-token"
    assert vault.get_secret("user-2", "gmail", requester_id="gmail-plugin") == "user-2-token"
