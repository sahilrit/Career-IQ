"""The canonical local data directory: the same ``.careeros/data``
default the CLI (Phase 15) and Dashboard (Phase 43) already use, so
every entry point into a self-hosted install agrees on where the
SQLite database lives.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_DATA_DIR = Path(".careeros/data")


def ensure_data_dir(data_dir: Path | str = DEFAULT_DATA_DIR) -> Path:
    resolved = Path(data_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
