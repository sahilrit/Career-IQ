"""IntelligenceNetworkDivision: the facade tying consent-gated signal
contribution and cross-tenant aggregation together. Every read this
division exposes operates only on already-anonymous
``SignalContribution`` records — there is no method here, and no way
to add one, that accepts or returns a workspace's private Career Brain.
"""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_intelligence_network.insights import NetworkInsight, aggregate_signals
from careeros_intelligence_network.signals import (
    SignalCategory,
    SignalContribution,
    SignalContributionRepository,
    contribute_signal,
)
from careeros_trust_layer import ConsentRepository


class IntelligenceNetworkDivision:
    def __init__(self, store: DocumentStore) -> None:
        self._signals = SignalContributionRepository(store)
        self._consent = ConsentRepository(store)

    def contribute(
        self, *, user_id: str, category: SignalCategory, label: str, weight: float = 1.0
    ) -> SignalContribution:
        return contribute_signal(
            self._signals,
            self._consent,
            user_id=user_id,
            category=category,
            label=label,
            weight=weight,
        )

    def insights_for_category(self, category: SignalCategory) -> NetworkInsight:
        return aggregate_signals(self._signals.list_all(), category=category)
