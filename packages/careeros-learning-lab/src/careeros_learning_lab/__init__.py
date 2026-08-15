"""careeros_learning_lab: the AI Learning Lab.

A/B experiments across content generated elsewhere in the platform —
resume, email, LinkedIn, portfolio, proposal, subject line — measuring
real outcomes (response, interview, offer, client conversion, revenue)
to learn what works best.
"""

from careeros_learning_lab.exceptions import LearningLabError
from careeros_learning_lab.experiment import (
    Experiment,
    ExperimentRepository,
    ExperimentStatus,
    ExperimentType,
)
from careeros_learning_lab.learning_lab_division import LearningLabDivision
from careeros_learning_lab.metrics import VariantMetrics, compute_variant_metrics
from careeros_learning_lab.outcome import OutcomeEvent, OutcomeEventRepository, OutcomeType
from careeros_learning_lab.variant import Variant, VariantRepository
from careeros_learning_lab.winner import DISCLAIMER, determine_winner

__all__ = [
    "DISCLAIMER",
    "Experiment",
    "ExperimentRepository",
    "ExperimentStatus",
    "ExperimentType",
    "LearningLabDivision",
    "LearningLabError",
    "OutcomeEvent",
    "OutcomeEventRepository",
    "OutcomeType",
    "Variant",
    "VariantMetrics",
    "VariantRepository",
    "compute_variant_metrics",
    "determine_winner",
]
