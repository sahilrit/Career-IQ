"""Tests for the local, zero-cost TF-IDF semantic index."""

from __future__ import annotations

from careeros_memory import LocalTfidfIndex


def test_search_with_no_documents_returns_empty():
    index = LocalTfidfIndex()
    assert index.search("shopify audit") == []


def test_search_with_empty_query_returns_empty():
    index = LocalTfidfIndex()
    index.index("company-1", "Shopify store selling handmade candles")
    assert index.search("") == []


def test_relevant_document_ranks_above_irrelevant_one():
    index = LocalTfidfIndex()
    index.index("company-1", "Shopify store selling handmade candles, strong CRO focus")
    index.index("company-2", "Enterprise Java backend team, no e-commerce at all")

    results = index.search("shopify ecommerce store")

    assert results[0][0] == "company-1"


def test_search_returns_only_documents_with_positive_similarity():
    index = LocalTfidfIndex()
    index.index("company-1", "Shopify store")
    index.index("company-2", "Completely unrelated aerospace engineering firm")

    results = index.search("shopify")

    assert [record_id for record_id, _score in results] == ["company-1"]


def test_top_k_limits_result_count():
    index = LocalTfidfIndex()
    for i in range(10):
        index.index(f"company-{i}", "shopify ecommerce store")

    results = index.search("shopify", top_k=3)

    assert len(results) == 3


def test_remove_excludes_document_from_future_searches():
    index = LocalTfidfIndex()
    index.index("company-1", "shopify store")
    index.remove("company-1")

    assert index.search("shopify") == []


def test_reindexing_the_same_id_replaces_its_content():
    index = LocalTfidfIndex()
    index.index("company-1", "aerospace engineering")
    index.index("company-1", "shopify store")

    results = index.search("shopify")

    assert results[0][0] == "company-1"
