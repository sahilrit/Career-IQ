"""Working memory: short-lived, in-process scratch space for agents.

Not persisted and not authoritative — it's where an agent keeps track of
what it's doing *right now* (e.g. "currently researching company X").
Anything worth keeping past the current run belongs in Career Brain or a
``HistoryLog`` instead.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float | None


class WorkingMemory:
    """A TTL-aware key-value store, scoped to a single process/run.

    Accepts an injectable ``clock`` (defaults to ``time.monotonic``) so
    TTL expiry can be tested without real sleeps.
    """

    def __init__(self, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._entries: dict[str, _Entry] = {}

    def set(self, key: str, value: Any, *, ttl_seconds: float | None = None) -> None:
        expires_at = self._clock() + ttl_seconds if ttl_seconds is not None else None
        self._entries[key] = _Entry(value=value, expires_at=expires_at)

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._entries.get(key)
        if entry is None:
            return default
        if entry.expires_at is not None and self._clock() >= entry.expires_at:
            del self._entries[key]
            return default
        return entry.value

    def delete(self, key: str) -> None:
        self._entries.pop(key, None)

    def clear(self) -> None:
        self._entries.clear()

    def keys(self) -> list[str]:
        self._evict_expired()
        return list(self._entries.keys())

    def _evict_expired(self) -> None:
        now = self._clock()
        expired = [
            key
            for key, entry in self._entries.items()
            if entry.expires_at is not None and now >= entry.expires_at
        ]
        for key in expired:
            del self._entries[key]
