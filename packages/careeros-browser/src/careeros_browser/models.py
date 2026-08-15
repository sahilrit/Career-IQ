"""Browser health reporting."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BrowserHealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class BrowserHealth(BaseModel):
    status: BrowserHealthStatus
    detail: str = ""
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
