"""Tests for TenancyRepository: User/Organization/Workspace/Membership."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_tenancy import Membership, Organization, Role, TenancyRepository, User, Workspace


@pytest.fixture
def repository():
    with DocumentStore() as store:
        yield TenancyRepository(store)


def test_save_then_load_user(repository):
    user = User(email="ada@example.com", full_name="Ada Lovelace")
    repository.save_user(user)
    assert repository.load_user(user.id).email == "ada@example.com"


def test_find_user_by_email(repository):
    repository.save_user(User(email="ada@example.com", full_name="Ada Lovelace"))
    found = repository.find_user_by_email("ada@example.com")
    assert found is not None
    assert repository.find_user_by_email("nobody@example.com") is None


def test_save_then_load_organization(repository):
    org = Organization(name="Acme Inc")
    repository.save_organization(org)
    assert repository.load_organization(org.id).name == "Acme Inc"


def test_workspaces_for_organization(repository):
    org = Organization(name="Acme Inc")
    repository.save_organization(org)
    ws_a = Workspace(organization_id=org.id, name="Main")
    ws_b = Workspace(organization_id=org.id, name="Client Project")
    other_org_ws = Workspace(organization_id="other-org", name="Unrelated")
    repository.save_workspace(ws_a)
    repository.save_workspace(ws_b)
    repository.save_workspace(other_org_ws)

    names = {w.name for w in repository.workspaces_for_organization(org.id)}
    assert names == {"Main", "Client Project"}


def test_membership_roundtrip_and_role(repository):
    user = User(email="ada@example.com", full_name="Ada Lovelace")
    workspace = Workspace(organization_id="org-1", name="Main")
    membership = Membership(user_id=user.id, workspace_id=workspace.id, role=Role.ADMIN)
    repository.add_membership(membership)

    membership = repository.membership_for(user.id, workspace.id)
    assert membership is not None
    assert membership.role == Role.ADMIN


def test_workspaces_for_user_lists_every_membership(repository):
    user = User(email="ada@example.com", full_name="Ada Lovelace")
    repository.add_membership(Membership(user_id=user.id, workspace_id="ws-1"))
    repository.add_membership(Membership(user_id=user.id, workspace_id="ws-2"))
    repository.add_membership(Membership(user_id="other-user", workspace_id="ws-3"))

    workspace_ids = {m.workspace_id for m in repository.workspaces_for_user(user.id)}
    assert workspace_ids == {"ws-1", "ws-2"}
