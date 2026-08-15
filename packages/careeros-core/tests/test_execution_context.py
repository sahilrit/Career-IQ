"""Tests for ExecutionContext."""

from __future__ import annotations

from careeros_core import ExecutionContext


def test_generates_a_correlation_id_by_default():
    a = ExecutionContext(identity_id="user-1")
    b = ExecutionContext(identity_id="user-1")
    assert a.correlation_id != b.correlation_id


def test_is_immutable():
    import dataclasses

    import pytest

    context = ExecutionContext(identity_id="user-1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.identity_id = "user-2"


def test_child_keeps_identity_and_tenant_but_gets_a_fresh_correlation_id():
    parent = ExecutionContext(identity_id="user-1", tenant_id="tenant-1")
    child = parent.child()

    assert child.identity_id == parent.identity_id
    assert child.tenant_id == parent.tenant_id
    assert child.correlation_id != parent.correlation_id


def test_tenant_id_defaults_to_none():
    context = ExecutionContext(identity_id="user-1")
    assert context.tenant_id is None
