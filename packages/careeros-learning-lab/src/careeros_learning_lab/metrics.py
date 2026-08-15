"""VariantMetrics: real counts and rates computed directly from a
variant's OutcomeEvents. A rate is ``None`` (not zero) when there's no
sent count to divide by — silence about missing data instead of a
misleading 0%.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_learning_lab.outcome import OutcomeEvent, OutcomeType


class VariantMetrics(BaseModel):
    variant_id: str
    sent_count: int
    response_count: int
    interview_count: int
    offer_count: int
    client_conversion_count: int
    total_revenue: float

    @property
    def response_rate(self) -> float | None:
        return self.response_count / self.sent_count if self.sent_count else None

    @property
    def interview_rate(self) -> float | None:
        return self.interview_count / self.sent_count if self.sent_count else None

    @property
    def offer_rate(self) -> float | None:
        return self.offer_count / self.sent_count if self.sent_count else None

    @property
    def client_conversion_rate(self) -> float | None:
        return self.client_conversion_count / self.sent_count if self.sent_count else None

    def score_for(self, outcome_type: OutcomeType) -> float | None:
        return {
            OutcomeType.SENT: float(self.sent_count),
            OutcomeType.RESPONSE: self.response_rate,
            OutcomeType.INTERVIEW: self.interview_rate,
            OutcomeType.OFFER: self.offer_rate,
            OutcomeType.CLIENT_CONVERSION: self.client_conversion_rate,
            OutcomeType.REVENUE: self.total_revenue,
        }[outcome_type]


def compute_variant_metrics(variant_id: str, events: list[OutcomeEvent]) -> VariantMetrics:
    def count(outcome_type: OutcomeType) -> int:
        return sum(1 for event in events if event.outcome_type == outcome_type)

    revenue = sum(event.value for event in events if event.outcome_type == OutcomeType.REVENUE)

    return VariantMetrics(
        variant_id=variant_id,
        sent_count=count(OutcomeType.SENT),
        response_count=count(OutcomeType.RESPONSE),
        interview_count=count(OutcomeType.INTERVIEW),
        offer_count=count(OutcomeType.OFFER),
        client_conversion_count=count(OutcomeType.CLIENT_CONVERSION),
        total_revenue=revenue,
    )
