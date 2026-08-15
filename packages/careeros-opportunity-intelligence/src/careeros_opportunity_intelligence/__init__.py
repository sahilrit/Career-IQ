"""careeros_opportunity_intelligence: "find jobs" becomes "find
opportunities" — a unifying Opportunity abstraction over employment and
freelance postings, unified scoring, lightweight client CRM, and
freelance proposal generation.
"""

from careeros_opportunity_intelligence.client import Client, ClientRepository, RelationshipStage
from careeros_opportunity_intelligence.opportunity import (
    Opportunity,
    OpportunityKind,
    from_gig_posting,
    from_job_posting,
)
from careeros_opportunity_intelligence.proposal import ProposalGenerator, TemplateProposalGenerator
from careeros_opportunity_intelligence.scoring import score_opportunity

__all__ = [
    "Client",
    "ClientRepository",
    "Opportunity",
    "OpportunityKind",
    "ProposalGenerator",
    "RelationshipStage",
    "TemplateProposalGenerator",
    "from_gig_posting",
    "from_job_posting",
    "score_opportunity",
]
