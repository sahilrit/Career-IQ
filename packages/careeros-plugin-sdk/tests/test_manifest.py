"""Tests for PluginManifest validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from careeros_plugin_sdk import PluginManifest


def test_valid_manifest():
    manifest = PluginManifest(id="careeros-remoteok", name="RemoteOK", version="1.0.0")
    assert manifest.id == "careeros-remoteok"


@pytest.mark.parametrize("bad_id", ["RemoteOK", "-remoteok", "remote ok", ""])
def test_rejects_invalid_ids(bad_id):
    with pytest.raises(ValidationError):
        PluginManifest(id=bad_id, name="x", version="1.0.0")


@pytest.mark.parametrize("bad_version", ["1.0", "1.0.0-beta", "v1.0.0", "1.0.0.0"])
def test_rejects_invalid_versions(bad_version):
    with pytest.raises(ValidationError):
        PluginManifest(id="plugin", name="x", version=bad_version)


def test_capabilities_and_dependencies_default_empty():
    manifest = PluginManifest(id="plugin", name="x", version="1.0.0")
    assert manifest.capabilities == []
    assert manifest.dependencies == {}
