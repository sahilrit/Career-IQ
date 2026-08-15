"""The marketplace's seed AI skills — every ``is_available=True`` entry
points at a real package already shipped in an earlier phase; nothing
here claims intelligence that doesn't actually exist yet.
"""

from __future__ import annotations

from careeros_skill_marketplace.skill_listing import AISkillCategory, AISkillListing

SEED_SKILLS: list[AISkillListing] = [
    AISkillListing(
        skill_id="resume-optimization",
        name="Resume Optimization",
        category=AISkillCategory.RESUME_OPTIMIZATION,
        description="Resume/cover-letter/answers generation from Career Brain, nothing fabricated.",
        source_package="careeros-application-engine",
        is_available=True,
    ),
    AISkillListing(
        skill_id="company-intelligence",
        name="Company Intelligence",
        category=AISkillCategory.COMPANY_INTELLIGENCE,
        description="Company research from real, user-verifiable sources — no invented facts.",
        source_package="careeros-interview-intelligence",
        is_available=True,
    ),
    AISkillListing(
        skill_id="meta-ads-audit",
        name="Meta Ads Audit",
        category=AISkillCategory.META_ADS_AUDIT,
        description="Creative/messaging/landing-page/offer checks against real ad creatives.",
        source_package="careeros-audit-proposal-engine",
        is_available=True,
    ),
    AISkillListing(
        skill_id="shopify-cro-audit",
        name="Shopify CRO Audit",
        category=AISkillCategory.SHOPIFY_CRO_AUDIT,
        description="UX/CRO/checkout/trust/mobile signals read off a real live storefront.",
        source_package="careeros-audit-proposal-engine",
        is_available=True,
    ),
    AISkillListing(
        skill_id="interview-preparation",
        name="Interview Preparation",
        category=AISkillCategory.INTERVIEW_PREPARATION,
        description=(
            "STAR questions and an H48/H24/H2 briefing schedule from real Career Brain data."
        ),
        source_package="careeros-interview-intelligence",
        is_available=True,
    ),
    AISkillListing(
        skill_id="salary-analysis",
        name="Salary Analysis",
        category=AISkillCategory.SALARY_ANALYSIS,
        description="Opportunity Value beyond salary, plus negotiation talking points.",
        source_package="careeros-offer-negotiation",
        is_available=True,
    ),
    AISkillListing(
        skill_id="proposal-optimization",
        name="Proposal Optimization",
        category=AISkillCategory.PROPOSAL_OPTIMIZATION,
        description="Freelance proposal generation, with A/B testing against real outcomes.",
        source_package="careeros-opportunity-intelligence",
        is_available=True,
    ),
    AISkillListing(
        skill_id="linkedin-optimization",
        name="LinkedIn Optimization",
        category=AISkillCategory.LINKEDIN_OPTIMIZATION,
        description="Not yet implemented — planned profile/content optimization skill.",
        source_package="",
        is_available=False,
    ),
    AISkillListing(
        skill_id="career-strategy",
        name="Career Strategy",
        category=AISkillCategory.CAREER_STRATEGY,
        description="Combines every signal into ranked recommendations and a direction summary.",
        source_package="careeros-career-intelligence",
        is_available=True,
    ),
]
