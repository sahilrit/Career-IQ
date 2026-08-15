"""LearningLabDivision: the facade tying experiments, variants,
outcome recording, metrics, and winner determination together.
"""

from __future__ import annotations

from careeros_learning_lab.experiment import Experiment, ExperimentRepository
from careeros_learning_lab.metrics import VariantMetrics, compute_variant_metrics
from careeros_learning_lab.outcome import OutcomeEvent, OutcomeEventRepository, OutcomeType
from careeros_learning_lab.variant import Variant, VariantRepository
from careeros_learning_lab.winner import determine_winner


class LearningLabDivision:
    def __init__(
        self,
        experiment_repository: ExperimentRepository,
        variant_repository: VariantRepository,
        outcome_repository: OutcomeEventRepository,
    ) -> None:
        self._experiments = experiment_repository
        self._variants = variant_repository
        self._outcomes = outcome_repository

    def create_experiment(self, experiment: Experiment) -> None:
        self._experiments.save(experiment)

    def add_variant(self, variant: Variant) -> None:
        self._variants.save(variant)

    def record_outcome(self, event: OutcomeEvent) -> None:
        self._outcomes.save(event)

    def metrics_for_variant(self, variant_id: str) -> VariantMetrics:
        return compute_variant_metrics(variant_id, self._outcomes.list_for_variant(variant_id))

    def metrics_for_experiment(self, experiment_id: str) -> dict[str, VariantMetrics]:
        variants = self._variants.list_for_experiment(experiment_id)
        return {variant.id: self.metrics_for_variant(variant.id) for variant in variants}

    def winner_for_experiment(
        self,
        experiment_id: str,
        *,
        primary_outcome: OutcomeType = OutcomeType.RESPONSE,
        min_sample_size: int = 5,
    ) -> str | None:
        metrics_by_variant = self.metrics_for_experiment(experiment_id)
        return determine_winner(
            metrics_by_variant, primary_outcome=primary_outcome, min_sample_size=min_sample_size
        )
