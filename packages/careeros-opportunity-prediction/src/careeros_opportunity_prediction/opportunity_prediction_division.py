"""OpportunityPredictionDivision: the facade tying signals, predicted
demand, decision-maker identification, and pipeline progress together.
"""

from __future__ import annotations

from careeros_opportunity_prediction.decision_maker import DecisionMaker, DecisionMakerRepository
from careeros_opportunity_prediction.demand_score import (
    PredictedDemandScore,
    calculate_predicted_demand,
)
from careeros_opportunity_prediction.pipeline_stage import (
    PredictionProgress,
    PredictionProgressRepository,
    PredictionStage,
)
from careeros_opportunity_prediction.signal import PredictionSignal, PredictionSignalRepository


class OpportunityPredictionDivision:
    def __init__(
        self,
        signal_repository: PredictionSignalRepository,
        decision_maker_repository: DecisionMakerRepository,
        progress_repository: PredictionProgressRepository,
    ) -> None:
        self._signals = signal_repository
        self._decision_makers = decision_maker_repository
        self._progress = progress_repository

    def record_signal(self, signal: PredictionSignal) -> None:
        self._signals.save(signal)
        self._progress.mark_complete(signal.company_id, PredictionStage.SIGNAL_DETECTED)

    def predict_demand(self, company_id: str) -> PredictedDemandScore:
        signals = self._signals.list_for_company(company_id)
        score = calculate_predicted_demand(company_id, signals)
        if score.score > 0:
            self._progress.mark_complete(company_id, PredictionStage.DEMAND_PREDICTED)
        return score

    def mark_researched(self, company_id: str) -> PredictionProgress:
        return self._progress.mark_complete(company_id, PredictionStage.RESEARCHED)

    def identify_decision_maker(self, decision_maker: DecisionMaker) -> None:
        self._decision_makers.save(decision_maker)
        self._progress.mark_complete(
            decision_maker.company_id, PredictionStage.DECISION_MAKER_IDENTIFIED
        )

    def mark_relationship_started(self, company_id: str) -> PredictionProgress:
        return self._progress.mark_complete(company_id, PredictionStage.RELATIONSHIP_STARTED)

    def mark_positioned(self, company_id: str) -> PredictionProgress:
        return self._progress.mark_complete(company_id, PredictionStage.POSITIONED)

    def progress_for(self, company_id: str) -> PredictionProgress:
        return self._progress.load(company_id)
