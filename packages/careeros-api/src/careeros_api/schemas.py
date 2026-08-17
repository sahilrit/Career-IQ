"""Request/response models for the API. Kept separate from domain models
so the HTTP contract can evolve without touching domain packages."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AiKeyRequest(BaseModel):
    api_key: str


class AiStatusResponse(BaseModel):
    has_key: bool
    model: str


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)
    full_name: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"


class ResetRequest(BaseModel):
    email: str


class ResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=1)


class MeResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    workspace_id: str
    role: str
    is_admin: bool


class MessageResponse(BaseModel):
    message: str


class BrainCreateRequest(BaseModel):
    full_name: str = Field(min_length=1)
    email: str = Field(min_length=1)


class SummaryUpdateRequest(BaseModel):
    summary: str = ""


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    proficiency: int = Field(default=3, ge=1, le=5)


class ExperienceCreateRequest(BaseModel):
    company_name: str = Field(min_length=1)
    title: str = Field(min_length=1)
    start_date: str = Field(min_length=1, description="ISO date, e.g. 2024-05-01")
    end_date: str | None = None
    description: str = ""


class SearchRequest(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    remote_only: bool = True
    limit: int = Field(default=100, ge=1, le=500)


class SearchResponse(BaseModel):
    discovered: int
    qualified: int


class GenerateRequest(BaseModel):
    job_url: str = Field(min_length=1)


class ApplicationPackageResponse(BaseModel):
    resume_text: str
    cover_letter: str
    ai_used: bool = False
    ai_error: str | None = None


class OfferCreateRequest(BaseModel):
    company_name: str = Field(min_length=1)
    job_title: str = Field(min_length=1)
    base_salary: float = Field(ge=0)
    bonus: float = Field(default=0, ge=0)
    equity_value: float = Field(default=0, ge=0)
    benefits_value: float = Field(default=0, ge=0)
    remote_policy: str = ""
    stability_score: int = Field(default=3, ge=1, le=5)
    growth_score: int = Field(default=3, ge=1, le=5)
    reputation_score: int = Field(default=3, ge=1, le=5)


class RankedOfferResponse(BaseModel):
    company_name: str
    job_title: str
    base_salary: float
    opportunity_value: float


class ContactCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    role: str = "prospect"
    organization_name: str = ""
    email: str | None = None


class ContactResponse(BaseModel):
    id: str
    name: str
    role: str
    organization_name: str
    stage: str | None
    email: str | None = None


class ProspectCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    website: str = Field(min_length=1)
    industry: str = ""


class ProspectResponse(BaseModel):
    id: str
    name: str
    website: str
    industry: str
    stage: str | None


class PlanInfo(BaseModel):
    tier: str
    name: str
    monthly_price_usd: float
    features: list[str]
    is_current: bool
    checkout_url: str | None


class BillingResponse(BaseModel):
    current_tier: str
    status: str
    plans: list[PlanInfo]


class AutopilotOutcome(BaseModel):
    job_title: str
    company_name: str
    submitted: bool
    reason: str


class AutopilotRunResponse(BaseModel):
    id: str
    ran_at: str
    discovered: int
    submitted: int
    qualified_total: int
    outcomes: list[AutopilotOutcome]


class CustomerResponse(BaseModel):
    name: str
    email: str
    role: str
    workspace_id: str
    plan: str
    status: str
    joined: str


class AdminOverviewResponse(BaseModel):
    accounts: int
    paying_workspaces: int
    mrr: float
    customers: list[CustomerResponse]


class ActivatePlanRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    tier: str = Field(min_length=1)
