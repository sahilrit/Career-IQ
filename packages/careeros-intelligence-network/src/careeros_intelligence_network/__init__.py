"""careeros_intelligence_network: the CareerOS Intelligence Network.

Aggregates anonymous, consented, non-personal performance signals
across the platform — which resume structures work, which outreach
patterns work, which skills are growing, which industries are hiring,
which freelance niches are growing — into general strategy insights.

``SignalContribution`` has no user_id, workspace_id, or any other
identity-linked field in its schema, and ``contribute_signal`` requires
active Phase 45 consent before writing one. One customer's private
Career Brain can never reach this package's storage, by construction.
"""

from careeros_intelligence_network.exceptions import (
    ConsentRequiredError,
    IntelligenceNetworkError,
)
from careeros_intelligence_network.insights import (
    LabelRanking,
    NetworkInsight,
    aggregate_signals,
)
from careeros_intelligence_network.network_division import IntelligenceNetworkDivision
from careeros_intelligence_network.signals import (
    SignalCategory,
    SignalContribution,
    SignalContributionRepository,
    contribute_signal,
)

__all__ = [
    "ConsentRequiredError",
    "IntelligenceNetworkDivision",
    "IntelligenceNetworkError",
    "LabelRanking",
    "NetworkInsight",
    "SignalCategory",
    "SignalContribution",
    "SignalContributionRepository",
    "aggregate_signals",
    "contribute_signal",
]
