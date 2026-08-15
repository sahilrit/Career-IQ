"""Tests for TenantScopedDocumentStore in isolation."""

from __future__ import annotations

import pytest

from careeros_common import DocumentNotFoundError, DocumentStore
from careeros_tenancy import TenantScopedDocumentStore


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


def test_put_then_get_roundtrips(store):
    scoped = TenantScopedDocumentStore(store, "tenant-a")
    scoped.put("widget", "1", {"name": "gadget"})
    assert scoped.get("widget", "1") == {"name": "gadget"}


def test_tenant_id_property(store):
    scoped = TenantScopedDocumentStore(store, "tenant-a")
    assert scoped.tenant_id == "tenant-a"


def test_two_tenants_on_the_same_underlying_store_cannot_see_each_others_data(store):
    tenant_a = TenantScopedDocumentStore(store, "tenant-a")
    tenant_b = TenantScopedDocumentStore(store, "tenant-b")

    tenant_a.put("widget", "1", {"owner": "a"})
    tenant_b.put("widget", "1", {"owner": "b"})

    assert tenant_a.get("widget", "1") == {"owner": "a"}
    assert tenant_b.get("widget", "1") == {"owner": "b"}


def test_tenant_b_cannot_read_a_document_only_tenant_a_ever_wrote(store):
    tenant_a = TenantScopedDocumentStore(store, "tenant-a")
    tenant_b = TenantScopedDocumentStore(store, "tenant-b")

    tenant_a.put("widget", "secret", {"data": "tenant a's private data"})

    assert tenant_b.get_or_none("widget", "secret") is None
    with pytest.raises(DocumentNotFoundError):
        tenant_b.get("widget", "secret")


def test_list_only_returns_the_calling_tenants_documents(store):
    tenant_a = TenantScopedDocumentStore(store, "tenant-a")
    tenant_b = TenantScopedDocumentStore(store, "tenant-b")

    tenant_a.put("widget", "1", {"owner": "a"})
    tenant_a.put("widget", "2", {"owner": "a"})
    tenant_b.put("widget", "1", {"owner": "b"})

    assert len(tenant_a.list("widget")) == 2
    assert len(tenant_b.list("widget")) == 1


def test_delete_only_affects_the_calling_tenants_document(store):
    tenant_a = TenantScopedDocumentStore(store, "tenant-a")
    tenant_b = TenantScopedDocumentStore(store, "tenant-b")

    tenant_a.put("widget", "1", {"owner": "a"})
    tenant_b.put("widget", "1", {"owner": "b"})

    tenant_a.delete("widget", "1")

    assert tenant_a.get_or_none("widget", "1") is None
    assert tenant_b.get("widget", "1") == {"owner": "b"}
