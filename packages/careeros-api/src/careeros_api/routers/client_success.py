"""Client Success: manage freelance clients — contracts, invoices,
outstanding balances, and lifecycle stage."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_client_success import (
    ClientSuccessDivision,
    Contract,
    ContractRepository,
    DeliverableRepository,
    Invoice,
    InvoiceRepository,
    InvoiceStatus,
    MeetingNoteRepository,
    ReferralRepository,
)
from careeros_opportunity_intelligence import Client, ClientRepository

router = APIRouter(prefix="/clients", tags=["client-success"])


class ClientCreateRequest(BaseModel):
    name: str = Field(min_length=1)


class ContractCreateRequest(BaseModel):
    client_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rate: float = 0.0
    start_date: str = Field(min_length=1)


class InvoiceCreateRequest(BaseModel):
    contract_id: str = Field(min_length=1)
    amount: float
    due_date: str = Field(min_length=1)


def _division(context: Context) -> ClientSuccessDivision:
    store = context.store
    return ClientSuccessDivision(
        ContractRepository(store),
        DeliverableRepository(store),
        MeetingNoteRepository(store),
        InvoiceRepository(store),
        ReferralRepository(store),
    )


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "dates must be ISO format (YYYY-MM-DD)"
        ) from error


@router.get("")
def list_clients(context: Context) -> list[dict[str, Any]]:
    division = _division(context)
    contracts_repo = ContractRepository(context.store)
    result: list[dict[str, Any]] = []
    for client in ClientRepository(context.store).list_all():
        contracts = contracts_repo.list_for_client(client.id)
        stage = division.lifecycle_stage_for(client.id)
        result.append(
            {
                "id": client.id,
                "name": client.name,
                "lifecycle_stage": stage.value if stage is not None else None,
                "contracts": [
                    {
                        "id": contract.id,
                        "title": contract.title,
                        "rate": contract.rate,
                        "status": contract.status.value,
                        "outstanding": division.outstanding_balance_for_contract(contract.id),
                    }
                    for contract in contracts
                ],
            }
        )
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
def add_client(body: ClientCreateRequest, context: Context) -> dict[str, Any]:
    client = Client(name=body.name)
    ClientRepository(context.store).save(client)
    return {"id": client.id, "name": client.name}


@router.post("/contracts", status_code=status.HTTP_201_CREATED)
def add_contract(body: ContractCreateRequest, context: Context) -> dict[str, Any]:
    contract = Contract(
        client_id=body.client_id,
        title=body.title,
        rate=body.rate,
        start_date=_parse_date(body.start_date),
    )
    _division(context).add_contract(contract)
    return {"id": contract.id, "title": contract.title}


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
def add_invoice(body: InvoiceCreateRequest, context: Context) -> dict[str, Any]:
    invoice = Invoice(
        contract_id=body.contract_id,
        amount=body.amount,
        issued_date=date.today(),
        due_date=_parse_date(body.due_date),
        status=InvoiceStatus.SENT,
    )
    _division(context).add_invoice(invoice)
    return {"id": invoice.id, "amount": invoice.amount}
