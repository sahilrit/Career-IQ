"""Tests for AccountDeletionCoordinator."""

from __future__ import annotations

from careeros_compliance import AccountDeletionCoordinator
from careeros_tenancy import Membership, Organization, TenancyRepository, User, Workspace
from careeros_trust_layer import DataPortabilityRegistry


class _FakeDeletor:
    def __init__(self) -> None:
        self.deleted_ids: list[str] = []

    def delete(self, identity_id: str) -> bool:
        self.deleted_ids.append(identity_id)
        return True


def _seed_tenant(store) -> tuple[TenancyRepository, User, Workspace]:
    tenancy = TenancyRepository(store)
    user = User(email="jane@example.com", full_name="Jane Doe")
    organization = Organization(name="Acme")
    workspace = Workspace(organization_id=organization.id, name="Acme Primary")
    tenancy.save_user(user)
    tenancy.save_organization(organization)
    tenancy.save_workspace(workspace)
    tenancy.add_membership(Membership(user_id=user.id, workspace_id=workspace.id))
    return tenancy, user, workspace


def test_delete_account_removes_domain_data_and_tenancy_records(store):
    tenancy, user, workspace = _seed_tenant(store)
    portability = DataPortabilityRegistry()
    deletor = _FakeDeletor()
    portability.register_deletor("career_brain", deletor)

    coordinator = AccountDeletionCoordinator(portability=portability, tenancy=tenancy)
    receipt = coordinator.delete_account(user.id)

    assert receipt.user_removed is True
    assert receipt.memberships_removed == 1
    assert receipt.workspace_ids == [workspace.id]
    assert receipt.deleted_sources == {"career_brain": True}
    assert deletor.deleted_ids == [user.id]
    assert tenancy.load_user(user.id) is None
    assert tenancy.membership_for(user.id, workspace.id) is None


def test_delete_account_for_unknown_user_removes_nothing(store):
    tenancy = TenancyRepository(store)
    portability = DataPortabilityRegistry()
    coordinator = AccountDeletionCoordinator(portability=portability, tenancy=tenancy)

    receipt = coordinator.delete_account("ghost-user")

    assert receipt.user_removed is False
    assert receipt.memberships_removed == 0
    assert receipt.workspace_ids == []
