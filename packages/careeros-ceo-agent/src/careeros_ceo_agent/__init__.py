"""careeros_ceo_agent: the Executive AI / CEO Agent.

Allocates effort across Employment, Freelance, Networking, and
Personal Brand as a transparent, evidence-weighted blend of a baseline
split and real recorded performance — the roadmap's "these percentages
change based on results."
"""

from careeros_ceo_agent.allocation import (
    DEFAULT_BASELINE,
    DISCLAIMER,
    AllocationPlan,
    allocate_resources,
)
from careeros_ceo_agent.allocation_history import AllocationPlanRepository
from careeros_ceo_agent.ceo_agent_division import CEOAgentDivision
from careeros_ceo_agent.exceptions import CeoAgentError
from careeros_ceo_agent.performance_input import (
    PerformanceInput,
    PerformanceInputRepository,
    ResourceCategory,
)

__all__ = [
    "DEFAULT_BASELINE",
    "DISCLAIMER",
    "AllocationPlan",
    "AllocationPlanRepository",
    "CEOAgentDivision",
    "CeoAgentError",
    "PerformanceInput",
    "PerformanceInputRepository",
    "ResourceCategory",
    "allocate_resources",
]
