"""Freelance endpoints: list and add prospect businesses. The website
audit + pitch kit (which needs a headless browser) stays in the
dashboard for now; this exposes the prospect pipeline itself."""

from __future__ import annotations

from fastapi import APIRouter, status

from careeros_api.dependencies import Context
from careeros_api.schemas import ProspectCreateRequest, ProspectResponse
from careeros_client_acquisition import (
    ClientAcquisitionProgressRepository,
    ClientAcquisitionStage,
    Company,
    CompanyRepository,
)

router = APIRouter(prefix="/freelance/prospects", tags=["freelance"])


def _to_response(context: Context, company: Company) -> ProspectResponse:
    stage = ClientAcquisitionProgressRepository(context.store).load(company.id).current_stage
    return ProspectResponse(
        id=company.id,
        name=company.name,
        website=company.website,
        industry=company.industry,
        stage=stage.value if stage else None,
    )


@router.get("", response_model=list[ProspectResponse])
def list_prospects(context: Context) -> list[ProspectResponse]:
    return [
        _to_response(context, company) for company in CompanyRepository(context.store).list_all()
    ]


@router.post("", response_model=ProspectResponse, status_code=status.HTTP_201_CREATED)
def add_prospect(body: ProspectCreateRequest, context: Context) -> ProspectResponse:
    website = body.website.strip()
    if website and not website.startswith(("http://", "https://")):
        website = f"https://{website}"
    company = Company(name=body.name.strip(), website=website, industry=body.industry.strip())
    CompanyRepository(context.store).save(company)
    ClientAcquisitionProgressRepository(context.store).mark_complete(
        company.id, ClientAcquisitionStage.DISCOVERY
    )
    return _to_response(context, company)
