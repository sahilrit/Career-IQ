"""careeros_beta: Beta Release.

The first real SaaS MVP milestone: a genuine readiness check across
the required subsystems (Career Brain, Opportunity Discovery, Job
Applications, Freelance Opportunities, Autonomous Execution, CRM,
Interview Preparation, Calendar, Dashboard — all already shipped in
earlier phases) and a capacity-limited invite cohort for starting with
a limited number of users.
"""

from careeros_beta.beta_division import BetaDivision
from careeros_beta.cohort import (
    BetaCohortRepository,
    BetaInvite,
    InviteStatus,
    accept_invite,
    invite_to_beta,
    is_admitted,
    revoke_invite,
)
from careeros_beta.exceptions import BetaCohortFullError, BetaError
from careeros_beta.platform_components import DEFAULT_BETA_COMPONENTS
from careeros_beta.readiness import BetaReadinessReport, ComponentReadiness, verify_beta_readiness

__all__ = [
    "DEFAULT_BETA_COMPONENTS",
    "BetaCohortFullError",
    "BetaCohortRepository",
    "BetaDivision",
    "BetaError",
    "BetaInvite",
    "BetaReadinessReport",
    "ComponentReadiness",
    "InviteStatus",
    "accept_invite",
    "invite_to_beta",
    "is_admitted",
    "revoke_invite",
    "verify_beta_readiness",
]
