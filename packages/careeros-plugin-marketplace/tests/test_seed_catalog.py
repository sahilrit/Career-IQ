"""Tests for the seed catalog's honesty guarantees."""

from __future__ import annotations

from careeros_plugin_marketplace import SEED_CATALOG


def test_remoteok_and_fiverr_are_installable():
    installable_ids = {listing.manifest.id for listing in SEED_CATALOG if listing.is_installable}
    assert installable_ids == {"careeros-remoteok", "careeros-fiverr"}


def test_every_other_listing_is_catalog_only():
    for listing in SEED_CATALOG:
        if listing.manifest.id not in {"careeros-remoteok", "careeros-fiverr"}:
            assert listing.is_installable is False


def test_catalog_only_listings_say_not_yet_implemented():
    for listing in SEED_CATALOG:
        if not listing.is_installable:
            assert "not yet implemented" in listing.manifest.description.lower()


def test_every_listing_has_a_unique_id():
    ids = [listing.manifest.id for listing in SEED_CATALOG]
    assert len(ids) == len(set(ids))
