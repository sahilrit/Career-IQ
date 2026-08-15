"""Tests for role-based access control."""

from __future__ import annotations

import pytest

from careeros_tenancy import (
    Permission,
    PermissionDeniedError,
    Role,
    has_permission,
    require_permission,
)


def test_owner_has_every_permission():
    for permission in Permission:
        assert has_permission(Role.OWNER, permission)


def test_viewer_can_only_read_career_brain():
    assert has_permission(Role.VIEWER, Permission.CAREER_BRAIN_READ)
    assert not has_permission(Role.VIEWER, Permission.CAREER_BRAIN_WRITE)
    assert not has_permission(Role.VIEWER, Permission.BILLING_MANAGE)


def test_member_can_submit_applications_but_not_manage_billing():
    assert has_permission(Role.MEMBER, Permission.APPLICATIONS_SUBMIT)
    assert not has_permission(Role.MEMBER, Permission.BILLING_MANAGE)


def test_only_owner_can_manage_billing():
    assert has_permission(Role.OWNER, Permission.BILLING_MANAGE)
    for role in (Role.ADMIN, Role.MEMBER, Role.VIEWER):
        assert not has_permission(role, Permission.BILLING_MANAGE)


def test_require_permission_passes_silently_when_allowed():
    require_permission(Role.ADMIN, Permission.MEMBERS_MANAGE)  # must not raise


def test_require_permission_raises_when_denied():
    with pytest.raises(PermissionDeniedError):
        require_permission(Role.VIEWER, Permission.CAREER_BRAIN_WRITE)
