"""Runtime health snapshot."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class RuntimeHealth(BaseModel):
    running: bool
    worker_pool_size: int
    alive_workers: int
    tasks_run: int
    tasks_failed: int
    registered_jobs: list[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
