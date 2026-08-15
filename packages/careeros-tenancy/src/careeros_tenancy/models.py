"""Identity & tenancy models: User, Organization, Workspace, Membership,
Role, Permission.

Workspace is the isolation boundary ("tenant" in the technical sense):
every per-customer resource (Career Brain, Memory, Applications,
Credentials, Plugins, Settings, Analytics) is scoped to a workspace_id,
enforced by ``TenantScopedDocumentStore``. Organization exists above
Workspace so a Business-tier customer can have multiple workspaces
(e.g. one per client) under one billing account (Phase 52).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(StrEnum):
    CAREER_BRAIN_READ = "career_brain:read"
    CAREER_BRAIN_WRITE = "career_brain:write"
    APPLICATIONS_SUBMIT = "applications:submit"
    SETTINGS_MANAGE = "settings:manage"
    MEMBERS_MANAGE = "members:manage"
    BILLING_MANAGE = "billing:manage"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),
    Role.ADMIN: frozenset(
        {
            Permission.CAREER_BRAIN_READ,
            Permission.CAREER_BRAIN_WRITE,
            Permission.APPLICATIONS_SUBMIT,
            Permission.SETTINGS_MANAGE,
            Permission.MEMBERS_MANAGE,
        }
    ),
    Role.MEMBER: frozenset(
        {
            Permission.CAREER_BRAIN_READ,
            Permission.CAREER_BRAIN_WRITE,
            Permission.APPLICATIONS_SUBMIT,
        }
    ),
    Role.VIEWER: frozenset({Permission.CAREER_BRAIN_READ}),
}


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Workspace(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Membership(BaseModel):
    user_id: str
    workspace_id: str
    role: Role = Role.MEMBER
