"""Shared Streamlit runtime helpers: a cached DocumentStore connection
every page reuses, resolved from ``CAREEROS_DATA_DIR`` (matching the
CLI's ``--data-dir`` default) or ``DEFAULT_DATA_DIR`` — so the
dashboard reads the same local database the CLI and Runtime write to.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from careeros_common import DocumentStore
from careeros_dashboard.data_access import DEFAULT_DATA_DIR, open_store


def resolve_data_dir() -> Path:
    return Path(os.environ.get("CAREEROS_DATA_DIR", str(DEFAULT_DATA_DIR)))


@st.cache_resource
def _cached_store(data_dir: str) -> DocumentStore:
    return open_store(data_dir)


def get_store() -> DocumentStore:
    """Cached per data dir — not per call — so a different
    ``CAREEROS_DATA_DIR`` (e.g. between test runs in the same process)
    never returns a stale connection to the wrong database.
    """
    return _cached_store(str(resolve_data_dir()))
