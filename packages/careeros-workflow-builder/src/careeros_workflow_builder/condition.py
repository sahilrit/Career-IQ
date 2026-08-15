"""Condition: the "WHEN" half of a no-code rule — a comparison against
one field of an event's payload. A missing field or a type mismatch
between the field and the comparison value both evaluate to False
rather than raising, so a malformed or partial event never crashes the
engine — it just doesn't match.
"""

from __future__ import annotations

import operator as operator_module
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ComparisonOperator(StrEnum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"


_OPERATORS: dict[ComparisonOperator, Callable[[Any, Any], bool]] = {
    ComparisonOperator.GT: operator_module.gt,
    ComparisonOperator.GTE: operator_module.ge,
    ComparisonOperator.LT: operator_module.lt,
    ComparisonOperator.LTE: operator_module.le,
    ComparisonOperator.EQ: operator_module.eq,
    ComparisonOperator.NEQ: operator_module.ne,
}


class Condition(BaseModel):
    field: str = Field(
        description="Dot-path into the event payload, e.g. 'score' or 'company.industry'."
    )
    operator: ComparisonOperator
    value: float | str | bool


def evaluate_condition(condition: Condition, payload: dict[str, Any]) -> bool:
    actual = _extract_field(payload, condition.field)
    if actual is None:
        return False
    try:
        return _OPERATORS[condition.operator](actual, condition.value)
    except TypeError:
        return False


def _extract_field(payload: dict[str, Any], field: str) -> Any:
    current: Any = payload
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
