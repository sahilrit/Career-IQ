"""careeros_opportunity_prediction: the Opportunity Prediction Engine.

Predicts likely demand from real company signals before an opportunity
is ever posted, and tracks positioning progress:

    Signal detected -> Demand predicted -> Researched
      -> Decision maker identified -> Relationship started -> Positioned
"""

from careeros_opportunity_prediction.decision_maker import DecisionMaker, DecisionMakerRepository
from careeros_opportunity_prediction.demand_score import (
    DISCLAIMER,
    PredictedDemandScore,
    calculate_predicted_demand,
)
from careeros_opportunity_prediction.exceptions import OpportunityPredictionError
from careeros_opportunity_prediction.hiring_velocity import compute_hiring_velocity_signal
from careeros_opportunity_prediction.opportunity_prediction_division import (
    OpportunityPredictionDivision,
)
from careeros_opportunity_prediction.pipeline_stage import (
    PredictionProgress,
    PredictionProgressRepository,
    PredictionStage,
)
from careeros_opportunity_prediction.signal import (
    PredictionSignal,
    PredictionSignalRepository,
    SignalType,
)

__all__ = [
    "DISCLAIMER",
    "DecisionMaker",
    "DecisionMakerRepository",
    "OpportunityPredictionDivision",
    "OpportunityPredictionError",
    "PredictedDemandScore",
    "PredictionProgress",
    "PredictionProgressRepository",
    "PredictionSignal",
    "PredictionSignalRepository",
    "PredictionStage",
    "SignalType",
    "calculate_predicted_demand",
    "compute_hiring_velocity_signal",
]
