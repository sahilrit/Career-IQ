"""Full account deletion: orchestrates Phase 45's DataPortabilityRegistry
(domain data, keyed by identity) together with Phase 25's tenancy
records (User, Membership) — neither package alone can erase a whole
account, so this is the composition, not new domain logic.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_tenancy import TenancyRepository
from careeros_trust_layer import DataPortabilityRegistry


class AccountDeletionReceipt(BaseModel):
    user_id: str
    workspace_ids: list[str]
    deleted_sources: dict[str, bool]
    memberships_removed: int
    user_removed: bool


class AccountDeletionCoordinator:
    def __init__(self, *, portability: DataPortabilityRegistry, tenancy: TenancyRepository) -> None:
        self._portability = portability
        self._tenancy = tenancy

    def delete_account(self, user_id: str) -> AccountDeletionReceipt:
        memberships = self._tenancy.workspaces_for_user(user_id)
        deleted_sources = self._portability.delete_user_data(user_id)
        memberships_removed = sum(
            1
            for membership in memberships
            if self._tenancy.remove_membership(user_id, membership.workspace_id)
        )
        user_removed = self._tenancy.delete_user(user_id)
        return AccountDeletionReceipt(
            user_id=user_id,
            workspace_ids=[membership.workspace_id for membership in memberships],
            deleted_sources=deleted_sources,
            memberships_removed=memberships_removed,
            user_removed=user_removed,
        )
