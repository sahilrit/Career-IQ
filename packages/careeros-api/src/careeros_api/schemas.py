"""Request/response models for the API. Kept separate from domain models
so the HTTP contract can evolve without touching domain packages."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
