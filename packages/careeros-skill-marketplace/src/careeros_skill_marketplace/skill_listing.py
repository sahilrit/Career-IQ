"""AISkillListing: an intelligence capability the marketplace lists —
distinct from Phase 48's plugin listings, which wrap external service
integrations. A skill listing points at the real CareerOS package that
provides it (or is honestly marked unavailable when none does yet).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AISkillCategory(StrEnum):
    RESUME_OPTIMIZATION = "resume_optimization"
    COMPANY_INTELLIGENCE = "company_intelligence"
    META_ADS_AUDIT = "meta_ads_audit"
    SHOPIFY_CRO_AUDIT = "shopify_cro_audit"
    INTERVIEW_PREPARATION = "interview_preparation"
    SALARY_ANALYSIS = "salary_analysis"
    PROPOSAL_OPTIMIZATION = "proposal_optimization"
    LINKEDIN_OPTIMIZATION = "linkedin_optimization"
    CAREER_STRATEGY = "career_strategy"


class AISkillListing(BaseModel):
    skill_id: str
    name: str
    category: AISkillCategory
    description: str
    source_package: str
    is_available: bool = Field(
        description="True only when a real CareerOS package already provides this skill."
    )
