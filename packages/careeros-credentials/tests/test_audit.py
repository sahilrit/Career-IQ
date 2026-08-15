"""Tests for CredentialAuditLog."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_credentials import AccessRecord, CredentialAuditLog


@pytest.fixture
def audit_log():
    with DocumentStore() as store:
        yield CredentialAuditLog(store)


def test_record_then_for_identity_returns_it(audit_log):
    audit_log.record(
        AccessRecord(
            identity_id="user-1",
            service="gmail",
            action="store",
            requester_id="gmail-plugin",
            success=True,
        )
    )
    records = audit_log.for_identity("user-1")
    assert len(records) == 1
    assert records[0].service == "gmail"


def test_for_identity_excludes_other_identities(audit_log):
    audit_log.record(
        AccessRecord(
            identity_id="user-1", service="gmail", action="store", requester_id="p", success=True
        )
    )
    audit_log.record(
        AccessRecord(
            identity_id="user-2", service="gmail", action="store", requester_id="p", success=True
        )
    )
    assert len(audit_log.for_identity("user-1")) == 1


def test_for_service_filters_within_an_identity(audit_log):
    audit_log.record(
        AccessRecord(
            identity_id="user-1", service="gmail", action="store", requester_id="p", success=True
        )
    )
    audit_log.record(
        AccessRecord(
            identity_id="user-1",
            service="calendar",
            action="store",
            requester_id="p",
            success=True,
        )
    )
    assert len(audit_log.for_service("user-1", "gmail")) == 1


def test_captures_failed_attempts_too(audit_log):
    audit_log.record(
        AccessRecord(
            identity_id="user-1",
            service="gmail",
            action="retrieve",
            requester_id="untrusted-plugin",
            success=False,
            detail="access denied",
        )
    )
    record = audit_log.for_identity("user-1")[0]
    assert record.success is False
    assert record.detail == "access denied"
