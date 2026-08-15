"""careeros_audit_proposal_engine: deep Shopify/Meta Ads audits, ROI
estimation, and deliverable generation (Loom script, PDF, email,
LinkedIn message, proposal) for the Client Acquisition pipeline.
"""

from careeros_audit_proposal_engine.audit_proposal_engine import (
    AuditDeliverables,
    AuditProposalEngine,
    from_baseline_finding,
)
from careeros_audit_proposal_engine.exceptions import AuditProposalEngineError
from careeros_audit_proposal_engine.finding import Finding
from careeros_audit_proposal_engine.meta_ads_audit import (
    AdCreative,
    ManualMetaAdsAuditProvider,
    MetaAdsAuditCategory,
    MetaAdsAuditProvider,
    audit_meta_ads,
)
from careeros_audit_proposal_engine.outputs import (
    generate_audit_pdf,
    render_audit_email,
    render_linkedin_message,
    render_loom_script,
    render_proposal,
)
from careeros_audit_proposal_engine.roi_estimate import (
    DISCLAIMER,
    ROIEstimate,
    ROIInputs,
    estimate_roi,
)
from careeros_audit_proposal_engine.shopify_audit import (
    ShopifyAuditCategory,
    ShopifyAuditor,
    ShopifyStorefrontRules,
)

__all__ = [
    "DISCLAIMER",
    "AdCreative",
    "AuditDeliverables",
    "AuditProposalEngine",
    "AuditProposalEngineError",
    "Finding",
    "ManualMetaAdsAuditProvider",
    "MetaAdsAuditCategory",
    "MetaAdsAuditProvider",
    "ROIEstimate",
    "ROIInputs",
    "ShopifyAuditCategory",
    "ShopifyAuditor",
    "ShopifyStorefrontRules",
    "audit_meta_ads",
    "estimate_roi",
    "from_baseline_finding",
    "generate_audit_pdf",
    "render_audit_email",
    "render_linkedin_message",
    "render_loom_script",
    "render_proposal",
]
