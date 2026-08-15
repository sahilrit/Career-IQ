"""Tests for the permission check enforcing "agent != credential owner"."""

from __future__ import annotations

import pytest

from careeros_credentials import AccessDeniedError, check_access, credential_permission


def test_credential_permission_format():
    assert credential_permission("gmail") == "credential:gmail"


def test_check_access_passes_when_permission_declared():
    check_access("gmail-plugin", "gmail", lambda plugin_id: frozenset({"credential:gmail"}))


def test_check_access_raises_when_permission_not_declared():
    with pytest.raises(AccessDeniedError):
        check_access("gmail-plugin", "gmail", lambda plugin_id: frozenset())


def test_check_access_raises_when_only_a_different_permission_declared():
    with pytest.raises(AccessDeniedError):
        check_access("gmail-plugin", "gmail", lambda plugin_id: frozenset({"credential:calendar"}))
