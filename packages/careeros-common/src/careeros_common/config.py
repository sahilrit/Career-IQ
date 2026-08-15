"""Layered configuration system for CareerOS.

Precedence, lowest to highest:

    config/default.yaml
    config/{environment}.yaml
    config/local.yaml            (gitignored, developer-local overrides)
    CAREEROS_*  environment variables ("__" separates nested keys)

No layer is required to exist except ``default.yaml``. This lets every
deployment mode (local dev, CI, self-hosted, SaaS) supply only what it
needs to override, and lets ``local.yaml`` hold developer-specific values
(including any optional paid-API keys) without touching version control.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from careeros_common.exceptions import ConfigurationError

DEFAULT_ENVIRONMENT = "development"
CONFIG_DIR_ENV_VAR = "CAREEROS_CONFIG_DIR"


def _find_config_dir() -> Path:
    """Locate the repo's ``config/`` directory, or honor an explicit override."""
    if override := os.environ.get(CONFIG_DIR_ENV_VAR):
        return Path(override)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "config"
        if candidate.is_dir():
            return candidate
    raise ConfigurationError(
        f"Could not locate a 'config/' directory above {__file__}. "
        f"Set {CONFIG_DIR_ENV_VAR} to override."
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigurationError(f"{path} must contain a YAML mapping at the top level.")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_layered_yaml(environment: str | None = None) -> dict[str, Any]:
    """Merge default.yaml -> {environment}.yaml -> local.yaml into one dict."""
    config_dir = _find_config_dir()
    environment = environment or os.environ.get("CAREEROS_ENV", DEFAULT_ENVIRONMENT)

    layered: dict[str, Any] = {}
    for filename in ("default.yaml", f"{environment}.yaml", "local.yaml"):
        layered = _deep_merge(layered, _load_yaml(config_dir / filename))
    # The requested environment always wins: it identifies *which* layers
    # were merged, so a stray "environment:" key inside one of those files
    # must not be able to override it.
    layered["environment"] = environment
    return layered


class _YamlSettingsSource(PydanticBaseSettingsSource):
    """A pydantic-settings source backed by the merged YAML layers."""

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        # Required by the ABC; __call__ below does the real work in bulk.
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        return load_layered_yaml()


class Settings(BaseSettings):
    """Root configuration object for CareerOS.

    Extra keys are allowed: later phases (Career Brain, providers, plugins,
    ...) add their own config sections to the same YAML files without this
    foundational model needing to enumerate every field up front.
    """

    model_config = SettingsConfigDict(
        env_prefix="CAREEROS_",
        env_nested_delimiter="__",
        extra="allow",
    )

    environment: str = DEFAULT_ENVIRONMENT
    debug: bool = False
    log_level: str = "INFO"
    data_dir: Path = Field(default=Path(".careeros/data"))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Earlier entries win. Explicit constructor kwargs beat env vars,
        # which beat YAML, which beats the secrets-file source.
        return (
            init_settings,
            env_settings,
            _YamlSettingsSource(settings_cls),
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide ``Settings`` singleton, built on first use."""
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached ``Settings`` singleton. Intended for tests."""
    get_settings.cache_clear()
