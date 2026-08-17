"""Shared Streamlit runtime helpers: a cached DocumentStore connection
every page reuses, resolved from ``CAREEROS_DATA_DIR`` (matching the
CLI's ``--data-dir`` default) or ``DEFAULT_DATA_DIR`` — so the
dashboard reads the same local database the CLI and Runtime write to.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st

from careeros_common import database_url
from careeros_common import open_store as open_configured_store
from careeros_dashboard.data_access import DEFAULT_DATA_DIR


def resolve_data_dir() -> Path:
    return Path(os.environ.get("CAREEROS_DATA_DIR", str(DEFAULT_DATA_DIR)))


@st.cache_resource
def _cached_store(cache_key: str) -> Any:
    # Postgres when CAREEROS_DATABASE_URL is set, else SQLite — the factory
    # reads the environment; cache_key just keys the cache to the target DB.
    return open_configured_store()


def get_store() -> Any:
    """Cached per target database — not per call — so a different
    ``CAREEROS_DATABASE_URL`` / ``CAREEROS_DATA_DIR`` (e.g. between test
    runs in the same process) never returns a stale connection.
    """
    return _cached_store(database_url() or str(resolve_data_dir()))
