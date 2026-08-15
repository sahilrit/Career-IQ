"""ReviewCheckResult: the shape every governance check reports through,
so the review report can combine checks from very different sources
(manifest authoring quality, permission policy, dependency resolution,
a real build smoke-test) uniformly.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class CheckSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ReviewCheckResult(BaseModel):
    check_name: str
    severity: CheckSeverity
    passed: bool
    detail: str = ""
