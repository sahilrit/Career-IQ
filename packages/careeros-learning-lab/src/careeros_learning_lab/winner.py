"""Winner determination: the simplest honest thing this can do —
compare real rates across variants that have enough samples to be worth
comparing. This is raw rate comparison, not a statistical significance
test; flagged as such so a two-sample lucky streak doesn't get treated
as proof.
"""

from __future__ import annotations

from careeros_learning_lab.metrics import VariantMetrics
from careeros_learning_lab.outcome import OutcomeType

DISCLAIMER = (
    "Based on raw rate comparison over collected samples — not a statistical significance test."
)
_DEFAULT_MIN_SAMPLE_SIZE = 5


def determine_winner(
    metrics_by_variant: dict[str, VariantMetrics],
    *,
    primary_outcome: OutcomeType = OutcomeType.RESPONSE,
    min_sample_size: int = _DEFAULT_MIN_SAMPLE_SIZE,
) -> str | None:
    eligible = {
        variant_id: metrics
        for variant_id, metrics in metrics_by_variant.items()
        if metrics.sent_count >= min_sample_size
    }

    scored = {
        variant_id: score
        for variant_id, metrics in eligible.items()
        if (score := metrics.score_for(primary_outcome)) is not None
    }
    if not scored:
        return None

    return max(scored, key=lambda variant_id: scored[variant_id])
