"""The critical security proof for this phase: an already-shipped,
completely unmodified repository (CareerBrainRepository, Phase 2)
becomes tenant-isolated just by handing it a TenantScopedDocumentStore
instead of a raw DocumentStore. This is the whole point of the wrapper
design — no changes to any earlier package were needed.
"""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_common import DocumentStore
from careeros_tenancy import TenantScopedDocumentStore


@pytest.fixture
def underlying_store():
    with DocumentStore() as store:
        yield store


def test_customer_a_cannot_see_customer_bs_career_brain(underlying_store):
    tenant_a_repo = CareerBrainRepository(TenantScopedDocumentStore(underlying_store, "tenant-a"))
    tenant_b_repo = CareerBrainRepository(TenantScopedDocumentStore(underlying_store, "tenant-b"))

    brain_a = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    brain_b = CareerBrain(identity=Identity(full_name="Grace Hopper", email="grace@example.com"))
    tenant_a_repo.save(brain_a)
    tenant_b_repo.save(brain_b)

    # Each tenant only ever sees their own data through list_all().
    assert [b.identity.full_name for b in tenant_a_repo.list_all()] == ["Ada Lovelace"]
    assert [b.identity.full_name for b in tenant_b_repo.list_all()] == ["Grace Hopper"]

    # And customer B cannot load customer A's brain even by guessing the id.
    assert tenant_b_repo.load_or_none(brain_a.identity.id) is None
    assert tenant_a_repo.load_or_none(brain_b.identity.id) is None


def test_isolation_holds_even_with_colliding_identity_ids(underlying_store):
    """The pathological case: two tenants' users happen to share an id
    (e.g. a UUID collision, or a non-UUID identity scheme). Isolation
    must not depend on ids being globally unique.
    """
    tenant_a_repo = CareerBrainRepository(TenantScopedDocumentStore(underlying_store, "tenant-a"))
    tenant_b_repo = CareerBrainRepository(TenantScopedDocumentStore(underlying_store, "tenant-b"))

    shared_id = "user-123"
    brain_a = CareerBrain(
        identity=Identity(id=shared_id, full_name="Tenant A's User", email="a@example.com")
    )
    brain_b = CareerBrain(
        identity=Identity(id=shared_id, full_name="Tenant B's User", email="b@example.com")
    )
    tenant_a_repo.save(brain_a)
    tenant_b_repo.save(brain_b)

    assert tenant_a_repo.load(shared_id).identity.full_name == "Tenant A's User"
    assert tenant_b_repo.load(shared_id).identity.full_name == "Tenant B's User"


def test_deleting_in_one_tenant_does_not_affect_the_other(underlying_store):
    tenant_a_repo = CareerBrainRepository(TenantScopedDocumentStore(underlying_store, "tenant-a"))
    tenant_b_repo = CareerBrainRepository(TenantScopedDocumentStore(underlying_store, "tenant-b"))

    shared_id = "user-123"
    tenant_a_repo.save(
        CareerBrain(identity=Identity(id=shared_id, full_name="A", email="a@example.com"))
    )
    tenant_b_repo.save(
        CareerBrain(identity=Identity(id=shared_id, full_name="B", email="b@example.com"))
    )

    tenant_a_repo.delete(shared_id)

    assert tenant_a_repo.load_or_none(shared_id) is None
    assert tenant_b_repo.load(shared_id).identity.full_name == "B"
