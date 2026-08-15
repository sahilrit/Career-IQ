"""Repositories for tenancy metadata (User, Organization, Workspace,
Membership).

These live in a shared, global ``DocumentStore`` — they ARE the mapping
that determines tenant scope, so they can't themselves be tenant-scoped
(that would be circular).
"""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_tenancy.models import Membership, Organization, User, Workspace

_USER_TYPE = "tenancy_user"
_ORG_TYPE = "tenancy_organization"
_WORKSPACE_TYPE = "tenancy_workspace"
_MEMBERSHIP_TYPE = "tenancy_membership"


class TenancyRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save_user(self, user: User) -> None:
        self._store.put(_USER_TYPE, user.id, user.model_dump(mode="json"))

    def load_user(self, user_id: str) -> User | None:
        data = self._store.get_or_none(_USER_TYPE, user_id)
        return User.model_validate(data) if data else None

    def find_user_by_email(self, email: str) -> User | None:
        for data in self._store.list(_USER_TYPE):
            if data.get("email") == email:
                return User.model_validate(data)
        return None

    def save_organization(self, organization: Organization) -> None:
        self._store.put(_ORG_TYPE, organization.id, organization.model_dump(mode="json"))

    def load_organization(self, organization_id: str) -> Organization | None:
        data = self._store.get_or_none(_ORG_TYPE, organization_id)
        return Organization.model_validate(data) if data else None

    def save_workspace(self, workspace: Workspace) -> None:
        self._store.put(_WORKSPACE_TYPE, workspace.id, workspace.model_dump(mode="json"))

    def load_workspace(self, workspace_id: str) -> Workspace | None:
        data = self._store.get_or_none(_WORKSPACE_TYPE, workspace_id)
        return Workspace.model_validate(data) if data else None

    def workspaces_for_organization(self, organization_id: str) -> list[Workspace]:
        return [
            Workspace.model_validate(data)
            for data in self._store.list(_WORKSPACE_TYPE)
            if data.get("organization_id") == organization_id
        ]

    def add_membership(self, membership: Membership) -> None:
        key = f"{membership.user_id}:{membership.workspace_id}"
        self._store.put(_MEMBERSHIP_TYPE, key, membership.model_dump(mode="json"))

    def membership_for(self, user_id: str, workspace_id: str) -> Membership | None:
        data = self._store.get_or_none(_MEMBERSHIP_TYPE, f"{user_id}:{workspace_id}")
        return Membership.model_validate(data) if data else None

    def workspaces_for_user(self, user_id: str) -> list[Membership]:
        return [
            Membership.model_validate(data)
            for data in self._store.list(_MEMBERSHIP_TYPE)
            if data.get("user_id") == user_id
        ]

    def remove_membership(self, user_id: str, workspace_id: str) -> bool:
        if self.membership_for(user_id, workspace_id) is None:
            return False
        self._store.delete(_MEMBERSHIP_TYPE, f"{user_id}:{workspace_id}")
        return True

    def delete_user(self, user_id: str) -> bool:
        if self.load_user(user_id) is None:
            return False
        self._store.delete(_USER_TYPE, user_id)
        return True
