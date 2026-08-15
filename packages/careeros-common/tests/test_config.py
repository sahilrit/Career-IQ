"""Tests for the layered configuration system."""

from __future__ import annotations

import pytest

from careeros_common.config import (
    Settings,
    get_settings,
    load_layered_yaml,
    reset_settings_cache,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_default_environment_is_development():
    assert Settings().environment == "development"


def test_get_settings_returns_a_cached_singleton():
    assert get_settings() is get_settings()


def test_reset_settings_cache_forces_a_rebuild():
    first = get_settings()
    reset_settings_cache()
    assert get_settings() is not first


def test_env_var_overrides_yaml_layers(monkeypatch):
    monkeypatch.setenv("CAREEROS_LOG_LEVEL", "CRITICAL")
    reset_settings_cache()
    assert get_settings().log_level == "CRITICAL"


def test_load_layered_yaml_tags_the_requested_environment():
    merged = load_layered_yaml(environment="test")
    assert merged["environment"] == "test"


def test_development_yaml_layer_overrides_default_yaml_layer():
    # config/default.yaml sets debug: false; config/development.yaml sets
    # debug: true. If this is true, layering (not just field defaults) works.
    merged = load_layered_yaml(environment="development")
    assert merged["debug"] is True


def test_unknown_environment_falls_back_to_default_yaml_only():
    merged = load_layered_yaml(environment="does-not-exist")
    assert merged["environment"] == "does-not-exist"
    assert merged["log_level"] == "INFO"
