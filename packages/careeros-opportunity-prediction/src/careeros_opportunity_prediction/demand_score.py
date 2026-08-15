"""Predicted demand: a transparent, signal-count-driven score — more
independent, real signals means a stronger prediction. Explicitly
flagged as a prediction, not a certainty.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_opportunity_prediction.signal import PredictionSignal

DISCLAIMER = "Prediction only, based on observed signals — not a certainty."
_POINTS_PER_SIGNAL = 12.5
_MAX_SCORE = 100.0


class PredictedDemandScore(BaseModel):
    company_id: str
    score: float
    signal_count: int
    disclaimer: str = DISCLAIMER


def calculate_predicted_demand(
    company_id: str, signals: list[PredictionSignal]
) -> PredictedDemandScore:
    return PredictedDemandScore(
        company_id=company_id,
        score=min(_MAX_SCORE, len(signals) * _POINTS_PER_SIGNAL),
        signal_count=len(signals),
    )
