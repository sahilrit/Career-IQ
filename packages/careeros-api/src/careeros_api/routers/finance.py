"""Financial Intelligence: track income across salary, freelance, and
client revenue — with totals, monthly breakdown, and trend."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_financial_intelligence import (
    FinancialIntelligenceDivision,
    IncomeRecord,
    IncomeRepository,
    IncomeSource,
)

router = APIRouter(prefix="/finance", tags=["finance"])


class IncomeCreateRequest(BaseModel):
    source: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    amount: float
    received_date: str = Field(min_length=1)
    hours_worked: float | None = None


def _division(context: Context) -> FinancialIntelligenceDivision:
    return FinancialIntelligenceDivision(IncomeRepository(context.store))


@router.get("/income")
def income(context: Context) -> dict[str, Any]:
    division = _division(context)
    records = IncomeRepository(context.store).list_all()
    trend = division.income_trend()
    return {
        "records": [
            {
                "id": record.id,
                "source": record.source.value,
                "source_name": record.source_name,
                "amount": record.amount,
                "received_date": record.received_date.isoformat(),
            }
            for record in records
        ],
        "total": division.total_income(),
        "monthly": [
            {"year": total.year, "month": total.month, "total": total.total}
            for total in division.monthly_totals()
        ],
        "trend": trend.value if trend is not None else None,
    }


@router.post("/income", status_code=status.HTTP_201_CREATED)
def add_income(body: IncomeCreateRequest, context: Context) -> dict[str, Any]:
    try:
        source = IncomeSource(body.source)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown source") from error
    try:
        received = date.fromisoformat(body.received_date)
    except ValueError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "received_date must be ISO (YYYY-MM-DD)"
        ) from error
    record = IncomeRecord(
        source=source,
        source_name=body.source_name,
        amount=body.amount,
        received_date=received,
        hours_worked=body.hours_worked,
    )
    _division(context).add_income(record)
    return {"id": record.id, "amount": record.amount}
